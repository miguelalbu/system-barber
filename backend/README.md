# Navalha · Core API

Sistema de registro do SaaS de barbearias. FastAPI + PostgreSQL, multi-tenant
com isolamento por Row-Level Security.

Este primeiro bloco entrega o núcleo de identidade: provisionamento de
barbearia, login, RBAC e convite de equipe. Agenda, financeiro e CRM entram como
módulos seguintes, sobre a mesma base de isolamento.

> **Convenção:** código em inglês (identificadores, tabelas, colunas, rotas).
> Ficam em português: as mensagens de erro da API, porque vão direto para a tela
> do dono da barbearia, e esta documentação.

## Rodar

Com Docker (sobe Postgres, Redis e a API, com migrations e reload):

```bash
docker compose up -d          # http://localhost:8000/docs
docker compose logs -f core-api
```

Direto na máquina, com o banco no compose:

```bash
docker compose up -d db redis
python -m venv .venv && ./.venv/Scripts/python.exe -m pip install -e ".[dev]"
./.venv/Scripts/python.exe -m alembic upgrade head
./.venv/Scripts/python.exe -m uvicorn app.main:app --reload
```

```bash
./.venv/Scripts/python.exe -m pytest      # 21 testes
./.venv/Scripts/python.exe -m ruff check app tests
```

## Conta de plataforma (super admin)

A conta de suporte da plataforma vive fora de qualquer barbearia e fora do RBAC
de tenant — é a única tabela de identidade sem RLS. Não nasce de migration nem
de cadastro; é criada pelo seed:

```bash
docker compose exec core-api python -m app.seed platform-admin \
    --email suporte@navalha.app --name "Seu Nome"
```

Sem `--password`, uma senha forte é gerada e exibida **uma única vez** — guarde
na hora. Os valores também podem vir de `SEED_ADMIN_EMAIL`, `SEED_ADMIN_NAME` e
`SEED_ADMIN_PASSWORD`.

Rodar de novo é seguro: uma conta existente não é tocada. Para redefinir a
senha, `--update-password` (omitir `--name` mantém o nome atual).

> **Ainda não há login de plataforma.** A conta é gravada e a senha validada,
> mas nenhuma rota autentica com ela — o fluxo de suporte cross-tenant é um
> bloco próprio, com tipo de token e regras de auditoria separados.

> O Postgres do compose sobe na porta **5433** do host, porque a 5432 costuma
> estar ocupada por uma instalação local. O Redis vai na **6380**.

## Como o isolamento funciona

Três camadas, nesta ordem:

**1. O domínio identifica a barbearia.** Cada uma atende em
`<slug>.navalha.app`, ou em domínio próprio apontado por CNAME
(`tenants.custom_domain`). O tenant vem do header `Host` — nunca de algo que o
cliente escolhe. Como o tenant já é conhecido antes do login, o e-mail pode ser
único por barbearia e o login não precisa perguntar "qual barbearia?".

**2. A RLS isola os dados.** Toda tabela de barbearia tem `tenant_id` e uma
policy que o Postgres injeta em toda query:

```sql
CREATE POLICY tenant_isolation ON users
    USING (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid)
    WITH CHECK (...);
```

`SELECT * FROM users` sem WHERE já vem filtrado. Esquecer o filtro devolve
**zero linhas**, nunca dados de outra barbearia.

**3. O RBAC limita o que o usuário faz.** Ver abaixo.

### Dois detalhes que fazem a RLS valer ou não valer nada

Ambos já estão resolvidos no código, mas precisam ser preservados:

**A aplicação conecta com um role sem privilégio.** Superusuário e dono de
tabela **ignoram RLS**. O usuário administrativo do Postgres é superusuário por
padrão — se a API conectar com ele, as policies não fazem nada e o vazamento é
silencioso. Por isso existem duas URLs:

| Variável | Role | Para quê |
|---|---|---|
| `DATABASE_URL` | `navalha_app` | runtime — sem SUPERUSER, sem BYPASSRLS |
| `DATABASE_URL_MIGRATIONS` | `navalha` | migrations — dono do schema |

O role de runtime nasce em `infra/postgres/init/01-app-role.sql`, e a migration
concede os privilégios (com `ALTER DEFAULT PRIVILEGES`, para as tabelas futuras
já nascerem acessíveis).

**O tenant é fixado com `SET LOCAL`, dentro da transação.** Em `app/db.py`:

```python
SELECT set_config('app.tenant_id', :tid, true)   # o `true` é o "local"
```

Sem o `true`, o valor gruda na conexão do pool e o próximo request — de outra
barbearia — herda o contexto. É o pior bug possível neste sistema.

### Quando uma barbearia precisar de banco próprio

`app/db.py` é o **único** lugar que abre sessão. Três regras mantêm essa porta
aberta sem custo hoje:

1. `tenant_id` em toda tabela, mesmo que um dia cada banco tenha um tenant só.
2. Todo acesso passa por `tenant_session()`. Trocar "um banco com RLS" por "um
   banco por barbearia" é mudança em um arquivo.
3. Nenhuma query cruza tenants no código de negócio. Quando precisar (billing,
   métricas da plataforma), isolar em um módulo explícito.

