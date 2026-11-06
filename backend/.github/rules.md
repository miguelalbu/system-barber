# Rules

Padrões inegociáveis deste projeto. Prevalecem sobre o conhecimento geral da IA.

## Code

- Código autoexplicativo; comentário explica o "porquê", nunca o "o quê".
- DRY: lógica repetida vira função reutilizável no lugar certo (ver "Architecture").
- Preferir solução nativa/pura antes de dependência nova.
- Todo erro é tratado explicitamente — nada de falha silenciosa.

## Multi-tenancy (DEC-001, DEC-002) — o que nunca pode quebrar

- Toda tabela com dado de barbearia herda `TenantMixin` (`tenant_id`) e ganha policy RLS **na
  mesma migration que a cria** (`apply_rls(...)`, ver `alembic/versions/0001_identity_core.py`).
  Tabela de control plane (sem RLS) só com decisão registrada.
- A aplicação conecta como `navalha_app` (sem SUPERUSER, sem BYPASSRLS). Migrations conectam como
  o dono do schema. Nunca usar `DATABASE_URL_MIGRATIONS` em runtime.
- O tenant é fixado com `set_config('app.tenant_id', :tid, true)` — o `true` (local à transação) é
  obrigatório. Toda sessão nasce de `app/core/database.py` ou das dependências do `identity`.
- O tenant vem do domínio (`Host`). `X-Tenant-Slug` só vale com `ENVIRONMENT=dev`.
- Código de negócio nunca filtra por `tenant_id` "para garantir" nem cruza tenants: a RLS é a
  fronteira. Query cross-tenant (billing, métricas de plataforma) só em módulo explícito, com spec.

## Authorization (DEC-004)

- O código pergunta a **permissão**, nunca o cargo: `Depends(require(Permission.X))`.
- O mapa cargo → permissão → escopo vive só em `app/modules/identity/permissions.py`.
- Toda rota autenticada aplica o escopo resolvido (`ctx.scope`: `all` / `unit` / `own`).
- Permissão nova entra no enum, no mapa de cada cargo e em `docs/PERMISSIONS_MAP.md` (o teste
  `test_permissions_doc` falha se o documento divergir).

## Architecture

Monólito modular por feature (DEC-006), no modelo do backend da ClaraAI. Spec:
`.github/specs/✅completed_backend-modular-architecture.md`.

- `app/core/` é infraestrutura sem regra de negócio e não importa módulo — exceto
  `core/model_registry.py`, que importa todo model (DEC-008).
- Cada domínio vive em `app/modules/<modulo>/`, sempre com a mesma forma:
  - `router/` — rotas HTTP, um arquivo por recurso. Fino: Pydantic valida, `Depends` resolve
    sessão/usuário/permissão, o service decide. O nome da função do handler é contrato (vira o
    `operationId`) e a docstring dele vira a descrição no OpenAPI.
  - `service/` — regra de negócio, um arquivo por ação (`invite_member.py`, `accept_invite.py`).
    Levanta exceções de `app/core/exceptions.py`, nunca `HTTPException`.
  - `repository/` — todo o SQL, um arquivo por agregado.
  - `model/` — tabelas SQLAlchemy, um arquivo por agregado, mais `model/enums.py`.
  - `schemas.py` — Pydantic de entrada e saída, um arquivo na raiz do módulo.
  - `public.py` — tudo o que outro módulo pode usar. **Única** porta de entrada.
  - `dependencies.py` — opcional: dependências FastAPI que o módulo oferece.
  - `cache/` e `jobs/` — só quando o módulo usar Redis ou worker (DEC-006). Chave Redis sempre com
    TTL e prefixo `<modulo>:`.
- Um módulo importa outro **só pelo `public.py`**. A dependência aponta para baixo; hoje:
  `<módulos de domínio>` → `identity` → `core`. Comunicação para cima será por evento, com decisão
  registrada quando surgir a primeira necessidade.
- Dentro do módulo, as camadas apontam para baixo: `router → service → repository → model`.
- `app/main.py` só cria o app, registra handlers e routers. `app/management/` guarda comandos de
  operador e usa módulos só pelo `public.py`.
- Fronteiras verificadas por `lint-imports` (contratos em `pyproject.toml`) e por
  `tests/test_contracts/test_module_layout.py`. Módulo novo entra no contrato de camadas.
- Nunca recriar o layout plano antigo: `app/models.py`, `schemas.py`, `deps.py`, `db.py`,
  `config.py`, `security.py`, `permissions.py`, `seed.py`, `routers/`.

## Contracts frozen

Mudar qualquer um destes é mudança de contrato com o frontend ou com o banco, e vira spec:
rota, método, status code, schema de request/response, mensagem de erro que o frontend trata,
`__tablename__`, nome de enum do Postgres, nome de constraint/índice.

