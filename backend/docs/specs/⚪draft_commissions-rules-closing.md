# Comissões: regras, lançamentos e fechamento

**Priority:** high
**Status:** draft
**Espelho no frontend:** `frontend/docs/specs/⚪draft_frontend-commissions.md`

## Overview

Os barbeiros são só comissionados (PD-12): o fechamento de comissão é o salário deles e a conversa
mais sensível da barbearia. Esta spec cria o módulo `commissions`: a barbearia **configura as
regras** (PD-13), cada comanda fechada **gera lançamentos** por barbeiro (e o estorno gera o
lançamento inverso), o gerente **fecha um período** (semana, quinzena, mês) e marca como pago, e o
barbeiro vê **as próprias comissões** no celular (PD-26).

Lançamento é **livro-razão**: nunca é editado nem apagado; correção é lançamento novo. Mudar a regra
vale para as próximas comandas, não reescreve as já lançadas (snapshot).

## Decisões de produto já tomadas

| Parâmetro | Valor |
|---|---|
| PD-12 | Barbeiro só comissionado: sem aluguel de cadeira, sem salão-parceiro. |
| PD-13 | Quatro regras, todas ligáveis e ajustáveis: (1) % padrão do barbeiro com exceção por serviço; (2) descontar a taxa do cartão antes de calcular; (3) comissão sobre produto; (4) comissão em atendimento de assinante do clube. |
| PD-14 | Fora: vales e adiantamentos (o fechamento não desconta vale). |
| PD-26 | O barbeiro vê "minhas comissões" no painel (PWA). |
| PD-35 | Comissão de atendimento de assinante (regra 4): **a barbearia escolhe o modo** — rateio da mensalidade, valor fixo por atendimento, % do preço de tabela ou sem comissão. **Sem padrão imposto**: o modo é escolhido ao ligar a regra. |
| PD-38 | **Gorjeta** por barbeiro, fora da receita, repassada **integral** no fechamento; a barbearia absorve a taxa do cartão sobre ela (a regra 2 nunca toca a gorjeta). |
| S06 | A comanda entrega por item: barbeiro, líquido, parte da taxa, benefício e valor pré-pago consumido. |

### Decisões técnicas desta spec

| # | Decisão | Por quê |
|---|---|---|
| T1 | Prioridade do percentual de um serviço: **barbeiro × serviço** > **serviço (todos os barbeiros)** > **% padrão do barbeiro** (`barbers.default_commission`). Com a regra 1 desligada, só o padrão do barbeiro vale. | É a ordem do Trinks e do AppBarber: a exceção mais específica vence. |
| T2 | Base de cálculo = líquido do item (já com desconto manual, desconto da comanda e desconto de clube) − parte da taxa do cartão (regra 2). Configurável: "desconto reduz a base" (padrão ligado); desligado, a base é o preço praticado antes dos descontos. Base nunca negativa. | Trinks oferece as duas; ligado é o que protege a margem e é o comum. |
| T3 | Produto: com a regra 3 ligada, `% do produto` (snapshot do item) > `% padrão de produto` das configurações. Produto sem barbeiro na comanda não gera comissão. | "Vendido por" é opcional na comanda (S06). |
| T4 | Uso de **pacote**: base = valor pré-pago consumido (`benefit_value_cents`: preço do pacote rateado por uso, vindo do S07), percentual como serviço comum, sem taxa. A venda do pacote em si não gera comissão. | O barbeiro recebe quando trabalha; o dinheiro já entrou na venda. |
| T5 | Atendimento de **assinante** (regra 4) tem três modos que pagam — `list_price_percent`, `fixed_per_service`, `revenue_share` — e o quarto modo da PD-35, **"sem comissão", é a regra desligada**. A regra nasce **desligada e sem modo** (`subscriber_mode = null`); ligar exige escolher o modo na mesma gravação (`422` sem ele). Não há modo padrão (PD-35). | É a regra mais discutida do mercado; quem decide é o dono, explicitamente. Usar o liga/desliga para "sem comissão" mantém o padrão das outras regras (PD-13) e evita dois jeitos de dizer a mesma coisa. |
| T6 | `revenue_share` (rateio) roda no **worker** no dia seguinte ao fim de cada ciclo **pago**: o valor pago (menos a taxa, se regra 2) é dividido entre os usos do ciclo pelo preço de tabela, e cada parte recebe o percentual do serviço (T1). Ciclo pago depois do fim entra na próxima rodada; ciclo sem uso não gera comissão. | Igual ao "pote do assinante" do BestBarbers: nunca paga mais comissão do que a mensalidade rendeu. |
| T7 | Gorjeta vira lançamento `tip` de **100%** para o barbeiro, sem desconto da taxa do cartão mesmo com a regra 2 ligada (PD-38: a barbearia absorve). Fica separada nos totais. | Gorjeta não é comissão, mas é paga no mesmo acerto; evita discussão por centavos. |
| T8 | Estorno de comanda gera, para cada lançamento dela ainda não estornado, um lançamento inverso com a data do estorno. Se o original já estava num fechamento pago, o inverso cai no próximo fechamento (desconta do próximo acerto). | Livro-razão: o acerto já pago não muda. |
| T9 | Fechamento por barbeiro: "fechar até a data X" pega **todos** os lançamentos em aberto com `business_date ≤ X` (inclusive atrasados), nunca deixa buraco. Pode-se fechar vários barbeiros de uma vez. | Evita lançamento esquecido entre dois períodos. |