## RBAC

O código **nunca pergunta o cargo, pergunta a permissão**:

```python
@router.get("/appointments")
def list_appointments(ctx = Depends(require(P.APPOINTMENT_READ))):
    q = select(Appointment)                     # tenant já garantido pela RLS
    if ctx.scope is Scope.OWN:
        q = q.where(Appointment.barber_id == ctx.barber_id)
    elif ctx.scope is Scope.UNIT and not ctx.all_units:
        q = q.where(Appointment.unit_id.in_(ctx.units))
```

O mapa cargo → permissão vive só em `app/permissions.py`. Cada permissão tem um
**escopo**, que é o eixo que o RBAC puro não cobre:

| Scope | Alcance |
|---|---|
| `all` | toda a barbearia |
| `unit` | apenas as unidades ligadas ao usuário (vazio = todas) |
| `own` | apenas os registros do próprio barbeiro |

Cargos: `owner` (tudo), `manager` (operação, escopo de unidade, sem assinatura),
`receptionist` (agenda, clientes, comandas — sem financeiro), `barber` (a
própria agenda e a própria comissão).

## Modelo de dados

**Control plane** — sem `tenant_id`, sem RLS:

- `tenants` — barbearia, slug, domínio próprio, plano, status
- `platform_admins` — equipe da plataforma, para suporte

**Dados da barbearia** — com `tenant_id` e RLS:

- `units` — filiais
- `users` — login da equipe; e-mail único **por barbearia**
- `user_units` — unidades visíveis; **vazio = todas**
- `barbers` — o profissional como recurso de agenda
- `refresh_tokens` — hash do token, com revogação
- `invites` — como um usuário nasce sem senha hardcoded

Dois pontos que costumam confundir:

**`Barber` não é `User`.** Barbeiro é a coluna do calendário: tem comissão,
serviços e horários. `barbers.user_id` é nullable de propósito — existe barbeiro
que nunca vai abrir o app, e a recepção agenda por ele.

**Cliente final não é `User`.** O cliente que corta o cabelo vai para `clients`,
com autenticação própria por telefone. É outro fluxo, no bloco seguinte.

## Autenticação

Access token JWT de 15 min + refresh opaco rotativo de 30 dias, guardado como
hash.

O access token carrega `sub`, `tid`, `rol` e `bid`. **As permissões não vão no
token** — são resolvidas no servidor a partir do cargo, então mudar o mapa vale
na hora em vez de esperar os tokens em circulação expirarem.

O refresh rotaciona: o token usado é revogado ao ser trocado. Token de uma
barbearia apresentado no domínio de outra é rejeitado com 403, mesmo sendo
assinado por nós.

## Endpoints

```
POST   /auth/register-shop        provisiona barbearia + primeiro dono (público)
POST   /auth/login                tenant vem do domínio
POST   /auth/refresh              rotativo
POST   /auth/logout               revoga o refresh
GET    /auth/me                   usuário, barbearia, unidades e permissões

GET    /tenant                    dados da barbearia
PATCH  /tenant                    nome e domínio próprio       [tenant:configure]
GET    /tenant/units              unidades visíveis

GET    /team                      membros                      [team:read]
POST   /team/invites              convida                      [team:manage]
GET    /team/invites              pendentes                    [team:read]
POST   /team/invites/accept       cria o login (público)
DELETE /team/{user_id}            desativa                     [team:manage]

GET    /health
```

Em desenvolvimento, o header `X-Tenant-Slug` substitui o subdomínio, para testar
com curl sem mexer no `hosts`. Em produção ele é ignorado.

```bash
curl -X POST localhost:8000/auth/login \
  -H 'Content-Type: application/json' -H 'X-Tenant-Slug: central' \
  -d '{"email":"miguel@central.com","password":"senha-forte-123"}'
```

## Pendências antes de produção

- **`JWT_SECRET`** — gerar com `python -c "import secrets; print(secrets.token_urlsafe(48))"`.
- **Senha do `navalha_app`** — a de dev está no init SQL; em produção vem de secret.
- **Envio de e-mail** — hoje o convite devolve o link na resposta, para o dono
  repassar por WhatsApp. Trocar por e-mail transacional.
- **Rate limit no login** — o Redis já está de pé, mas ainda não é usado.
- **Detecção de reuso de refresh token** — hoje o reuso apenas falha; deveria
  revogar toda a família de tokens e registrar o evento.
- **Verificação de e-mail** e **recuperação de senha**.
- **Login da conta de plataforma** — a conta existe (ver seed), falta a rota de
  autenticação, com tipo de token próprio e auditoria de acesso cross-tenant.
- **TLS e domínio próprio** — Caddy ou Traefik com ACME sob demanda, para o
  cliente apontar CNAME e o certificado ser emitido sozinho.

## Próximos blocos

1. Catálogo — serviços, combos, clubes, planos de assinatura
2. Agenda — disponibilidade, agendamentos, bloqueios (o núcleo que a IA vai chamar)
3. Clientes e autenticação do cliente final (telefone + OTP)
4. Financeiro — comandas, comissões, pagamentos
5. Eventos de domínio no RabbitMQ, e então o `ai-agent`
