# Arquitetura por feature do frontend

**Priority:** high
**Status:** completed
**Espelho no backend:** `backend/docs/specs/✅completed_backend-modular-architecture.md` (mesmo objetivo, outra stack)

## Overview

O frontend estava organizado por tipo de arquivo: `app/pages/`, `app/components/`, `api/`, `auth/`,
`data/app.ts` (todos os mocks juntos) e `types.ts` (todos os tipos de domínio juntos). As telas
importavam o shell (`useShell` de `app/shell-context.ts`) e o `api/client.ts` estava morto (nenhuma
tela o usava). Esta spec reorganiza o código em **vertical slices por feature**, no modelo do
frontend da ClaraAI (`~/Documents/ClaraAI/frontend`), com a direção de dependência verificada pelo
ESLint. A mudança é estrutural: nenhuma tela, rota ou comportamento muda.

## Decisões de produto já tomadas

| Parâmetro | Valor |
|---|---|
| Comportamento e visual | idênticos — mesmas rotas, telas e CSS |
| Stack | continua Vite + React Router (o padrão do Clara é Next; ver DEC-001) |
| Nomes de feature | inglês, alinhados aos módulos futuros do backend: `scheduling`, `conversations`, `customers`, `registry`, `finance`, `dashboard` |
| URLs | continuam em português (`/app/agenda`, `/app/cadastros`…) |
| TanStack Query | adotado, mas instalado com a primeira feature real (DEC-005) |

## Business Rules

- [x] `src/` tem só `main.tsx`, `vite-env.d.ts`, `app/`, `features/` e `shared/`.
- [x] Cada feature tem `index.ts` + `api/ model/ pages/ ui/` (só as pastas que usa).
- [x] Uma feature só importa outra pelo `index.ts`; `shared/` não importa feature nem app; feature
      não importa app — tudo verificado por `import/no-restricted-paths`, com zonas geradas a partir
      das pastas de `src/features/`.
- [x] `shared/` não conhece tipo de negócio: `Badge`/`Tag` viraram componentes visuais genéricos
      (`BadgeVariant`, `TagVariant`); o mapeamento de status de conversa para variante foi para
      `conversations/ui/ThreadTagLabel.tsx`.
- [x] O `shell-context` deixou de existir: a seleção de unidade é da feature `auth`
      (`UnitSelectionProvider`, as unidades vêm do `/auth/me`) e o modal de agendamento é da feature
      `scheduling` (`AppointmentModalProvider`). O shell só compõe os providers.
- [x] `types.ts` e `data/app.ts` foram divididos entre as features donas (`model/*.types.ts`,
      `api/*.mock.ts`).
- [x] A ordem das folhas de estilo mudou (panel antes de landing); verificado que as duas só usam
      seletores de classe sem nenhum em comum, então a cascata não muda.

## Telas e fluxos

| Rota | Antes | Depois |
|---|---|---|
| `/` | `landing/LandingPage.tsx` | `features/landing/pages/LandingScreen.tsx` (+ `pages/landing/` seções) |
| `/entrar` | `auth/LoginPage.tsx` | `features/auth/pages/LoginScreen.tsx` + `pages/login/LoginForm.tsx` |
| `/app/*` (layout) | `app/AppLayout.tsx` | `app/_shell/AppLayout.tsx` |
| `/app/dashboard` | `app/pages/DashboardPage.tsx` | `features/dashboard/pages/DashboardScreen.tsx` |
| `/app/agenda` | `app/pages/AgendaPage.tsx` | `features/scheduling/pages/AgendaScreen.tsx` |
| `/app/conversas` | `app/pages/InboxPage.tsx` | `features/conversations/pages/InboxScreen.tsx` |
| `/app/clientes` | `app/pages/ClientesPage.tsx` | `features/customers/pages/CustomersScreen.tsx` |
| `/app/cadastros` | `app/pages/CadastrosPage.tsx` | `features/registry/pages/RegistryScreen.tsx` |
| `/app/financeiro` | `app/pages/FinanceiroPage.tsx` | `features/finance/pages/FinanceScreen.tsx` |
| `/app/tokens` | `app/pages/TokensPage.tsx` | `features/design-system/pages/TokensScreen.tsx` |

Outros movimentos: `api/http.ts` → `shared/api/`; `auth/tokens.ts`, `auth/tenant.ts` →
`shared/session/`; `app/components/{Icon,Badge}.tsx`, `app/pages/ModulePlaceholder.tsx` →
`shared/ui/`; `styles/*.css` + `app/app.css` → `shared/styles/` (`app.css` virou `panel.css`);
`api/client.ts` (morto) removido.

## Acceptance Criteria

- [x] ESLint configurado (`eslint.config.js`), com as fronteiras provadas por violações de
      propósito: import profundo de outra feature (alias e relativo), feature importando `app/` e
      `shared/` importando feature — as quatro barradas.
- [x] Vitest configurado; 10 testes em `tests/`.
- [x] `npm run lint`, `npm run typecheck`, `npm run test` e `npm run build` verdes.
- [x] Dev server do compose servindo os módulos novos (HTTP 200) sem erro de transformação.
- [x] `rules.md`, `CLAUDE.md`, `README.md` e `memory/` descrevem a estrutura nova.

## Dependencies

- Dev: `eslint@9`, `@eslint/js`, `typescript-eslint`, `eslint-plugin-react-hooks`,
  `eslint-plugin-import`, `eslint-import-resolver-typescript`, `globals`, `vitest` (DEC-008).

## Notes

- Um `eslint-disable-next-line jsx-a11y/no-autofocus` apontava para um plugin que nunca foi
  instalado; removido.
- O container `web` tem `node_modules` próprio (volume anônimo); as dependências novas são só de
  desenvolvimento e não são necessárias para o dev server (ISS-007).
