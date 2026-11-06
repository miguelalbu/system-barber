# Decisions

Architecture Decision Records (ADR). **Só acrescentar** — nunca editar uma entrada passada. Para
mudar uma decisão, crie outra e marque a antiga como `superseded by DEC-NNN`.

<!-- Modelo:

## DEC-NNN — Título

**Date:** AAAA-MM-DD
**Status:** accepted | superseded by DEC-NNN

**Context:** Que problema exigiu a decisão?

**Options considered:**
1. Opção A — prós e contras
2. Opção B — prós e contras

**Decision:** O que foi escolhido e por quê.

**Consequences:** Que trade-offs foram aceitos.
-->

## DEC-001 — Multi-tenant em banco compartilhado com Row-Level Security

**Date:** 2026-11-05 (registro retroativo; a decisão é da migration 0001)
**Status:** accepted

**Context:** SaaS de barbearias: muitas barbearias pequenas, dados que nunca podem vazar entre elas,
e a porta aberta para uma barbearia grande ganhar banco próprio no futuro.

**Options considered:**
1. Banco por tenant — isolamento máximo, custo e operação altos desde o primeiro cliente.
2. Schema por tenant — migrations multiplicadas, pool de conexões complicado.
3. Banco compartilhado + `tenant_id` + RLS — um banco, isolamento garantido pelo Postgres.

**Decision:** Opção 3. Toda tabela de barbearia tem `tenant_id` e policy
`tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid` com `ENABLE` + `FORCE`. A
aplicação conecta com `navalha_app` (sem SUPERUSER/BYPASSRLS); migrations com o dono do schema. O
tenant é fixado por transação com `set_config(..., true)`.

**Consequences:** Esquecer um filtro devolve zero linhas, nunca dado de outra barbearia. Exige
disciplina: toda tabela nova precisa da policy na migration, e o `true` do `set_config` não pode
sumir (com `SET` simples, o tenant gruda na conexão do pool). `tenant_id` fica mesmo se um dia um
tenant tiver banco próprio — é o que torna essa migração possível.

## DEC-002 — O tenant vem do domínio de acesso

**Date:** 2026-11-05 (retroativo)
**Status:** accepted

**Context:** Login precisa saber de qual barbearia é o usuário; e-mail precisa poder repetir entre
barbearias.

**Decision:** Cada barbearia atende em `<slug>.<BASE_DOMAIN>` ou em domínio próprio
(`tenants.custom_domain`, via CNAME). O tenant é resolvido do header `Host` antes de qualquer
regra. Em `ENVIRONMENT=dev`, o header `X-Tenant-Slug` substitui o subdomínio (curl, localhost);
fora de dev ele é ignorado. Token emitido para uma barbearia é recusado (403) no domínio de outra.

**Consequences:** E-mail é único por barbearia, e o login não pergunta "qual barbearia?" em
produção. Em localhost o frontend precisa pedir o slug.

## DEC-003 — Admin da plataforma fora da tenancy

**Date:** 2026-11-05 (retroativo)
**Status:** accepted

**Context:** A equipe Navalha precisa de acesso de suporte cross-tenant.

**Decision:** `platform_admins` é tabela de control plane, sem RLS e fora do RBAC de barbearia. A
conta nasce só pelo seed (`python -m app.management.seed platform-admin`), com senha de no mínimo
12 caracteres, gerada e exibida uma única vez se omitida. Ainda não há rota de login para ela
(ISS-005).

**Consequences:** É a credencial mais valiosa do sistema; o login dela, quando existir, terá tipo de
token próprio e auditoria de acesso cross-tenant (spec própria).

## DEC-004 — RBAC por permissão, com eixo de escopo

**Date:** 2026-11-05 (retroativo)
**Status:** accepted

**Context:** "Barbeiro vê agendamentos, mas só os dele" — RBAC puro não expressa isso; e pedidos de
cliente como "a recepção pode ver o faturamento do dia" não podem custar quarenta endpoints.

**Decision:** O código pede a permissão (`require(Permission.X)`), nunca o cargo. O mapa cargo →
permissão → escopo (`all` / `unit` / `own`) vive só em `identity/permissions.py`. As permissões não
vão no JWT: são resolvidas no servidor a cada request.

**Consequences:** Mudar o mapa vale na hora. Toda rota que lista dados aplica `ctx.scope`.

## DEC-005 — Access JWT curto + refresh opaco rotativo

**Date:** 2026-11-05 (retroativo)
**Status:** accepted

