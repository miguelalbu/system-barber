# Multi-tenancy com schema por barbearia

**Priority:** high
**Status:** completed
**Espelho no frontend:** `frontend/docs/specs/✅completed_frontend-invite-acceptance.md`
**Referência:** `docs/multi-tenant-architecture-v2.md` (ClaraCRM v2) — esta spec é a tradução dele para
o Navalha, com as divergências listadas abaixo.

## Overview

Troca a base de isolamento do sistema: de **tabelas compartilhadas + `tenant_id` + RLS** (DEC-001)
para **um schema PostgreSQL por barbearia**, no desenho do ClaraCRM v2. O `public` passa a ser só o
schema de controle (catálogo de tenants, chaves e auditoria do control plane); cada barbearia tem o
seu `tenant_<slug>`, com estrutura idêntica e sem nenhuma FK cruzando schemas. Barbearias passam a
nascer **só pelo control plane** (`/core/tenants`, credencial própria `X-Core-Key`), que no futuro é
chamado pelo Core da plataforma a partir da venda de planos.

## Decisões de produto já tomadas

| Parâmetro | Valor |
|---|---|
| Isolamento | schema por barbearia; `public` = controle, sem dado de barbearia |
| Acesso | **subdomínio personalizado por barbearia** (`<slug>.<BASE_DOMAIN>`) e domínio próprio (`custom_domain`) — **diverge do doc §1/§4** (URL única + login por e-mail) |
| Login | e-mail + senha no host da barbearia; e-mail único **por barbearia**; sem diretório global de login |
| Criação de barbearia | só pelo control plane (`X-Core-Key`), por administradores/Core; `POST /auth/register-shop` é removido |
| Senha do dono inicial | nunca no contrato: o provisionamento gera um **convite de primeiro acesso** (uso único, 24 h) |
| Exclusão | só barbearia suspensa, escopo próprio `tenant:destroy`, `confirm` = slug e `exported: true`; a linha do tenant fica `archived` |
| Dados atuais | só desenvolvimento (não há produção): o banco de dev é recriado, sem script de migração de dados (doc §3 não se aplica) |

## Business Rules

### Desenho do banco

- [x] `public` contém só tabelas de controle: `tenants`, `platform_admins`, `core_keys`,
      `provisioning_jobs`, `core_audit_log` e o `alembic_version` do controle.
- [x] Cada barbearia tem `tenant_<slug>` com `units`, `users`, `user_units`, `barbers`,
      `refresh_tokens`, `invites`, os tipos enum próprios (cópia por schema, doc §2) e o próprio
      `alembic_version`.
- [x] Nenhuma FK cruza schemas; tabelas de barbearia não têm mais `tenant_id` nem RLS.

### Nome do schema (fronteira de injeção de DDL)

- [x] Slug = subdomínio: `^[a-z][a-z0-9-]{1,38}[a-z0-9]$` (3–40 caracteres, DNS-safe), sem `--`.
- [x] Reservados: `www, app, api, admin, painel, static, assets, core, docs, public, template, mail`.
- [x] `schema_name = "tenant_" + slug.replace("-", "_")`, gravado em `tenants.schema_name` (`UNIQUE`) e
      lido dali para sempre — nunca recalculado de entrada de usuário.
- [x] Todo nome de schema lido do banco é revalidado (`^tenant_[a-z][a-z0-9_]{1,39}$`) antes de entrar
      num `schema_translate_map` ou em DDL; DDL sempre com o identificador quotado pelo dialeto.

### Contexto e sessões (doc Camadas 1 e 2)

- [x] O tenant de uma request vem **só** do host (subdomínio ou `custom_domain`); `X-Tenant-Slug` só
      com `ENVIRONMENT=dev`. O JWT carrega `tid` e é recusado (403) em outro host.
- [x] As queries são qualificadas por `schema_translate_map` (o equivalente SQLAlchemy da opção
      `schema` do adapter do Prisma): **nenhum `SET search_path` em sessão da aplicação**. Os models
      de barbearia ficam sob o schema-marcador `tenant`: fora de uma sessão de tenant, a query aponta
      para um schema inexistente e falha (testado).
