# Caixa, despesas e resultado no painel

**Priority:** high
**Status:** draft
**Espelho no backend:** `backend/docs/specs/⚪draft_finance-cash-expenses.md`

## Overview

Três páginas no índice do financeiro (`/app/financeiro`, criado em `⚪draft_frontend-commissions.md`):
**Caixa** — a recepção abre a gaveta com o fundo, registra sangria e reforço e fecha contando cada
forma de pagamento; **Despesas** — contas a pagar com vencimento, recorrência, parcelas e baixa;
**Resultado do mês** — receita, taxas, comissões, despesas e o que sobrou. Regras e contrato no
espelho do backend.

## Decisões de produto já tomadas

| Parâmetro | Valor |
|---|---|
| PD-14 | Caixa diário (abertura, fechamento, sangria, reforço), despesas/contas a pagar, resultado do mês. Fora: vales, NFS-e. |
| PD-10 | Pix e cartão são conferidos contra extrato/maquininha; o sistema só registra. |
| Permissão nova | `cash:operate` (dono, gerente, recepção): a recepção opera o caixa sem ver faturamento. |
| Fechamento cego | Padrão: quem não tem `finance:read` conta sem ver o esperado (Q-S09-2). |
| PD-38 | Gorjeta fora da receita, repassada integral; a taxa do cartão sobre ela é da barbearia (está em "Taxas"). |

## Business Rules

### Caixa (`/app/financeiro/caixa`)

- [ ] Mostra o caixa da unidade selecionada (`useUnitSelection`). Sem caixa aberto: card "Caixa
      fechado" com "Abrir caixa" — fundo de troco pré-preenchido com o deixado no último
      fechamento; valor diferente mostra o aviso "Diferente do fundo deixado ontem (R$ X)".
- [ ] Caixa aberto: aberto por/às, fundo, e por forma de pagamento a quantidade de recebimentos;
      o **valor esperado** só para quem tem `finance:read` (o backend manda `null` para os demais).
- [ ] Sangria e reforço: diálogo com valor, motivo (Depósito no banco, Pagamento de comissão,
      Despesa, Troco, Outro) e descrição; lista de movimentos do dia. Erro de sangria acima do
      saldo aparece no campo valor.
- [ ] Fechar: uma linha por forma (dinheiro sempre; as demais quando tiveram recebimento) com
      "Contado"; para dinheiro, contador opcional por cédula/moeda que soma o total (função pura).
      "Fundo que fica para amanhã" ≤ dinheiro contado. Comandas abertas na unidade geram aviso
      "Há N comandas abertas" com link — não bloqueia.
- [ ] Depois de fechar: quem tem `finance:read` vê esperado × contado × diferença por forma (verde
      zero, vermelho falta, âmbar sobra) e a nota; a recepção vê "Caixa fechado às HH:MM".
      Diferença ≠ 0 exige a nota antes de enviar (o backend valida de novo).
- [ ] Histórico (`finance:read`): lista de caixas por data e unidade com diferença total;
      "Reabrir" no mais recente (`finance:write`).

### Despesas (`/app/financeiro/despesas`)

- [ ] Abas na URL: **A pagar** (pendentes, vencidas primeiro, em vermelho), **Pagas**,
      **Canceladas**, **Recorrentes**. Filtros: período de vencimento, categoria, unidade, busca.
      Soma do filtro no topo.
- [ ] Nova despesa: categoria, descrição, fornecedor, valor, vencimento, competência (padrão =
      mês do vencimento, editável), unidade (ou "Geral da barbearia", só com todas as unidades),
      observações, "Parcelar em N vezes" (prévia das parcelas) ou "Repetir" (vira recorrência:
      mensal/semanal/anual, dia, início, fim opcional).
- [ ] Pagar: data, valor pago (padrão = valor), forma (opcional), "Saiu do caixa" (só com
      `cash:operate` e caixa aberto; avisa que vira sangria). Desfazer pagamento com confirmação.
- [ ] Ocorrência de recorrência mostra o selo "Recorrente"; editar só ela pergunta "Só esta" (a
      edição a desliga do modelo) ou "Esta e as próximas" (edita o modelo).
- [ ] Categorias: gerenciadas num diálogo da própria página (criar, renomear, inativar).

### Resultado do mês (`/app/financeiro/resultado`)

