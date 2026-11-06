# Multi-tenancy no ClaraCRM — schema por tenant (v2)

Documento de arquitetura. **Substitui `multi-tenant-architecture.md`**, que assumia
subdomínio por cliente e um schema de controle chamado `platform` — duas premissas
que foram descartadas.

**Stack:** Next.js 16 (App Router) · Prisma 7.10 com driver adapter `@prisma/adapter-pg`
· PostgreSQL · NextAuth v4 (JWT) · Cloudflare R2 · Docker atrás de Load Balancer.

---

## 1. As duas restrições que definem o desenho

1. **URL única: `crm.claraaiapp.store`.** Não existe subdomínio nem domínio por
   cliente. Mesma infra, mesmo banco, mesma aplicação, mesmo host.
2. **Não existe schema `platform`.** Tudo que é global vive no **`public`**.

Elas parecem pequenas e mudam três coisas de fundo:

| | Consequência |
|---|---|
| **Login** | Sem host para identificar o cliente, o tenant tem de ser resolvido **pelo e-mail**. Exige um diretório global de login no `public`. |
| **`public`** | Hoje o `public` contém as tabelas do CRM. Se ele passa a ser o schema de controle, **os dados atuais precisam sair dele** (§3). |
| **Defesa** | Sem subdomínio não há checagem host↔token. O **JWT é a única fonte de verdade** do tenant, então a integridade dele pesa mais. |

Também há um ganho real: com uma URL só, a configuração na Meta fica única —
um callback de webhook, um redirect URI do Embedded Signup, um App ID. Nada
disso se multiplica por cliente.

---

## 2. O desenho

```
postgres (um banco)
│
├── public                        ← controle + login, NENHUM dado de CRM
│   ├── Tenant                    id, slug, schemaName, status, dekWrapped, schemaVersion
│   │                             + externalTenantId → o id do cliente no core (§6)
│   ├── AgentDirectory            email (UNIQUE global) → tenantId, agentId, active
│   ├── WhatsappNumberRoute       phoneNumberId (UNIQUE) → tenantId
│   ├── WhatsappAccount           App Secret + verify token + apiVersion  (globais — §5)
│   ├── ApiKey                    keyHash, tenantId, scopes, revokedAt  (por tenant)
│   ├── CoreKey                   keyHash, scopes, ipAllowlist  (credencial do core — §6)
│   ├── ProvisioningJob           tenantId, step, status, log
│   ├── CoreAuditLog              toda chamada ao control plane
│   └── _prisma_migrations        histórico do schema de controle
│
├── tenant_clara                  ← 16 tabelas do CRM + 8 enums + _prisma_migrations
├── tenant_acme                   ← idem, estrutura idêntica
└── tenant_...
```

Duas coisas nunca acontecem: **nenhuma foreign key cruza schemas**, e
**nenhum schema de tenant contém dado de outro tenant**.

### Por que os enums ficam duplicados em cada schema

Cada schema de tenant tem sua própria cópia dos 8 tipos enum. É o que
`prisma migrate deploy --schema=<nome>` produz naturalmente, sem caso especial, e
mantém **o mesmo conjunto de migrations para todos os tenants**.

A alternativa — enums compartilhados no `public` — parece mais limpa mas obriga o
role de cada tenant a ter `USAGE` no `public` para resolver os tipos, e aí o
schema de controle fica ao alcance dele. Duplicar tipos é barato (são definições,
não dados) e deixa os grants perfeitos: **tenant nenhum precisa de acesso ao
`public`.**

---

## 3. Migração do estado atual (faça primeiro, é pré-requisito)

Hoje o `public` contém as 16 tabelas do CRM. Como o `public` passa a ser o schema
de controle, esses dados precisam ser movidos para um schema de tenant real.

**Não pule isso e não tente conviver com as duas coisas no `public`.** Se os dados
do primeiro cliente ficarem no `public` junto com o catálogo, o role
`tenant_clara` precisará de acesso ao `public` para ler os próprios dados — e
enxergará `Tenant`, `AgentDirectory` e `ApiKey` de todos os clientes. É
exatamente o vazamento que a arquitetura existe para impedir.

A boa notícia: é barato. `ALTER TABLE ... SET SCHEMA` é uma operação de catálogo,
não copia dados, e leva as FKs, índices e sequences junto.

O script pronto está em **`scripts/00-move-public-to-tenant.sql`** — validado num
banco descartável: move as 17 tabelas (16 do CRM + `_prisma_migrations`) e os 8
tipos enum, preserva as 16 foreign keys todas internas ao schema, e rodar de novo
é no-op. Use-o em vez do trecho abaixo, que é a versão explicativa.

```bash
pg_dump -Fc -d <banco> -f antes-do-passo-0.dump   # backup primeiro
psql -d <banco> -v tenant_schema=tenant_clara -f scripts/00-move-public-to-tenant.sql
```

> **Pegadinha do psql:** ele **não interpola variáveis dentro de `$$...$$`**, então
> `:'tenant_schema'` num bloco `DO` não é substituído. O script passa o nome por
> `set_config('claracrm.target_schema', ..., true)` e o lê com `current_setting()`.

```sql
-- Versão explicativa. Faça backup antes; app parada, dentro de uma transação.
BEGIN;

CREATE SCHEMA IF NOT EXISTS tenant_clara;

DO $$
DECLARE r record;
BEGIN
  -- As 16 tabelas (15 modelos + o join implícito _LeadToTag) e o histórico
  -- de migrations, que passa a pertencer ao tenant.
  FOR r IN SELECT tablename FROM pg_tables WHERE schemaname = 'public'
  LOOP
    EXECUTE format('ALTER TABLE public.%I SET SCHEMA tenant_clara', r.tablename);
  END LOOP;

  -- Os 8 enums vivos: AgentRole, DepartmentId, LinkedRecordType, MessageType,
  -- MessageDirection, SenderType, MessageStatus, StageKind.
  -- (StageId já foi dropado em 20260915120000_stages_become_a_table.)
  FOR r IN SELECT t.typname FROM pg_type t
             JOIN pg_namespace n ON n.oid = t.typnamespace
            WHERE n.nspname = 'public' AND t.typtype = 'e'
  LOOP
    EXECUTE format('ALTER TYPE public.%I SET SCHEMA tenant_clara', r.typname);
  END LOOP;
END $$;

-- Confira que o public ficou vazio ANTES de commitar.
-- Esperado: zero linhas nas duas consultas.
SELECT tablename FROM pg_tables WHERE schemaname = 'public';
SELECT t.typname FROM pg_type t JOIN pg_namespace n ON n.oid = t.typnamespace
 WHERE n.nspname = 'public' AND t.typtype = 'e';

COMMIT;
```

Depois: crie as tabelas de controle no `public` (primeira migration do schema de
controle) e insira a linha `Tenant` do cliente existente, com
`schemaName = 'tenant_clara'`, mais as linhas de `AgentDirectory` derivadas dos
`Agent` que já existem.

> **Atenção ao `.env` e ao `docker-compose.yml`:** a `DATABASE_URL` hoje usa
> `?schema=public`. Ela continua assim — é o schema de controle. O schema do
> tenant é escolhido em runtime pelo adapter, não pela URL de conexão.

---

## 4. Login com URL única

É a parte que mais muda em relação ao v1. Sem subdomínio, o fluxo é:

```
1. POST /login  { email, senha }
2. public.AgentDirectory.findUnique({ email })   → tenantId, agentId, active
3. Não encontrou? → bcrypt contra um hash dummy, depois "credenciais inválidas".
4. public.Tenant → status ACTIVE? schemaVersion == esperada? Se não, recusa.
5. Client do tenant → Agent.findUnique({ id: agentId }) → bcrypt.compare
6. JWT recebe tenantId (além de id, role, departments que já carrega)
```

