# Dashboard e relatórios no painel

**Priority:** medium
**Status:** draft
**Espelho no backend:** `backend/docs/specs/⚪draft_reports-dashboard.md`

## Overview

Troca o dashboard mock (`features/dashboard`, `dashboard.mock.ts`, data fixa `DASHBOARD_DAY` — ISS-002)
pelos números reais e cria a área **Relatórios** com quatro abas: Faturamento, Ocupação, Clientes e
IA. Cada relatório tem filtro de período, unidade e barbeiro, comparação com o período anterior,
gráficos simples e exportação CSV. O desenho do dashboard (cartões de KPI, "Próximos agendamentos",
"Ocupação por barbeiro", "Conversas aguardando") é mantido — só a fonte muda.

## Decisões de produto já tomadas

| Parâmetro | Valor |
|---|---|
| PD-25 | Faturamento, ocupação da agenda, clientes e retenção, desempenho da IA. |
| PD-26 | O barbeiro tem a tela "Meu dia" (S18), não o dashboard da casa. |
| PD-22 | Partes avançadas ficam fora do plano básico (S15, Q-S14-4): para o dono a aba aparece travada com o convite de upgrade; para a equipe, some (Q-S15-5). |
| PD-37 | A IA não fecha venda de clube/pacote: a aba IA mostra interesses encaminhados à equipe, não "vendas". |
| PD-40 | IA por créditos (S15). |
| PD-43 | Crédito **proporcional ao custo real** de cada chamada ao modelo e de cada transcrição; valores chegam em milicréditos. |
| PD-44 | O custo da IA aparece **em créditos consumidos e em custo estimado em US$** (`cost_usd_micros`). |
| Gráficos | Sem biblioteca de gráficos: barras e linha em SVG próprio (`features/dashboard/ui/`), com os tokens. Poucos tipos (barra, linha, mapa de calor), e uma dependência de 50+ kB não se paga. |

## Business Rules

### Dashboard (`/app/dashboard`)

- [ ] Data de hoje real (fuso da unidade selecionada; "Todas as unidades" usa o da primeira) — some
      `DASHBOARD_DAY`.
- [ ] Cartões: Agendamentos hoje ("N não confirmados"), Ocupação, Faturamento do dia e Ticket médio
      (só com `finance:read`), Faltas evitadas (7 dias). Valor `null` → cartão não aparece.
- [ ] "Próximos agendamentos" usa a lista da agenda (S03) do dia, a partir de agora, 7 linhas;
      "Conversas aguardando" usa a fila de handoff (S10). Cada bloco tem o próprio estado de
      carregando/erro — um módulo fora do ar não derruba o dashboard.
- [ ] "Ocupação por barbeiro" vem do relatório de ocupação de hoje.
- [ ] Recarrega a cada 60 s com a aba visível (`refetchInterval` + `refetchIntervalInBackground:
      false`) e mostra "Atualizado há N s" (de `freshness_seconds`).
- [ ] Barbeiro sem outras permissões entra em `/app/meu-dia` (S18) em vez do dashboard.

### Relatórios (`/app/relatorios/:aba`)

- [ ] Abas: `faturamento`, `ocupacao`, `clientes`, `ia` — cada uma só aparece com a permissão dela.
- [ ] Filtros na URL (`de`, `ate`, `unidade`, `barbeiro`, `agrupar`, `comparar`), com atalhos: Hoje,
      Últimos 7 dias, Este mês, Mês passado, Últimos 12 meses, Personalizado. Padrão: este mês.
      Período acima de 366 dias é recusado no formulário.
- [ ] Barbeiro (escopo `own`) não vê o filtro de barbeiro; gerente só vê as unidades dele.
- [ ] Totais com variação contra o período anterior ("+12% vs. mês passado"), seta e cor
      semântica — falta e cancelamento subindo é vermelho (regra pura, testada).
- [ ] **Faturamento**: série (barras), formas de pagamento, produção por barbeiro, top serviços e
      produtos.
- [ ] **Ocupação**: série, por barbeiro (barra de progresso igual à do dashboard), mapa de calor dia
      da semana × hora, agendamentos por origem (painel, IA, link, importação), faltas e não
      confirmados.
- [ ] **Clientes**: ativos, inativos, novos × recorrentes (série empilhada), retenção, frequência
      média, top clientes (link para a ficha da S13).
- [ ] **IA**: conversas, resolvidas pela IA, handoffs (e motivos, inclusive "Venda de clube/pacote" e
      "Sem créditos de IA"), agendamentos pela IA, interesses em clube/pacote encaminhados, abandono e
      recuperados e o **consumo** em **créditos e em custo estimado em US$** (PD-44): total do
      período, série, média por conversa, média por agendamento feito pela IA e por tipo (Conversas,
      Transcrição de áudio). Formatação por `formatCredits`/`formatUsdMicros` da feature `plan`.
      Sem `finance:read` (recepção) o backend devolve `null` e os blocos de consumo não aparecem.
      Saldo, extrato e compra de créditos ficam na página Plano (S15), com link para o dono.