- [ ] Mês e unidade na URL (padrão: mês corrente, todas as unidades do escopo).
- [ ] Quadro em cascata: Receita (serviços, produtos, mensalidades, pacotes) → − Taxas →
      − Comissões → − Despesas por categoria → **Resultado** e margem %. Descontos concedidos e
      gorjetas aparecem como informação, fora da conta (gorjeta: "repassada integral aos
      barbeiros"; a taxa sobre ela já está em Taxas, PD-38).
- [ ] Com unidade escolhida: linha "Despesas gerais (não rateadas)" e os dois resultados.
- [ ] Gráfico diário receita × despesas (barras) e tabela por forma de pagamento com taxa.
- [ ] Cada linha leva ao detalhe: receita → Comandas fechadas no período; comissões → Comissões;
      despesas → Despesas filtradas.

## Telas e fluxos

| Rota | Tela | Fluxos |
|---|---|---|
| `/app/financeiro/caixa` | `features/finance/pages/CashScreen.tsx` | `pages/cash/open/`, `movements/`, `close/`, `history/` |
| `/app/financeiro/despesas` | `ExpensesScreen.tsx` | `pages/expenses/list/`, `form/`, `pay/`, `recurrences/`, `categories/` |
| `/app/financeiro/resultado` | `MonthResultScreen.tsx` | `pages/result/` |

## Data Contract

```text
GET /cash-sessions/current · GET /cash-sessions · POST /cash-sessions · GET /cash-sessions/{id}
POST /cash-sessions/{id}/movements · /close · /reopen
GET/POST /expense-categories · PATCH/DELETE /expense-categories/{id}
GET/POST /expenses · GET/PATCH/DELETE /expenses/{id} · POST /expenses/{id}/pay|unpay|cancel
GET/POST /expense-recurrences · PATCH/DELETE /expense-recurrences/{id}
GET /finance/result · GET/PUT /finance/settings
GET /payment-methods (via registry) · GET /tenant/units (já existe)
```

```text
features/finance/model/cash.types.ts · expenses.types.ts · result.types.ts
features/finance/model/cashCount.rules.ts     contador de cédulas, fundo ≤ contado, cor da diferença
features/finance/model/expenses.rules.ts      prévia de parcelas (resto na primeira), vencida,
                                              competência padrão, validação
features/finance/api/cash.api.ts · expenses.api.ts · result.api.ts (+ *.queries.ts)
```

Chart: barras simples em SVG com tokens (sem dependência nova).

## Estado

| Estado | Onde |
|---|---|
| Caixa atual, histórico, despesas, resultado | TanStack Query (`['cash-session', unitId]`, `['cash-sessions', filtros]`, `['expenses', filtros]`, `['finance-result', mês, unidade]`); fechar comanda (S06) invalida `['cash-session', unitId]` |
| Aba, filtros, mês | URL |
| Contagem do fechamento, formulários | estado local |

## Permissões

| Ação | Permissão em `/auth/me` |
|---|---|
| ver Caixa, abrir, movimentar, fechar | `cash:operate` |
| ver esperado/diferença, histórico | `finance:read` |
| reabrir caixa | `finance:write` |
| ver Despesas e Resultado | `finance:read` |
| criar/pagar/editar despesas, categorias, recorrências | `finance:write` |
| "Saiu do caixa" ao pagar despesa | `finance:write` + `cash:operate` |

## Acceptance Criteria

- [ ] Três páginas no índice do financeiro, com as permissões acima; `cash:operate` reconhecida
      no tipo de permissões de `auth`.
- [ ] Testes em `tests/`: contador de cédulas, prévia de parcelas, despesa vencida no fuso,
      montagem da cascata do resultado.
- [ ] `make docs-api` dentro do contrato.
- [ ] Tela conferida no navegador: como recepção (abrir, sangria, fechar cego) e como dono
      (diferença, histórico, reabrir, despesas recorrente e parcelada, resultado).
- [ ] `make check-frontend` verde; `README.md` e `memory/progress.md` atualizados.

## Dependencies

- Backend `⚪draft_finance-cash-expenses.md` implementado e congelado (com `cash:operate` no mapa).
- `⚪draft_frontend-commissions.md` — índice do financeiro.
- `⚪draft_frontend-tickets.md` — link "Abrir caixa" no fechamento da comanda e invalidação do
  caixa.

## Notes

- Perguntas de produto: Q-S09-1 a Q-S09-3 no espelho do backend.
  > Resolvido em 2026-11-06: Q-S09-1 — fechar comanda exige caixa aberto (configurável, ligado);
  > Q-S09-2 — fechamento cego para a recepção (configurável, ligado); Q-S09-3 — despesa por
  > competência (ROADMAP §7). A tela acima já segue essas respostas.
- Recepção sem `finance:read` vê só o Caixa no índice do financeiro.
