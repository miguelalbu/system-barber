# Decisions

Architecture Decision Records (ADR). **Só acrescentar** — nunca editar uma entrada passada. Para
mudar uma decisão, crie outra e marque a antiga como `superseded by DEC-NNN`.

<!-- Modelo:

## DEC-NNN — Título

**Date:** AAAA-MM-DD
**Status:** accepted | superseded by DEC-NNN

**Context:** Que problema exigiu a decisão?

**Options considered:**
1. Opção A — prós e contras
2. Opção B — prós e contras

**Decision:** O que foi escolhido e por quê.

**Consequences:** Que trade-offs foram aceitos.
-->

## DEC-001 — Multi-tenant em banco compartilhado com Row-Level Security

**Date:** 2026-11-05 (registro retroativo; a decisão é da migration 0001)
**Status:** superseded by DEC-011

**Context:** SaaS de barbearias: muitas barbearias pequenas, dados que nunca podem vazar entre elas,
e a porta aberta para uma barbearia grande ganhar banco próprio no futuro.

**Options considered:**
1. Banco por tenant — isolamento máximo, custo e operação altos desde o primeiro cliente.
2. Schema por tenant — migrations multiplicadas, pool de conexões complicado.
3. Banco compartilhado + `tenant_id` + RLS — um banco, isolamento garantido pelo Postgres.

**Decision:** Opção 3. Toda tabela de barbearia tem `tenant_id` e policy
`tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid` com `ENABLE` + `FORCE`. A
aplicação conecta com `navalha_app` (sem SUPERUSER/BYPASSRLS); migrations com o dono do schema. O
tenant é fixado por transação com `set_config(..., true)`.

**Consequences:** Esquecer um filtro devolve zero linhas, nunca dado de outra barbearia. Exige
disciplina: toda tabela nova precisa da policy na migration, e o `true` do `set_config` não pode
sumir (com `SET` simples, o tenant gruda na conexão do pool). `tenant_id` fica mesmo se um dia um
tenant tiver banco próprio — é o que torna essa migração possível.

## DEC-002 — O tenant vem do domínio de acesso

**Date:** 2026-11-05 (retroativo)
**Status:** accepted — reafirmada em DEC-011 (subdomínio personalizado por barbearia)

**Context:** Login precisa saber de qual barbearia é o usuário; e-mail precisa poder repetir entre
barbearias.

**Decision:** Cada barbearia atende em `<slug>.<BASE_DOMAIN>` ou em domínio próprio
(`tenants.custom_domain`, via CNAME). O tenant é resolvido do header `Host` antes de qualquer
regra. Em `ENVIRONMENT=dev`, o header `X-Tenant-Slug` substitui o subdomínio (curl, localhost);
fora de dev ele é ignorado. Token emitido para uma barbearia é recusado (403) no domínio de outra.

**Consequences:** E-mail é único por barbearia, e o login não pergunta "qual barbearia?" em
produção. Em localhost o frontend precisa pedir o slug.

## DEC-003 — Admin da plataforma fora da tenancy

**Date:** 2026-11-05 (retroativo)
**Status:** accepted

**Context:** A equipe Navalha precisa de acesso de suporte cross-tenant.

**Decision:** `platform_admins` é tabela de control plane, sem RLS e fora do RBAC de barbearia. A
conta nasce só pelo seed (`python -m app.management.seed platform-admin`), com senha de no mínimo
12 caracteres, gerada e exibida uma única vez se omitida. Ainda não há rota de login para ela
(ISS-005).

**Consequences:** É a credencial mais valiosa do sistema; o login dela, quando existir, terá tipo de
token próprio e auditoria de acesso cross-tenant (spec própria).

## DEC-004 — RBAC por permissão, com eixo de escopo

**Date:** 2026-11-05 (retroativo)
**Status:** accepted

**Context:** "Barbeiro vê agendamentos, mas só os dele" — RBAC puro não expressa isso; e pedidos de
cliente como "a recepção pode ver o faturamento do dia" não podem custar quarenta endpoints.

**Decision:** O código pede a permissão (`require(Permission.X)`), nunca o cargo. O mapa cargo →
permissão → escopo (`all` / `unit` / `own`) vive só em `identity/permissions.py`. As permissões não
vão no JWT: são resolvidas no servidor a cada request.

