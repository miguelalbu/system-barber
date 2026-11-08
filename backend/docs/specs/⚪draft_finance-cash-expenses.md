# Caixa diário, despesas e resultado do mês

**Priority:** high
**Status:** draft
**Espelho no frontend:** `frontend/docs/specs/⚪draft_frontend-cash-expenses.md`

## Overview

Fecha o dinheiro da barbearia em três peças (PD-14). **Caixa diário** por unidade: a recepção abre
com o fundo de troco, a comanda (S06) registra os recebimentos na sessão aberta, sangrias e
reforços entram durante o dia e, no fim, a recepção **conta** o que tem por forma de pagamento e o
sistema mostra a diferença. **Despesas e contas a pagar**: aluguel, luz, fornecedor, com categoria,
vencimento, recorrência e baixa. **Resultado do mês**: receita das comandas − taxas − comissões −
despesas. Esta spec cria o módulo `finance`, o mais alto da cadeia do dinheiro: ele **lê** `sales`,
`commissions` e `catalog` pelo `public.py` e não publica evento.

## Decisões de produto já tomadas

| Parâmetro | Valor |
|---|---|
| PD-10 | Sem gateway: o caixa confere o que foi registrado; Pix e cartão são conferidos contra o extrato/maquininha. |
| PD-14 | Financeiro = comanda + caixa diário (abertura, fechamento, sangria, reforço) + despesas/contas a pagar (resultado do mês). Fora: vales/adiantamentos, NFS-e. |
| PD-12 | Comissão é o custo de pessoal do resultado (barbeiro só comissionado). |
| PD-38 | Gorjeta fica fora da receita e é repassada integral ao barbeiro; a taxa do cartão sobre ela é custo da barbearia (entra em "taxas"). |
| S06 T6 | A comanda pergunta ao `finance`, na mesma transação do fechamento, qual a sessão de caixa aberta (resolvedor registrado no `main.py`). |
| Convenções | Centavos; "dia" no fuso da unidade; escopo por unidade. |

### Decisões técnicas desta spec

| # | Decisão | Por quê |
|---|---|---|
| T1 | **Permissão nova `cash:operate`** (owner `all`, manager `unit`, receptionist `unit`, barber —) para abrir, movimentar e fechar o caixa. | A recepção opera a gaveta mas não tem `finance:*` de propósito ("a recepção fecha comanda, não vê faturamento"). `finance:write` daria a ela despesas e resultado; `ticket:write` funcionaria, mas amarraria duas coisas diferentes — uma barbearia que separar "quem atende no balcão" de "quem mexe na gaveta" (cargos customizados, futuro) não conseguiria. É uma linha no mapa e deixa a rota autoexplicativa no `docs/api`. |
| T2 | **Uma sessão aberta por unidade** (índice único parcial). | Barbearia pequena tem uma gaveta; vários caixas por unidade entram com `register_id` sem quebrar o contrato. |
| T3 | Valor esperado por forma = soma dos pagamentos da sessão (`sales.public.payments_by_cash_session`, estornos negativos); para dinheiro, + fundo + reforços − sangrias. O fechamento grava o **snapshot** esperado/contado/diferença por forma. | Calcula-se do registro, sem duplicar o dinheiro em outra tabela; o snapshot congela a conferência. |
| T4 | **Fechamento cego** como padrão: quem não tem `finance:read` não vê o esperado nem a diferença (Q-S09-2). | Anti-fraude padrão de PDV; a recepção conta sem saber quanto "deveria" dar. |
| T5 | Despesa paga "com dinheiro do caixa" gera a **sangria** vinculada automaticamente. | Sem isso, o caixa fecharia com falta toda vez que se paga o entregador da gaveta. |
| T6 | Recorrência gera as ocorrências pelo **worker**, até 45 dias à frente; editar o modelo atualiza as futuras não editadas à mão. Compra parcelada gera N despesas de uma vez (`installment_group_id`). | O "contas a pagar" do próximo mês aparece sem ninguém lançar. |
| T7 | Resultado **calculado na hora** (sem tabela de fechamento de mês): comanda estornada sai do mês dela. | Simples e sempre consistente; congelar mês (competência fechada) entra se o contador pedir. |

## Business Rules

### Caixa