## Naming

- Identificadores em inglês, `snake_case`; classes em `PascalCase`; constantes em
  `SCREAMING_SNAKE_CASE`.
- Mensagens ao usuário em português, escritas para uma pessoa.
- Arquivo de service tem nome de ação (verbo + objeto); de repository, nome do agregado no plural.

## Error Handling

- Service levanta `BadRequest`, `Unauthorized`, `Forbidden`, `NotFound`, `Conflict`
  (`app/core/exceptions.py`). O handler único responde `{"detail": "<mensagem>"}`.
- Mensagem ao usuário nunca expõe detalhe interno (SQL, ids de outro tenant, stack trace).
- Validar toda entrada externa na fronteira (schemas Pydantic).

## Security

- Nunca escrever segredo, token ou credencial no código; configuração vem de variável de ambiente
  (`docs/ENVIRONMENT_VARIABLES.md`).
- Query sempre parametrizada (SQLAlchemy). `text()` só com bind params.
- Senha só com argon2id (`core/security.py`); token opaco só como hash SHA-256.
- Menor privilégio em todo acesso.

## Database

- Toda mudança de schema é migration Alembic revisada à mão; `alembic check` limpo no fim.
- Migration nova de tabela de barbearia: `tenant_id` + `apply_rls(...)` + `GRANT` para o role de
  runtime (os `ALTER DEFAULT PRIVILEGES` da 0001 já cobrem tabelas novas do schema `public`).
- Enum Postgres sempre com `pg_enum(...)` (`values_callable`), senão grava o nome em vez do valor.

## Tests

- Testes ficam em `tests/`, um pacote por módulo (`tests/test_<modulo>/`), fora de `app/`.
- A suíte roda contra o Postgres de desenvolvimento (porta 5433), com slug aleatório por teste
  (ISS-006).
- `tests/test_contracts/` guarda snapshots de OpenAPI, da tabela de rotas com as guardas de cada
  uma e do schema do ORM. Snapshot falhando = comportamento mudou: ache a causa, **nunca** regenere
  para passar. `UPDATE_CONTRACT_SNAPSHOTS=1` só para mudança intencional e registrada na spec.
- Toda regra de negócio de uma spec tem teste.

## Directory Structure

```text
backend/
├── app/
│   ├── main.py               cria o app, registra handlers e routers. Nada mais.
│   ├── core/                 infraestrutura sem regra de negócio
│   │   ├── config.py         Settings (pydantic-settings)
│   │   ├── database.py       engine, SessionFactory, set_tenant, tenant/platform_session
│   │   ├── security.py       argon2id, JWT, tokens opacos
│   │   ├── exceptions.py     AppError + subclasses e o handler HTTP único
│   │   ├── model_base.py     Base, pg_enum, uuid_pk, TimestampMixin, TenantMixin
│   │   └── model_registry.py importa todo model (Alembic) — DEC-008
│   ├── modules/
│   │   └── identity/         tenants, unidades, usuários, RBAC, convites, sessões, admin da plataforma
│   │       ├── router/       auth.py · tenant.py · team.py
│   │       ├── service/      uma ação por arquivo
│   │       ├── repository/   tenants · units · users · barbers · refresh_tokens · invites · platform_admins
│   │       ├── model/        enums · tenant · unit · user · barber · refresh_token · invite · platform_admin
│   │       ├── dependencies.py  Host → Tenant → sessão com RLS → usuário → permissão
│   │       ├── permissions.py   mapa cargo → permissão → escopo (DEC-004)
│   │       ├── schemas.py
│   │       └── public.py
│   └── management/
│       └── seed.py           python -m app.management.seed platform-admin
├── alembic/                  migrations (env.py lê app.core.model_registry)
├── tests/
│   ├── conftest.py
│   ├── test_contracts/       snapshots + layout dos módulos + mapa de permissões
│   └── test_identity/
├── docs/                     ENVIRONMENT_VARIABLES.md · PERMISSIONS_MAP.md
├── .github/                  camada de contexto da IA (este diretório)
├── pyproject.toml            dependências, ruff, pytest, import-linter
└── CLAUDE.md
```

## Documentation

- Código autoexplicativo reduz a necessidade de comentário; documente o "porquê".
- `README.md` sempre com setup e endpoints atualizados.
- Variável de ambiente nova entra em `.env.example` e em `docs/ENVIRONMENT_VARIABLES.md`.

## Versioning

- SemVer: MAJOR.MINOR.PATCH.
- Commits `type(scope): description` — `feat`, `fix`, `refactor`, `docs`, `test`, `chore`.
  Escopo = módulo ou área (`identity`, `core`, `ci`, `frontend`).
