# Progress

Estado atual do frontend. Atualizado ao fim de cada tarefa concluída.
Estados: `stable` · `in progress` · `blocked` · `planned` · `deprecated`.

## Features

| Feature | Rota | Estado | Atualizado | Notas |
|---|---|---|---|---|
| Arquitetura por feature | — | stable | 2026-11-05 | Spec `✅completed_frontend-feature-architecture.md`. `features/` + `shared/` + `app/`; fronteiras no ESLint (provadas com violações de propósito); Vitest. |
| `auth` — primeiro acesso / convite | `/convite/:token` | stable | 2026-11-05 | **API real.** Valida o link antes de pedir a senha, aceita e entra. Spec `✅completed_frontend-invite-acceptance.md`. Não conferida em navegador ainda. |
| `auth` — sessão e login | `/entrar` | stable | 2026-11-05 | **API real.** Login, `/auth/me`, renovação única em 401, logout, guarda de rota com retorno ao destino, slug da barbearia em localhost. Spec `✅completed_frontend-auth-session.md`. |
| `auth` — seleção de unidade | sidebar | stable | 2026-11-05 | Unidades reais do `/auth/me`; opção "Todas as unidades" para quem vê várias. Ainda não filtra nenhum dado (as telas são mock). |
| `landing` | `/` | stable | 2026-11-05 | Hero, WhatsApp, planos, FAQ, CTA. Conteúdo estático em `model/landing.content.ts`; captura de lead sem backend. |
| `scheduling` — Escala e Ausências | `/app/agenda/escala`, `/app/agenda/ausencias` | in progress | 2026-11-07 | **API real.** Grade semanal por barbeiro ("Horário da unidade" quando não há escala), editor expediente + pausas, dias especiais, folgas/férias/atestados. Filtra pela unidade do seletor (`unitId`). Spec `⏳active_frontend-barber-schedule.md` (S02); bloqueio pela agenda vai com a S03; falta o navegador (ISS-010). |
| `scheduling` — Agenda | `/app/agenda` | in progress | 2026-11-05 | UI completa sobre mock (ISS-002, ISS-003). Aguarda o módulo de agenda do backend. |
| `scheduling` — modal de agendamento | painel | in progress | 2026-11-05 | Origem IA (pré-preenchido) ou manual; não salva nada ainda. |
| `dashboard` | `/app/dashboard` | in progress | 2026-11-05 | KPIs, próximos, ocupação, conversas — tudo mock. |
| `conversations` — Central | `/app/conversas` | in progress | 2026-11-05 | Lista, thread e ficha do cliente — mock. Aguarda WhatsApp + `ai-agent`. |
| `registry` — Cadastros | `/app/cadastros` | in progress | 2026-11-06 | **API real.** "Cadastros" é um dropdown na sidebar com Unidades, Barbeiros, Serviços, Produtos, Combos, Clubes, Pacotes e Formas de pagamento (PD-09/S05), cada um na própria rota `/app/cadastros/<cadastro>`; `/app/cadastros` abre o primeiro permitido e `?aba=` antigo redireciona (2026-11-06). Barbeiros (filtros na URL, serviços habilitados, vínculo opcional com login) e Serviços (duração, preço em reais → centavos). Unidades, Clubes e Planos: "em breve". Spec `⏳active_frontend-registry-basic-crud.md`; falta conferir no navegador (ISS-010). |
| `registry` — Unidades | `/app/cadastros/unidades` | in progress | 2026-11-06 | **API real.** Lista, formulário (fuso, telefone, agendamento online), horário semanal (`WeeklyHoursEditor`, exportado para S16) e feriados/datas especiais com "Aplicar também em" e sugestão dos feriados nacionais. Spec `⏳active_frontend-units-settings.md` (S01); falta o navegador (ISS-010). |
| `settings` — Configurações | `/app/configuracoes` | in progress | 2026-11-06 | **API real.** Seções Barbearia (nome, contato, Instagram, sobre, contato visível ao barbeiro) e Agendamento (políticas). Só com `tenant:configure` (menu filtrado por permissão). Spec S01. |
| `customers` — Clientes | `/app/clientes` | in progress | 2026-11-06 | **API real.** Busca com espera de 300 ms e página na URL, telefone com máscara e E.164, inativar/apagar. Spec `⏳active_frontend-registry-basic-crud.md`; falta conferir no navegador (ISS-010). |
| `finance` — Financeiro | `/app/financeiro` | planned | 2026-11-06 | Placeholder. Specs `⚪draft_frontend-cash-expenses.md` (S09) e `⚪draft_frontend-commissions.md` (S08). |
| `design-system` — Tokens | `/app/tokens` | stable | 2026-11-05 | Documentação viva de `tokens.css`. |

## Planejamento

Produto inteiro planejado em 2026-11-06: [`docs/ROADMAP.md`](../../../docs/ROADMAP.md) (decisões,
features e rotas-alvo) e specs `⚪draft_frontend-*` em `docs/specs/`, espelhando as do backend
(S01–S17) mais `⚪draft_frontend-pwa-mobile.md` (S18, só frontend).

## Qualidade

| Item | Estado | Notas |
|---|---|---|
| Lint | verde | `npm run lint` — ESLint 9 + fronteiras entre features. |
| Typecheck | verde | `tsc -b --noEmit`, inclui `tests/`. |
| Testes | 15 verdes (2026-11-05) | `tests/tenant.test.ts`, `unit-selection.test.ts`, `initials.test.ts`, `invite-rules.test.ts`. |
| Build | verde | `npm run build` (~270 kB JS, ~41 kB CSS). |
| CI | configurado | `.github/workflows/ci.yml` na raiz do repo. |