**Consequences:** Mudar o mapa vale na hora. Toda rota que lista dados aplica `ctx.scope`.

## DEC-005 — Access JWT curto + refresh opaco rotativo

**Date:** 2026-11-05 (retroativo)
**Status:** accepted

**Decision:** Access token JWT HS256 de 15 min (`sub`, `tid`, `rol`, `bid`, `typ`); refresh token
opaco de 30 dias guardado só como SHA-256, revogado ao ser trocado (rotação). Senhas com argon2id,
com rehash transparente no login quando os parâmetros mudam.

**Consequences:** Logout revoga na hora. Falta detecção de reuso de refresh (ISS-003).

## DEC-006 — Monólito modular por feature

**Date:** 2026-11-05
**Status:** accepted

**Context:** O backend era um pacote plano (`models.py`, `schemas.py`, `deps.py`, `routers/`) com
regra de negócio nos handlers. Os próximos blocos (catálogo, agenda, clientes, financeiro,
conversas) transformariam cada arquivo plano num depósito de domínios.

**Options considered:**
1. Manter o layout plano por camada — simples hoje, cresce mal.
2. Microserviços — custo operacional sem justificativa para o tamanho atual.
3. Monólito modular por feature, no modelo do backend da ClaraAI.

**Decision:** Opção 3. `app/core/` + `app/modules/<modulo>/` com `router/ service/ repository/
model/` + `schemas.py` + `public.py`. Divergências do Clara, deliberadas: `cache/` e `jobs/` só
quando o módulo usar Redis/worker (o Clara exige as seis pastas sempre); `dependencies.py` opcional
na raiz do módulo para as dependências FastAPI. Spec:
`docs/specs/✅completed_backend-modular-architecture.md`.

**Consequences:** Um pouco mais de arquivos por funcionalidade; em troca, cada domínio novo tem
lugar óbvio e fronteiras verificadas por `lint-imports` e testes.

## DEC-007 — `identity` é o único módulo do núcleo, e guarda tenants e barbeiros

**Date:** 2026-11-05
**Status:** accepted

**Context:** Separar `tenancy` de `identity` criaria um ciclo: as rotas de tenant precisam de
usuário autenticado (identity) e o identity precisa de tenant (sessão com RLS, cadastro de
barbearia).

**Decision:** Um módulo só, `identity`, com tenants, unidades, usuários, convites, sessões, RBAC,
admin da plataforma e `Barber` (que nasce no aceite de convite). Todo módulo de domínio depende dele
pelo `public.py`.

**Consequences:** Quando o módulo de agenda existir, reavaliar se `Barber` migra para lá (recurso de
agenda) — ele é mais agenda do que identidade. A mudança não afeta o banco (a fronteira de módulo é
de código, não de dado).

## DEC-008 — `core/model_registry.py` é a única exceção a "core não importa módulo"

**Date:** 2026-11-05
**Status:** accepted

**Context:** O Alembic compara o banco com `Base.metadata`; model não importado parece tabela a
apagar. Algo precisa importar todos os models, e o `alembic/env.py` precisa de um ponto único.

**Decision:** `app/core/model_registry.py` importa o pacote `model` de cada módulo. É a única
exceção no contrato do import-linter (`ignore_imports`).

**Consequences:** Módulo novo adiciona uma linha no registry; o snapshot `db_schema` e o
`alembic check` acusam se faltar.

## DEC-009 — Snapshots de contrato como portão

**Date:** 2026-11-05
**Status:** accepted

**Decision:** `tests/test_contracts/` congela o OpenAPI, a tabela de rotas com a cadeia de
dependências de cada uma (incluindo `require(<permissão>)`) e o schema do ORM. Foram gerados antes
da migração modular e não mudaram com ela. Regenerar só com `UPDATE_CONTRACT_SNAPSHOTS=1`, para
mudança intencional registrada na spec.

**Consequences:** Uma guarda de permissão removida por engano, uma rota renomeada ou uma coluna
alterada quebram o teste em segundos, sem precisar de teste de comportamento para cada caso.

## DEC-010 — Monorepo com camada de contexto por projeto

**Date:** 2026-11-05
**Status:** accepted