Quatro detalhes que não são opcionais:

- **Passo 3, o bcrypt dummy.** Sem ele, e-mail inexistente responde rápido e
  e-mail existente responde lento: dá para enumerar a base de clientes por
  timing. Compare contra um hash fixo descartável para igualar o tempo.
- **Mensagem de erro sempre genérica.** Nunca "esta conta não existe" nem
  "empresa inativa" — as duas contam ao atacante se o e-mail está na base.
- **A revalidação de 30s do `src/lib/auth.ts` precisa crescer.** Hoje o callback
  `jwt` reconsulta `active`, `role` e `departments`. Passa a reconsultar também
  **se o `AgentDirectory` ainda aponta esse e-mail para esse tenant** e **se o
  tenant continua ativo**. Sem isso, desativar um cliente inteiro só faz efeito
  quando o token expira — até 30 dias depois.
- **O `tenantId` vem do token e de nada mais.** Sem subdomínio não existe segunda
  fonte para cruzar, então o token é a única. Trate `NEXTAUTH_SECRET` como
  credencial de primeira ordem.

### O mesmo e-mail em dois clientes

`AgentDirectory.email` é `UNIQUE` global, então **um e-mail pertence a um tenant**.
Isso é simples, cobre a realidade de hoje e evita a tela de "escolha a empresa".

É também a decisão mais provável de doer depois (um consultor que atende dois
clientes, alguém que troca de empresa). O caminho de upgrade, quando precisar:

```
public.Identity    id, email UNIQUE, passwordHash     ← credencial sai do tenant
public.Membership  identityId, tenantId, agentId      ← UNIQUE (identityId, tenantId)
```

Valida a senha uma vez no `public`, e se houver mais de um `Membership` mostra um
seletor **depois** da autenticação. Desenhe `AgentDirectory` já pensando nessa
troca — ela reescreve o `authorize()`, não o resto do sistema.

---

## 5. WhatsApp: o que é global e o que é do tenant

**Isto corrige o v1.** Com um único app da Meta e uma única URL de webhook, a
assinatura `X-Hub-Signature-256` é verificada **antes** de existir qualquer
tenant — logo o App Secret não pode morar no schema do tenant.

A ordem em `POST /api/webhooks/meta` passa a ser:

```
1. Verifica a assinatura com o App Secret GLOBAL (public.WhatsappAccount → env)
2. Faz o parse, extrai o phoneNumberId
3. public.WhatsappNumberRoute → tenantId          ← única forma de rotear
4. Client do tenant → ingestMessages / applyStatusUpdate
5. Relay para a Clara com a claraRelayUrl DO TENANT
```

Portanto o `WhatsappConfig` de hoje **se divide**:

| Campo | Vai para | Por quê |
|---|---|---|
| `appSecretEnc` | `public.WhatsappAccount` | valida a assinatura antes de saber o tenant |
| `verifyTokenEnc` | `public.WhatsappAccount` | pertence à URL de callback, que é uma só |
| `apiVersion` | `public.WhatsappAccount` | é do app, não do cliente |
| `claraRelayUrl` | schema do tenant | cada cliente tem seu destino de automação |
| `WhatsappNumber.*` (tokens, PIN) | schema do tenant | a Meta emite token por negócio; nunca é compartilhado |

`WhatsappNumberRoute` no `public` é o **espelho** de `WhatsappNumber` do tenant:
escreva as duas na mesma transação lógica ao conectar um número, e trate a rota
como derivada. Se as duas divergirem, a mensagem cai no tenant errado — vale um
teste dedicado.

Um número (`phoneNumberId`) pertence a **um** tenant. O `UNIQUE` em
`WhatsappNumberRoute.phoneNumberId` é o que garante isso no banco.

---

## 6. Provisionamento de tenant (control plane)

O objetivo é um **core** que reúne os produtos e a Clara principal, e que cria um
cliente novo chamando o CRM por HTTP (Swagger ou `curl`): cria o schema, roda as
migrations e deixa uma conta inicial de administrador.

Esse é o endpoint **mais poderoso do sistema** — executa DDL e cria um
administrador. Tudo abaixo existe por causa disso.

### O contrato

```
POST /api/core/tenants
X-Core-Key: <chave do core>
Content-Type: application/json

{
  "slug": "acme",                      // vira o nome do schema — validado a ferro (abaixo)
  "name": "ACME Distribuidora",
  "external_tenant_id": "core_01H...", // o id que o core usa para este cliente
  "admin": { "name": "Fulano", "email": "fulano@acme.com.br" }
}

→ 202 Accepted
  Location: /api/core/tenants/tn_01H...
  { "tenant_id": "tn_01H...", "status": "PROVISIONING", "job_id": "job_01H..." }
```

Depois: `GET /api/core/tenants/{id}` devolve `PROVISIONING | ACTIVE | FAILED` com o
log do job. Para uso manual, um `?wait=true` síncrono com teto de ~60s é aceitável,
mas **o contrato é o 202** (motivo abaixo).

### Por que assíncrono

`prisma migrate deploy` leva de segundos a minutos e o custo cresce com o número de
migrations — já são 15. Rota do Next mais timeout de Load Balancer no caminho
tornam a versão síncrona frágil exatamente no pior momento: o cliente novo.

Então a rota **valida, grava e devolve 202**; um job faz o trabalho.

### Autenticação: credencial própria, separada de tudo

```
public.CoreKey        keyHash, name, scopes[], ipAllowlist, revokedAt, lastUsedAt
public.CoreAuditLog   coreKeyId, action, payload (sem segredos), result, createdAt
```

- Header **`X-Core-Key`**, e **não** o `X-Validation-Token` que o fluxo da Clara usa.
  Reutilizar aquele token daria ao fluxo de automação o poder de criar clientes.
- Guardada como hash SHA-256, comparada com `timingSafeEqual` (o
  `src/lib/webhook-auth.ts` já tem o padrão certo para copiar).
- Escopo `tenant:provision`. Destruir tenant exige outro escopo (ver Offboarding).
- Rate limit agressivo (~5/min) e `ipAllowlist` opcional — só o core chama isso.
- **Toda chamada auditada**, com o payload sem segredos.

### `slug` é superfície de injeção de DDL

O `slug` termina dentro de um `CREATE SCHEMA`. Trate como entrada hostil:

- Whitelist estrita: `^[a-z][a-z0-9_]{2,40}$` (Zod, na borda).
- Rejeite reservados: `public`, `information_schema`, qualquer coisa começando com
  `pg_`, e os nomes do controle.
- `schemaName = "tenant_" + slug`, **gravado em `Tenant.schemaName`** e lido dali
  para sempre. Nunca recalcule o nome do schema a partir de entrada de usuário.
- No SQL, sempre `format('%I', ...)` / `quote_ident`. Nunca concatenação.

### Idempotência é obrigatória

Um `curl` que estoura o timeout **vai** ser repetido. Dois schemas para o mesmo
cliente é um incidente de dados, não um bug cosmético.

- `Tenant.slug` é `UNIQUE`. Um segundo POST com o mesmo slug devolve o job que já
  existe (200), nunca um segundo schema.
- Aceite também `Idempotency-Key` para o caso de retry antes do commit.

### O que o job faz (cada passo idempotente e retomável)

