# Comanda e pagamentos registrados

**Priority:** high
**Status:** draft
**Espelho no frontend:** `frontend/docs/specs/⚪draft_frontend-tickets.md`

## Overview

A **comanda** é onde o atendimento vira dinheiro: o que foi feito (serviços, produtos, combos), por
quem (barbeiro por item), quanto saiu (preço do momento, descontos, benefício de clube ou pacote),
quanto o cliente deixou de gorjeta e **como pagou** (uma ou várias formas). Fechada, ela é o fato
de que dependem comissões (S08), caixa e resultado (S09), consumo de clube e pacote (S07), ficha
do cliente (S13) e relatórios (S14). Esta spec cria o módulo `sales`.

A comanda abre **a partir de um agendamento** (já com os serviços e barbeiros dele) ou **avulsa**
(venda de balcão, cliente que chegou sem marcar). Enquanto aberta é editável; fechada, é imutável
— corrigir é **estornar** (e, se quiser, abrir uma cópia). Não há gateway (PD-10): o pagamento é
**registrado**, mas o modelo já tem status, provedor e id externo para o gateway entrar depois.

## Decisões de produto já tomadas

| Parâmetro | Valor |
|---|---|
| PD-05 | Um agendamento pode ter vários serviços, inclusive com barbeiros diferentes: a comanda herda um item por serviço, cada um com o seu barbeiro. |
| PD-09 | Combo vendido avulso com preço fechado (S05); clube e pacote são **consumidos** na comanda (S07). |
| PD-10 | Sem gateway: só registro de pagamento feito fora. Modelar para o gateway entrar sem refazer. |
| PD-11 | Produto sem estoque: vender nunca falha por quantidade. |
| PD-13 | A comanda entrega a S08 o que as regras precisam: barbeiro por item, valor líquido, parte da taxa do cartão por item, benefício aplicado. |
| PD-14 | A comanda alimenta o caixa diário; fora: vales/adiantamentos, NFS-e. |
| PD-38 | **Gorjeta** na comanda, por barbeiro, fora da receita, repassada **integral** no fechamento de comissão (S08); a barbearia **absorve a taxa do cartão** sobre ela. |
| Convenções | Centavos; snapshot de nome/preço/taxa; `timestamptz` em UTC e "dia" no fuso da unidade. |

### Decisões técnicas desta spec

| # | Decisão | Por quê |
|---|---|---|
| T1 | Item guarda **snapshot**: nome, preço de tabela, preço praticado, percentual de comissão do produto, e no fechamento o líquido e a parte da taxa. | Mudar o catálogo depois não reescreve o passado (convenção do ROADMAP). |
| T2 | Combo vira um item-grupo (`kind = combo`, fora das somas) com os componentes como itens-filho, preço rateado por `catalog.allocate_combo_price`. | Comissão e relatório por serviço continuam funcionando dentro do combo; cada componente-serviço tem seu barbeiro. |
| T3 | Desconto por item e desconto na comanda (valor ou %). O da comanda é **rateado** entre os itens pelo valor (maior resto). Todo desconto manual exige motivo (ver Q-S06-2). | O líquido por item é o que a comissão usa; motivo dá rastreabilidade sem criar fluxo de aprovação. |
| T4 | A taxa de cada pagamento é calculada no fechamento (snapshot da forma) e **rateada** entre itens e gorjetas pelo valor líquido. A parte da gorjeta (`fee_share_cents` da gorjeta) é só informativa: é custo da barbearia (PD-38) e nunca sai do repasse do barbeiro. | S08 (regra "desconta taxa", só sobre itens) e S09 (resultado) usam o mesmo número; ninguém recalcula. |
| T5 | Itens de clube/pacote (`package_sale`, `membership_charge`) e benefícios aplicados a itens são **gerenciados pelo `memberships`**, que chama `sales.public`. A rota genérica de item recusa mexer neles (`409`). | `memberships` fica acima de `sales` (DEC-006): quem valida saldo e regra de uso é ele; `sales` não importa módulo de cima. |
| T6 | O caixa (S09, módulo `finance`, acima de `sales`) entra por **porta síncrona**: `sales.public.set_cash_session_resolver(fn)`, registrada no `main.py`. No fechamento/estorno a comanda pergunta "qual a sessão de caixa aberta desta unidade?"; o resolvedor devolve o id ou recusa (`409`). | Conferência de caixa exata exige o vínculo na mesma transação (o evento é assíncrono). Inversão de dependência evita import para cima. Vira DEC ao implementar. |
| T7 | Numeração humana `number` por barbearia, de uma sequence do schema (`ticket_number_seq`). | "Comanda #1532" na tela e no recibo; buracos (comanda descartada) são aceitáveis. |
| T8 | Uma comanda por agendamento (`UNIQUE appointment_id`); fechar a comanda marca o agendamento como concluído (`scheduling.public.complete_appointment`, idempotente). | A recepção fecha o atendimento num gesto só; `appointment.completed` sai do `scheduling`, que é o dono. |
| T9 | Estorno de comanda fechada gera **pagamentos negativos** espelhando os originais (mesma forma, taxa revertida), na sessão de caixa aberta **no momento do estorno**. | O caixa de ontem, já conferido, não muda; o de hoje mostra a devolução. Igual a PDV de varejo. |

