# Desenvolvimento

Como subir, testar e usar o Navalha na sua máquina.

## Pré-requisitos

- Docker (Docker Desktop no macOS/Windows).
- Para rodar testes e lint fora do container: Python 3.12 e Node 22 (Node 20 também funciona
  localmente; o CI e a imagem usam 22).
- `make` (no Windows, via Git Bash).

## Subir tudo

```bash
make up          # backend (db, redis, core-api) + frontend (web)
make ps
```

| Serviço | Endereço | O que é |
|---|---|---|
| `web` | http://localhost:5173 | Vite com HMR — landing `/`, login `/entrar`, painel `/app` |
| `core-api` | http://localhost:8000 | FastAPI — docs em `/docs` |
| `db` | localhost:**5433** | PostgreSQL 16 (usuário admin `navalha`; runtime `navalha_app`) |
| `redis` | localhost:**6380** | Redis 7 (ainda não usado) |

As migrations rodam sozinhas na subida do `core-api`. Código de `backend/app` e `frontend/` é
montado nos containers: editar reflete na hora. Rebuild (`make build`) só quando muda dependência
ou Dockerfile.

## Primeiro acesso ao painel

Barbearias nascem **só pelo control plane** (`/core/*`), como fará o Core da plataforma a partir da
venda de um plano (backend DEC-014). Em dev:

```bash
# 1. Uma chave do Core (o valor aparece uma vez — guarde)
make core-key NAME=core-dev SCOPES=tenant:read,tenant:provision,tenant:destroy

# 2. Provisionar (202 + job: schema, migrations, grants, unidade inicial, convite do dono)
curl -X POST localhost:8000/core/tenants -H "X-Core-Key: $KEY" -H 'Content-Type: application/json' \
  -d '{"slug":"central","name":"Barbearia Central","owner":{"name":"Seu Nome","email":"voce@central.com"}}'

# 3. Consultar até "active" — o invite_link vem UMA vez (guarde antes de processar a resposta)
curl -s localhost:8000/core/tenants/<tenant_id> -H "X-Core-Key: $KEY"
```

Abra `http://localhost:5173/convite/<token>` — o token é o fim do `invite_link`; o host
`<slug>.navalha.local` do link não resolve em dev (backend ISS-015). A tela pede a barbearia
(`central`), mostra o convite, você define a senha e já entra no painel.

Perdeu o link? `POST /core/tenants/<tenant_id>/invite` emite outro e invalida o anterior.

Em localhost não há subdomínio, por isso o login e o convite pedem a barbearia (vira o header
`X-Tenant-Slug`). Contrato completo do control plane: `GET /core/openapi.json` com a `X-Core-Key`.

> A conta de **suporte da plataforma** (`make seed-admin`) não entra no painel: ela vive fora das
> barbearias e ainda não tem rota de login (backend ISS-005).

## Testes e lint

```bash
make setup-backend     # uma vez: backend/.venv + backend/.env
make setup-frontend    # uma vez: npm ci

make check             # tudo (o mesmo portão do CI)
make test-backend      # pytest contra o Postgres do compose (precisa de `make up`)
make lint-backend      # ruff + lint-imports
make test-frontend     # Vitest
make lint-frontend     # ESLint + fronteiras entre features
```

Os testes do backend usam o banco de desenvolvimento e criam barbearias com slug aleatório
(`t<hex>`) que não são apagadas (backend ISS-006).

## Banco

Um schema por barbearia (`tenant_<slug>`) e o `public` só com o control plane (backend DEC-011).

```bash
make psql              # como dono do schema
make migrate           # controle + cada barbearia, em ordem (serviço one-shot)
cd backend && .venv/bin/python -m app.management.migrate          # só lista o que rodaria

# migration nova de tabela de barbearia (conjunto tenant, revisão tNNNN):
cd backend && .venv/bin/alembic -n tenant -x schema=tenant_template \
    revision --autogenerate --rev-id t0002 -m "descricao"
# migration nova de controle (public, revisão cNNNN):
cd backend && .venv/bin/alembic -n control revision --autogenerate --rev-id c0002 -m "descricao"
```

Conferir os dados de uma barbearia no `psql`:

```sql
\dn                                  -- os schemas: public + tenant_<slug>
SELECT * FROM tenant_central.users;  -- sempre qualificado; nada de SET search_path
SELECT slug, status, schema_version FROM public.tenants;
```

## Problemas comuns

- **Login 401 com a senha certa:** confira se não colou um espaço no fim (frontend ISS-006).
- **503 "Barbearia em manutenção":** o schema dela está atrás das migrations do build — `make migrate`.
- **403 "Assinatura inativa":** a barbearia foi suspensa pelo control plane (`.../resume` reativa).
- **Variável do `.env` sem efeito:** o nome precisa bater com `backend/app/core/config.py`;
  nome errado é ignorado sem aviso (backend ISS-001). Refaça com `cp backend/.env.example backend/.env`.
- **Dependência nova do frontend não aparece no container:** `make build` (frontend ISS-007).
