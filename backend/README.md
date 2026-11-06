# Navalha · Core API

Sistema de registro do SaaS de barbearias. FastAPI + PostgreSQL, multi-tenant
com **um schema por barbearia** e o `public` só como control plane — o desenho
do ClaraCRM v2 ([`docs/multi-tenant-architecture-v2.md`](../docs/multi-tenant-architecture-v2.md)),
com acesso por subdomínio personalizado.

Este primeiro bloco entrega o núcleo de identidade e o control plane:
provisionamento de barbearia (schema próprio), login, RBAC e convite de equipe. Agenda, financeiro e CRM entram como
módulos seguintes, sobre a mesma base de isolamento.

> **Para quem vai desenvolver (pessoa ou IA):** comece por [`CLAUDE.md`](CLAUDE.md)
> e pela camada de contexto em [`.github/`](.github/README.md) — regras, specs,
> decisões (DEC-NNN) e problemas conhecidos (ISS-NNN).

> **Convenção:** código em inglês (identificadores, tabelas, colunas, rotas).
> Ficam em português: as mensagens de erro da API, porque vão direto para a tela
> do dono da barbearia, e esta documentação.

## Rodar

Com Docker (sobe Postgres, Redis e a API, com migrations e reload):

```bash
docker compose up -d          # http://localhost:8000/docs
docker compose logs -f core-api
```

Direto na máquina, com o banco no compose:

```bash
docker compose up -d db redis
make setup-backend                       # cria backend/.venv (na raiz do repo)
.venv/bin/python -m app.management.migrate --apply   # Windows: .venv/Scripts/
.venv/bin/uvicorn app.main:app --reload
```

Verificação (na raiz do repo):

```bash
make test-backend     # pytest: comportamento + snapshots de contrato
make lint-backend     # ruff + lint-imports (fronteiras entre módulos)
make check-backend    # tudo acima + alembic check
```

## Estrutura

Monólito modular por feature (DEC-006). Detalhes e regras em
[`.github/rules.md`](.github/rules.md); para criar um módulo novo,
[`.github/skills/new-module.md`](.github/skills/new-module.md).

```
app/
├── main.py          cria o app e registra os módulos
├── core/            config, pool + sessões por schema, segurança, exceções, bases dos models
├── modules/
│   ├── identity/    catálogo de tenants, equipe, RBAC, convites, sessões
│   └── provisioning/ control plane /core/* (X-Core-Key)
└── management/      migrate (controle + cada tenant) · core_key · seed
alembic/
├── control/         schema public
└── tenant/          cada tenant_<slug>
tests/
├── test_contracts/  snapshots de OpenAPI (público e core), rotas+guardas, schema; layout
├── test_identity/
└── test_provisioning/
docs/                ENVIRONMENT_VARIABLES.md · PERMISSIONS_MAP.md
```

## Conta de plataforma (super admin)

A conta de suporte da plataforma vive fora de qualquer barbearia e fora do RBAC
de tenant — fica no `public`, no control plane. Não nasce de migration nem
de cadastro; é criada pelo seed:

```bash
docker compose exec core-api python -m app.management.seed platform-admin \
    --email suporte@navalha.app --name "Seu Nome"
```

Sem `--password`, uma senha forte é gerada e exibida **uma única vez** — guarde
na hora. Os valores também podem vir de `SEED_ADMIN_EMAIL`, `SEED_ADMIN_NAME` e
`SEED_ADMIN_PASSWORD`.

Rodar de novo é seguro: uma conta existente não é tocada. Para redefinir a
senha, `--update-password` (omitir `--name` mantém o nome atual).

> **Ainda não há login de plataforma.** A conta é gravada e a senha validada,
> mas nenhuma rota autentica com ela — o fluxo de suporte cross-tenant é um
> bloco próprio, com tipo de token e regras de auditoria separados.

> O Postgres do compose sobe na porta **5433** do host, porque a 5432 costuma
> estar ocupada por uma instalação local. O Redis vai na **6380**.

## Como o isolamento funciona

Decisões DEC-011 a DEC-014 em [`.github/memory/decisions.md`](.github/memory/decisions.md);
spec em [`docs/specs/`](docs/specs/).

```
postgres (um banco)
├── public              control plane: tenants, core_keys, provisioning_jobs,
│                       core_audit_log, platform_admins — nenhum dado de barbearia
├── tenant_central      units, users, user_units, barbers, refresh_tokens,
│                       invites + os próprios enums + alembic_version
└── tenant_<slug>       idem, estrutura idêntica; nenhuma FK cruza schemas
```

**1. O domínio identifica a barbearia.** Cada uma atende no próprio subdomínio
(`<slug>.navalha.app`) ou em domínio próprio apontado por CNAME
(`tenants.custom_domain`). O tenant vem do `Host` — nunca de algo que o cliente
escolhe. O JWT carrega `tid` e é recusado (403) em outro host.