- [ ] **Plano (Q-S14-4)**: sem `advanced_reports`, Faturamento e Ocupação funcionam com o seletor de
      mês (um mês de calendário, sem comparar, sem agrupar, sem CSV); as abas Clientes e IA, o
      período personalizado, "comparar" e "Exportar CSV" ficam travados para o dono e escondidos para
      a equipe.
- [ ] Barbeiro (`own`, Q-S14-1) vê só a aba Ocupação e a produção dele, sem faturamento da casa.
- [ ] "Exportar CSV" baixa o arquivo do backend com os filtros atuais (nome
      `navalha-<relatorio>-<de>-<ate>.csv`).
- [ ] `402` (fora do plano) mostra o aviso de upgrade da S15 no lugar do conteúdo, com os filtros
      desabilitados.

## Telas e fluxos

| Rota | Tela | Fluxos |
|---|---|---|
| `/app/dashboard` | `features/dashboard/pages/DashboardScreen.tsx` (existe) | `pages/kpis/`, `pages/upcoming/`, `pages/waiting/` |
| `/app/relatorios/:aba` | `features/dashboard/pages/ReportsScreen.tsx` | `pages/reports/revenue/`, `occupancy/`, `clients/`, `ai/`, `pages/reports/filters/` |

Item "Relatórios" na sidebar logo abaixo de Dashboard. A feature continua `dashboard` (ROADMAP §3).

## Data Contract

```text
GET /reports/dashboard?unit_id=
GET /reports/revenue | occupancy | clients | ai
    ?date_from&date_to&unit_id&barber_id&group_by&compare
GET /reports/{revenue|occupancy|clients|ai}/export   (mesmos filtros; text/csv)
GET /agenda?unit_id=&from=&to=                       (S03 — próximos agendamentos de hoje)
GET /conversations?queue=waiting_human&limit=3       (S10 — conversas aguardando)
```

O download do CSV passa pelo `shared/api/http.ts` (precisa do token e do `X-Tenant-Slug`): ganha
`requestBlob()` que devolve `Blob` + nome do `Content-Disposition`.

```text
features/dashboard/model/reports.types.ts   DashboardSummary, RevenueReport, OccupancyReport, …
features/dashboard/model/reports.rules.ts   atalhos de período, período anterior, variação %, cor da variação
features/dashboard/api/reports.api.ts       · reports.queries.ts
features/dashboard/ui/                      BarChart, LineChart, Heatmap, KpiCard, DeltaBadge (SVG + tokens)
dashboard.mock.ts                           apagado; ISS-002 atualizada
```

## Estado

| Estado | Onde |
|---|---|
| Relatórios e dashboard | TanStack Query: `['reports', aba, filtros]`, `['reports', 'dashboard', unidade]`; `placeholderData: keepPreviousData` ao trocar filtro |
| Filtros e aba | URL |
| Unidade do dashboard | `useUnitSelection()` (existe) |

## Permissões

| Ação | Permissão em `/auth/me` |
|---|---|
| ver dashboard | `appointment:read` |
| valores em dinheiro (dashboard e relatórios), créditos e US$ da IA | `finance:read` |
| aba Faturamento | `finance:read` |
| aba Ocupação | `appointment:read` |
| aba Clientes | `client:read` com escopo ≠ `own` |
| aba IA | `conversation:reply` |
| item "Relatórios" na sidebar | qualquer uma das quatro abas |

## Acceptance Criteria

- [ ] Dashboard sem nenhum dado mock; `dashboard.mock.ts` apagado.
- [ ] Testes em `tests/`: atalhos de período (virada de mês e ano), período anterior, variação e cor,
      formatação dos eixos (R$ abreviado, %, créditos, US$), escala dos gráficos com tudo zero, aba
      IA sem os blocos de consumo quando vêm `null`.
- [ ] Relatórios conferidos no navegador como dono, gerente de uma unidade e recepção.
- [ ] Testes em `tests/` cobrindo as regras puras da feature
- [ ] Tela conferida no navegador (estados vazio, carregando, erro)
- [ ] `make check-frontend` verde

## Dependencies

- Backend `⚪draft_reports-dashboard.md`; S03 (lista da agenda), S10 (fila de handoff).
- `⚪draft_frontend-plan-limits.md` (S15): `PlanUpgradeNotice`, o tratamento do `402` e
  `formatCredits`/`formatUsdMicros`.
- `⚪draft_frontend-pwa-mobile.md` (S18): "Meu dia" e a navegação por permissão.

## Notes

- Gráfico acessível: cada gráfico tem a tabela equivalente em `<details>` ("Ver dados") e `aria-label`
  com o total.
- No celular (S18) os relatórios viram uma coluna; o mapa de calor rola na horizontal dentro do
  próprio bloco, sem rolar a página.
- Perguntas do backend que mudam esta tela:
  > Resolvido em 2026-11-06: Q-S14-1 — barbeiro vê só os dele (ocupação e produção); Q-S14-2 — faturamento pela data de fechamento da comanda; Q-S14-3 — inativo = limite da reativação (40 dias); Q-S14-4 — básico com dashboard + faturamento e ocupação do mês, o resto em `advanced_reports` (ROADMAP §7). Custo da IA em créditos e em US$ estimado (PD-43, PD-44).