```
1. CREATE SCHEMA IF NOT EXISTS tenant_acme
2. prisma migrate deploy   com DATABASE_URL=...?schema=tenant_acme
3. prisma/bootstrap.ts     papéis, etapas, funis e o admin inicial
4. CREATE ROLE tenant_acme + grants (Camada 3)
5. gera a DEK, wrap com a KEK, grava em Tenant.dekWrapped (Camada 4)
6. insere a linha em public.AgentDirectory apontando o e-mail do admin
7. Tenant.status = ACTIVE, schemaVersion = versão aplicada
```

Dois pontos que economizam trabalho:

- **O passo 2 é viável nesta imagem.** O `Dockerfile` roda `npm ci` sem prune e
  instala `openssl` justamente porque o engine de migration precisa dele: o CLI do
  Prisma **está presente em produção**. Dá para `spawn` do `prisma migrate deploy`
  com a `DATABASE_URL` do tenant e capturar stdout/stderr no registro do job.
- **O passo 3 já existe.** O `prisma/bootstrap.ts` cria papéis, etapas, funis e
  **um** administrador, sem dado fictício, e é idempotente — foi escrito para
  primeiro acesso de produção. É o provisionador; não reescreva.

**Em falha:** `status = FAILED` com o erro capturado, e retry é seguro porque todo
passo é idempotente. O `DROP SCHEMA` de rollback é **manual e explícito, nunca
automático** — derrubar schema por falha transitória é como se apaga o dado de um
cliente sem querer.

### A senha do admin não vai no corpo da requisição

Senha em corpo de POST acaba no histórico do shell, na aba do Swagger, no log do
proxy reverso e na auditoria. Não aceite.

Em vez disso: crie o admin com hash inutilizável e devolva um **token de primeiro
acesso** — uso único, TTL curto (~24h), guardado como hash:

```
https://crm.claraaiapp.store/primeiro-acesso?token=<uso único>
```

O administrador define a própria senha. O `bootstrap.ts` continua aceitando
`ADMIN_PASSWORD` por env para uso manual via CLI; é a rota HTTP que usa o token.

### Onde isso entra no Swagger

`src/lib/docs/openapi.ts` é escrito à mão e já tem `securitySchemes`. Acrescente um
esquema **`CoreKey`** (`apiKey`, header `X-Core-Key`) — não reaproveite o
`ValidationToken` — e uma tag própria.

Mas decida uma coisa antes: o `/docs` de hoje descreve a superfície de integração
que o fluxo da Clara consome. Publicar o provisionamento no mesmo Swagger conta a
todo mundo que o control plane existe e onde ele fica. **Recomendo um documento
OpenAPI separado** em `/api/core/docs`, atrás da própria `X-Core-Key` ou de sessão
de admin.

### O core é o dono da identidade do cliente, não o CRM

Como o objetivo é um core com vários produtos, `public.Tenant` no banco do CRM é
uma **projeção**, não a verdade:

- `Tenant.externalTenantId` (`UNIQUE`, nullable) guarda o id do core.
- O core chama um endpoint desta forma por produto que estiver habilitando
  (CRM, ERP, SAC), e o `external_tenant_id` é o que correlaciona os três.
- Se o CRM virar autoridade sobre a identidade do cliente, dois produtos vão
  disputar quem manda no cadastro. Resolva isso agora, que é uma coluna.

### Offboarding precisa existir junto

Sem o caminho inverso, o primeiro cancelamento vira `psql` na produção. E a LGPD dá
ao titular direito à eliminação.

- **Suspender** — `POST /api/core/tenants/{id}/suspend` → `status = SUSPENDED`. O
  login recusa, o webhook para de rotear. Instantâneo, reversível, sem perda de
  dado. É o que se usa para inadimplência.
- **Excluir** — exporte primeiro (`pg_dump -n tenant_acme`), depois
  `DROP SCHEMA ... CASCADE`, atrás de um portão mais forte: escopo próprio
  (`tenant:destroy`) e `confirm: "<slug>"` no corpo. Considere **não expor por
  HTTP** e deixar num CLI com a credencial de migrator.
- Excluir tenant é mais que o schema: apague também o prefixo `tenants/<id>/` no R2
  e as linhas de `WhatsappNumberRoute`, senão uma mensagem da Meta chega e não
  encontra destino.

### Conserte o `docker-entrypoint.sh` junto com isso

Hoje ele roda `npx prisma migrate deploy` **a cada boot do container**. Em
multi-tenant isso fica errado de três formas:

1. migra só o schema da `DATABASE_URL` (o controle) e deixa **todos os tenants
   atrás**, sem avisar;
2. com várias instâncias atrás do Load Balancer, todas rodam no boot ao mesmo
   tempo — o Prisma serializa por advisory lock, mas o boot fica lento e frágil;
3. um loop sobre N tenants não pertence ao caminho de subida de container.

Tire as migrations do entrypoint e faça delas um passo deliberado (job de CI ou
container one-shot). A proteção que sobra é a da Camada 6: o app **recusa servir**
tenant cuja `schemaVersion` esteja atrás da esperada pelo build.

---

## 7. As camadas

### Camada 1 — contexto resolvido só no servidor

`getTenantContext()` com **exatamente três** origens:

| Superfície | Origem |
|---|---|
| UI e API autenticada | `token.tenantId` do JWT |
| `POST /api/webhooks/meta` | `phoneNumberId` → `public.WhatsappNumberRoute` |
| `/api/tools/*` | hash da API key → `public.ApiKey` |

**Nunca** de header, query param, body ou path. Se o cliente puder influenciar o
tenant, não existe isolamento — existe uma convenção. Propague por
`AsyncLocalStorage` para não passar o contexto por 40 assinaturas de função.

### Camada 2 — client Prisma qualificado por schema, nunca `search_path` de sessão

O `@prisma/adapter-pg@7.10` (já instalado) aceita a opção `schema`:

```ts
// node_modules/@prisma/adapter-pg/dist/index.d.ts
declare type PrismaPgOptions = {
  /** The name of the schema to use in generated queries */
  schema?: string;
  ...
}
```

Com isso o Prisma emite `"tenant_acme"."Lead"` qualificado — **sem estado de
sessão**.

Isso importa porque a falha clássica desta arquitetura é
`SET search_path TO tenant_x`: num pooler em transaction mode a conexão que serviu
o tenant A volta ao pool e é entregue ao tenant B milissegundos depois, **ainda
com o `search_path` do A**. O bug passa em desenvolvimento (um dev, uma conexão,
sempre o mesmo backend) e vaza em produção sob concorrência.

```ts
// esboço
const pool = new pg.Pool({ connectionString: process.env.DATABASE_URL });  // UM pool

function clientFor(schemaName: string) {
  return new PrismaClient({ adapter: new PrismaPg(pool, { schema: schemaName }) });
}
```

- **Um único `pg.Pool` compartilhado**, N PrismaClients finos por cima.
- **Nunca um pool por tenant** — é assim que se estoura `max_connections`.
- Cache LRU limitado (~50) com eviction por idle.
- `src/lib/prisma.ts` vira um proxy resolvido pelo contexto da Camada 1, **então
  as 40 rotas não precisam ser alteradas.**

**Verificado nesta versão do stack (Prisma 7.10 + `@prisma/adapter-pg`):** a
qualificação alcança **também os casts de enum**, inclusive arrays. O SQL
emitido para um insert em `Agent`, com `schema: "tenant_test_b"`, é:

```sql
INSERT INTO "tenant_test_b"."Agent" (...)
VALUES ($1,$2,$3,$4,
        CAST($5::text  AS "tenant_test_b"."AgentRole"),
        CAST($6::text[] AS "tenant_test_b"."DepartmentId"[]), ...)
```

