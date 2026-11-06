# Rules

Padrões inegociáveis deste projeto. Prevalecem sobre o conhecimento geral da IA.

## Code

- Código autoexplicativo; comentário explica o "porquê", nunca o "o quê".
- DRY: lógica repetida vira função reutilizável no lugar certo (ver "Architecture").
- Preferir solução nativa/pura antes de dependência nova.
- Todo erro é tratado explicitamente — nada de falha silenciosa.

## Multi-tenancy (DEC-011 a DEC-014) — o que nunca pode quebrar

Schema por barbearia, no desenho do ClaraCRM v2 (`docs/multi-tenant-architecture-v2.md`), com
acesso por subdomínio personalizado. Spec: `docs/specs/✅completed_identity-schema-per-tenant.md`.

- `public` é **só controle**: catálogo de tenants, chaves do Core, jobs, auditoria, admins da
  plataforma. Nenhum dado de barbearia ali, nunca.
- Cada barbearia tem `tenant_<slug>` com as próprias tabelas e enums. **Nenhuma FK cruza schemas.**
  Tabela de barbearia não tem `tenant_id` nem RLS: o schema é a fronteira.
- Model de barbearia herda `TenantBase` (schema-marcador `tenant`); model de controle herda
  `ControlBase`. Nunca misture as duas bases numa FK ou `relationship()`.
- Dado de barbearia só por `SessionDep` / `tenant_session(schema)`, que qualificam toda query via
  `schema_translate_map`. **Nunca `SET search_path` em sessão de request** (com pool, vaza para o
  próximo tenant). SQL cru em tabela de barbearia: qualifique com `quote_identifier(schema)` ou use o
  ORM.
- O nome do schema vem **só** de `tenants.schema_name` e passa por `assert_safe_schema_name` antes de
  qualquer SQL/DDL. Nunca derive de entrada de usuário fora do provisionamento.
- O tenant vem do host (subdomínio ou `custom_domain`); `X-Tenant-Slug` só com `ENVIRONMENT=dev`.
  Nunca de body, query ou path. O JWT carrega `tid` e é recusado em outro host.
- Só tenant `active` com `schema_version` não atrasada é servido (`assert_servable`).
- O runtime (`navalha_app`) não tem DDL; DDL é do migrator. Barbearias nascem e morrem só pelo control
  plane (`/core/*`, `X-Core-Key`). `DROP SCHEMA` nunca é automático.
- Estado em memória de processo (cache, fila, evento) que guarde dado de barbearia é **particionado
  pelo schema/tenant** — o vazamento real costuma estar aí, não no SQL (doc, Camada 5).

## Authorization (DEC-004)

- O código pergunta a **permissão**, nunca o cargo: `Depends(require(Permission.X))`.
- O mapa cargo → permissão → escopo vive só em `app/modules/identity/permissions.py`.
- Toda rota autenticada aplica o escopo resolvido (`ctx.scope`: `all` / `unit` / `own`).
- Permissão nova entra no enum, no mapa de cada cargo e em `docs/PERMISSIONS_MAP.md` (o teste
  `test_permissions_doc` falha se o documento divergir).

## Architecture

Monólito modular por feature (DEC-006), no modelo do backend da ClaraAI. Spec:
`docs/specs/✅completed_backend-modular-architecture.md`.

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
  `provisioning` → `identity` → `core`, e todo módulo de domínio novo → `identity`. Comunicação para cima será por evento, com decisão
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

- Dois conjuntos de migrations (DEC-011): `alembic/control/` (schema `public`) e `alembic/tenant/`
  (aplicado em cada `tenant_<slug>`). Sempre com `-n control` ou `-n tenant -x schema=...`.
- Tabela nova de barbearia: migration em `alembic/tenant/versions/`, revisão `tNNNN`
  (`alembic -n tenant -x schema=tenant_template revision --autogenerate --rev-id t0002 -m "..."`),
  sem nomear schema. Os privilégios do runtime vêm dos default privileges do provisionamento.
- Conjunto de tenant **só expand/contract**: os schemas migram um a um e o mesmo build atende versões
  vizinhas por alguns minutos.
- Tabela nova de controle: migration em `alembic/control/versions/` (`cNNNN`) com o `GRANT` explícito
  do que o runtime pode fazer nela (`APP_GRANTS`).
- Migrations nunca no boot da API: `python -m app.management.migrate --apply` (ou `make migrate`).
- `alembic check` limpo nos dois conjuntos no fim (`make check-backend` faz isso no `tenant_template`).
- Enum Postgres sempre com `pg_enum(...)` (`values_callable`), senão grava o nome em vez do valor.

## Tests

- Testes ficam em `tests/`, um pacote por módulo (`tests/test_<modulo>/`), fora de `app/`.
- A suíte roda contra o Postgres de desenvolvimento com o controle migrado. Toda barbearia de teste
  nasce pelo caminho real (`create_shop` / `provision` em `tests/conftest.py`: control plane → job →
  convite → aceite) e é destruída no fim da sessão.
