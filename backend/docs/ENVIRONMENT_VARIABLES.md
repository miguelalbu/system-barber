# Variáveis de ambiente — backend

Lidas por `app/core/config.py` (pydantic-settings) do ambiente e do arquivo `.env` na pasta
`backend/`. Os nomes não diferenciam maiúsculas de minúsculas.

> **Atenção:** o `Settings` usa `extra="ignore"`. Uma variável com nome errado é **ignorada sem
> aviso** e o valor padrão entra no lugar (ISS-001). Ao criar uma variável, adicione o campo em
> `config.py`, a linha em `.env.example` e a linha nesta tabela.

| Variável | Padrão | Para quê |
|---|---|---|
| `ENVIRONMENT` | `dev` | `dev` habilita o header `X-Tenant-Slug` (DEC-002). Qualquer outro valor desliga. |
| `DATABASE_URL` | `postgresql+asyncpg://navalha_app:navalha_app@localhost:5433/navalha` | Runtime. Role **sem** SUPERUSER/BYPASSRLS — é o que faz a RLS valer (DEC-001). |
| `DATABASE_URL_MIGRATIONS` | `postgresql+asyncpg://navalha:navalha@localhost:5433/navalha` | Só Alembic. Dono do schema. Nunca usar em runtime. |
| `REDIS_URL` | `redis://localhost:6380/0` | Provisionado, ainda não usado. |
| `JWT_SECRET` | `change-me-in-production` | Assinatura HS256 do access token. Mínimo 32 bytes (ISS-002). |
| `JWT_ALGORITHM` | `HS256` | |
| `ACCESS_TOKEN_MINUTES` | `15` | Vida do access token. |
| `REFRESH_TOKEN_DAYS` | `30` | Vida do refresh token rotativo. |
| `INVITE_EXPIRY_DAYS` | `7` | Validade do link de convite. |
| `BASE_DOMAIN` | `navalha.local` | Cada barbearia atende em `<slug>.<BASE_DOMAIN>`; também libera o CORS desses subdomínios. |
| `ALLOW_SELF_SIGNUP` | `true` | `POST /auth/register-shop` aberto. Desligue para provisionar à mão. |
| `CORS_ORIGINS` | `["http://localhost:5173"]` | Lista JSON de origens extras (ex.: domínio próprio de um cliente). |

## Só para o seed (`app/management/seed.py`)

| Variável | Para quê |
|---|---|
| `SEED_ADMIN_EMAIL` | E-mail da conta de suporte da plataforma. |
| `SEED_ADMIN_NAME` | Nome exibido. Omitido ao atualizar = mantém o atual. |
| `SEED_ADMIN_PASSWORD` | Sem ela, o seed gera uma senha forte e a mostra uma única vez. Mínimo 12 caracteres. |

## No Docker Compose

`docker-compose.yml` define as variáveis do container `core-api` diretamente (hosts `db` e `redis`
da rede interna) e não lê o `.env`. O `.env` vale para o que roda **no host**: testes, Alembic e o
seed via venv.