- [x] **Um** pool de conexões; engines finos por schema (`engine.execution_options(...)`), em cache
      limitado.
- [x] SQL cru em tabela de barbearia é proibido sem qualificação explícita pelo schema do tenant.

### Banco endurecido (doc Camada 3)

- [x] A aplicação (`navalha_app`) não tem DDL: só `USAGE` + DML nos schemas e tabelas que usa.
- [x] O provisionamento cria um role `tenant_<slug>` `NOLOGIN`, restrito ao próprio schema, para
      acesso fora de banda (suporte, `pg_dump`, BI). Ele não alcança o `public`.
- [x] Como no doc, `SET LOCAL ROLE` por request **não** é usado: role e schema sairiam do mesmo
      contexto e um bug erraria os dois na mesma direção.

### Ciclo de vida e migrations (doc Camada 6)

- [x] Dois conjuntos de migrations: `alembic/control/` (public) e `alembic/tenant/` (aplicado em
      cada schema). Só migrations backward-compatible (expand/contract) no conjunto de tenant.
- [x] Migrations **saem do boot do container**: rodam por `python -m app.management.migrate`
      (controle, depois cada tenant, sequencial e fail-fast), ou pelo serviço one-shot `migrate` do
      compose.
- [x] `tenants.schema_version` guarda a revisão que o banco diz ter (lida do `alembic_version` do
      schema depois do deploy).
- [x] A API **recusa servir** (503) barbearia cuja versão esteja **atrás** do head do build; versão à
      frente ou ainda não registrada é servida.
- [x] Status do tenant: `provisioning`, `active`, `failed`, `suspended`, `archived`. Só `active` é
      servido. `suspended` → 403 `Assinatura inativa`; `provisioning`/`failed`/versão atrás → 503;
      `archived` ou inexistente → 404.

### Control plane (doc §6)

- [x] Credencial própria: header `X-Core-Key`, guardada como SHA-256, comparada em tempo constante,
      com escopos (`tenant:read`, `tenant:provision`, `tenant:destroy`), `ip_allowlist` opcional,
      revogação e `last_used_at`.
- [x] Toda chamada ao control plane é auditada em `core_audit_log` (inclusive as negadas), com o
      payload **sem segredos**.
- [x] Rate limit por chave (por processo): leitura 240/min, mutação 20/min.
- [x] `POST /core/tenants` valida, grava e devolve **202** com o job; o trabalho acontece depois da
      resposta. Mesmo slug de novo → **200** com o job existente; `Idempotency-Key` repetida → o mesmo
      job. Nunca um segundo schema.
- [x] O job tem passos idempotentes e retomáveis: schema + privilégios padrão → migrations → grants e
      role do tenant → bootstrap (unidade inicial + convite do dono) → `active` + `schema_version`.
- [x] Falha → `failed` com o erro no job; `POST .../retry` retoma. **Nunca** `DROP SCHEMA` automático.
- [x] Campo `password` no corpo é descartado e não aparece na auditoria.
- [x] O link de primeiro acesso é entregue **uma vez** (`GET /core/tenants/{id}` depois do sucesso) e
      apagado na leitura; `POST .../invite` reemite e invalida os convites de dono pendentes.
- [x] Suspender/reativar é instantâneo e reversível. Excluir exige `tenant:destroy`, tenant
      `suspended`, `confirm` igual ao slug e `exported: true`; apaga schema e role e deixa a linha
      `archived`.
- [x] O OpenAPI do control plane não aparece no `/docs` público: fica em `GET /core/openapi.json`,
      atrás da `X-Core-Key`.
- [x] A primeira chave nasce por CLI com credencial de banco (`python -m app.management.core_key`);
      o valor cru aparece uma vez.

### Login e convites (doc §4, adaptado ao host)

