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

O banco começa vazio. Crie uma barbearia de desenvolvimento:

```bash
curl -X POST localhost:8000/auth/register-shop -H 'Content-Type: application/json' -d '{
  "shop_name": "Barbearia Demo", "slug": "demo",
  "owner_name": "Seu Nome", "email": "dono@navalha.app", "password": "navalha123"}'
```

Entre em http://localhost:5173/entrar com **Barbearia** `demo`, o e-mail e a senha acima. Em
localhost não há subdomínio, por isso o login pede a barbearia (vira o header `X-Tenant-Slug`).

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

```bash
make psql              # como dono do schema: IGNORA a RLS — cuidado ao conferir isolamento
make migrate           # alembic upgrade head no container
cd backend && .venv/bin/alembic revision --autogenerate -m "descricao"   # migration nova
```

Para ver o banco como a aplicação vê (com RLS), conecte como `navalha_app` e fixe o tenant:

```sql
SELECT set_config('app.tenant_id', '<uuid da barbearia>', false);
SELECT * FROM users;
```

## Problemas comuns

- **Login 401 com a senha certa:** confira se não colou um espaço no fim (frontend ISS-006).
- **Variável do `.env` sem efeito:** o nome precisa bater com `backend/app/core/config.py`;
  nome errado é ignorado sem aviso (backend ISS-001). Refaça com `cp backend/.env.example backend/.env`.
- **Dependência nova do frontend não aparece no container:** `make build` (frontend ISS-007).
