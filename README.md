# Navalha.app

SaaS de gestão para barbearias, com atendimento automatizado no WhatsApp.

```
frontend/   React 18 + Vite + TypeScript — landing e painel
backend/    FastAPI + PostgreSQL — core-api (cadastros, agenda, CRM)
infra/      init do Postgres (role de runtime)
docs/       desenvolvimento e contribuição
.github/    CI e templates de issue/PR
```

Cada projeto tem seu `CLAUDE.md` e sua camada de contexto `.github/` (regras,
specs, decisões, problemas conhecidos). Comece por [`CLAUDE.md`](CLAUDE.md),
[`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md) e
[`docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md).

```bash
make help     # todos os atalhos
make up       # sobe tudo
make check    # o portão que o CI roda
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
| `migrate` | `navalha-backend` | — | one-shot: migra o controle e cada barbearia, e sai |
| `db` | `navalha-backend` | localhost:**5433** | PostgreSQL 16 |
| `redis` | `navalha-backend` | localhost:**6380** | Redis 7 |

Os dois projetos compartilham uma rede Docker chamada `navalha`. Quem subir
primeiro a cria; o outro se conecta. É por ela que o dev server alcança a API
pelo nome `core-api`.

As migrations **não** rodam no boot da API: o serviço one-shot `migrate` roda
antes dela (controle, depois cada barbearia, em ordem) e encerra. Para rodar de
novo: `make migrate`.

> Portas 5433 e 6380 de propósito: 5432 e 6379 costumam estar ocupadas por
> instalações locais.

O frontend também roda sozinho, sem o backend — fora o login, as telas usam os
dados de demonstração de `frontend/src/features/*/api/*.mock.ts`.

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
```

Para criar uma barbearia e entrar no painel, siga
[docs/DEVELOPMENT.md](docs/DEVELOPMENT.md#primeiro-acesso-ao-painel): chave do
Core → `POST /core/tenants` → link de primeiro acesso → `/convite/<token>`.

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

- **Integração:** o login, a sessão e o primeiro acesso (`/convite/:token`)
  usam a API de verdade; agenda, conversas, cadastros e dashboard ainda usam os
  dados de demonstração de `frontend/src/features/*/api/*.mock.ts`, até o
  backend ter os módulos correspondentes.
- **Convenção de código:** identificadores, tabelas, colunas e rotas da API em
  inglês. Em português ficam as mensagens de erro da API, o texto da interface
  e as URLs que o usuário final vê (`/app/agenda`, `/convite/:token`).
- **Multi-tenancy:** um schema PostgreSQL por barbearia (`tenant_<slug>`); o
  `public` é só o control plane. Cada barbearia atende no próprio subdomínio
  (ou domínio) e nasce pelo control plane `/core/*`, nunca por cadastro
  público. Detalhes em [backend/README.md](backend/README.md) e
  [docs/multi-tenant-architecture-v2.md](docs/multi-tenant-architecture-v2.md)
  (o desenho de referência, do ClaraCRM).
