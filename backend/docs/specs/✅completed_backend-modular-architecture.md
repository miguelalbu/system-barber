# Arquitetura modular do backend

**Priority:** high
**Status:** completed
**Espelho no frontend:** `frontend/docs/specs/✅completed_frontend-feature-architecture.md` (mesmo objetivo, outra stack)

## Overview

O backend nasceu como um pacote plano: `app/models.py`, `app/schemas.py`, `app/deps.py`,
`app/permissions.py`, `app/security.py`, `app/db.py` e `app/routers/`. As regras de negócio vivem
dentro dos handlers HTTP (ex.: `register_shop` cria tenant, unidade e dono no próprio router). Isso
funciona com três routers. Com os próximos blocos (catálogo, agenda, clientes, financeiro,
conversas), cada arquivo plano vira um depósito de domínios misturados.

Esta spec reorganiza o código em **monólito modular por feature**, no modelo do backend da ClaraAI
(`~/Documents/ClaraAI/backend`, DEC-004 de lá): infraestrutura em `app/core/` e cada domínio em
`app/modules/<modulo>/`, todos com a mesma forma. A mudança é **estrutural**: nenhuma rota, payload,
tabela ou regra de negócio muda de comportamento.

## Decisões de produto já tomadas

| Parâmetro | Valor |
|---|---|
| Comportamento da API | idêntico — mesmas rotas, métodos, schemas, códigos e mensagens de erro |
| Banco | nenhuma migration nova; `alembic check` continua limpo |
| Nome do pacote | continua `app` (Dockerfile, compose e Alembic seguem apontando para `app.main:app`) |
| Módulos iniciais | só `identity` — tudo o que existe hoje é o núcleo de identidade e tenancy (DEC-007) |
| Pastas obrigatórias | `router/ service/ repository/ model/` + `schemas.py` + `public.py`; `cache/` e `jobs/` só quando o módulo usar Redis ou worker (DEC-006) |
| Comando do seed | passa de `python -m app.seed` para `python -m app.management.seed` |

## Business Rules

- [x] `app/core/` é infraestrutura: config, banco e contexto de tenant, base dos models, segurança
      (hash, tokens), exceções de domínio e o handler HTTP único. Não importa nenhum módulo e não
      tem regra de negócio — exceto `core/model_registry.py`, que importa todo model para o
      `Base.metadata` ficar completo (Alembic).
- [x] Todo módulo tem a forma `router/ service/ repository/ model/` + `schemas.py` + `public.py`.
- [x] `router/` é fino: Pydantic valida, `Depends` resolve sessão/usuário/permissão, o service decide.
      Um arquivo por recurso.
- [x] `service/` guarda a regra de negócio, um arquivo por ação. Levanta exceções de
      `core/exceptions.py`, nunca `HTTPException`.
- [x] `repository/` guarda todo o SQL, um arquivo por agregado.
- [x] `model/` guarda as tabelas SQLAlchemy, um arquivo por agregado, mais `model/enums.py`.
- [x] Um módulo importa outro **só pelo `public.py`**. Com um único módulo hoje, a regra vale a
      partir do segundo (catálogo/agenda).
- [x] O handler único de `core/exceptions.py` responde `{"detail": "<mensagem>"}` — o mesmo formato
      do `HTTPException`, que o frontend já lê em `errorFrom()`.
- [x] As fronteiras são verificadas por `lint-imports` (contratos em `pyproject.toml`) e por
      `tests/test_contracts/test_module_layout.py`.

## Data Contract

Sem mudança de contrato externo. O mapa de arquivos antigo → novo:

```text
app/config.py          → app/core/config.py
app/db.py              → app/core/database.py
app/security.py        → app/core/security.py
(novo)                 → app/core/exceptions.py       AppError + handler único
(novo)                 → app/core/model_base.py       Base, pg_enum, uuid_pk, mixins
(novo)                 → app/core/model_registry.py   importa todo model (Alembic)
app/models.py          → app/modules/identity/model/{enums,tenant,platform_admin,unit,user,barber,refresh_token,invite}.py
app/schemas.py         → app/modules/identity/schemas.py
app/permissions.py     → app/modules/identity/permissions.py
app/deps.py            → app/modules/identity/dependencies.py
app/routers/auth.py    → app/modules/identity/router/auth.py    + service/{register_shop,login,refresh_session,logout,get_profile}.py
app/routers/team.py    → app/modules/identity/router/team.py    + service/{list_members,invite_member,list_invites,accept_invite,deactivate_member}.py
app/routers/tenants.py → app/modules/identity/router/tenant.py  + service/{update_tenant,list_units}.py
app/seed.py            → app/management/seed.py (CLI) + service/seed_platform_admin.py
tests/test_*.py        → tests/test_identity/ ; novos tests/test_contracts/
```

### Portão de cada fatia

Uma fatia só fecha com tudo verde:

```text
pytest                       21 testes de comportamento + 8 de contrato
ruff check app tests
lint-imports
alembic check                "No new upgrade operations detected."
```

Os snapshots de `tests/test_contracts/snapshots/` são gerados **antes** de mover qualquer arquivo e
não podem mudar durante a migração.

## Acceptance Criteria

- [x] Fatia 0 — snapshots de contrato gerados sobre o código antigo: OpenAPI, tabela de rotas com
      as guardas de permissão de cada uma e schema do ORM (`tests/test_contracts/`).
- [x] Fatia 0 — `import-linter` configurado em `pyproject.toml` (`core` não importa módulos;
      camadas `router → service → repository → model` dentro de cada módulo).
- [x] Fatia 1 — `app/core/` criado (config, database, security, exceptions, model_base,
      model_registry); `alembic/env.py` lê o metadata do registry.
- [x] Fatia 2 — models do `identity` divididos por agregado em `model/`.
- [x] Fatia 3 — `repository/`, `service/`, `router/`, `dependencies.py`, `permissions.py`,
      `schemas.py` e `public.py` do `identity`; `main.py` só cria o app e registra os routers.
- [x] Fatia 4 — seed em `app/management/seed.py`; testes em `tests/test_identity/`; arquivos
      antigos removidos (sem shims).
- [x] Portão final: 21 testes de comportamento + contratos verdes, ruff, lint-imports e
      `alembic check` limpos, snapshots inalterados.
- [x] `rules.md`, `CLAUDE.md`, `README.md` e `memory/` descrevem a estrutura nova.

## Dependencies

- Nenhuma dependência de runtime nova. Dev: `import-linter`.

## Notes

- Não há shims de compatibilidade (`app/models.py` reexportando): o projeto é pequeno e não tem
  consumidores externos do pacote, então os imports são trocados de uma vez.
- **Resultado (2026-11-05):** 29 testes verdes (21 de comportamento inalterados + 8 de contrato),
  `ruff`, `lint-imports` (3 contratos) e `alembic check` limpos. Os snapshots `openapi`, `routes`
  e `db_schema` foram gerados sobre o código antigo e não mudaram. A API em execução no compose foi
  verificada depois da migração (health, login, formato de erro 404, CLI do seed).
- Divergências do modelo Clara, registradas em DEC-006: `cache/` e `jobs/` não são obrigatórias, e
  existe `dependencies.py` opcional.
- O FastAPI 0.16x guarda os routers incluídos atrás de um wrapper (`original_router`); o teste da
  tabela de rotas percorre os dois formatos.
- `Barber` fica em `identity` por enquanto, porque nasce no aceite de convite. Quando o módulo de
  agenda existir, decidir se ele migra para lá (ver DEC-007).