**Decision:** Access token JWT HS256 de 15 min (`sub`, `tid`, `rol`, `bid`, `typ`); refresh token
opaco de 30 dias guardado só como SHA-256, revogado ao ser trocado (rotação). Senhas com argon2id,
com rehash transparente no login quando os parâmetros mudam.

**Consequences:** Logout revoga na hora. Falta detecção de reuso de refresh (ISS-003).

## DEC-006 — Monólito modular por feature

**Date:** 2026-11-05
**Status:** accepted

**Context:** O backend era um pacote plano (`models.py`, `schemas.py`, `deps.py`, `routers/`) com
regra de negócio nos handlers. Os próximos blocos (catálogo, agenda, clientes, financeiro,
conversas) transformariam cada arquivo plano num depósito de domínios.

**Options considered:**
1. Manter o layout plano por camada — simples hoje, cresce mal.
2. Microserviços — custo operacional sem justificativa para o tamanho atual.
3. Monólito modular por feature, no modelo do backend da ClaraAI.

**Decision:** Opção 3. `app/core/` + `app/modules/<modulo>/` com `router/ service/ repository/
model/` + `schemas.py` + `public.py`. Divergências do Clara, deliberadas: `cache/` e `jobs/` só
quando o módulo usar Redis/worker (o Clara exige as seis pastas sempre); `dependencies.py` opcional
na raiz do módulo para as dependências FastAPI. Spec:
`specs/✅completed_backend-modular-architecture.md`.

**Consequences:** Um pouco mais de arquivos por funcionalidade; em troca, cada domínio novo tem
lugar óbvio e fronteiras verificadas por `lint-imports` e testes.

## DEC-007 — `identity` é o único módulo do núcleo, e guarda tenants e barbeiros

**Date:** 2026-11-05
**Status:** accepted

**Context:** Separar `tenancy` de `identity` criaria um ciclo: as rotas de tenant precisam de
usuário autenticado (identity) e o identity precisa de tenant (sessão com RLS, cadastro de
barbearia).

**Decision:** Um módulo só, `identity`, com tenants, unidades, usuários, convites, sessões, RBAC,
admin da plataforma e `Barber` (que nasce no aceite de convite). Todo módulo de domínio depende dele
pelo `public.py`.

**Consequences:** Quando o módulo de agenda existir, reavaliar se `Barber` migra para lá (recurso de
agenda) — ele é mais agenda do que identidade. A mudança não afeta o banco (a fronteira de módulo é
de código, não de dado).

## DEC-008 — `core/model_registry.py` é a única exceção a "core não importa módulo"

**Date:** 2026-11-05
**Status:** accepted

**Context:** O Alembic compara o banco com `Base.metadata`; model não importado parece tabela a
apagar. Algo precisa importar todos os models, e o `alembic/env.py` precisa de um ponto único.

**Decision:** `app/core/model_registry.py` importa o pacote `model` de cada módulo. É a única
exceção no contrato do import-linter (`ignore_imports`).

**Consequences:** Módulo novo adiciona uma linha no registry; o snapshot `db_schema` e o
`alembic check` acusam se faltar.

## DEC-009 — Snapshots de contrato como portão

**Date:** 2026-11-05
**Status:** accepted

**Decision:** `tests/test_contracts/` congela o OpenAPI, a tabela de rotas com a cadeia de
dependências de cada uma (incluindo `require(<permissão>)`) e o schema do ORM. Foram gerados antes
da migração modular e não mudaram com ela. Regenerar só com `UPDATE_CONTRACT_SNAPSHOTS=1`, para
mudança intencional registrada na spec.

**Consequences:** Uma guarda de permissão removida por engano, uma rota renomeada ou uma coluna
alterada quebram o teste em segundos, sem precisar de teste de comportamento para cada caso.

## DEC-010 — Monorepo com camada de contexto por projeto

**Date:** 2026-11-05
**Status:** accepted

**Context:** No Clara, backend e frontend são repositórios separados, cada um com seu `CLAUDE.md` e
sua `.github/`. Aqui os dois vivem num repositório só.

**Decision:** Cada projeto mantém a própria camada de contexto (`backend/.github/`,
`frontend/.github/`) e o próprio `CLAUDE.md`; o `CLAUDE.md` da raiz só orienta e aponta para eles.
A `.github/` da raiz guarda o que o GitHub lê: workflows de CI e templates de issue/PR. Spec que
toca os dois lados existe nas duas pastas, uma apontando para a outra.

**Consequences:** O contexto que a IA carrega continua focado num projeto. O CI é um só, com jobs
separados por projeto.