Ou seja: **não é preciso `search_path` em lugar nenhum** do caminho do Prisma, e
cada schema pode ter a sua própria cópia dos tipos com segurança. Isso vale para
o ORM; SQL cru escrito à mão continua sendo responsabilidade de quem escreve
(qualifique o schema, ou use `SET LOCAL search_path` **dentro da transação** —
nunca um `SET` solto).

Se um upgrade de Prisma mudar isso, o teste `tests/tenant-isolation.test.ts`
falha, que é o lugar certo para descobrir.

### Camada 3 — defesa em profundidade no Postgres

Isolamento por nome de schema é *correção de aplicação*: um bug que monte o nome
errado devolve dados de outro cliente. Para que isso vire erro em vez de vazamento:

```sql
-- por tenant, no provisionamento
CREATE ROLE tenant_acme NOLOGIN;
GRANT USAGE ON SCHEMA tenant_acme TO tenant_acme;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA tenant_acme TO tenant_acme;
ALTER DEFAULT PRIVILEGES IN SCHEMA tenant_acme
  GRANT ALL ON TABLES TO tenant_acme;
-- e nada, em nenhuma hipótese, no public nem em outro schema de tenant

-- uma vez, no banco
REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
```

A aplicação conecta com um role de baixo privilégio e faz
`SET LOCAL ROLE tenant_acme` **dentro da transação** (morre no commit, seguro com
pooler). Schema errado ⇒ `permission denied`, não os dados do vizinho. É o
equivalente ao que a RLS faz no modelo de schema compartilhado: transforma um
vazamento em erro.

**Custo:** um round-trip por transação e mais complexidade no provisionamento.
Variante para começar: dois roles (migrator / app) + a qualificação da Camada 2.
Defensável, mas role-per-tenant é a resposta certa para "seguro", não apenas
"correto".

### Camada 4 — segredos com envelope encryption

Hoje uma única `CONFIG_ENCRYPTION_KEY` cifra os tokens Meta de todos os clientes.

Passe a uma **DEK por tenant**, guardada wrapped pela KEK master em
`public.Tenant.dekWrapped`. Um ciphertext vazado deixa de destrancar todos os
tenants, e rotacionar a chave de um cliente não toca nos outros. Os segredos
globais (`WhatsappAccount`) são cifrados direto com a KEK.

`src/lib/crypto.ts` já grava com prefixo de versão (`v1:<iv>:<tag>:<ct>`), então a
migração cabe como `v2:` com leitura retrocompatível.

### Camada 5 — particione tudo que não é banco

É onde os vazamentos reais acontecem, não no SQL.

- **R2** — prefixe as chaves com `tenants/<tenantId>/`. **E atenção:**
  `src/lib/r2.ts` usa `CLOUDFLARE_R2_PUBLIC_URL`; o bucket é **público por URL**.
  Áudio e documento de conversa de cliente são legíveis por qualquer um com o
  link. Já é discutível hoje; com multi-tenant, troque por URL assinada com
  expiração.
- **`src/lib/events.ts`** — o `EventEmitter` é global e `notifyCrmChange` avisa
  **todo** navegador conectado. Não expõe dado (o cliente refetcha com escopo),
  mas vaza timing de atividade entre clientes e gera refetch cruzado. Canal
  `crm:change:<tenantId>`.
- **`src/lib/rate-limit.ts`** — a chave é só IP, e o backend da Clara chama todos
  os tenants **do mesmo IP**: o tráfego de um consome a cota de todos. Chave passa
  a ser `tenantId + IP`. No `/login` ainda não há tenant: use `email + IP`.
- **Logs** — todo log carrega `tenantId`.
- Com várias instâncias atrás do LB, `events` e `rate-limit` seguem per-process. O
  poll de backstop do cliente cobre os eventos; para exatidão, Redis ou
  `LISTEN/NOTIFY` (já anotado como pendência no próprio arquivo).

### Camada 6 — migrations e ciclo de vida

- **Dois conjuntos de migrations**, separados: o do `public` (controle) e o dos
  tenants (o `prisma/` atual). Recomendo um segundo schema Prisma para o controle,
  gerando um segundo client (ex.: `src/generated/control`), com seu próprio
  arquivo de config — o `prisma.config.ts` atual aponta `schema: "prisma/"` e
  continua sendo o dos tenants.
- `prisma migrate deploy` em loop sobre `public.Tenant`, com
  `DATABASE_URL=...?schema=<schemaName>`. **Sequencial e fail-fast.**
- Grave `schemaVersion` por tenant. **O app recusa servir** tenant cuja versão seja
  menor que a esperada pelo build — melhor 503 que schema meio migrado. É também o
  passo 4 do login.
- **Somente migrations backward-compatible** (expand/contract): os tenants migram
  um a um e o mesmo build atende schemas em versões diferentes por alguns minutos.
- **Provisionar** = `CREATE SCHEMA` + `migrate deploy` + `prisma/bootstrap.ts` +
  criar o role + inserir `Tenant` e `AgentDirectory`. O `bootstrap.ts` **já existe
  e já faz a parte difícil**: papéis, etapas, funis e um admin, sem dado fictício,
  idempotente. Ele é o provisionador, quase de graça.