- [x] E-mail desconhecido verifica a senha contra um hash argon2 descartável, para igualar o tempo
      de resposta a um e-mail existente; a mensagem é sempre a mesma.
- [x] Aceitar convite é de uso único de verdade: a reivindicação é um `UPDATE ... WHERE accepted_at
      IS NULL` atômico; dois aceites simultâneos resultam em um login criado.
- [x] `POST /team/invites/lookup` descreve um convite válido (nome, e-mail, cargo, validade) **sem
      gastá-lo**, para a tela validar o link antes de pedir a senha.

## Data Contract

```text
Control plane — header X-Core-Key, fora do /docs público
POST   /core/tenants                 tenant:provision  ProvisionIn → 202 ProvisionAccepted | 200 (mesmo slug)
GET    /core/tenants                 tenant:read       → CoreTenantOut[]
GET    /core/tenants/{id}            tenant:read       → CoreTenantDetail {…, job, invite_link (uma vez)}
POST   /core/tenants/{id}/retry      tenant:provision  → 202
POST   /core/tenants/{id}/suspend    tenant:provision  → CoreTenantOut
POST   /core/tenants/{id}/resume     tenant:provision  → CoreTenantOut
POST   /core/tenants/{id}/invite     tenant:provision  → {invite_link}
DELETE /core/tenants/{id}            tenant:destroy    DestroyIn {confirm, exported} → 204
GET    /core/openapi.json            tenant:read       → OpenAPI só do control plane

ProvisionIn: slug, name, owner {name, email}, unit_name?, plan?, custom_domain?, external_tenant_id?
Header opcional: Idempotency-Key

Identidade (mudanças)
REMOVIDO  POST /auth/register-shop
NOVO      POST /team/invites/lookup   público  {token} → InviteLookupOut {name, email, role, expires_at}
TenantOut.status: provisioning | active | failed | suspended | archived   (antes: trial | active | suspended | canceled)
```

### Banco de dados

```text
public.tenants            id, slug UQ, schema_name UQ, name, custom_domain UQ, plan, status,
                          schema_version, external_tenant_id UQ null, created_at, updated_at
public.core_keys          id, name, key_hash UQ, scopes text[], ip_allowlist text[], revoked_at,
                          last_used_at, created_at
public.provisioning_jobs  id, tenant_id FK, idempotency_key UQ null, status, step, log, error,
                          setup_token_once, created_at, updated_at, finished_at
public.core_audit_log     id, core_key_id null, action, target, payload jsonb, result, ip, created_at
public.platform_admins    (inalterada)
tenant_<slug>.*           units, users, user_units, barbers, refresh_tokens, invites — sem tenant_id
```

## Permissões

Sem permissão nova de barbearia. O control plane usa escopos de `X-Core-Key`, não o RBAC.

## Acceptance Criteria

- [x] Testes de isolamento com dois schemas reais: mesmo e-mail nas duas barbearias, token não cruza,
      equipe só vê a própria, e-mail de A com senha de B falha, dados ficam fisicamente no schema
      certo e nada de barbearia no `public`.
- [x] Testes de ciclo de vida: suspensa recusa login mesmo com a senha certa; `provisioning`, `failed`
      e versão atrás → 503; arquivada → 404.
- [x] Testes do control plane: sem chave/chave errada/revogada → 401 indistinguível; escopo errado →
      403; auditoria registrada inclusive nas negadas; `password` descartado; idempotência por slug e
      por `Idempotency-Key`; convite entregue uma vez; reemissão invalida o anterior; exclusão com os
      quatro portões e o schema sumindo do `pg_namespace`.
- [x] Teste de guarda do nome de schema (válidos, reservados, injeção, tamanho, valor malicioso vindo
      do banco).
- [x] Teste de que o role de runtime não tem DDL.
- [x] Teste de aceite de convite concorrente (um sucesso, um 400).
- [x] Snapshots de contrato regenerados com o diff descrito nas Notes.
- [x] `make check` verde; CI com migrations de controle + checagem do conjunto de tenant.
- [x] Ambiente de dev recriado e uma barbearia `demo` provisionada pelo control plane, com login real.