- [ ] Abrir: `unit_id` no escopo, `opening_float_cents` ≥ 0; outra sessão aberta na unidade →
      `409` "Já existe um caixa aberto nesta unidade". A resposta sugere o fundo deixado no último
      fechamento (`suggested_float_cents`); fundo diferente só gera aviso.
- [ ] `business_date` da sessão = data local da abertura. Sessão pode atravessar a meia-noite (o
      fechamento não muda a data).
- [ ] Resolvedor (S06 T6): devolve a sessão aberta da unidade. Sem sessão: com
      `require_open_cash = true` → `409` "Abra o caixa da unidade antes de receber"; com `false` →
      sem sessão (pagamento fica "fora do caixa"). Ver Q-S09-1.
- [ ] Sangria (`withdrawal`) e reforço (`deposit`): valor > 0, motivo (`bank_deposit`,
      `commission_payout`, `expense`, `change_fund`, `other`) e descrição (até 200). Sangria maior
      que o dinheiro esperado na gaveta → `409` "Sangria maior que o dinheiro em caixa".
      Movimento não se edita; erro corrige-se com o movimento inverso.
- [ ] Fechar: contagem `counted_cents` para **cada** forma com valor esperado ≠ 0 e sempre para
      dinheiro (`422` "Conte todas as formas de pagamento"); `cash_left_cents` (fundo que fica) ≤
      dinheiro contado. Diferença ≠ 0 exige `closing_note` (`422` "Explique a diferença").
- [ ] A resposta do fechamento traz `open_tickets_count` da unidade (aviso, não bloqueia).
- [ ] Fechamento cego (T4): sem `finance:read`, `expected_cents` e `difference_cents` vêm `null`
      na sessão aberta e na fechada; com `finance:read`, vêm sempre.
- [ ] Reabrir: `finance:write`, só a sessão mais recente da unidade e sem outra aberta; apaga o
      snapshot, guarda `reopened_at/by`. Pagamentos e movimentos continuam ligados a ela.
- [ ] Histórico de sessões (lista com esperado, contado e diferença) exige `finance:read`.

### Despesas e contas a pagar

- [ ] Categorias: nome único (2–60), ativa; dez nascem com a barbearia (Aluguel, Energia, Água,
      Internet e telefone, Produtos e insumos, Manutenção, Marketing, Impostos e taxas, Pró-labore,
      Outros). Apagar só sem despesa; senão inativar.
- [ ] Despesa: `category_id`, `description` (2–120), `supplier` (opcional, até 120), `amount_cents`
      (> 0), `due_date`, `competence_date` (padrão = `due_date`), `unit_id` (nulo = despesa geral
      da barbearia; só quem vê todas as unidades cria geral), `notes` (até 500).
- [ ] Status `pending` → `paid` → (desfazer) `pending`; `pending` → `cancelled`. `overdue` é
      derivado (`pending` e `due_date` < hoje no fuso da barbearia) e filtrável.
- [ ] Pagar: `paid_at` (data), `paid_amount_cents` (padrão = valor; pode diferir por juros ou
      desconto), `payment_method_id` opcional, `from_cash: bool`. `from_cash` exige `cash:operate`
      e caixa aberto na unidade da despesa (despesa geral: informar `cash_unit_id`) e cria a sangria
      vinculada (T5); falta de caixa → `409`.
- [ ] Desfazer pagamento: remove a sangria vinculada se o caixa ainda estiver aberto; caixa já
      fechado → `409` "O caixa desse pagamento já foi fechado".
- [ ] Parcelada: `installments` 2–48 no `POST` cria N despesas mensais a partir de `due_date`,
      valor dividido (resto na primeira), descrição "… (2/10)".
- [ ] Recorrente: modelo com frequência `monthly` | `weekly` | `yearly`, dia (mês: 1–31, com
      ajuste para o último dia do mês; semana: 0–6), início, fim opcional (T6). Desativar o modelo
      cancela as ocorrências futuras ainda pendentes. Ocorrência editada à mão fica `detached`.
- [ ] Apagar despesa só `pending` sem vínculo; paga → `409`.

### Resultado do mês

- [ ] `GET /finance/result?month=AAAA-MM&unit_id=`: receita (líquida de descontos, por tipo:
      serviços, produtos, mensalidades de clube, venda de pacotes), descontos concedidos, gorjetas
      (informativo, fora da receita e do resultado: entram e saem integrais para o barbeiro, PD-38),
      taxas de pagamento (inclusive a parte rateada sobre gorjetas, que a barbearia absorve),
      comissões (sem gorjeta, de
      `commissions.public.commission_cost`), despesas por categoria (por `competence_date`, Q-S09-3,
      sem canceladas), resultado = receita − taxas − comissões − despesas, margem %.