## Business Rules

### Configurações e exceções

- [ ] Configuração única por barbearia (linha criada com os padrões na primeira leitura):
      `service_overrides_enabled` (R1, true), `deduct_card_fee` (R2, false),
      `discount_reduces_base` (true), `product_commission_enabled` (R3, true),
      `product_default_percent` (10,00), `subscriber_commission_enabled` (R4, **false**),
      `subscriber_mode` (**null**; obrigatório para ligar a R4, PD-35), `subscriber_fixed_cents`
      (valor do modo fixo; obrigatório quando o modo é `fixed_per_service`),
      `payout_frequency` (`weekly` | `biweekly` | `monthly`, só sugere o período na tela).
- [ ] Exceções (`commission_service_rates`): por serviço, opcionalmente por barbeiro, com
      `percent` (0–100) e/ou `subscriber_fixed_cents`; pelo menos um dos dois. `PUT` substitui a
      lista inteira; par serviço/barbeiro repetido → `422`; serviço ou barbeiro inexistente → `400`.
- [ ] Ligar a R4 sem `subscriber_mode` → `422` "Escolha como pagar o atendimento de assinante";
      modo `fixed_per_service` sem `subscriber_fixed_cents` → `422`. Desligar a R4 mantém o último
      modo gravado (para religar), mas ele não vale enquanto a regra estiver desligada.
- [ ] Mudar configuração ou exceção não altera lançamento existente.
- [ ] Ler e escrever configurações/exceções exige `finance:write` + todas as unidades (são da
      barbearia inteira); ler também com `finance:read`.

### Lançamentos a partir da comanda (`ticket.closed`)

- [ ] Assinante idempotente: chave `(ticket_item_id, source)`; o mesmo evento duas vezes não
      duplica.
- [ ] Item `service` sem benefício ou com `club_discount`: base T2, percentual T1, regra
      `service_default` | `service_override` | `barber_service_override`.
- [ ] Item `service` com `club_included`: regra 4 desligada ("sem comissão") → nada; `list_price_percent` → base
      = preço de tabela × qtd (− parte da taxa, que é zero), percentual T1; `fixed_per_service` →
      valor da exceção do serviço (barbeiro × serviço > serviço) ou `subscriber_fixed_cents`;
      `revenue_share` → nada agora (T6).
- [ ] Item `service` com `package`: T4.
- [ ] Item `product`: T3. Itens `package_sale` e `membership_charge`: nada.
- [ ] Gorjetas: T7 — `amount_cents` integral da gorjeta, regra `tip`, sem `fee_share_cents`.
- [ ] Cada lançamento guarda base, percentual ou valor fixo, regra aplicada, barbeiro, unidade,
      comanda, item e `business_date` da comanda. Valor arredondado meio-para-cima por lançamento.
- [ ] Barbeiro inativo continua recebendo lançamento (atendeu antes de sair).

### Rateio do assinante (worker, T6)

- [ ] Diariamente, para ciclos de clube encerrados e pagos ainda não rateados
      (`memberships.public.list_cycles_for_commission`), gera um lançamento `subscriber_share` por
      uso, com `membership_cycle_id`. Maior resto para os centavos. Ciclo marcado como rateado
      (`commission_share_runs`) na mesma transação.
- [ ] Ciclo cujo pagamento foi estornado depois do rateio → lançamentos inversos (T8).

### Estorno (`ticket.voided`)

- [ ] Para cada lançamento da comanda (e de rateio ligado a um item de mensalidade dela), cria o
      inverso com `reversed_entry_id` e `business_date` do estorno. Idempotente por
      `reversed_entry_id` único. Comanda aberta descartada não tem lançamento: nada a fazer.

