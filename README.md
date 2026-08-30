# Navalha.app

SaaS de gestão para barbearias, com atendimento automatizado no WhatsApp.

```
frontend/   React 18 + Vite + TypeScript — landing e painel
backend/    FastAPI + PostgreSQL — core-api (cadastros, agenda, CRM)
infra/      init do Postgres (role de runtime)
```

## Subir

Cada projeto tem seu próprio `docker-compose.yml` e seus próprios containers.
Podem subir juntos ou separados, em qualquer ordem:

```bash
docker compose -f backend/docker-compose.yml up -d
docker compose -f frontend/docker-compose.yml up -d
```

Ou, de dentro de cada pasta:

```bash
cd backend  && docker compose up -d
cd frontend && docker compose up -d
```

| Container | Projeto | Endereço | O que é |
|---|---|---|---|
| `web` | `navalha-frontend` | http://localhost:5173 | Vite dev server, com HMR |
| `core-api` | `navalha-backend` | http://localhost:8000 | FastAPI (docs em `/docs`) |
| `db` | `navalha-backend` | localhost:**5433** | PostgreSQL 16 |
| `redis` | `navalha-backend` | localhost:**6380** | Redis 7 |

Os dois projetos compartilham uma rede Docker chamada `navalha`. Quem subir
primeiro a cria; o outro se conecta. É por ela que o dev server alcança a API
pelo nome `core-api`.

As migrations rodam sozinhas na subida do `core-api` (`alembic upgrade head`).

> Portas 5433 e 6380 de propósito: 5432 e 6379 costumam estar ocupadas por
> instalações locais.

O frontend também roda sozinho, sem o backend — as telas ainda usam os dados de
demonstração de `frontend/src/data/`.

## Dia a dia

Os dois serviços de aplicação recarregam a quente: `./frontend` e
`./backend/app` estão montados nos containers, então editar no editor reflete
direto, sem rebuild.

```bash
docker compose -f frontend/docker-compose.yml logs -f    # acompanhar
docker compose -f backend/docker-compose.yml down        # parar
docker compose -f backend/docker-compose.yml down -v     # parar e apagar o banco
```

Rebuild só é necessário quando muda dependência (`package.json`,
`pyproject.toml`) ou o Dockerfile:

```bash
docker compose -f frontend/docker-compose.yml build
```

## Verificar

```bash
curl localhost:8000/health

curl -X POST localhost:8000/auth/register-shop \
  -H 'Content-Type: application/json' \
  -d '{"shop_name":"Barbearia Central","slug":"central",
       "owner_name":"Miguel","email":"miguel@central.com","password":"senha-forte-123"}'
```

Em desenvolvimento o header `X-Tenant-Slug` substitui o subdomínio, para não
precisar mexer no `hosts`:

```bash
curl -X POST localhost:8000/auth/login \
  -H 'Content-Type: application/json' -H 'X-Tenant-Slug: central' \
  -d '{"email":"miguel@central.com","password":"senha-forte-123"}'
```

## Imagem de produção do frontend

O `Dockerfile` do frontend tem dois alvos. O compose usa `dev` (Vite com HMR);
`prod` compila e serve os estáticos por nginx, com fallback de SPA e cache
correto — `index.html` sem cache, assets com hash cacheados por um ano.

```bash
docker build -t navalha-web:prod --target prod ./frontend
docker run --rm -p 8080:80 navalha-web:prod
```

## Rodar fora do Docker

Cada parte tem seu README: [frontend/README.md](frontend/README.md) e
[backend/README.md](backend/README.md). O banco e o Redis podem continuar no
compose:

```bash
docker compose -f backend/docker-compose.yml up -d db redis
```

## Notas

- **O frontend ainda não consome a API.** As telas rodam com os dados de
  demonstração de `frontend/src/data/`; `frontend/src/api/client.ts` já tem a
  ponte pronta e passa a chamar o backend quando `VITE_API_URL` for definida.
- **Convenção de código:** identificadores, tabelas, colunas e rotas da API em
  inglês. Em português ficam as mensagens de erro da API, o texto da interface
  e as URLs que o usuário final vê (`/app/agenda`, `/convite/:token`).
- **Isolamento entre barbearias** é feito com Row-Level Security do PostgreSQL.
  Os dois detalhes que fazem isso valer (role de runtime sem privilégio e
  `SET LOCAL` dentro da transação) estão explicados em
  [backend/README.md](backend/README.md).