**2. O schema isola os dados.** Toda query de barbearia é qualificada com o
schema dela pelo `schema_translate_map` do SQLAlchemy — `"tenant_central"."users"`
no próprio SQL. Nada no caminho de request usa `SET search_path`: com pool de
conexões, ele sobrevive ao request e o próximo tenant herda (o pior bug possível
aqui). Os models de barbearia ficam sob o schema-marcador `tenant`; fora de uma
sessão de barbearia eles apontam para um schema que não existe e **falham**.

**3. O banco recusa o que a aplicação não deve fazer.** A API conecta como
`navalha_app`, sem DDL; o `PUBLIC` não tem acesso ao `public`; cada barbearia
tem um role `tenant_<slug>` `NOLOGIN` que só alcança o próprio schema (acesso de
suporte, `pg_dump`, BI).

**4. Só barbearia pronta é servida.** `suspended` → 403, `provisioning`/`failed`
→ 503, `archived` → 404, e schema atrás das migrations do build → 503.

**5. O RBAC limita o que o usuário faz.** Ver abaixo.

### Ciclo de vida: o control plane

Barbearias nascem e morrem pelo `/core/*`, chamado pelo Core da plataforma com a
credencial `X-Core-Key` (hash SHA-256, escopos, allowlist de IP, rate limit,
auditoria de toda chamada). Fora do `/docs` público — o OpenAPI dele fica em
`GET /core/openapi.json`, atrás da chave.

```
POST /core/tenants  → 202 + job:  schema → migrations → grants e role → unidade
                                   inicial + convite do dono → active
GET  /core/tenants/{id}            status, job e o link de primeiro acesso (uma vez)
```

A senha do dono nunca passa pelo contrato: ele recebe um convite de uso único e
define a senha em `/convite/<token>`. A primeira chave do Core nasce por CLI:

```bash
make core-key NAME=core-prod SCOPES=tenant:read,tenant:provision
```

### Migrations

Dois conjuntos: `alembic/control` (o `public`) e `alembic/tenant` (aplicado em
cada schema). Nunca no boot da API: o serviço one-shot `migrate` (ou
`python -m app.management.migrate --apply`) migra o controle e depois cada
barbearia, em ordem, parando na primeira falha, e grava a versão que cada schema
reporta em `tenants.schema_version`.

## RBAC

O código **nunca pergunta o cargo, pergunta a permissão**:

```python
@router.get("/appointments")
def list_appointments(ctx = Depends(require(P.APPOINTMENT_READ))):
    q = select(Appointment)                     # sessão já está no schema da barbearia
    if ctx.scope is Scope.OWN:
        q = q.where(Appointment.barber_id == ctx.barber_id)
    elif ctx.scope is Scope.UNIT and not ctx.all_units:
        q = q.where(Appointment.unit_id.in_(ctx.units))
```

O mapa cargo → permissão vive só em `app/modules/identity/permissions.py`
(tabela completa em [`docs/PERMISSIONS_MAP.md`](docs/PERMISSIONS_MAP.md)). Cada permissão tem um
**escopo**, que é o eixo que o RBAC puro não cobre:

| Scope | Alcance |
|---|---|
| `all` | toda a barbearia |
| `unit` | apenas as unidades ligadas ao usuário (vazio = todas) |
| `own` | apenas os registros do próprio barbeiro |

Cargos: `owner` (tudo), `manager` (operação, escopo de unidade, sem assinatura),
`receptionist` (agenda, clientes, comandas — sem financeiro), `barber` (a
própria agenda e a própria comissão).

## Modelo de dados

**Control plane** — no `public`:

- `tenants` — barbearia: slug (subdomínio), `schema_name`, domínio próprio,
  plano, status, `schema_version`, `external_tenant_id` (id no Core)
- `core_keys`, `provisioning_jobs`, `core_audit_log` — o control plane
- `platform_admins` — equipe da plataforma, para suporte

**Dados da barbearia** — no `tenant_<slug>` dela, sem `tenant_id`:

- `units` — filiais
- `users` — login da equipe; e-mail único **na barbearia**
- `user_units` — unidades visíveis; **vazio = todas**
- `barbers` — o profissional como recurso de agenda
- `refresh_tokens` — hash do token, com revogação
- `invites` — convites de equipe e o primeiro acesso do dono

Dois pontos que costumam confundir:

**`Barber` não é `User`.** Barbeiro é a coluna do calendário: tem comissão,
serviços e horários. `barbers.user_id` é nullable de propósito — existe barbeiro
que nunca vai abrir o app, e a recepção agenda por ele.