## Business Rules

### Abrir

- [ ] `POST /tickets` com `appointment_id`: copia `unit_id`, `client_id` e um item `service` por
      item do agendamento (serviço, barbeiro, preço snapshot do agendamento). Agendamento cancelado
      ou faltou → `409` "Este agendamento não pode virar comanda"; já tem comanda (aberta ou
      fechada) → `409` "Este agendamento já tem a comanda #N" (estornada não conta).
- [ ] Avulsa: `unit_id` obrigatório (dentro do escopo do usuário, senão `403`), `client_id`
      opcional ("cliente não identificado" só para produto/serviço sem benefício).
- [ ] `copy_from_ticket_id` (só de comanda estornada): abre outra com os mesmos itens, barbeiros e
      cliente, preços **atuais** do catálogo e sem benefícios (precisam ser aplicados de novo).
- [ ] Comanda nasce `open`, com `opened_by`, `opened_at` e `number` (T7).

### Itens (comanda aberta)

- [ ] Tipos que a rota genérica aceita: `service` (barbeiro obrigatório no fechamento),
      `product` (barbeiro opcional = "vendido por"; `quantity` 1–99) e `combo` (expande nos
      componentes, T2; serviços do combo herdam o `barber_id` informado, editáveis um a um).
- [ ] Preço vem do catálogo no momento da inclusão (snapshot); não há edição de preço — muda-se com
      desconto. Item de catálogo inativo ou inexistente → `400`.
- [ ] Barbeiro do item precisa estar ativo, ser da unidade da comanda e (para serviço) ter o
      serviço habilitado em `barber_services`; senão `400` "Este barbeiro não faz este serviço".
- [ ] Componente de combo não pode ser removido sozinho (remove-se o combo); pode ter barbeiro e
      desconto próprios.
- [ ] Desconto de item: `{kind: amount|percent, value}`, nunca maior que o valor do item; motivo
      obrigatório (`discount_reason`, 3–200). Item com benefício de clube/pacote não aceita
      desconto manual (`409`).
- [ ] Item com benefício não pode trocar de serviço nem de barbeiro sem tirar o benefício antes
      (`409` "Remova o benefício antes de alterar este item") — a regra de uso depende dos dois.
- [ ] Itens `package_sale` e `membership_charge` e os benefícios só mudam pelas rotas do
      `memberships` (T5); pela rota genérica → `409` "Altere pelo clube ou pacote".
- [ ] Toda alteração recalcula e grava os totais da comanda.