## Dependencies

- Nenhuma dependência nova de runtime.
- Supersede DEC-001; altera DEC-002 e DEC-003 (ver `memory/decisions.md`, DEC-011 a DEC-014).

## Notes

- **Fora do escopo agora, mas parte do desenho** (entram com os módulos que criam a necessidade):
  envelope encryption com DEK por tenant (doc Camada 4) — hoje não há segredo de barbearia guardado;
  roteamento do WhatsApp (`WhatsappNumberRoute`, App Secret global — doc §5) e API keys por tenant —
  entram com o módulo de conversas; particionamento de storage/eventos/rate limit por tenant (doc
  Camada 5) — entram com upload de mídia e eventos.
- O registry de tenants não tem cache (uma consulta por request ao `public.tenants`); se virar
  gargalo, cache com TTL curto e invalidação explícita, como no doc.
- O control plane roda no mesmo processo da API e usa a credencial de migrator só para DDL
  (`DATABASE_URL_MIGRATIONS`); em produção o migrator precisa de `CREATEROLE` (ISS-013).

### Divergências e descobertas da implementação (2026-11-05)

- **Schema-marcador invertido.** A primeira versão deixava as tabelas de barbearia sem schema e as
  de controle com `schema="public"` explícito; o `alembic check` do controle acusava diferença
  (o Alembic reflete o schema padrão como `None`, não como `public`, em enums e FKs). Invertido: o
  controle fica sem schema (resolve para `public` pelo search_path padrão do role) e as tabelas de
  barbearia ganham o marcador `tenant`. Ganho de segurança: fora de uma sessão de tenant, uma
  tabela de barbearia **falha** em vez de cair no `public`.
- **Migrations de tenant usam `search_path`, e só elas.** É a receita do Alembic para schema por
  tenant; vale porque a conexão é privada (NullPool) e morre com a execução. O `env.py` compara os
  models contra uma cópia do metadata sem schema.
- **Versão "atrás"** é calculada pela cadeia do Alembic (revisão é ancestral do head), não por
  comparação de strings como no doc (lá os nomes eram timestamps).
- **Job no mesmo processo** (`BackgroundTask` depois da resposta); queda no meio → `retry` (ISS-014).
  O Alembic roda numa thread, um schema por vez (lock), porque guarda contexto em globais.
- **Mensagem de convite unificada**: "Convite inválido, expirado ou já utilizado" (antes eram duas
  mensagens — distinguir expirado de usado não ajuda quem recebeu o link).
- **Link de convite** usa o domínio próprio da barbearia quando ela tem um.
- **Dev:** o volume não foi recriado (remoção negada por ser destrutiva); o `public` antigo virou o
  schema `legacy_rls_v1` (ISS-011). A `demo` foi reprovisionada pelo control plane; o primeiro link
  se perdeu num parse de shell e foi reemitido por `POST .../invite` (ISS-017) — o caminho de
  recuperação funcionou como desenhado.
- **Resultado:** 85 testes (21 de comportamento herdados, sem mudar o que afirmam, + 54 novos de
  tenancy, control plane e endurecimento + contratos); `alembic check` limpo nos dois conjuntos;
  job de CI simulado num Postgres zerado.

### Diff dos snapshots de contrato (intencional)

- `openapi.json`: sai `POST /auth/register-shop` (`RegisterShop`, `RegistrationOut`); entra
  `POST /team/invites/lookup` (`InviteLookupIn/Out`); `TenantStatus` passa a `provisioning, active,
  failed, suspended, archived`; descrição do app.
- `routes.json`: as 9 rotas `/core/*`, cada uma com `core(<escopo>)`; `accept` e `lookup` usam a
  sessão do tenant; `PATCH /tenant` usa a sessão de controle.
- `core_openapi.json` (novo): o contrato privado do control plane.
- `db_schema.json`: separado em controle e tenant; tabelas de barbearia sem `tenant_id`.