- **`migrate dev` continua num banco local de schema único.** Há regressão conhecida
  no Prisma 6/7: o `shadowDatabaseUrl` ignora o `?schema=` e conecta no `public`
  (prisma/orm#29709). Estamos no 7.10, então nos atinge. Só o `deploy` vai em loop.
- `prisma/migrations/00000000000000_init/migration.sql` abre com
  `CREATE SCHEMA IF NOT EXISTS "public"`. Inofensivo, mas **troque por uma criação
  do schema corrente** antes de provisionar o primeiro tenant novo — como está, a
  linha não descreve mais a intenção.
- **Cuidado:** `20260915120000_stages_become_a_table` foi escrita à mão e o Prisma
  não consegue regerá-la. Não rode `migrate dev` esperando reproduzi-la.

### Camada 7 — verificação contínua

Um teste que sobe **dois** tenants e afirma que **toda** rota devolve 404/vazio ao
cruzar. É o que impede a regressão silenciosa, e a literatura de segurança
multi-tenant nomeia isso como defesa central.

Já existem 15 suítes em `tests/`; `department-scoping.test.ts` é o modelo mais
próximo. Casos que merecem teste próprio nesta arquitetura:

- dois tenants com o mesmo `telefone` de cliente e o mesmo nome de tag (ambos são
  `@unique` **por schema**, então isso é legítimo e precisa funcionar);
- webhook com `phoneNumberId` de A não escreve nada em B;
- API key de A recebe 401/404 em recurso de B;
- login com e-mail de A e senha de B falha;
- tenant com `status != ACTIVE` não autentica.

---

## 8. Ordem de implementação

| # | Passo | Observação |
|---|---|---|
| 0 | **Mover o CRM do `public` para `tenant_clara`** (§3) | Pré-requisito de tudo. Backup, app parada, transação. |
| 1 | Tabelas de controle no `public` + segundo client Prisma | Uma linha `Tenant` para o cliente atual. |
| 2 | `getTenantContext()` + `AsyncLocalStorage` + `getPrismaForTenant()` | `prisma.ts` vira proxy; as 40 rotas não mudam. |
| 3 | `AgentDirectory` + `tenantId` no JWT + revalidação ampliada (§4) | Aqui o login passa a ser multi-tenant. |
| 4 | `WhatsappAccount` global + `WhatsappNumberRoute` + **API key por tenant** | Ver §5 e a armadilha abaixo. |
| 5 | Camada 5 (R2, events, rate-limit) + testes cross-tenant | |
| 6 | Roles por tenant + envelope encryption | |
| 7 | Migrator em loop + `schemaVersion`, fora do entrypoint (§6) | |
| 8 | **Control plane:** `POST /api/core/tenants` + job + offboarding (§6) | Depende de 1–7: provisionar é automatizar o que os passos anteriores definiram. |

Os passos **1 e 2 não mudam comportamento observável** e podem ser mergeados antes
de decidir o resto. O passo 0 é o único com janela de indisponibilidade, e é curta
(`SET SCHEMA` não copia dados).

### A armadilha do passo 4

`src/lib/webhook-auth.ts` protege **todos** os endpoints `/api/tools/*` com **um**
`WEBHOOK_VALIDATION_TOKEN` compartilhado, usado pelo fluxo da Clara AI. Num mundo
multi-tenant, um token vazado lê e escreve em **todos** os clientes. Trocar por API
key por tenant (`public.ApiKey`, comparação por hash, `timingSafeEqual`) é
obrigatório, não melhoria. Preserve o mecanismo de rotação que já existe
(`WEBHOOK_VALIDATION_TOKEN_PREVIOUS`), mas por chave.

### Estado da implementação

Branch `feat/multi-tenant-crm`.

**Passo 2 — pronto e verde.** 196 testes passando (eram 163; nenhum teste
existente foi alterado).

| Arquivo | O que faz |
|---|---|
| `src/lib/tenant/schema-name.ts` | Whitelist do slug, reservados, limite de identificador. A fronteira de injeção de DDL. |
| `src/lib/tenant/context.ts` | `AsyncLocalStorage`: `runWithTenant`, `getTenantContext`, `requireTenantContext`. |
| `src/lib/tenant/client-cache.ts` | Um `pg.Pool` compartilhado, N clients finos, LRU em 50 com disconnect diferido em 30s. |
| `src/lib/prisma.ts` | Virou proxy resolvido por contexto. É o que torna as 40 rotas multi-tenant sem editar nenhuma. |
| `tests/tenant-isolation.test.ts` | Provisiona um segundo schema de verdade e prova o isolamento nos dois sentidos. |
| `tests/tenant-schema-name.test.ts` | 26 casos do guard de slug. |

O proxy tem **fallback deliberado**: sem contexto, resolve para o schema da
`DATABASE_URL`. É o que mantém as rotas ainda não migradas funcionando como hoje.
Quando toda entrada definir contexto, troque `getTenantContext` por
`requireTenantContext` em `src/lib/prisma.ts` e o fallback vira erro.

**Passo 0 — script pronto, não executado.**
`scripts/00-move-public-to-tenant.sql`, validado em banco descartável.

**Passo 1 — pronto.** O control plane é um projeto Prisma separado:

| Arquivo | O que faz |
|---|---|
| `prisma-control/` | 8 modelos: `Tenant`, `AgentDirectory`, `WhatsappNumberRoute`, `WhatsappAccount`, `ApiKey`, `CoreKey`, `ProvisioningJob`, `CoreAuditLog`. |
| `prisma-control.config.ts` | Config própria. Scripts: `control:generate`, `control:migrate`, `control:migrate:dev`. |
| `prisma-control/migrations/…_init_control/` | Migration inicial, gerada e aplicada num banco limpo. |
| `src/lib/control/client.ts` | Client do controle. Compartilha o pool com os clients de tenant — mesmo banco, outro schema. |
| `src/lib/tenant/registry.ts` | Resolve tenant por id, slug, `phoneNumberId`, hash de API key e e-mail de login. Cache de 10s. |
| `tests/tenant-registry.test.ts` | 20 casos, incluindo chave revogada/expirada, rota inativa e `schemaName` malicioso vindo do banco. |

As restrições que sustentam o desenho estão no banco: `AgentDirectory.email`
`UNIQUE` global (login com URL única), `WhatsappNumberRoute.phoneNumberId`
`UNIQUE` (um número, um tenant), `Tenant.schemaName` `UNIQUE` e
`ProvisioningJob.idempotencyKey` `UNIQUE` (retry de curl não cria dois schemas).

O cache do registry tem TTL curto **de propósito**: é ele que também atrasa uma
suspensão. Depois de mudar status ou roteamento, chame `invalidateTenantCache()`.

**Passo 3 — pronto.** O login roteia pelo diretório.

| Arquivo | O que faz |
|---|---|
| `src/lib/auth.ts` | `authorize()` resolve o tenant pelo e-mail, `tenantId` entra no JWT, e a revalidação de 30s passa a checar tenant e diretório. |
| `src/lib/tenant/request.ts` | `tenantContextFromSession` / `runWithSessionTenant`: liga a sessão ao escopo de tenant. |
| `src/types/next-auth.d.ts` | `tenantId` opcional em `Session.user`, `User` e `JWT`. |
| `scripts/01-seed-control-from-existing.ts` | Backfill: cria a linha `Tenant` e deriva `AgentDirectory` e `WhatsappNumberRoute` do que já existe. Lista por padrão, escreve com `--apply`, idempotente. |
| `tests/tenant-login.test.ts` | 17 casos. |

**O flag `MULTI_TENANT`.** O caminho multi-tenant é opt-in, porque
`AgentDirectory` só existe depois do passo 0 e um ambiente não migrado tem de
continuar logando como hoje. Com o flag ausente, `authorize()` usa o caminho
legado — idêntico ao atual, e coberto por teste. É uma chave que se vira junto
com a migração, não uma preferência; remova o flag e o `legacyAuthorize` quando
todos os ambientes estiverem migrados.

**O bcrypt dummy é real.** `DUMMY_HASH` é um hash cost 10 de uma string
aleatória, comparado quando o e-mail não resolve, para que um miss custe os
mesmos ~50ms de um hit. Há um teste que falha se essa proteção cair — sem ela, o
formulário de login enumera quem é cliente.

**Toda falha é indistinguível.** E-mail inexistente, tenant suspenso, agente
desativado, diretório removido e senha errada devolvem o mesmo `null`. Um teste
cobre cada status de tenant recusando **mesmo com a senha certa**.

**Sequência para virar a chave em produção:**

```bash
psql -d <banco> -v tenant_schema=tenant_clara -f scripts/00-move-public-to-tenant.sql
npm run control:migrate
npx tsx scripts/01-seed-control-from-existing.ts --slug=clara --apply
# só então:  MULTI_TENANT=true
```

**Passo 4 — pronto.** WhatsApp separado e integração por tenant.

| Arquivo | O que faz |
|---|---|
| `src/lib/multi-tenant.ts` | O flag `MULTI_TENANT`, agora compartilhado por auth e WhatsApp. |
| `src/lib/whatsapp/global-account.ts` | App Secret, verify token e apiVersion vindos do `public`. |
| `src/lib/whatsapp/routing.ts` | `sliceByTenant`: fatia um payload da Meta pelos tenants que ele contém. |
| `src/lib/whatsapp/config.ts` | Caches **particionados por schema** (ver abaixo) e segredos globais vindos do control plane. |
| `src/lib/whatsapp/meta-payload.ts` | Status passam a carregar `toPhoneNumberId`; novo `onlyPhoneNumberIds` para fatiar o relay. |
| `src/lib/webhook-auth.ts` | `withIntegrationAuth`: rate limit, API key por tenant e escopo, num invólucro só. |
| 7 rotas de integração | 6 tools + o webhook de conversa passaram a usar o invólucro. |
| `tests/tenant-whatsapp.test.ts` | 11 casos. |

**Um vazamento que só apareceu ao implementar.** `config.ts` guardava a conta e
os números conectados em **duas variáveis de módulo**. Isso era correto com um
cliente só e é vazamento entre tenants agora: o primeiro tenant a esquentar o
cache entregava os próprios números — e os access tokens deles — ao tenant
seguinte. Os caches passaram a ser `Map` por schema, e há teste dedicado. É o
exemplo concreto do que a Camada 5 avisa: o risco não está no SQL, está no que
o processo guarda na memória.

**O relay é fatiado por tenant.** Uma requisição da Meta pode trazer números de
clientes diferentes, e cada cliente tem sua própria `claraRelayUrl`. Repassar o
corpo inteiro entregaria a conversa de um à automação do outro — vazamento para
um sistema fora do nosso controle. Quando há um só tenant no payload, os bytes
originais da Meta seguem intactos, com a assinatura dela; quando há mais de um,
o corpo é recortado e reassinado com o mesmo App Secret.

**Tráfego sem rota é descartado, não adivinhado.** Número desconhecido, tenant
suspenso ou atrás nas migrations: nada é gravado, e a resposta conta quantos
foram, em vez de sumir em silêncio.

**A API key mantém o header `X-Validation-Token`.** Trocar o nome obrigaria a
mexer no fluxo da Clara; o que muda é o valor passar a ser por cliente, achado
por hash em `public.ApiKey`. Chave desconhecida, revogada e expirada devolvem o
mesmo 401 — distingui-las diria se a chave já existiu. Tenant suspenso devolve
**503**, não 401: é estado que se resolve, e o fluxo pode repetir.

**Passo 5 — pronto. O flag agora pode ser ligado.**

| Arquivo | O que faz |
|---|---|
| `src/lib/tenant/route.ts` | `withTenantScope`: envolve um handler de sessão no escopo do tenant. |
| 32 rotas de sessão / 47 handlers | Passaram a `export const GET = withTenantScope(async (…) => {…})`. |
| `src/lib/events.ts` | Canal `crm:change:<tenantId>`. |
| `src/lib/r2.ts` | Chaves sob `tenants/<tenantId>/`. |
| `src/lib/rate-limit.ts` | Aceita chave explícita; a integração usa `tenant:<id>`. |
| `src/app/api/settings/whatsapp/route.ts` | Recusa escrita dos segredos globais (ver abaixo). |
| `tests/tenant-layer5.test.ts` | 7 casos, incluindo uma rota de sessão real. |

**Por que envolver o export, e não usar `enterWith`.** `AsyncLocalStorage.enterWith`
dispensaria o invólucro, mas define o store para o resto do contexto assíncrono
em volta. Se esse contexto for reaproveitado entre requisições — e isso é
decisão do Next, não nossa — o tenant de uma requisição escorre para a
seguinte. É o pior bug possível aqui. `run` não consegue fazer isso.

**Dois comportamentos preservados de propósito:** sem sessão, o handler roda e
devolve o próprio 401 (autenticação é trabalho dele); sem `tenantId` no token,
não há escopo e o `prisma` cai no schema da `DATABASE_URL`, como antes.

**Token que nomeia tenant inexistente dá 503**, e **não** escorrega para o
schema padrão. O fallback do proxy existe para ambiente single-tenant, não para
um token órfão. Há teste.

**O R2 já estava resolvido** — bucket privado, chave no banco e URL assinada de
5 minutos. Só faltava o segmento por tenant. As leituras já eram seguras, porque
a chave vem da linha `Media` do próprio tenant e nunca do chamador; o segmento é
o que particiona o bucket e permite política por tenant depois. Objetos antigos
não têm o segmento e continuam legíveis: a chave é guardada inteira.

**Os segredos da Meta deixaram de ser editáveis pelo tenant.** App Secret, token
de verificação e versão da API valem para **todos** os clientes: um admin de
tenant que os trocasse derrubaria o webhook de todo mundo. Em multi-tenant a tela
mostra o valor em vigor e recusa a escrita com 403 `managed_by_platform`. Só o
`claraRelayUrl` continua sendo de cada cliente. Isto não estava no documento —
apareceu ao implementar.

**Verificação:** 251 testes, `tsc` limpo, e `next build` passa — o que confirma
que o App Router aceita os handlers exportados como `const`.

**Passo 6 — pronto, com uma ressalva importante sobre roles.**

| Arquivo | O que faz |
|---|---|
| `src/lib/crypto.ts` | Formatos `v1` (KEK) e `v2` (DEK do tenant) convivendo; `wrapDek`/`unwrapDek`. |
| `src/lib/tenant/dek.ts` | DEK por tenant, criada no primeiro uso, guardada embrulhada, cacheada em memória. |
| `src/lib/whatsapp/number-route.ts` | Espelha `WhatsappNumber` em `public.WhatsappNumberRoute`. |
| `scripts/02-harden-database.sql` | Separa `claracrm_migrator` (DDL) de `claracrm_app` (sem DDL) e revoga o `PUBLIC`. |
| `scripts/03-tenant-role.sql` | Um role Postgres por tenant, restrito ao schema dele. |
| `tests/tenant-crypto.test.ts` | 8 casos. |

**Envelope encryption está completo.** Segredo de cliente (token de número, PIN)
é selado com a DEK do tenant e sai como `v2`; segredo de plataforma (as
credenciais do app da Meta) segue `v1`/KEK. Nada precisou migrar: a versão é
lida na saída, então um `v1` de antes convive com um `v2` de agora — há teste
para isso. A DEK nasce sob `updateMany` condicional, então duas chamadas
simultâneas convergem para a mesma chave em vez de deixarem o ciphertext da
perdedora ilegível. Sem KEK, guardar segredo é recusado, como já era.

**O que os roles entregam — e o que não.** Isto corrige o que a Camada 3
sugeria. Enforcement por tenant em tempo de requisição **não foi implementado**,
por duas razões:

1. `SET LOCAL ROLE` vive numa transação, e o driver adapter do Prisma não dá
   gancho por query — cobrir tudo exigiria envolver toda leitura numa transação.
2. Mesmo envolvendo, o role e o nome do schema sairiam do **mesmo** contexto de
   tenant. Um bug erraria os dois na mesma direção, e a checagem não pegaria
   nada. A proteção parece maior do que é.

O isolamento entre tenants continua vindo da **qualificação de schema do Prisma**
(Camada 2), que é verificada por teste. O que os scripts entregam de concreto:

- **`claracrm_app` sem DDL.** Verificado: `CREATE TABLE` e `DROP TABLE` são
  negados, `SELECT`/`INSERT` funcionam, inclusive em tabela criada depois pelo
  migrator (os privilégios padrão pegam). Um SQL cru com bug deixa de poder
  destruir.
- **`PUBLIC` revogado** no schema e no banco.
- **Role por tenant** que **não alcança o `public`** — verificado: `permission
  denied for schema public`. Serve para acesso fora de banda com escopo (`psql`
  de suporte, `pg_dump` de um cliente, credencial de BI) e deixa a superfície
  pronta caso o `SET LOCAL ROLE` seja ligado depois.

**Um gap que apareceu ao implementar: conectar um número não criava a rota.**
`WhatsappNumber` era gravado no schema do tenant e `public.WhatsappNumberRoute`
ficava vazia — a Meta entregaria mensagens desse número e o webhook não acharia
dono, deixando o Inbox do cliente vazio **sem erro nenhum**. Agora as quatro
operações espelham: embedded signup, criação manual, edição (o `active` chega à
rota) e desconexão (a rota é desativada, não apagada, porque o `phoneNumberId` é
único e reconectar reaproveita a linha).

**O token de verificação também deixou de ser do tenant.** O embedded signup o
gerava e salvava no `WhatsappConfig` do cliente. Ele pertence à única URL de
callback: em multi-tenant, se a plataforma não o tiver configurado, o fluxo
devolve 503 em vez de inventar um que ninguém usaria.

**Verificação:** 259 testes, `tsc` limpo, lint sem regressão, `next build` passa,
e os dois scripts de role rodados num banco descartável com as permissões
conferidas conectando como cada role.

**Passo 7 — pronto. As migrations saíram do entrypoint.**

| Arquivo | O que faz |
|---|---|
| `scripts/04-migrate-all-tenants.ts` | Migra o controle e depois cada tenant, sequencial e fail-fast. `npm run migrate:all` lista; `-- --apply` aplica; `--slug=` filtra. |
| `src/lib/tenant/schema-version.ts` | Lê a última migration da pasta — a versão que este build espera. |
| `src/lib/tenant/registry.ts` | `assertServable` passou a checar a versão **por padrão**. |
| `docker-entrypoint.sh` | Não roda mais `prisma migrate deploy`. |
| `tests/tenant-schema-version.test.ts` | 11 casos. |

**A versão esperada é lida da pasta `prisma/migrations`,** que viaja dentro da
imagem. Não há número para alguém lembrar de bumpar, e código e schema não
podem divergir por esquecimento.

**Só "atrás" é recusado, não "diferente".** Um schema à frente do código é
seguro por construção, porque as migrations são expand/contract — e é
exatamente o que acontece durante um deploy em rolagem, quando algumas
instâncias ainda rodam o build anterior. Recusar aí seria causar a
indisponibilidade que a checagem existe para evitar. Nomes de migration são
timestamp de largura fixa, então comparar as strings compara a ordem.

**Versão não registrada (`null`) não é tratada como atrasada.** É o estado de
todo tenant que existia antes desta checagem; derrubá-los para aplicar uma rede
de proteção seria o próprio incidente. Quem registra são os scripts 01 e 04.

**`assertServable` ganhou o padrão, então os quatro pontos de guarda já
existentes herdaram a checagem** — login, `withTenantScope`,
`withIntegrationAuth` e o fatiamento do webhook — sem precisar tocar em nenhum
deles.

**O `schemaVersion` gravado é o que o banco diz**, lido do `_prisma_migrations`
do schema depois do deploy, e não o que esperávamos aplicar. Se um deploy
parar no meio, o campo conta a verdade.

**Verificação:** 270 testes, `tsc` limpo, lint sem regressão, `next build`
passa. O migrator foi rodado num banco descartável com dois tenants — um vindo
do passo 0 e um schema vazio criado só com a linha no catálogo. Ambos receberam
as 17 tabelas, o `schemaVersion` foi gravado nos dois, e a segunda execução é
no-op.

**Passo 8 — pronto. O control plane está de pé.**

| Arquivo | O que faz |
|---|---|
| `src/lib/core/auth.ts` | `X-Core-Key`, escopos, allowlist de IP, auditoria de toda chamada. |
| `src/lib/core/provisioning.ts` | O job: schema, migrations, bootstrap, role, DEK, diretório, ativação. |
| `src/lib/core/bootstrap-tenant.ts` | Reaproveita `prisma/structure.ts` — o mesmo seed do primeiro acesso de produção. |
| `POST /api/core/tenants` | 202 + job. `GET` lista, para o core reconciliar. |
| `GET /api/core/tenants/{id}` | Polling do job; entrega o convite **uma vez**. |
| `POST .../suspend` e `.../resume` | Inadimplência: instantâneo, reversível, sem perda de dado. |
| `POST .../retry` | Retoma um job que falhou. |
| `DELETE /api/core/tenants/{id}` | Exclusão, atrás de escopo próprio. |
| `scripts/05-core-key.ts` | `npm run core:key` — cria, lista e revoga chaves do core. |
| `tests/core-provisioning.test.ts` | 16 casos, com provisionamento real. |

**A primeira chave é de linha de comando.** Não há como autenticar por HTTP a
chamada que cria a primeira chave, então o caminho é `npm run core:key --
--create`, com acesso ao banco — a única credencial que faz sentido exigir para
criar a credencial mais poderosa do sistema. O valor cru aparece uma vez.

**A senha do admin não existe no contrato.** O tenant nasce com um admin cujo
hash é de um valor aleatório que ninguém conhece, e o core recebe um convite de
uso único (24h). Há teste que tenta cinco senhas prováveis contra esse hash e
confirma que nenhuma entra. Mandar `password` no corpo não cria caminho para
ela: o schema Zod a descarta, e a auditoria não a registra — também testado.

**O convite sai em coluna própria (`setupTokenOnce`), não no log do job.**
Segredo misturado com diagnóstico é segredo que alguém copia junto ao
investigar um problema. É apagado na primeira leitura.

**Excluir exige quatro coisas ao mesmo tempo:** o escopo `tenant:destroy`
(separado de quem provisiona), o cliente já suspenso, o slug repetido no corpo e
`exported: true`. E a linha do `Tenant` **não** é apagada — fica `ARCHIVED`,
porque o histórico de que o cliente existiu tem valor. O que é apagado é o
roteamento, senão uma mensagem chega e encontra destino para um schema que não
existe mais.

**Rollback não é automático.** Um job que falha deixa o cliente `FAILED` com o
schema onde parou; todo passo é idempotente, então o retry retoma. `DROP SCHEMA`
por falha transitória é como se apaga o dado de um cliente sem querer.

**Um defeito que o teste revelou:** o limite de 20/min que eu havia posto para o
control plane estourava no próprio polling do core — ele consulta o job a cada
poucos segundos enquanto o tenant provisiona. Leitura passou a 240/min e
mutação ficou em 20/min.

**Verificação:** 286 testes, `tsc` limpo, lint sem regressão, `next build`
registra as cinco rotas do core. O provisionamento é exercitado de verdade nos
testes: cria schema, roda as 15 migrations, semeia, ativa, e o caso de exclusão
confirma que o schema desaparece do `pg_namespace`.

**Fechamento — as duas pendências do passo 8.**

| Arquivo | O que faz |
|---|---|
| `src/lib/core/setup-token.ts` | Descreve e consome o convite; política de senha. |
| `GET/POST /api/setup/accept` | Sem sessão — o convite é a credencial. 10/min por IP. |
| `/primeiro-acesso` + `src/components/FirstAccessForm.tsx` | A tela onde a pessoa define a senha e já entra. |
| `src/lib/docs/core-openapi.ts` + `GET /api/core/docs` | OpenAPI do control plane, atrás da `X-Core-Key`. |
| `tests/setup-invitation.test.ts` | 10 casos. |

**O convite é de uso único de verdade.** O `updateMany` condicional em
`usedAt: null` é o que garante isso: dois cliques simultâneos no link resultam
em **uma** senha definida, e há teste com `Promise.all` que afirma exatamente
isso (um 200 e um 400).

**Senha recusada não gasta o convite.** Senha curta ou a senha pública do seed
devolvem 400 com o convite intacto — cobrar o link da pessoa por ter escolhido
uma senha fraca seria trocar um problema por outro.

**A tela valida o convite antes de pedir a senha.** Descobrir que o link expirou
depois de digitar a senha duas vezes é a pior ordem possível. O `GET` descreve
sem gastar.

**O OpenAPI do core é separado e fechado.** Diferente do `/api/docs`, que é
só de desenvolvimento, este funciona em produção — o core precisa dele — mas
exige a `X-Core-Key`. Publicá-lo aberto contaria a todo mundo que o control
plane existe, onde fica e o que aceita. Há teste que confirma o 401 sem chave, e
outro que afirma que o corpo documentado do provisionamento **não** tem campo de
senha.

**Verificação final:** 299 testes, `tsc` limpo, lint sem erros, `next build`
registra `/primeiro-acesso`, `/api/setup/accept` e `/api/core/docs`.

---

## 9. O que só apareceu ao rodar de verdade

Um ensaio local completo (banco próprio, dois tenants, login real) encontrou três
coisas que 299 testes verdes não encontraram. Vale registrar porque duas delas
eram falhas de produção esperando.

**1. O middleware barrava o control plane.** `src/proxy.ts` tem um matcher que
exclui `api/tools` e `api/webhooks` da sessão, e eu adicionei `api/core`,
`api/setup` e `primeiro-acesso` sem atualizá-lo. O resultado era um **307 para
`/login`** no lugar do 202 — para uma API, um redirect com corpo HTML, que
demora a ser entendido. Toda superfície que carrega credencial própria, ou que
tem de funcionar antes de alguém ter uma, precisa estar nessa lista; agora o
arquivo diz por que cada exclusão existe.

**2. SQL cru sem qualificação de schema — e o teste passava.** O próprio
documento avisava disso desde a §2 e listava os arquivos, e eu não corrigi.
`GET /api/leads` respondia **500** com `relation "Message" does not exist`,
porque `FROM "Message"` resolve pelo `search_path`, que não tem o schema do
tenant. O mesmo valia para `src/lib/dashboard-metrics.ts`.

O detalhe que importa: **o teste dele estava verde**. A suíte rodava com o CRM
no `public`, então a consulta não qualificada encontrava a tabela. O teste
passava pelo motivo errado, e nenhuma quantidade de casos novos teria pego isso
— o ambiente é que estava mentindo.

A correção foi em dois níveis. O bug: `src/lib/tenant/raw.ts` expõe
`tenantSchema()`, e as consultas cruas passaram a interpolá-lo. O ambiente:
`vitest.config.ts` aponta para `?schema=tenant_test_a` e `npm run test:db`
recria o banco com o CRM **fora do `public`**, como em produção depois do passo
0. Isso obrigou a desacoplar o schema do controle do `?schema=` da URL —
`src/lib/control/client.ts` usa `CONTROL_SCHEMA` (padrão `public`).

Verificado removendo a qualificação de propósito: dois testes falham com o erro
exato de produção. A rede existe agora.

**3. Não havia como reemitir um convite.** O convite de primeiro acesso é
entregue uma vez e vale 24h. Se o core o perdesse — ou a pessoa não clicasse no
mesmo dia — a conta ficava inacessível: o provisionamento já estava concluído, o
retry recusava por `already_active`, e a única saída era o banco à mão. Isso ia
acontecer no primeiro cliente real. `POST /api/core/tenants/{id}/invite`
(`src/lib/core/invite.ts`) reemite e invalida os anteriores; só alcança quem já
está no diretório daquele tenant, então não é caminho para criar acesso novo.

**Como rodar o ensaio.** `.env.multitenant` + `scripts/dev-multitenant.sh` subem
o CRM em modo multi-tenant contra um banco local separado, sem tocar no `.env`
de desenvolvimento.

---

## 10. Os dados de produção não somem — e há caminho de volta

`ALTER TABLE ... SET SCHEMA` é operação de **catálogo**: troca o namespace da
tabela, não copia nem apaga linha. O passo 0 não move dados, move nomes.

Provado com um ensaio de ida e volta, com dados dentro: 1 lead, 1 mensagem, 1
cliente, 1 agente e as 5 etapas semeadas. Depois de `public → tenant_clara →
public`, as contagens são idênticas, o texto da mensagem é o mesmo, as 16 FKs
seguem no lugar e uma leitura atravessando relações funciona.

**`scripts/00-rollback-tenant-to-public.sql`** é o caminho de volta. Ele derruba
as tabelas de **controle** (catálogo e roteamento, reconstruíveis por
`control:migrate` + script 01) e devolve o CRM para o `public`. Não toca em
nenhuma linha de atendimento.

**O rollback é OBRIGATÓRIO antes de voltar a uma imagem pré-multi-tenant.** O
entrypoint antigo roda `prisma migrate deploy` apontando para o `public`: ele
recriaria as 17 tabelas do CRM **vazias** ali. Os dados reais continuariam em
`tenant_<slug>`, mas o app serviria o schema vazio — e isso se parece com perda
total sem ser.

**O que realmente dá problema não é o move, é a ordem.** Rodar o passo 0 com o
app ainda em `MULTI_TENANT=false` faz toda query procurar o CRM num `public` que
já não o tem. Nada se perde, mas tudo falha até o flag subir.

---

## 9. Resumo do que NÃO fazer

- ❌ Deixar dado de CRM no `public` junto com o catálogo (§3)
- ❌ `SET search_path` de sessão — vaza entre tenants com pooler (Camada 2)
- ❌ Um `pg.Pool` por tenant — estoura `max_connections`
- ❌ Tenant vindo de header, query param, body ou path
- ❌ App Secret da Meta por tenant — a assinatura é verificada antes de haver tenant (§5)
- ❌ Foreign key cruzando schemas
- ❌ Uma única chave de cifragem para os segredos de todos os tenants
- ❌ Migration não-backward-compatible — os tenants migram um a um
- ❌ Mensagem de login que revele se o e-mail ou a empresa existe (§4)
- ❌ Bucket R2 público com mídia de conversa
- ❌ Provisionar com o mesmo token do fluxo da Clara — o control plane tem credencial própria (§6)
- ❌ `slug` chegando cru num `CREATE SCHEMA` — é injeção de DDL (§6)
- ❌ Senha do admin inicial no corpo do POST (§6)
- ❌ `DROP SCHEMA` automático quando o provisionamento falha (§6)
- ❌ Deixar `migrate deploy` no `docker-entrypoint.sh` (§6)

---

## 10. Referências

- [Isolating multi-tenant data via database schemas — prisma/prisma#12420](https://github.com/prisma/prisma/issues/12420)
- [migrate dev ignora schema no shadowDatabaseUrl (regressão v6+) — prisma/orm#29709](https://github.com/prisma/orm/issues/29709)
- [Deploying migrations and seeding on multi-tenant databases — prisma/prisma#17569](https://github.com/prisma/prisma/discussions/17569)
- [prisma migrate deploy — Prisma Docs](https://www.prisma.io/docs/cli/migrate/deploy)
- [PgBouncer Transaction Pooling: The Multi-Tenant Nightmare](https://blog.sagarregmi.info.np/transaction-pooling-the-multi-tenant-nightmare)
- [PgBouncer Transaction Pooling for Multi-Tenant SaaS](https://multi-tenant-saas.com/tenant-aware-data-routing-query-scoping/connection-pooling-in-multi-tenant-systems/pgbouncer-transaction-pooling-for-multi-tenant-saas/)
- [PostgreSQL Multi-Tenant Architecture: Schema-Per-Tenant Guide for B2B SaaS](https://www.wellally.tech/blog/postgres-multi-tenant-database-schema-saas)
- [Tenant Isolation Strategies: Infrastructure Patterns for Multi-Tenant SaaS](https://securityboulevard.com/2026/01/tenant-isolation-strategies-infrastructure-patterns-for-multi-tenant-saas/)
- [ALTER TABLE ... SET SCHEMA — PostgreSQL Docs](https://www.postgresql.org/docs/current/sql-altertable.html)