**Context:** No Clara, backend e frontend são repositórios separados, cada um com seu `CLAUDE.md` e
sua `.github/`. Aqui os dois vivem num repositório só.

**Decision:** Cada projeto mantém a própria camada de contexto (`backend/.github/`,
`frontend/.github/`) e o próprio `CLAUDE.md`; o `CLAUDE.md` da raiz só orienta e aponta para eles.
A `.github/` da raiz guarda o que o GitHub lê: workflows de CI e templates de issue/PR. Spec que
toca os dois lados existe nas duas pastas, uma apontando para a outra.

**Consequences:** O contexto que a IA carrega continua focado num projeto. O CI é um só, com jobs
separados por projeto.

## DEC-011 — Schema por barbearia, no desenho do ClaraCRM v2

**Date:** 2026-11-05
**Status:** accepted (substitui DEC-001)

**Context:** Pedido do dono do produto: seguir a arquitetura multi-tenant do ClaraCRM
(`docs/multi-tenant-architecture-v2.md`) — schema por tenant, `public` só de controle — com uma
mudança: o acesso continua por **subdomínio personalizado por barbearia** (e domínio próprio), em vez
da URL única do ClaraCRM.

**Options considered:**
1. Manter RLS em tabelas compartilhadas (DEC-001) — já funcionava, mas diverge da plataforma.
2. Schema por tenant com URL única e login por e-mail (doc exato) — perde o subdomínio que o produto
   quer oferecer a cada barbearia.
3. Schema por tenant com o tenant vindo do host (doc com §1/§4 adaptados).

**Decision:** Opção 3. `public` tem só controle (`tenants`, `platform_admins`, `core_keys`,
`provisioning_jobs`, `core_audit_log`); cada barbearia tem `tenant_<slug>` com as próprias tabelas e
enums, sem `tenant_id` e sem FK entre schemas. Os models de barbearia ficam sob o schema-marcador
`tenant`, trocado em runtime por `schema_translate_map` — equivalente SQLAlchemy da opção `schema` do
adapter do Prisma: **nenhum `SET search_path` em sessão de request**, um pool único, engines finos por
schema em cache. Fora de uma sessão de tenant, uma tabela de barbearia aponta para o schema `tenant`
(que não existe) e falha, em vez de cair no `public`. O tenant vem do host; o JWT carrega `tid` e é
recusado em outro host. O slug segue regras de DNS (com hífen); o schema é derivado uma vez
(`-` → `_`), gravado em `tenants.schema_name` e revalidado por regex antes de qualquer uso.

**Consequences:** RLS deixou de existir (o isolamento é a qualificação de schema, provada por teste).
Dois conjuntos de migrations (`alembic/control`, `alembic/tenant`). E-mail único por barbearia (cada
uma tem sua tabela `users`). Diretório global de login do doc não é necessário. O banco de dev antigo
foi preservado no schema `legacy_rls_v1` (ISS-011).

## DEC-012 — Banco endurecido: app sem DDL, migrator separado, role por barbearia

**Date:** 2026-11-05
**Status:** accepted

**Decision:** O role de runtime (`navalha_app`, o usuário da `DATABASE_URL`) tem só `USAGE` + DML
nas tabelas que usa; o `PUBLIC` perde todo acesso ao schema `public`. O dono do schema (migrator,
`DATABASE_URL_MIGRATIONS`) faz migrations, o DDL do provisionamento e o CLI de chaves. Cada barbearia
ganha um role `tenant_<slug>` `NOLOGIN`, restrito ao próprio schema, para acesso fora de banda.
`SET LOCAL ROLE` por request **não** é usado: como o doc concluiu, role e schema sairiam do mesmo
contexto e um bug erraria os dois na mesma direção.

**Consequences:** Um SQL cru com bug não consegue criar nem derrubar tabela (testado). A API guarda a
credencial de migrator para provisionar (ISS-013).

## DEC-013 — Ciclo de vida do tenant, `schema_version` e migrations fora do boot

**Date:** 2026-11-05
**Status:** accepted