- Todo módulo de domínio novo tem teste de **cruzamento entre duas barbearias** (doc Camada 7): o dado
  de A nunca aparece, nem é alterável, em B.
- `tests/test_contracts/` guarda snapshots de OpenAPI público, OpenAPI do control plane, tabela de
  rotas com as guardas (`require(...)`, `core(...)`) e schema do ORM (controle e tenant). Snapshot
  falhando = comportamento mudou: ache a causa, **nunca** regenere para passar.
  `UPDATE_CONTRACT_SNAPSHOTS=1` só para mudança intencional e registrada na spec.
- Toda regra de negócio de uma spec tem teste.

## Directory Structure

```text
backend/
├── app/
│   ├── main.py               cria o app, registra handlers e routers. Nada mais.
│   ├── core/                 infraestrutura sem regra de negócio
│   │   ├── config.py         Settings (pydantic-settings)
│   │   ├── database.py       pool único, tenant_session (schema_translate_map), control_session,
│   │   │                     migrator_engine, guarda do nome de schema
│   │   ├── model_base.py     ControlBase (public) · TenantBase (marcador `tenant`) · pg_enum · mixins
│   │   ├── model_registry.py importa todo model (Alembic) — DEC-008
│   │   ├── schema_version.py head esperado do conjunto de tenant; is_behind()
│   │   ├── security.py       argon2id, JWT, tokens opacos
│   │   ├── exceptions.py     AppError + subclasses e o handler HTTP único
│   │   └── rate_limit.py     limitador em memória (por processo)
│   ├── modules/
│   │   ├── identity/         catálogo de tenants, unidades, equipe, RBAC, convites, sessões
│   │   │   ├── router/       auth.py · tenant.py · team.py
│   │   │   ├── service/      uma ação por arquivo (inclui bootstrap_tenant para o provisionamento)
│   │   │   ├── repository/   tenants · units · users · barbers · refresh_tokens · invites · platform_admins
│   │   │   ├── model/        tenant, platform_admin (controle) · unit, user, barber, refresh_token, invite (tenant)
│   │   │   ├── dependencies.py  Host → Tenant → servível? → sessão do schema → usuário → permissão
│   │   │   ├── tenant_naming.py slug ↔ schema (fronteira de injeção de DDL)
│   │   │   ├── permissions.py   mapa cargo → permissão → escopo (DEC-004)
│   │   │   ├── schemas.py
│   │   │   └── public.py
│   │   └── provisioning/     control plane /core/* (X-Core-Key)
│   │       ├── router/       tenants.py (fora do /docs público)
│   │       ├── service/      provision, run_provisioning_job, get/list, change_status, retry,
│   │       │                 reissue_invite, destroy
│   │       ├── repository/   catalog · jobs · core_keys · audit
│   │       ├── model/        core_key · provisioning_job · core_audit_log · enums
│   │       ├── dependencies.py  autenticação X-Core-Key, escopos, rate limit, auditoria de negadas
│   │       ├── schemas.py
│   │       └── public.py
│   └── management/
│       ├── migrate.py        controle + cada tenant, sequencial e fail-fast
│       ├── core_key.py       cria/lista/revoga chaves do Core (credencial de banco)
│       └── seed.py           conta de suporte da plataforma
├── alembic/
│   ├── control/              schema public (cNNNN)
│   └── tenant/               cada tenant_<slug> (tNNNN)
├── tests/
│   ├── conftest.py           provisionamento real + limpeza no fim da sessão
│   ├── test_contracts/       snapshots + layout dos módulos + mapa de permissões
│   ├── test_identity/
│   └── test_provisioning/
├── docs/                     ENVIRONMENT_VARIABLES.md · PERMISSIONS_MAP.md
├── .github/                  camada de contexto da IA (este diretório)
├── pyproject.toml            dependências, ruff, pytest, import-linter
└── CLAUDE.md
```

## Documentation

- `docs/` do projeto (índice em `docs/README.md`):
  - `docs/specs/` — planejamento **antes** do código; a spec é o contrato da funcionalidade.
  - `docs/api/` é **gerada** do OpenAPI (`make docs-api`) e verificada por `tests/test_contracts/test_api_docs.py`; nunca editar à mão.
  - referências avulsas (`ENVIRONMENT_VARIABLES.md`, `PERMISSIONS_MAP.md`).
- Código autoexplicativo reduz a necessidade de comentário; documente o "porquê".
- `README.md` com setup e o estado atual atualizados.
- Variável de ambiente nova entra em `.env.example` e em `docs/ENVIRONMENT_VARIABLES.md`.

## Versioning

- SemVer: MAJOR.MINOR.PATCH.
- Commits `type(scope): description` — `feat`, `fix`, `refactor`, `docs`, `test`, `chore`.
  Escopo = módulo ou área (`identity`, `core`, `ci`, `frontend`).
