# Criar um módulo de domínio novo

**Quando usar:** ao começar um bloco novo do produto (catálogo, agenda, clientes, financeiro,
conversas) no backend. Exemplo usado abaixo: `scheduling`.

## Antes de começar

- A spec existe e está `⏳active` em `.github/specs/` (`<dominio>-<feature>.md`), com rotas,
  payloads, tabelas e permissões definidos. Sem spec, não comece.
- Leia `memory/issues.md` e as decisões DEC-001 (RLS), DEC-004 (RBAC) e DEC-006 (forma do módulo).
- Confira em `docs/PERMISSIONS_MAP.md` se as permissões já existem (várias já estão declaradas).

## Passos

1. **Esqueleto** — `app/modules/scheduling/` com `__init__.py` (docstring do domínio),
   `router/__init__.py`, `service/__init__.py`, `repository/__init__.py`, `model/__init__.py`,
   `schemas.py` e `public.py`. O teste `test_module_layout` falha enquanto faltar algum.
2. **Models** — um arquivo por agregado em `model/`, enums em `model/enums.py`. Tabela de
   barbearia herda `Base, TenantMixin, TimestampMixin` de `app.core.model_base`; enum com
   `pg_enum(...)`; PK com `uuid_pk()`. FK para tabelas do identity por string
   (`ForeignKey("units.id")`) — não importe models de outro módulo.
3. **Registry** — adicione `from app.modules.scheduling import model as scheduling_models  # noqa`
   em `app/core/model_registry.py`.
4. **Migration** — `cd backend && .venv/bin/alembic revision --autogenerate -m "scheduling"`, revise
   à mão e acrescente, para cada tabela de barbearia, a mesma chamada `apply_rls("<tabela>")` da
   0001 (copie a função ou extraia-a para um helper em `alembic/`). Rode `make migrate` e
   `alembic check`.
5. **Repository** — todo SQL em `repository/<agregado>.py`, funções que recebem `AsyncSession`.
   Não filtre por `tenant_id`: a RLS já filtra. Aplique o escopo de unidade/barbeiro recebendo os
   filtros como parâmetro (`unit_ids: list[UUID] | None`, `barber_id`).
6. **Service** — um arquivo por ação. Recebe `session`, `ctx: AuthContext` e o schema de entrada;
   levanta `BadRequest/NotFound/Conflict/Forbidden` de `app.core.exceptions`. Aplica `ctx.scope`:
   `OWN` → filtra por `ctx.barber_id`; `UNIT` → `ctx.unit_filter`.
7. **Router** — um arquivo por recurso; guardas com
   `Annotated[AuthContext, Depends(require(Permission.APPOINTMENT_READ))]`, tudo importado de
   `app.modules.identity.public`. Handler fino: chama o service e devolve.
8. **Registro no app** — `router/__init__.py` exporta `routers = [...]`; `app/main.py` inclui.
9. **Fronteiras** — acrescente `"app.modules.scheduling"` em `containers` do contrato de camadas
   em `pyproject.toml`.
10. **Permissões** — permissão nova: enum + mapa de cada cargo em `identity/permissions.py`, depois
    `UPDATE_CONTRACT_SNAPSHOTS=1` só no `test_permissions_doc.py` para atualizar o
    `docs/PERMISSIONS_MAP.md`.
11. **Testes** — `tests/test_scheduling/`, um teste por regra de negócio da spec, incluindo
    isolamento (o dado de uma barbearia não aparece em outra) e escopo (barbeiro só vê o próprio).
    Use os helpers de `tests/conftest.py` (`create_shop`, `login`, `auth`).
12. **Snapshots** — as rotas e tabelas novas mudam `openapi.json`, `routes.json` e
    `db_schema.json`. Regenere com `UPDATE_CONTRACT_SNAPSHOTS=1` e **leia o diff**: só pode conter
    o que a spec descreve.
13. **Documentação** — checkboxes da spec, `memory/progress.md`, endpoints no `README.md`.

## Verificação

```bash
make check-backend   # pytest + ruff + lint-imports + alembic check
```

## Armadilhas conhecidas

- Esquecer o `apply_rls` na migration: a tabela fica visível para todas as barbearias. O teste de
  isolamento do módulo é o que pega isso — não pule.
- `server_default`/`default` divergentes entre model e migration fazem o `alembic check` acusar.
- Importar `app.modules.identity.service...` em vez do `public`: o `test_module_layout` falha.
- O nome da função do handler vira `operationId`; renomear depois muda o contrato.