**Decision:** Status operacional `provisioning | active | failed | suspended | archived` (cobrança é
do Core, não daqui). Só `active` é servido: `suspended` → 403, `provisioning`/`failed` → 503,
`archived` → 404 como desconhecido. `tenants.schema_version` guarda o que o `alembic_version` do
schema diz; a API recusa (503) schema **atrás** do head do build, lido da pasta
`alembic/tenant` (versão à frente ou nunca registrada é servida). Migrations saem do boot: serviço
one-shot `migrate` no compose e `python -m app.management.migrate --apply` (controle, depois cada
tenant, sequencial e fail-fast). Só migrations expand/contract no conjunto de tenant.

**Consequences:** Uma barbearia nunca é servida com schema meio migrado; o deploy precisa rodar o
migrate antes de trocar as instâncias.

## DEC-014 — Barbearias nascem só pelo control plane (`X-Core-Key`)

**Date:** 2026-11-05
**Status:** accepted

**Context:** No futuro, um Core de plataforma controla os tenants e os ambientes de cada cliente, e a
criação acontece pelos administradores a partir da venda de planos.

**Decision:** `POST /auth/register-shop` foi removido. `/core/tenants` (fora do `/docs` público,
OpenAPI próprio em `/core/openapi.json`) provisiona por job assíncrono (202), idempotente por slug e
por `Idempotency-Key`; suspende, reativa, retoma, reemite o convite e exclui (quatro portões). A
credencial é `X-Core-Key`: SHA-256, escopos (`tenant:read`, `tenant:provision`, `tenant:destroy`),
allowlist de IP, rate limit por processo e auditoria de toda chamada, inclusive as negadas. A primeira
chave nasce por CLI com credencial de banco. A senha do dono nunca está no contrato: o job gera um
convite de primeiro acesso (entregue uma vez) e a pessoa define a senha em `/convite/<token>`.

**Consequences:** A landing não cadastra mais barbearias (capta lead). `external_tenant_id` guarda o id
do Core. `platform_admins` (DEC-003) continua, sem login, para o futuro painel de suporte.

## DEC-015 — `docs/` do projeto: `specs/` para planejamento e `api/` gerada

**Date:** 2026-11-06
**Status:** accepted

**Context:** As specs viviam em `.github/specs/` (modelo Clara), misturadas com o que só orienta a
IA, e não havia referência da API. Pedido do dono do produto: cada projeto organiza a própria
`docs/` com `specs/` e `api/`, separados, para documentar durante o desenvolvimento com as specs
escritas antes, no planejamento.

**Decision:** Specs em `backend/docs/specs/` (espelho em `frontend/docs/specs/` quando a
funcionalidade toca os dois lados). A `.github/` fica com regras, memória e skills, e aponta para lá.
A referência da API é **gerada**, nunca escrita à mão: `tools/api_docs.py` gera `docs/api/` do `app.openapi()` e do contrato do control plane, com a guarda de cada rota (permissão ou escopo do Core) lida da cadeia de dependências; `test_api_docs.py` falha se divergir. `make docs-api` regenera os dois lados.

**Consequences:** A documentação de API não envelhece em silêncio — o CI pega a divergência. Texto
explicativo (o porquê de uma regra) continua na spec, não na referência gerada.

## DEC-016 — Cadastros básicos: barbeiro ≠ usuário, apagar só sem histórico, telefone E.164

**Date:** 2026-11-06
**Status:** accepted

**Context:** Primeiro bloco de domínio (spec `✅completed_registry-basic-crud.md`): CRUD de
barbeiros, serviços e clientes. O dono do produto decidiu que o cadastro de barbeiros é separado do
de usuários com acesso ao painel; o convite com cargo `barber` criava um barbeiro sozinho.

**Decision:**
- **Barbeiro ≠ usuário.** Nenhum dos dois cria o outro; o vínculo é opcional e explícito — convite
  com `barber_id` (o aceite liga) ou `user_id` no cadastro do barbeiro. Convite `barber` exige
  `barber_id`; `create_barber` saiu do contrato (a coluna sai numa migration de contract).
- **Apagar (P1):** `DELETE` remove de verdade enquanto não há histórico; o histórico futuro
  referencia com `ON DELETE RESTRICT` e o `IntegrityError` vira `409` → o caminho é inativar.
- **Cliente** é da barbearia, não da unidade (P3), com telefone obrigatório e único em E.164 (P2).
- **Serviço** tem preço único para todas as unidades (P4), em centavos inteiros (P6); só quem vê
  todas as unidades escreve.
