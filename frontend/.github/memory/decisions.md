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

## DEC-001 — SPA com Vite + React Router, sem BFF

**Date:** 2026-11-05 (registro retroativo)
**Status:** accepted

**Context:** O frontend da ClaraAI usa Next.js com BFF (rotas `app/api/` que injetam o JWT no
servidor). Este projeto nasceu como conversão de protótipos para React + Vite.

**Decision:** SPA estática (Vite + React Router), servida por nginx em produção. Em dev, o Vite
proxya `/api` para o core-api (mesma origem, sem CORS). O tenant vem do subdomínio em produção e do
campo "Barbearia" no login em localhost (`X-Tenant-Slug`, backend DEC-002).

**Consequences:** Sem servidor próprio, o JWT fica no navegador (ISS-001). O padrão de pastas do
Clara se aplica igual; o que é específico de Next (BFF, `proxy.ts`, `next-intl`) não.

## DEC-002 — Sessão: tokens no localStorage, renovação única compartilhada

**Date:** 2026-11-05 (retroativo)
**Status:** accepted

**Decision:** A API devolve access e refresh no corpo; ambos ficam em `localStorage`
(`shared/session/tokens.ts`). Na subida, `/auth/me` prova que o token ainda vale. Um 401 dispara
uma única renovação compartilhada entre chamadas simultâneas (senão a rotação do backend invalida
os tokens umas das outras) e refaz a chamada uma vez.

**Consequences:** Legível por qualquer script da página — tão seguro quanto o app for livre de XSS.
O formato mais seguro (refresh em cookie httpOnly, access em memória) depende de mudança no backend
(ISS-001).

## DEC-003 — Vertical slice por feature

**Date:** 2026-11-05
**Status:** accepted

**Context:** O código estava em pastas por tipo (`app/pages`, `app/components`, `api/`, `auth/`,
`data/`, `types.ts`), com o shell importado pelas telas (`useShell`) e um `types.ts` único para
todos os domínios.

**Options considered:**
1. Manter pastas por tipo — cresce como depósito.
2. Feature folders no modelo do frontend da ClaraAI (`features/` + `shared/` + `app/`), com a
   direção de dependência verificada pelo ESLint.

**Decision:** Opção 2. Divergências do Clara, deliberadas: componente vai para `shared/ui/` a
partir de **2** features (o Clara exige 3), porque o projeto é menor; há `*.mock.ts` em `api/`
para os módulos que o backend ainda não tem; contexts transversais moram na feature dona (não em
`app/_providers`). Spec: `docs/specs/✅completed_frontend-feature-architecture.md`.

**Consequences:** O `shell-context` foi dividido: seleção de unidade foi para `auth`, modal de
agendamento para `scheduling` — as telas não importam mais o `app/`.

## DEC-004 — Testes em `tests/` com Vitest

**Date:** 2026-11-05
**Status:** accepted

**Context:** Não havia testes. O Clara roda testes com `node --test` e strip-types (Node 22.6+); o
ambiente local aqui tem Node 20 e o projeto já usa Vite.

**Decision:** Vitest (reaproveita o `vite.config.ts` e o alias `@/`), testes em `tests/` na raiz,
como no Clara (DEC-003 de lá). Começa por regras puras; testes de componente entram quando houver
lógica de tela que valha a pena (exigiria `jsdom` + Testing Library — dependência a aprovar).

**Consequences:** `npm run test` roda em ~1 s; o CI roda junto com lint e typecheck.

## DEC-005 — TanStack Query para dado de servidor, adotado com a primeira feature real

**Date:** 2026-11-05
**Status:** accepted

**Context:** O Clara usa TanStack Query v5 para todo dado de servidor. Aqui, hoje, a única
integração real é a sessão (`/auth/me`, coberta pelo `AuthProvider`); o resto é mock.

**Decision:** Adotar TanStack Query, mas instalá-lo junto com a primeira feature que consumir dado
de servidor além da sessão (provavelmente a Agenda), na spec dela — `QueryClientProvider` em
`main.tsx`, `*.queries.ts` em `api/` de cada feature. Instalar agora seria um provider sem nenhum
consumidor.

**Consequences:** A spec da primeira feature real precisa incluir o setup e registrar a aprovação
da dependência.

## DEC-006 — Sem i18n: só português

**Date:** 2026-11-05
**Status:** accepted

**Decision:** Produto para barbearias brasileiras; todo texto de UI direto em português, sem
biblioteca de i18n (o Clara usa `next-intl` em três línguas).

**Consequences:** Se surgir outro idioma, extrair textos vira projeto próprio (spec).

## DEC-007 — CSS puro com design tokens

**Date:** 2026-11-05 (retroativo)
**Status:** accepted

**Decision:** Sem framework de CSS. Tokens em `shared/styles/tokens.css` (variáveis CSS), classes
em `panel.css`/`landing.css`, e a tela `/app/tokens` como documentação viva. Trocar `--accent`
repinta o painel inteiro.

**Consequences:** Nada de Tailwind/CSS-in-JS sem nova decisão.

## DEC-008 — ESLint 9 com fronteiras geradas a partir das pastas de feature

**Date:** 2026-11-05
**Status:** accepted

**Decision:** `eslint.config.js` (flat config) com `typescript-eslint`, `react-hooks` e
`import/no-restricted-paths`. As zonas entre features são geradas lendo `src/features/`, então
feature nova já nasce protegida. Dependências aprovadas na reorganização: `eslint@9`,
`@eslint/js`, `typescript-eslint`, `eslint-plugin-react-hooks`, `eslint-plugin-import`,
`eslint-import-resolver-typescript`, `globals`, `vitest`.

**Consequences:** ESLint 9 já não é a versão suportada mais recente (o npm avisa); ficou no 9
porque o `eslint-plugin-import` é o que oferece `no-restricted-paths`. Reavaliar (ou trocar por
`eslint-plugin-import-x`) ao subir para o 10.

## DEC-009 — `docs/` do projeto: `specs/` para planejamento e `api/` gerada

**Date:** 2026-11-06
**Status:** accepted

**Context:** As specs viviam em `.github/specs/` (modelo Clara), misturadas com o que só orienta a
IA, e não havia referência da API. Pedido do dono do produto: cada projeto organiza a própria
`docs/` com `specs/` e `api/`, separados, para documentar durante o desenvolvimento com as specs
escritas antes, no planejamento.

**Decision:** Specs em `frontend/docs/specs/` (espelho em `backend/docs/specs/` quando a
funcionalidade toca os dois lados). A `.github/` fica com regras, memória e skills, e aponta para lá.
A referência da API é **gerada**, nunca escrita à mão: `scripts/api-docs.ts` (rodado com `vite-node`) casa as chamadas `request(...)` de cada `*.api.ts` (e do `shared/api`) com o OpenAPI congelado do backend e gera `docs/api/` com links para `backend/docs/api/`; `tests/api-docs.test.ts` falha se divergir ou se o frontend chamar rota fora do contrato. `make docs-api` regenera os dois lados.

**Consequences:** A documentação de API não envelhece em silêncio — o CI pega a divergência. Texto
explicativo (o porquê de uma regra) continua na spec, não na referência gerada.