### Ajuste manual (Q-S08-2)

- [ ] `POST /commissions/entries` cria lançamento `source = adjustment`, `rule = manual`, positivo
      ou negativo (≠ 0), para um barbeiro, com `business_date` e motivo obrigatório (3–200, vai em
      `description`). Exige `finance:write` no escopo da unidade. Não é vale nem adiantamento
      (PD-14): não tem saldo devedor nem parcelas; entra no próximo fechamento como qualquer
      lançamento em aberto. Ajuste não é editado nem apagado — corrige-se com outro ajuste.

### Fechamento e pagamento

- [ ] `POST /commissions/payouts` com `period_end` (e `barber_ids` opcional; sem lista = todos os
      barbeiros do escopo com saldo): um fechamento por barbeiro com os lançamentos em aberto até a
      data (T9). Barbeiro sem lançamento é ignorado; total pode ser negativo (estorno maior que o
      período) e aparece em destaque.
- [ ] Fechamento `closed` pode ser desfeito (`DELETE`, lançamentos voltam a ficar em aberto) ou
      pago (`POST .../pay` com `paid_at` e `notes` até 300). Pago é definitivo: desfazer → `409`.
- [ ] Pagar comissão não mexe no caixa: se saiu da gaveta, a recepção registra a sangria (S09).
- [ ] Exige `finance:write` no escopo (gerente fecha os barbeiros das próprias unidades).

### Leitura e "minhas comissões"

- [ ] `commission:read`: `all` tudo; `unit` lançamentos das comandas das unidades do usuário; `own`
      só os do próprio barbeiro (`barber_id` do token; filtro de outro barbeiro → `403`).
- [ ] Resumo por barbeiro no período: em aberto, em fechamento, pago; separado em serviços,
      produtos, assinantes, gorjetas.
- [ ] O barbeiro vê os próprios lançamentos com cliente, serviço, valor da base e percentual — a
      transparência é o que evita a discussão no acerto.

## Data Contract

```text
# Módulo commissions, tag "commissions"
GET  /commission-settings                         → 200 CommissionSettingsOut
PUT  /commission-settings  CommissionSettingsIn   → 200 CommissionSettingsOut | 403 | 422
GET  /commission-rates                            → 200 CommissionRateOut[]
PUT  /commission-rates     CommissionRateIn[]     → 200 CommissionRateOut[] | 400 | 403 | 422

GET  /commissions/entries?barber_id=&unit_id=&date_from=&date_to=&status=open|in_payout|paid
                         &source=&limit=50&offset=0 → 200 {items: EntryOut[], total, sum_cents}
GET  /commissions/summary?date_from=&date_to=&unit_id=&barber_id= → 200 BarberSummary[]
GET  /commissions/payouts?barber_id=&status=closed|paid&limit=&offset= → 200 {items, total}
POST /commissions/entries  AdjustmentIn            → 201 EntryOut | 400 | 403 | 422
POST /commissions/payouts  {period_end, period_start?, barber_ids?, unit_id?}
                                                  → 201 PayoutOut[] | 403 | 422
GET  /commissions/payouts/{id}                    → 200 PayoutDetailOut | 404
POST /commissions/payouts/{id}/pay {paid_at?, notes?} → 200 PayoutOut | 404 | 409
DELETE /commissions/payouts/{id}                  → 204 | 404 | 409

CommissionSettingsIn/Out {service_overrides_enabled, deduct_card_fee, discount_reduces_base,
     product_commission_enabled, product_default_percent, subscriber_commission_enabled,
     subscriber_mode: list_price_percent|fixed_per_service|revenue_share|null,
     subscriber_fixed_cents, payout_frequency}  (+ updated_at, updated_by na saída)
     (subscriber_commission_enabled = true exige subscriber_mode; sem comissão = false, PD-35)
AdjustmentIn {barber_id, unit_id, business_date, amount_cents (≠ 0), reason}
CommissionRateIn  {service_id, barber_id?, percent?, subscriber_fixed_cents?}
CommissionRateOut {id, service_id, service_name, barber_id, barber_name, percent,
                   subscriber_fixed_cents}
EntryOut   {id, barber_id, barber_name, unit_id, source, rule, ticket_id, ticket_number,
            ticket_item_id, membership_cycle_id, client_name, description, business_date,
            base_cents, percent, fixed_cents, amount_cents, reversed_entry_id, payout_id,
            payout_status, created_at}
BarberSummary {barber_id, barber_name, open_cents, in_payout_cents, paid_cents,
               services_cents, products_cents, subscriber_cents, tips_cents, reversals_cents}
PayoutOut  {id, barber_id, barber_name, unit_id, period_start, period_end, total_cents,
            entries_count, status, closed_at, closed_by, paid_at, paid_by, notes}
PayoutDetailOut = PayoutOut + {entries: EntryOut[]}

Erros: 400 "Serviço não encontrado" · "Barbeiro não encontrado"
       403 "Regras de comissão valem para todas as unidades" · "Você só vê as suas comissões"
       409 "Fechamento já pago" · 422 "Informe o percentual ou o valor fixo" ·
       422 "Escolha como pagar o atendimento de assinante"
```