- **Módulos:** `catalog` (serviços + `barber_services`) e `clients` novos; `/barbers` fica no
  `identity` (DEC-007 mantida: mover criaria ciclo). Novo contrato do import-linter: o `identity`
  não importa módulo de domínio.

**Consequences:** Os limites de plano (barbeiros e unidades por plano) vão contar o cadastro de
barbeiros, não os logins. A lista de clientes do barbeiro (`own`) fica vazia até a agenda existir.

## DEC-017 — Unidades, expediente, exceções de calendário e configurações da barbearia

**Date:** 2026-11-06
**Status:** accepted

**Context:** Primeira spec da Fase 1 do ROADMAP (S01, `⏳active_identity-units-hours.md`): a agenda,
a IA e o link precisam saber quando cada unidade está aberta e quais são as políticas de
agendamento.

**Decision:**
- Unidades, expediente (`unit_business_hours`, até 3 intervalos por dia, sem cruzar meia-noite),
  exceções (`unit_exceptions`: `closed` ou `special_hours`, de um a 366 dias) e `shop_settings`
  (uma linha, `id = 1`) ficam no `identity`, ao lado de `units`. Políticas são da barbearia, não da
  unidade.
- Permissão nova **`unit:configure`** (dono `all`, gerente `unit`) para expediente e exceções
  (PD-33); criar, editar e apagar unidade e as políticas continuam `tenant:configure`.
- Sobreposição de exceções barrada no banco por `EXCLUDE USING gist` com a extensão **`btree_gist`**
  no `public` (migration de controle `c0002`), que a agenda (S03) também vai usar.
- Unidade nasce com a semana padrão seg–sáb 09:00–19:00 (migration para as existentes,
  `bootstrap_tenant` e `create_unit` para as novas).
- Normalização de telefone desceu para `app/core/phone.py` (formato, não regra de negócio).
- `UnprocessableEntity` (422) em `app/core/exceptions.py` para regras que dependem de dado guardado.
- Outros módulos leem pelo `identity.public`: `get_unit`, `list_units`, `get_unit_calendar`
  (calendário efetivo no fuso da unidade) e `get_shop_settings`.

**Consequences:** Apagar unidade é recusado também quando há `user_units` (o `CASCADE` tornaria um
usuário restrito em "vê todas"). O limite de unidades do plano (402) entra com a S15.

## DEC-018 — Módulo `scheduling`: jornada do barbeiro, turnos especiais e ausências

**Date:** 2026-11-07
**Status:** accepted

**Context:** Spec S02 (`⏳active_scheduling-barber-schedule.md`). A agenda (S03) precisa do tempo
de trabalho efetivo de cada barbeiro.

**Decision:**
- Módulo novo **`scheduling`** (no contrato de camadas; o `identity` não o importa). Tabelas
  `barber_work_hours`, `barber_shift_overrides` e `barber_time_off`, com FK para `barbers.id` em
  `CASCADE` (configuração, não histórico).
- **DEC-007 reavaliada e mantida:** o `Barber` fica no `identity`; o `scheduling` lê pelo
  `identity.public` (`BarberInfo`, `get_barber_info`, `list_barber_infos`, `get_unit_week`).
- Tempo efetivo = (turno especial, ou jornada, ou horário da unidade se não houver jornada) ∩
  horário aberto da unidade no dia − ausências, calculado no fuso da unidade e devolvido em UTC
  (`service/working_time.py`).
- Jornada como intervalos (almoço = lacuna); sem versão "vale a partir de"; semana toda vazia é
  recusada (para afastar, ausência ou inativar).
- Ausência de dia inteiro guardada de meia-noite local a meia-noite local; sobreposição barrada por
  `EXCLUDE USING gist` (`btree_gist`). Permissão por tipo: folga/férias/atestado `team:manage`,
  bloqueio `appointment:create` (barbeiro só o próprio).
- `ClockTime` em `app/core/clock.py`, compartilhado com o horário da unidade.

**Consequences:** A S03 consome `effective_intervals` direto (mesmo módulo); a S14 e a S16 usam
`capacity_minutes` e `barbers_without_hours` pelo `scheduling.public`.