- [ ] Também por forma de pagamento e por dia (gráfico).
- [ ] Com `unit_id`, despesas gerais aparecem numa linha própria ("Despesas gerais da barbearia,
      não rateadas") e o resultado da unidade é mostrado antes e depois delas.
- [ ] Gerente com escopo `unit` vê só as próprias unidades e as despesas gerais como linha
      informativa.

## Data Contract

```text
# Módulo finance, tags "cash" e "expenses"
GET  /cash-sessions/current?unit_id=                → 200 CashSessionOut | 404
GET  /cash-sessions?unit_id=&date_from=&date_to=&limit=&offset= → 200 {items, total}  (finance:read)
POST /cash-sessions        {unit_id, opening_float_cents, note?} → 201 CashSessionOut | 403 | 409
GET  /cash-sessions/{id}                            → 200 CashSessionOut | 404
POST /cash-sessions/{id}/movements {kind: withdrawal|deposit, amount_cents, reason, description}
                                                    → 201 CashSessionOut | 409 | 422
POST /cash-sessions/{id}/close {counts: [{payment_method_id, counted_cents}], cash_left_cents,
                                closing_note?}      → 200 CashSessionOut | 409 | 422
POST /cash-sessions/{id}/reopen                     → 200 CashSessionOut | 403 | 409

CashSessionOut {id, unit_id, status: open|closed, business_date, opened_at, opened_by,
     opening_float_cents, suggested_float_cents, closed_at, closed_by, closing_note,
     cash_left_cents, reopened_at, open_tickets_count,
     methods: [{payment_method_id, name, kind, payments_count, expected_cents|null,
                counted_cents|null, difference_cents|null}],
     movements: [{id, kind, amount_cents, reason, description, expense_id, created_at,
                  created_by}],
     total_difference_cents|null}

GET    /expense-categories                          → 200 CategoryOut[]
POST   /expense-categories {name}                   → 201 | 409 | 422
PATCH  /expense-categories/{id} {name?, active?}    → 200 | 404 | 409
DELETE /expense-categories/{id}                     → 204 | 404 | 409

GET    /expenses?status=pending|overdue|paid|cancelled&unit_id=&category_id=&due_from=&due_to=
               &q=&limit=&offset=                   → 200 {items: ExpenseOut[], total, sum_cents}
POST   /expenses  ExpenseIn                         → 201 ExpenseOut[] (1 ou N parcelas) | 400 | 403
GET    /expenses/{id}                               → 200 ExpenseOut | 404
PATCH  /expenses/{id}  ExpenseUpdate                → 200 ExpenseOut | 404 | 409
DELETE /expenses/{id}                               → 204 | 404 | 409
POST   /expenses/{id}/pay   {paid_at, paid_amount_cents?, payment_method_id?, from_cash?,
                             cash_unit_id?}         → 200 ExpenseOut | 403 | 409
POST   /expenses/{id}/unpay                         → 200 ExpenseOut | 409
POST   /expenses/{id}/cancel                        → 200 ExpenseOut | 409

GET    /expense-recurrences                         → 200 RecurrenceOut[]
POST   /expense-recurrences  RecurrenceIn           → 201 RecurrenceOut | 400 | 422
PATCH  /expense-recurrences/{id}  RecurrenceUpdate  → 200 | 404
DELETE /expense-recurrences/{id}                    → 204 (desativa e cancela futuras pendentes)

ExpenseIn  {category_id, description, supplier?, amount_cents, due_date, competence_date?,
            unit_id?, notes?, installments? = 1}
ExpenseOut {id, category_id, category_name, description, supplier, amount_cents, due_date,
            competence_date, unit_id, status, overdue, paid_at, paid_amount_cents,
            payment_method_id, cash_movement_id, recurrence_id, detached,
            installment_group_id, installment_number, installment_count, notes,
            created_at, created_by}
RecurrenceIn {category_id, description, supplier?, amount_cents, unit_id?,
              frequency: monthly|weekly|yearly, day, start_date, end_date?}

GET /finance/result?month=&unit_id=                 → 200 MonthResultOut       (finance:read)
GET /finance/settings  · PUT /finance/settings {require_open_cash, blind_cash_count}
                                                    → 200 (finance:write + todas as unidades)

MonthResultOut {month, unit_id, revenue: {services, products, membership_charges,
     package_sales, total}, discounts_cents, tips_cents, fees_cents,
     commissions: {services, products, subscriber, total}, expenses: {by_category:
     [{category_id, name, amount_cents}], unit_total, shared_total},
     result_cents, result_after_shared_cents, margin_percent,
     by_payment_method: [{payment_method_id, name, amount_cents, fee_cents}],
     daily: [{date, revenue_cents, expenses_cents}]}
```

`finance/public.py`: `install_cash_resolver()` — chamado uma vez no `main.py`, registra o resolvedor
em `sales.public.set_cash_session_resolver`. Eventos: nenhum consumido, nenhum publicado.

### Banco de dados

Migration de tenant `tNNNN_finance`:

```text
finance_settings     id smallint pk check (id = 1) · require_open_cash bool default true ·
                     blind_cash_count bool default true · updated_at · updated_by null

cash_sessions        id uuid pk · unit_id → units RESTRICT · status cash_session_status
                     ('open','closed') · business_date date · opening_float_cents integer >= 0 ·
                     opened_at · opened_by → users · note varchar(200) null ·
                     closed_at null · closed_by null · closing_note varchar(500) null ·
                     cash_left_cents integer null · reopened_at null · reopened_by null
                     UNIQUE INDEX uq_cash_session_open ON (unit_id) WHERE status = 'open'
                     INDEX (unit_id, business_date)

cash_session_counts  id uuid pk · cash_session_id → cash_sessions CASCADE ·
                     payment_method_id → payment_methods RESTRICT · method_name varchar(60) ·
                     method_kind payment_method_kind · expected_cents · counted_cents ·
                     difference_cents   UNIQUE (cash_session_id, payment_method_id)

cash_movements       id uuid pk · cash_session_id → cash_sessions RESTRICT ·
                     kind cash_movement_kind ('withdrawal','deposit') · amount_cents > 0 ·
                     reason cash_movement_reason · description varchar(200) ·
                     expense_id → expenses SET NULL null · created_at · created_by → users

expense_categories   id uuid pk · name varchar(60) · active · UNIQUE INDEX ON lower(name)

expense_recurrences  id uuid pk · category_id RESTRICT · unit_id → units RESTRICT null ·
                     description varchar(120) · supplier varchar(120) null · amount_cents > 0 ·
                     frequency expense_frequency · day smallint · start_date · end_date null ·
                     generated_until date null · active · created_at · updated_at

expenses             id uuid pk · category_id RESTRICT · unit_id → units RESTRICT null ·
                     description varchar(120) · supplier varchar(120) null · amount_cents > 0 ·
                     due_date date · competence_date date · status expense_status
                     ('pending','paid','cancelled') · paid_at date null · paid_amount_cents null ·
                     payment_method_id → payment_methods RESTRICT null ·
                     recurrence_id → expense_recurrences SET NULL null · detached bool ·
                     installment_group_id uuid null · installment_number smallint null ·
                     installment_count smallint null · notes varchar(500) null ·
                     created_at · updated_at · created_by
                     INDEX (status, due_date) · INDEX (competence_date) · INDEX (unit_id)
                     UNIQUE (recurrence_id, due_date)   (o worker não duplica ocorrência)
```

`ticket_payments.cash_session_id` (S06) aponta para `cash_sessions.id` sem FK (T6 do S06); esta
migration pode acrescentar a FK `ON DELETE RESTRICT` porque roda depois da de `sales`.

## Permissões

**Uma permissão nova: `cash:operate`** (T1). Entra no enum, no mapa de cada cargo e no
`docs/PERMISSIONS_MAP.md`.

| Ação | Permissão | owner | manager | receptionist | barber |
|---|---|---|---|---|---|
| ver caixa atual, abrir, sangria, reforço, fechar | `cash:operate` | all | unit | unit | — |
| ver esperado e diferença, histórico de caixas | `finance:read` | all | unit | — | — |
| reabrir caixa | `finance:write` | all | unit | — | — |
| ver despesas e resultado | `finance:read` | all | unit | — | — |
| criar, editar, pagar despesas; categorias; recorrências | `finance:write` | all | unit | — | — |
| configurações do financeiro, despesa geral | `finance:write` + todas as unidades | sim | só se vê todas | — | — |

## Acceptance Criteria

- [ ] `cash:operate` no `permissions.py`, `PERMISSIONS_MAP.md` regenerado, `test_permissions_doc`
      verde; frontend avisado (permissão nova em `/auth/me`).
- [ ] Módulo `finance` com layout completo; importa `identity`, `catalog`, `sales`, `commissions`
      só pelo `public.py`; resolvedor instalado no `main.py`.
- [ ] Testes de caixa: abrir duas vezes, comanda fechando sem caixa (com e sem a exigência), conta
      com fundo + dinheiro + troco + reforço − sangria − estorno, sangria acima do saldo, fechamento
      sem contar uma forma, diferença sem nota, cego para recepção e aberto para gerente, reabrir.
- [ ] Testes de despesa: parcelada (resto na primeira), recorrência mensal no dia 31, edição do
      modelo sem tocar a ocorrência `detached`, pagar do caixa gera sangria, desfazer com caixa
      fechado.
- [ ] Teste do resultado com comandas, estorno, gorjeta, taxa, comissão e despesas geral e de
      unidade.
- [ ] Cruzamento entre duas barbearias; escopo de gerente de uma unidade.
- [ ] Snapshots, `make docs-api`, `make check` verde, memória atualizada (DEC para `cash:operate`).

## Dependencies

- **S06** — `set_cash_session_resolver`, `payments_by_cash_session`, `revenue_summary`, tabela
  `ticket_payments`.
- **S08** — `commissions.public.commission_cost`.
- **S05** — `list_payment_methods`, `get_payment_method`.
- **S00** — worker com tarefa diária (recorrências).
- **S01** — fuso da unidade (já existe `units.timezone`) e fuso "da barbearia" para despesa geral
  (assume-se o da primeira unidade até S01 definir um fuso do tenant).
- Oferece: leitura para **S14** (relatórios usam `revenue_summary` direto do `sales`; o resultado
  pode ser exposto em `finance.public.month_result` se S14 quiser).

## Notes

- **Mensalidade de clube** é paga por comanda (S07), então já entra no caixa e na receita sem
  evento `membership.charge_paid` para o `finance`.
- **Fluxo de caixa projetado** (contas a pagar × recebíveis por prazo da maquininha) e conciliação
  bancária ficam fora.
- **Anexo de boleto/nota** na despesa precisa de armazenamento de arquivo: fora desta spec.

### Perguntas em aberto

✅ **Q-S09-1 — Exigir caixa aberto para fechar comanda?**
1. Sempre (configurável, padrão ligado): nenhuma comanda fecha sem caixa aberto na unidade.
2. Só quando há pagamento em dinheiro; Pix e cartão fecham sem caixa.
3. Nunca: o caixa é só conferência.

Recomendação: **1**. Trinks faz assim; garante que todo recebimento do dia esteja numa conferência.
O custo (recepção esquecer de abrir) é resolvido pelo aviso "Abra o caixa" com botão na própria
comanda.

> Resolvido em 2026-11-06: opção 1 — fechar comanda exige caixa aberto, configurável
> (`require_open_cash`, ligado por padrão) (ROADMAP §7).

✅ **Q-S09-2 — Fechamento cego para a recepção?**
1. Sim: a recepção conta sem ver o esperado; só gerente/dono vê a diferença.
2. Não: todos veem esperado e diferença.

Recomendação: **1**, configurável (`blind_cash_count`). É a prática anti-fraude de PDV; a dona que
confia na recepção desliga.

> Resolvido em 2026-11-06: opção 1 — fechamento cego para a recepção, configurável
> (`blind_cash_count`, ligado por padrão) (ROADMAP §7).

✅ **Q-S09-3 — Despesa entra no resultado pela competência ou pela data em que foi paga?**
1. Competência (o aluguel de novembro pesa em novembro, pago quando for).
2. Caixa (entra no mês em que foi pago).

Recomendação: **1**, com o "contas a pagar" mostrando o que vence. A receita também é por data da
comanda, e o dono compara meses de forma justa.

> Resolvido em 2026-11-06: opção 1 — despesa entra no resultado por competência
> (`competence_date`) (ROADMAP §7).
