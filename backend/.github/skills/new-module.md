# Criar um módulo de domínio novo

**Quando usar:** ao começar um bloco novo do produto (catálogo, agenda, clientes, financeiro,
conversas) no backend. Exemplo usado abaixo: `scheduling`.

## Antes de começar

- A spec existe e está `⏳active` em `docs/specs/` (`<dominio>-<feature>.md`), com rotas,
  payloads, tabelas e permissões definidos. Sem spec, não comece.
- Leia `memory/issues.md` e as decisões DEC-011 (schema por barbearia), DEC-004 (RBAC) e DEC-006
  (forma do módulo).
- Confira em `docs/PERMISSIONS_MAP.md` se as permissões já existem (várias já estão declaradas).

## Passos

1. **Esqueleto** — `app/modules/scheduling/` com `__init__.py` (docstring do domínio),
   `router/__init__.py`, `service/__init__.py`, `repository/__init__.py`, `model/__init__.py`,
   `schemas.py` e `public.py`. O teste `test_module_layout` falha enquanto faltar algum.
2. **Models** — um arquivo por agregado em `model/`, enums em `model/enums.py`. Tabela de barbearia
   herda `TenantBase, TimestampMixin` de `app.core.model_base` — **sem `tenant_id`**: o schema é a
   fronteira. Enum com `pg_enum(...)`; PK com `uuid_pk()`. FK para tabelas do identity por string e
   sem schema (`ForeignKey("units.id")` — o `MetaData` da `TenantBase` resolve para o mesmo schema);
   não importe models de outro módulo. Nunca FK para tabela de controle (`ControlBase`).
3. **Registry** — adicione `from app.modules.scheduling import model as scheduling_models  # noqa`
   em `app/core/model_registry.py`.
4. **Migration** — no conjunto de tenant, sem nomear schema:
   `cd backend && .venv/bin/alembic -n tenant -x schema=tenant_template revision --autogenerate
   --rev-id t0002 -m "scheduling"` (rode antes `python -m app.management.migrate --apply --template`).
   Revise à mão. **Só expand/contract**: os schemas migram um a um, e o build atende versões
   vizinhas por alguns minutos. Não precisa de `GRANT`: os default privileges do provisionamento já
   cobrem as tabelas novas. Depois: `make migrate` (todas as barbearias) e `make check-backend`.
5. **Repository** — todo SQL em `repository/<agregado>.py`, funções que recebem `AsyncSession` (a
   sessão já está no schema da barbearia). Aplique o escopo de unidade/barbeiro recebendo os filtros
   como parâmetro (`unit_ids: list[UUID] | None`, `barber_id`). SQL cru só qualificado com
   `quote_identifier(schema)` — nunca `SET search_path`.
6. **Service** — um arquivo por ação. Recebe `session`, `ctx: AuthContext` e o schema de entrada;
   levanta `BadRequest/NotFound/Conflict/Forbidden` de `app.core.exceptions`. Aplica `ctx.scope`:
   `OWN` → filtra por `ctx.barber_id`; `UNIT` → `ctx.unit_filter`. Cache ou estado em memória de
   processo sempre com chave que inclua o tenant (`ctx.tenant.id`).
7. **Router** — um arquivo por recurso; guardas com
   `Annotated[AuthContext, Depends(require(Permission.APPOINTMENT_READ))]` e `SessionDep`, tudo de
   `app.modules.identity.public`. Handler fino: chama o service e devolve.
8. **Registro no app** — `router/__init__.py` exporta `routers = [...]`; `app/main.py` inclui.
9. **Fronteiras** — acrescente `"app.modules.scheduling"` em `containers` do contrato de camadas
   em `pyproject.toml`.
10. **Permissões** — permissão nova: enum + mapa de cada cargo em `identity/permissions.py`, depois
    `UPDATE_CONTRACT_SNAPSHOTS=1` só no `test_permissions_doc.py` para atualizar o
    `docs/PERMISSIONS_MAP.md`.
11. **Testes** — `tests/test_scheduling/`, um teste por regra de negócio da spec, e o teste de
    **cruzamento**: duas barbearias (`create_shop` duas vezes), o dado de A não aparece nem é
    alterável em B. Escopo: barbeiro só vê o próprio. Helpers em `tests/conftest.py` (`create_shop`,
    `login`, `auth`); as barbearias de teste são destruídas no fim da sessão.
12. **Snapshots** — as rotas e tabelas novas mudam `openapi.json`, `routes.json` e
    `db_schema.json`. Regenere com `UPDATE_CONTRACT_SNAPSHOTS=1` e **leia o diff**: só pode conter
    o que a spec descreve.
13. **Documentação** — checkboxes da spec, `memory/progress.md`, endpoints no `README.md`.

## Verificação

```bash
make check-backend   # pytest + ruff + lint-imports + alembic check (controle e tenant)
```

## Armadilhas conhecidas

- Usar `ControlBase` (ou `public`) para dado de barbearia: vira dado compartilhado entre todas.
- Migration de tenant que renomeia/remove coluna em um passo só (não é expand/contract): o build
  antigo quebra nos schemas ainda não migrados durante o deploy.
- `server_default`/`default` divergentes entre model e migration fazem o `alembic check` acusar.
- Importar `app.modules.identity.service...` em vez do `public`: o `test_module_layout` falha.
- O nome da função do handler vira `operationId`; renomear depois muda o contrato.