Eventos consumidos: `ticket.closed`, `ticket.voided`. Nenhum publicado nesta spec (S14 lê pelo
`public.py`).

`commissions/public.py`: `commission_cost(session, unit_ids, date_from, date_to)` →
`{services, products, subscriber, tips, total}` por `business_date` (para o resultado do mês, S09).

### Banco de dados

Migration de tenant `tNNNN_commissions`:

```text
commission_settings  id smallint pk check (id = 1) · as colunas das configurações ·
                     subscriber_commission_enabled bool default false ·
                     subscriber_mode commission_subscriber_mode null ·
                     CHECK (NOT subscriber_commission_enabled OR subscriber_mode IS NOT NULL) ·
                     payout_frequency
                     commission_payout_frequency · updated_at · updated_by → users null

commission_service_rates id uuid pk · service_id → services RESTRICT ·
                     barber_id → barbers RESTRICT null · percent numeric(5,2) null check (0..100) ·
                     subscriber_fixed_cents integer null check (>= 0)
                     UNIQUE NULLS NOT DISTINCT (service_id, barber_id)
                     CHECK (percent IS NOT NULL OR subscriber_fixed_cents IS NOT NULL)

commission_payouts   id uuid pk · barber_id → barbers RESTRICT · unit_id → units RESTRICT ·
                     period_start date · period_end date · total_cents integer ·
                     entries_count integer · status commission_payout_status ('closed','paid') ·
                     closed_at · closed_by → users · paid_at null · paid_by null ·
                     notes varchar(300) null
                     INDEX (barber_id, period_end)

commission_entries   id uuid pk · barber_id → barbers RESTRICT · unit_id → units RESTRICT ·
                     source commission_source ('ticket_item','tip','subscriber_share','reversal',
                     'adjustment') · rule commission_rule ('service_default','service_override',
                     'barber_service_override','product','subscriber_list_price',
                     'subscriber_fixed','subscriber_share','package_usage','tip','manual') ·
                     ticket_id → tickets RESTRICT null · ticket_item_id uuid null ·
                     membership_cycle_id uuid null · business_date date ·
                     base_cents integer · percent numeric(5,2) null · fixed_cents integer null ·
                     amount_cents integer (negativo no inverso) · description varchar(200) ·
                     reversed_entry_id → commission_entries.id null UNIQUE ·
                     payout_id → commission_payouts.id SET NULL null · created_at · created_by null
                     UNIQUE INDEX uq_entry_item_source ON (ticket_item_id, source)
                            WHERE ticket_item_id IS NOT NULL AND source <> 'reversal'
                     INDEX (barber_id, business_date) · INDEX (payout_id) · INDEX (ticket_id)

commission_share_runs membership_cycle_id uuid pk · processed_at
```

## Permissões

Nenhuma permissão nova.

| Ação | Permissão | owner | manager | receptionist | barber |
|---|---|---|---|---|---|
| ver lançamentos, resumo, fechamentos | `commission:read` | all | unit | — | own |
| ver configurações e exceções | `finance:read` | all | unit | — | — |
| alterar configurações e exceções | `finance:write` + todas as unidades | sim | só se vê todas | — | — |
| fechar, desfazer, pagar; ajuste manual | `finance:write` | all | unit | — | — |

## Acceptance Criteria

- [ ] Módulo `commissions` com layout completo; importa `identity`, `catalog`, `sales` (tipos do
      evento) e `memberships` (rateio) só pelo `public.py`.
- [ ] Teste por regra: prioridade T1 nas três camadas e com R1 desligada; base com e sem desconto,
      com e sem taxa; produto com % próprio, padrão e R3 desligada; os três modos da R4 e R4
      desligada; ligar R4 sem modo → `422`; pacote; gorjeta integral com R2 ligada; combo (serviço
      com preço rateado).
- [ ] Teste do rateio: dois barbeiros, preços de tabela diferentes, centavos fecham com a
      mensalidade × percentual; ciclo sem uso; ciclo pago atrasado; estorno da mensalidade.
