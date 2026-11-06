# Progress

Estado atual do frontend. Atualizado ao fim de cada tarefa concluída.
Estados: `stable` · `in progress` · `blocked` · `planned` · `deprecated`.

## Features

| Feature | Rota | Estado | Atualizado | Notas |
|---|---|---|---|---|
| Arquitetura por feature | — | stable | 2026-11-05 | Spec `✅completed_frontend-feature-architecture.md`. `features/` + `shared/` + `app/`; fronteiras no ESLint (provadas com violações de propósito); Vitest com 10 testes. |
| `auth` — sessão e login | `/entrar` | stable | 2026-11-05 | **API real.** Login, `/auth/me`, renovação única em 401, logout, guarda de rota com retorno ao destino, slug da barbearia em localhost. Spec `✅completed_frontend-auth-session.md`. |
| `auth` — seleção de unidade | sidebar | stable | 2026-11-05 | Unidades reais do `/auth/me`; opção "Todas as unidades" para quem vê várias. Ainda não filtra nenhum dado (as telas são mock). |
| `landing` | `/` | stable | 2026-11-05 | Hero, WhatsApp, planos, FAQ, CTA. Conteúdo estático em `model/landing.content.ts`; captura de lead sem backend. |
| `scheduling` — Agenda | `/app/agenda` | in progress | 2026-11-05 | UI completa sobre mock (ISS-002, ISS-003). Aguarda o módulo de agenda do backend. |
| `scheduling` — modal de agendamento | painel | in progress | 2026-11-05 | Origem IA (pré-preenchido) ou manual; não salva nada ainda. |
| `dashboard` | `/app/dashboard` | in progress | 2026-11-05 | KPIs, próximos, ocupação, conversas — tudo mock. |
| `conversations` — Central | `/app/conversas` | in progress | 2026-11-05 | Lista, thread e ficha do cliente — mock. Aguarda WhatsApp + `ai-agent`. |
| `registry` — Cadastros | `/app/cadastros` | in progress | 2026-11-05 | Aba Barbeiros com tabela e formulário — mock. As outras abas (Unidades, Serviços, Clubes, Planos) não existem. |
| `customers` — Clientes | `/app/clientes` | planned | 2026-11-05 | Placeholder. |
| `finance` — Financeiro | `/app/financeiro` | planned | 2026-11-05 | Placeholder. |
| `design-system` — Tokens | `/app/tokens` | stable | 2026-11-05 | Documentação viva de `tokens.css`. |

## Qualidade

| Item | Estado | Notas |
|---|---|---|
| Lint | verde | `npm run lint` — ESLint 9 + fronteiras entre features. |
| Typecheck | verde | `tsc -b --noEmit`, inclui `tests/`. |
| Testes | 10 verdes (2026-11-05) | `tests/tenant.test.ts`, `unit-selection.test.ts`, `initials.test.ts`. |
| Build | verde | `npm run build` (~270 kB JS, ~41 kB CSS). |
| CI | configurado | `.github/workflows/ci.yml` na raiz do repo. |