**Cliente final não é `User`.** O cliente que corta o cabelo vai para `clients`,
com autenticação própria por telefone. É outro fluxo, no bloco seguinte.

## Autenticação

Access token JWT de 15 min + refresh opaco rotativo de 30 dias, guardado como
hash.

O access token carrega `sub`, `tid`, `rol` e `bid`. **As permissões não vão no
token** — são resolvidas no servidor a partir do cargo, então mudar o mapa vale
na hora em vez de esperar os tokens em circulação expirarem.

O refresh rotaciona: o token usado é revogado ao ser trocado. Token de uma
barbearia apresentado no domínio de outra é rejeitado com 403, mesmo sendo
assinado por nós.

## Endpoints

```
POST   /auth/login                tenant vem do domínio
POST   /auth/refresh              rotativo
POST   /auth/logout               revoga o refresh
GET    /auth/me                   usuário, barbearia, unidades e permissões

GET    /tenant                    dados da barbearia
PATCH  /tenant                    nome e domínio próprio       [tenant:configure]
GET    /tenant/units              unidades visíveis

GET    /team                      membros                      [team:read]
POST   /team/invites              convida (cargo barber: barber_id) [team:manage]
GET    /team/invites              pendentes                    [team:read]
POST   /team/invites/lookup       descreve um convite sem gastá-lo (público)
POST   /team/invites/accept       cria o login (público) — também o 1º acesso do dono
DELETE /team/{user_id}            desativa                     [team:manage]

GET    /barbers                   barbeiros (escopo de unidade) [team:read]
POST   /barbers                   cadastra (não cria login)     [team:manage]
GET    /barbers/{id}                                            [team:read]
PATCH  /barbers/{id}              edita; user_id liga/desliga   [team:manage]
DELETE /barbers/{id}              só sem histórico e sem login  [team:manage]
PUT    /barbers/{id}/services     serviços habilitados          [team:manage]

GET    /services                  serviços                      [catalog:read]
POST   /services · PATCH · DELETE /services/{id}  (todas as unidades) [catalog:write]

GET    /clients?q=&limit=&offset= busca paginada                [client:read]
POST   /clients · PATCH · DELETE /clients/{id}                  [client:write]

GET    /health

Control plane (X-Core-Key, fora do /docs)
POST   /core/tenants              provisiona (202 + job)       [tenant:provision]
GET    /core/tenants              lista                        [tenant:read]
GET    /core/tenants/{id}         status, job, convite (1 vez) [tenant:read]
POST   /core/tenants/{id}/retry   retoma job que falhou        [tenant:provision]
POST   /core/tenants/{id}/suspend · /resume                    [tenant:provision]
POST   /core/tenants/{id}/invite  reemite o convite do dono    [tenant:provision]
DELETE /core/tenants/{id}         exclui (suspensa + confirm + exported) [tenant:destroy]
GET    /core/openapi.json         contrato do control plane    [tenant:read]
```

Em desenvolvimento, o header `X-Tenant-Slug` substitui o subdomínio, para testar
com curl sem mexer no `hosts`. Em produção ele é ignorado.

```bash
curl -X POST localhost:8000/auth/login \
  -H 'Content-Type: application/json' -H 'X-Tenant-Slug: central' \
  -d '{"email":"voce@central.com","password":"senha-forte-123"}'
```

## Pendências antes de produção

Acompanhadas, com número, em [`.github/memory/issues.md`](.github/memory/issues.md).

- **`JWT_SECRET`** — gerar com `python -c "import secrets; print(secrets.token_urlsafe(48))"`.
- **Senha do `navalha_app`** — a de dev está no init SQL; em produção vem de secret.
- **Envio de e-mail** — hoje o convite devolve o link na resposta, para o dono
  repassar por WhatsApp. Trocar por e-mail transacional.
- **Rate limit no login** — o Redis já está de pé, mas ainda não é usado.
- **Detecção de reuso de refresh token** — hoje o reuso apenas falha; deveria
  revogar toda a família de tokens e registrar o evento.
- **Verificação de e-mail** e **recuperação de senha**.
- **Login da conta de plataforma** — a conta existe (ver seed), falta a rota de
  autenticação, com tipo de token próprio e auditoria de acesso cross-tenant.
- **TLS e domínio próprio** — Caddy ou Traefik com ACME sob demanda, para o
  cliente apontar CNAME e o certificado ser emitido sozinho.

## Próximos blocos

1. Catálogo — serviços, combos, clubes, planos de assinatura
2. Agenda — disponibilidade, agendamentos, bloqueios (o núcleo que a IA vai chamar)
3. Clientes e autenticação do cliente final (telefone + OTP)
4. Financeiro — comandas, comissões, pagamentos
5. Eventos de domínio no RabbitMQ, e então o `ai-agent`