- [ ] Idempotência: `ticket.closed` e `ticket.voided` entregues duas vezes.
- [ ] Fechamento: pega lançamento atrasado, ignora o já fechado, desfaz, paga, recusa desfazer o
      pago; estorno após pagamento cai no próximo.
- [ ] Escopos: barbeiro só vê os próprios (`403` ao pedir outro), gerente só das suas unidades;
      cruzamento entre duas barbearias.
- [ ] Snapshots, `make docs-api`, `make check` verde, memória atualizada.

## Dependencies

- **S06** — eventos `ticket.closed`/`ticket.voided` com o payload descrito lá, incluindo
  `benefit_value_cents` por item.
- **S07** — `memberships.public.list_cycles_for_commission(session, ended_before, exclude_ids)` →
  `[{cycle_id, client_membership_id, charge_ticket_item_id, paid_cents, fee_cents,
  usages: [{ticket_item_id, barber_id, unit_id, service_id, list_price_cents, business_date}]}]`.
  Só necessário para o modo `revenue_share`; as regras 1–3 não dependem do S07.
- **identity** — `get_barber` (percentual padrão).
- **S00** — assinatura de eventos e tarefa diária no worker.
- Oferece: `commission_cost` para **S09**; leitura para **S14** e **S18** ("minhas comissões").

## Notes

- **Ordem de implementação.** Regras 1–3, gorjeta, estorno e fechamento saem com esta spec; o modo
  `revenue_share` só funciona depois do S07 (antes dele, não há `club_included`).
- **Recalcular** lançamentos em aberto depois de mudar a regra fica fora: o dono faz um ajuste manual
  (Q-S08-2) ou estorna a comanda.
- **Comissão de recepcionista** ou meta/bonificação por faturamento: fora (PD-12 fala de barbeiros).

### Perguntas em aberto

✅ **Q-S08-1 — Como paga o atendimento de assinante do clube (regra 4)?**
1. **Rateio da mensalidade** (`revenue_share`): no fim do ciclo pago, a mensalidade é dividida
   entre os barbeiros pelos atendimentos feitos, e cada parte recebe o % do serviço. Nunca custa
   mais que a mensalidade; o barbeiro só vê o valor depois do ciclo.
2. **Valor fixo por atendimento** (`fixed_per_service`): ex. R$ 12 por corte de assinante. Simples
   e imediato; no clube ilimitado, cliente que vem toda semana pode custar mais que a mensalidade.
3. **Como cliente normal** (`list_price_percent`): % sobre o preço de tabela; a barbearia absorve
   tudo.
4. Não paga comissão em atendimento de assinante.

Recomendação: oferecer os três modos e vir **1 (rateio)** como padrão — é o que protege a margem do
clube, que é o produto de recorrência da barbearia. Se o dono achar que o barbeiro não aceita
esperar o fim do ciclo, **2** como padrão.

> Resolvido em 2026-11-06: os quatro modos ficam disponíveis e **não há padrão** — a barbearia
> escolhe o modo ao ligar a regra 4; "sem comissão" é a regra desligada, que é como ela nasce
> (PD-35).

✅ **Q-S08-2 — Ajuste manual em lançamento (bônus ou desconto avulso)?**
1. Não: corrige-se só estornando a comanda.
2. Sim, lançamento `adjustment` positivo ou negativo, com motivo obrigatório, só por quem tem
   `finance:write` — explicitamente **não** é vale nem adiantamento (PD-14).

Recomendação: **2**. Sem ele, um erro de regra só se resolve fora do sistema, e o fechamento deixa
de bater com o que foi pago. (O enum `adjustment`/`manual` já está reservado no banco; a rota
`POST /commissions/entries` entra se a resposta for 2.)

> Resolvido em 2026-11-06: opção 2 — ajuste manual com motivo, só `finance:write`; não é vale
> (ROADMAP §7).

✅ **Q-S08-3 — Quem vende clube ou pacote ganha comissão pela venda?**
1. Não: a comissão vem do atendimento (regras 1 e 4).
2. Sim, % configurável sobre a venda para o barbeiro que vendeu.

Recomendação: **1** agora. Quem fecha a venda é a recepção ou o gerente no balcão (a IA só
encaminha o interesse, PD-37), nem sempre um barbeiro; incentivo de venda entra depois como regra
5, sem mudar o livro-razão.

> Resolvido em 2026-11-06: opção 1 — sem comissão sobre venda de clube/pacote (ROADMAP §7).