### Desconto da comanda e gorjeta

- [ ] Desconto da comanda: valor ou %, até o total depois dos descontos de item, com motivo;
      rateado entre os itens não cobertos por benefício (T3).
- [ ] Gorjeta (PD-38): `PUT /tickets/{id}/tips` com `[{barber_id, amount_cents}]`
      substitui a lista; barbeiro precisa ter item na comanda. Gorjeta **não** é receita: soma ao
      valor a pagar, não entra no subtotal nem no desconto. É repassada **integral** ao barbeiro
      (S08); a parte da taxa do cartão que cai sobre ela é absorvida pela barbearia (entra como
      taxa no resultado, S09).

### Fechar

- [ ] Só comanda `open`, com pelo menos um item; todo serviço com barbeiro (`422` "Informe o
      barbeiro de cada serviço").
- [ ] `payments` (0–10 linhas): forma ativa, `amount_cents > 0`, `installments` entre 1 e o máximo
      da forma. A soma dos valores aplicados é **exatamente** `amount_due_cents` (total + gorjeta),
      senão `422` "O pagamento não fecha com o total".
- [ ] Troco: só em forma `cash`, via `tendered_cents ≥ amount_cents`; `change_cents` = soma das
      diferenças. Total zero (tudo coberto por clube) fecha sem pagamento.
- [ ] Taxa por pagamento = `catalog.payment_fee_cents` com snapshot de percentual, fixo e parcelas;
      rateio da taxa total entre itens-folha e gorjetas pelo líquido (T4), maior resto.
- [ ] Líquido do item (`net_cents`) = preço × quantidade − desconto de item − parte do desconto da
      comanda − desconto do benefício. Soma dos `net_cents` = `total_cents`.
- [ ] Sessão de caixa pelo resolvedor (T6); a recusa dele (`409`, mensagem dele) cancela o
      fechamento inteiro. Sem resolvedor registrado, `cash_session_id` fica nulo.
- [ ] `business_date` = data local de `closed_at` no fuso da unidade.
- [ ] Com agendamento, chama `complete_appointment` (T8) na mesma transação, com o usuário como
      `actor`.
- [ ] Publica `ticket.closed` (outbox, mesma transação). Comanda fechada é imutável: qualquer
      escrita → `409` "Comanda fechada; estorne para corrigir".

### Estornar

- [ ] Comanda aberta: "descartar" = `void` com motivo; exige `ticket:write`.
- [ ] Comanda fechada: exige `finance:write` no escopo da unidade (ver Q-S06-4); motivo 3–300;
      gera os pagamentos negativos (T9) na sessão de caixa que o resolvedor indicar agora.
- [ ] O agendamento continua concluído (o atendimento aconteceu); clube, pacote, comissão e caixa
      reagem ao evento.
- [ ] Publica `ticket.voided` com `was_closed`. Estornar duas vezes → `409`.

### Leitura e escopo

- [ ] `all`: tudo; `unit`: comandas das unidades do usuário; `own` (barbeiro): comandas com item ou
      gorjeta dele (a comanda inteira é exibida).
- [ ] Lista paginada, filtros por status, unidade, período (`business_date`, ou `opened_at` para
      abertas), cliente, barbeiro, agendamento; ordenada pela mais recente.

## Data Contract

```text
# Módulo sales, tag "tickets"
GET    /tickets?status=open|closed|voided&unit_id=&date_from=&date_to=&client_id=&barber_id=
              &appointment_id=&limit=50&offset=0      → 200 {items: TicketSummary[], total}
POST   /tickets            TicketOpenIn               → 201 TicketOut | 400 | 403 | 404 | 409
GET    /tickets/{id}                                  → 200 TicketOut | 404
PATCH  /tickets/{id}       TicketUpdate               → 200 TicketOut | 400 | 409 | 422
POST   /tickets/{id}/items TicketItemIn               → 201 TicketOut | 400 | 409 | 422
PATCH  /tickets/{id}/items/{item_id} TicketItemUpdate → 200 TicketOut | 400 | 404 | 409 | 422
DELETE /tickets/{id}/items/{item_id}                  → 200 TicketOut | 404 | 409
PUT    /tickets/{id}/tips  TipIn[]                    → 200 TicketOut | 400 | 409
POST   /tickets/{id}/close TicketCloseIn              → 200 TicketOut | 409 | 422
POST   /tickets/{id}/void  {reason}                   → 200 TicketOut | 403 | 409 | 422

TicketOpenIn   {unit_id?, client_id?, appointment_id?, copy_from_ticket_id?, notes?}
               (appointment_id e copy_from_ticket_id são exclusivos; sem eles, unit_id obrigatório)
TicketUpdate   {client_id?, notes?, discount?: Discount|null, discount_reason?}
Discount       {kind: amount|percent, value}           (amount em centavos; percent 0–100)
TicketItemIn   {kind: service|product|combo, service_id?|product_id?|combo_id?, barber_id?,
                quantity? = 1}
TicketItemUpdate {barber_id?, quantity?, discount?: Discount|null, discount_reason?}
TipIn          {barber_id, amount_cents}
TicketCloseIn  {payments: [{payment_method_id, amount_cents, installments? = 1,
                            tendered_cents?, authorization_code? (até 40)}]}

TicketOut      {id, number, unit_id, status, client: {id, name, phone}|null, appointment_id,
                opened_at, opened_by, closed_at, closed_by, business_date, voided_at, voided_by,
                void_reason, notes, discount: Discount|null, discount_reason,
                subtotal_cents, discount_cents, total_cents, tip_cents, amount_due_cents,
                paid_cents, change_cents, fee_cents,
                items: TicketItemOut[], tips: [{barber_id, amount_cents, fee_share_cents}],
                payments: TicketPaymentOut[]}
TicketItemOut  {id, kind, parent_item_id, service_id, product_id, combo_id, source_ref_id,
                name, barber_id, quantity, list_price_cents, unit_price_cents, discount: Discount|null,
                discount_reason, discount_cents, ticket_discount_share_cents,
                benefit: {kind: club_included|club_discount|package, ref_id, discount_cents,
                          value_cents}|null,
                net_cents, fee_share_cents, managed_by: sales|memberships}
TicketPaymentOut {id, payment_method_id, method_name, method_kind, amount_cents, installments,
                fee_percent, fee_fixed_cents, fee_cents, tendered_cents, change_cents,
                authorization_code, status, provider, external_id, refund_of_id,
                cash_session_id, received_at, received_by}
TicketSummary  {id, number, unit_id, status, client_name, barber_ids[], total_cents,
                amount_due_cents, opened_at, closed_at, business_date}

Erros: 400 "Serviço|Produto|Combo não encontrado", "Este barbeiro não faz este serviço",
           "Barbeiro de outra unidade", "Forma de pagamento não encontrada"
       409 "Este agendamento não pode virar comanda", "Este agendamento já tem a comanda #N",
           "Comanda fechada; estorne para corrigir", "Comanda já estornada",
           "Altere pelo clube ou pacote", "Remova o benefício antes de alterar este item",
           "Comanda sem itens" (+ mensagens do resolvedor de caixa, S09)
       422 "O pagamento não fecha com o total", "Informe o barbeiro de cada serviço",
           "Desconto maior que o valor", "Informe o motivo do desconto"
```

### Eventos publicados (outbox, S00)

```text
ticket.closed  {ticket_id, number, unit_id, client_id, appointment_id, closed_at, business_date,
                subtotal_cents, discount_cents, total_cents, tip_cents, fee_cents,
                items: [{item_id, kind, parent_item_id, service_id, product_id, combo_id,
                         source_ref_id, barber_id, quantity, list_price_cents, unit_price_cents,
                         net_cents, fee_share_cents, product_commission_percent,
                         benefit_kind, benefit_ref_id, benefit_value_cents}],      (sem o item-grupo de combo)
                tips: [{barber_id, amount_cents, fee_share_cents}],
                payments: [{payment_id, payment_method_id, method_kind, amount_cents, fee_cents}]}
ticket.voided  {ticket_id, number, unit_id, client_id, was_closed, voided_at, business_date
                (data local do estorno), reason, item_ids[]}
```

### `sales/public.py` (oferecido a outros módulos)

```text
get_ticket(session, ticket_id) -> TicketView
open_ticket(session, ctx, unit_id, client_id) -> TicketView
find_open_ticket(session, client_id, unit_id) -> TicketView | None
add_managed_item(session, ticket_id, kind, source_ref_id, name, unit_price_cents) -> item_id
remove_managed_item(session, ticket_id, item_id)
apply_item_benefit(session, ticket_id, item_id, kind, ref_id, discount_cents, value_cents=None)
remove_item_benefit(session, ticket_id, item_id)
set_cash_session_resolver(resolver)       # resolver(session, unit_id, at, method_kinds) -> uuid | None
                                          # (method_kinds: tipos de pagamento envolvidos; Q-S09-1)
payments_by_cash_session(session, cash_session_id) -> [{payment_method_id, kind, amount, fee, n}]
revenue_summary(session, unit_ids, date_from, date_to) -> receita por tipo de item, descontos,
                gorjetas, taxas, por forma de pagamento e por dia (comandas fechadas, sem estornadas)
iter_report_facts(session, since)          # pedido da S14 (reconstrução dos fatos de relatório)
```

### Banco de dados

Migration de tenant `tNNNN_sales` (expand only):

```text
tickets         id uuid pk · number integer default nextval(ticket_number_seq) UNIQUE ·
                unit_id → units.id RESTRICT · client_id → clients.id RESTRICT null ·
                appointment_id → appointments.id RESTRICT null ·
                status ticket_status ('open','closed','voided') ·
                discount_kind discount_kind ('amount','percent') null ·
                discount_value integer null · discount_reason varchar(200) null ·
                subtotal_cents · discount_cents · total_cents · tip_cents · amount_due_cents ·
                paid_cents · change_cents · fee_cents  (integer, check >= 0) ·
                notes varchar(500) null · business_date date null ·
                opened_at · opened_by → users.id · closed_at null · closed_by null ·
                voided_at null · voided_by null · void_reason varchar(300) null ·
                created_at · updated_at
                UNIQUE INDEX uq_ticket_appointment ON (appointment_id)
                       WHERE appointment_id IS NOT NULL AND status <> 'voided'
                INDEX (unit_id, status) · INDEX (business_date) · INDEX (client_id)

ticket_items    id uuid pk · ticket_id → tickets.id CASCADE · parent_item_id → ticket_items.id
                CASCADE null · kind ticket_item_kind ('service','product','combo','package_sale',
                'membership_charge') · service_id → services RESTRICT null ·
                product_id → products RESTRICT null · combo_id → combos RESTRICT null ·
                source_ref_id uuid null (sem FK: dono é o memberships) ·
                appointment_item_id uuid null · barber_id → barbers RESTRICT null ·
                name varchar(120) · quantity smallint check (1..99) ·
                list_price_cents · unit_price_cents · discount_kind null · discount_value null ·
                discount_reason null · discount_cents · ticket_discount_share_cents ·
                benefit_kind ticket_benefit_kind ('club_included','club_discount','package') null ·
                benefit_ref_id uuid null · benefit_discount_cents default 0 ·
                benefit_value_cents integer null (valor pré-pago que o uso consome: pacote) ·
                product_commission_percent numeric(5,2) null ·
                net_cents null · fee_share_cents null · position smallint
                CHECK ck_item_ref (kind ↔ coluna de referência preenchida)
                INDEX (ticket_id) · INDEX (barber_id) · INDEX (benefit_ref_id)

ticket_tips     id uuid pk · ticket_id CASCADE · barber_id RESTRICT · amount_cents check (> 0) ·
                fee_share_cents null · UNIQUE (ticket_id, barber_id)

ticket_payments id uuid pk · ticket_id → tickets RESTRICT · payment_method_id → payment_methods
                RESTRICT · method_name varchar(60) · method_kind payment_method_kind ·
                amount_cents integer (negativo só em estorno) · installments smallint ·
                fee_percent numeric(5,2) · fee_fixed_cents · fee_cents ·
                tendered_cents null · change_cents default 0 · authorization_code varchar(40) null ·
                status payment_status ('pending','confirmed','failed','refunded') ·
                provider varchar(30) default 'manual' · external_id varchar(100) null ·
                refund_of_id → ticket_payments.id null · cash_session_id uuid null (sem FK, T6) ·
                received_at · received_by → users.id
                INDEX (cash_session_id) · INDEX (ticket_id)
                UNIQUE INDEX uq_payment_external ON (provider, external_id) WHERE external_id IS NOT NULL
```

`appointments.id` vem de S03; se a migration da agenda ainda não existir, esta migration depende
dela (`down_revision`).

## Permissões

Nenhuma permissão nova.

| Ação | Permissão | owner | manager | receptionist | barber |
|---|---|---|---|---|---|
| ver comandas | `ticket:read` | all | unit | unit | own |
| abrir, editar, fechar, descartar aberta | `ticket:write` | all | unit | unit | — |
| estornar comanda fechada | `finance:write` | all | unit | — (Q-S06-4) | — |

## Acceptance Criteria

- [ ] Módulo `sales` com layout completo, no `model_registry`, `main.py` e contrato de camadas;
      `sales` importa só `identity`, `catalog`, `clients`, `scheduling` pelo `public.py`.
- [ ] Testes de cálculo puro: rateio do desconto da comanda, rateio da taxa, combo, troco, total
      zero, arredondamento (soma dos líquidos = total, soma das partes da taxa = taxa).
- [ ] Testes de fluxo: abrir do agendamento (multisserviço, barbeiros diferentes), avulsa, cópia de
      estornada, fechar com três formas, recusa do resolvedor de caixa, estorno com pagamentos
      negativos, imutabilidade da fechada, rota genérica recusando item gerenciado.
- [ ] Eventos `ticket.closed`/`ticket.voided` gravados no outbox na mesma transação (rollback não
      publica).
- [ ] Cruzamento entre duas barbearias e escopos (recepção de outra unidade, barbeiro `own`).
- [ ] Snapshots e `make docs-api`; `make check` verde; memória atualizada; DEC nova para T5/T6.

## Dependencies

- **S00** — outbox (`publish(session, type, payload, *, aggregate_id, actor)` na transação) e
  worker.
- **S03** (assumido do `scheduling`, nomes conforme `⚪draft_scheduling-appointments.md`):
  `get_appointment(session, appointment_id) -> AppointmentView | None`, do qual a comanda usa
  `{id, unit_id, client_id, status, items: [{id, service_id, service_name, barber_id, starts_at,
  price_cents, combo_id?}]}`; `complete_appointment(session, *, appointment_id, actor)`
  idempotente, que publica `appointment.completed`; tabela `appointments`. Status que não abrem comanda: `cancelled`,
  `no_show`.
- **S05** — `get_product`, `get_combo`, `get_payment_method`, `allocate_combo_price`,
  `payment_fee_cents`; `get_service` (já existe).
- **identity** — `get_barber` (já existe); verificação de `barber_services` vem do `catalog`
  (`barber_offers_service`, a acrescentar no `catalog/public.py`).
- **clients** — `get_client(session, id)` no `clients/public.py` (oferecido pela S13; hoje só há
  `create_client`).
- Oferece: eventos acima; `sales/public.py` acima para **S07** (itens gerenciados, benefícios),
  **S09** (resolvedor de caixa, pagamentos por sessão, receita), **S08** (só eventos), **S13/S14**
  (eventos e `revenue_summary`).

## Notes

- **Gateway (PD-10).** Hoje todo pagamento nasce `confirmed`/`manual` dentro do `close`. Com
  gateway: `POST /tickets/{id}/payments` cria pagamento `pending` com `provider`/`external_id`, o
  webhook confirma, e o `close` passa a aceitar pagamentos já confirmados. Nenhuma coluna muda.
- **Estorno de cartão.** O pagamento negativo reverte também a taxa (`fee_cents` negativo). Se a
  adquirente não devolver a taxa, o dono ajusta como despesa (S09).
- **Barbeiro lançando produto** na própria comanda (PD-26, PWA) fica fora: barbeiro não tem
  `ticket:write`. Se pedirem, é mudança de mapa (`ticket:write` `own`), não de contrato.
- **Recibo/impressão** e envio do comprovante no WhatsApp ficam para S12/S18.
- Comanda aberta há mais de um dia aparece destacada na lista (decisão de tela, frontend).

### Perguntas em aberto

✅ **Q-S06-1 — Gorjeta entra na comanda?**
1. Não: gorjeta fica fora do sistema.
2. Sim, valor por barbeiro na comanda, fora da receita, repassada 100% no fechamento de comissão;
   se a regra "desconta taxa do cartão" estiver ligada, a parte da taxa sobre a gorjeta é
   descontada.
3. Como 2, mas a barbearia sempre absorve a taxa da gorjeta.

Recomendação: **3**. Booksy e Fresha tratam gorjeta como do profissional, sem desconto; evita
discussão com o barbeiro por centavos. (O modelo acima suporta 2 e 3; 1 só remove `ticket_tips`.)

> Resolvido em 2026-11-06: opção 3 — gorjeta por barbeiro na comanda, fora da receita, repassada
> integral; a barbearia absorve a taxa do cartão sobre ela (PD-38).

✅ **Q-S06-2 — Limite de desconto para a recepção?**
1. Livre para quem tem `ticket:write`, com motivo obrigatório e relatório de descontos por usuário.
2. Limite em % para a recepção; acima disso, gerente digita a senha na hora.
3. Livre, sem motivo.

Recomendação: **1** agora; o relatório (S14) mostra quem dá desconto. A aprovação com senha (2)
pode entrar depois sem mudar o contrato do item.

> Resolvido em 2026-11-06: opção 1 — desconto livre para quem tem `ticket:write`, com motivo
> obrigatório e relatório de descontos por usuário (ROADMAP §7).

✅ **Q-S06-3 — "Fiado" (cliente leva e paga depois)?**
1. Não: comanda só fecha paga.
2. Sim: forma "a receber" que deixa saldo devedor no cliente, quitado numa comanda futura.

Recomendação: **1**. Contas a receber de cliente é um módulo à parte (cobrança, lembrete); fica
para depois de PD-14.

> Resolvido em 2026-11-06: opção 1 — sem "fiado"; a comanda só fecha paga (ROADMAP §7).

✅ **Q-S06-4 — Quem pode estornar uma comanda fechada?**
1. Só gerente e dono (`finance:write`).
2. Recepção também, enquanto o caixa em que ela foi recebida estiver aberto; depois, só gerente.
3. Qualquer um com `ticket:write`.

Recomendação: **1**, mais simples e seguro; se a recepção reclamar do erro de digitação no mesmo
minuto, a 2 entra como regra extra sem mudar o contrato.

> Resolvido em 2026-11-06: opção 1 — só gerente e dono (`finance:write`) estornam comanda fechada
> (ROADMAP §7).
