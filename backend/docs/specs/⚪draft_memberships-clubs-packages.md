# Clubes e pacotes

**Priority:** high
**Status:** draft
**Espelho no frontend:** `frontend/docs/specs/⚪draft_frontend-clubs-packages.md`

## Overview

Clube de assinatura é o produto de recorrência que mais cresceu nas barbearias (BestBarbers,
AppBarber e Trinks vendem isso como carro-chefe): o cliente paga um valor por mês e corta à
vontade, ou N vezes, ou com desconto. **Pacote** é o pré-pago: 4 cortes por um preço, com validade.
Esta spec cria o módulo `memberships`: o **cadastro** de clubes e pacotes, a **adesão** do cliente,
os **ciclos** com a cobrança do mês **registrada** e baixada na comanda (PD-10, sem gateway), a
**inadimplência**, o **cancelamento**, o **consumo** na comanda com as regras de uso, o **saldo**, a
**expiração** e a consulta que a IA do WhatsApp usa ("esse cliente tem clube?", PD-17).

Toda entrada de dinheiro — mensalidade, venda de pacote — passa por uma **comanda** (S06). Assim
caixa, taxa do cartão, receita e relatórios funcionam sem caminho paralelo.

## Decisões de produto já tomadas

| Parâmetro | Valor |
|---|---|
| PD-09 | **Clube**: assinatura mensal com serviços ilimitados ou N por ciclo, e/ou desconto. **Pacote**: N serviços por um preço, com validade. Menu Cadastros: Clubes, Pacotes, Combos. |
| PD-10 | Sem gateway: o sistema gera a cobrança do ciclo e a recepção dá baixa. Modelar para o gateway (cobrança recorrente no cartão) entrar depois. |
| PD-13 | Atendimento de assinante tem regra de comissão própria (S08); o uso precisa dizer barbeiro, serviço e preço de tabela. |
| PD-17 | A IA responde sobre clube e pacote e os oferece — **refinada pela PD-37**: ela não fecha a venda. |
| PD-35 | Comissão de atendimento de assinante: a barbearia **escolhe o modo** ao ligar a regra (rateio da mensalidade, valor fixo por atendimento, % do preço de tabela ou sem comissão), sem padrão imposto (S08). Esta spec entrega o uso com barbeiro, serviço e preço de tabela, e os ciclos pagos para o rateio. |
| PD-36 | Mensalidade vencida: **tolerância configurável (padrão 5 dias)** usando normalmente; depois **bloqueia o uso** até pagar. Nunca cancela sozinho. |
| PD-37 | A IA **não fecha venda** de clube ou pacote: explica (`list_offers`, `get_client_benefits`), registra o interesse e passa para a fila de humano (handoff com motivo `sale`, S10/S11); **a equipe fecha** no painel. Nenhuma adesão ou pacote nasce pela IA. |
| PD-22 | "Clubes e pacotes" é recurso de plano (`PlanFeature.MEMBERSHIPS`, S15): sem ele, `402`. |
| PD-03 | Cliente é da barbearia; a adesão vale em qualquer unidade que o clube permitir. |

### Decisões técnicas desta spec

| # | Decisão | Por quê |
|---|---|---|
| T1 | Ciclo **pré-pago e mensal**, ancorado no dia do **primeiro pagamento** (dia 29–31 vira o último dia nos meses curtos). Ciclo `n` = cobrança `n`: uma tabela só (`membership_cycles`). | Clube de barbearia é pago adiantado; ancorar no pagamento evita cobrar dias que o cliente não usou. |
| T2 | No máximo **uma adesão não cancelada por cliente** (um clube por vez). Trocar de clube = cancelar e aderir. | A resposta da IA e da comanda fica inequívoca; nenhum player relevante empilha clubes. |
| T3 | Cobrança e venda viram **item de comanda** (`membership_charge`, `package_sale`) por `sales.public.add_managed_item`; benefício aplicado ao item por `apply_item_benefit`. A baixa acontece no `ticket.closed`. | Um caminho de dinheiro só (S06 T5). |
| T4 | Uso é registrado em `membership_usages` como `reserved` (comanda aberta) → `consumed` (`ticket.closed`) → `reverted` (estorno ou remoção). Saldo = limite − (`reserved` + `consumed`). Aplicar benefício trava a adesão/pacote (`SELECT … FOR UPDATE`). | Duas comandas abertas não gastam o último uso duas vezes. |
| T5 | Benefício pago na **mesma comanda** vale: adesão `pending` ou pacote `pending_payment` cujo item de cobrança/venda está na comanda pode ser usado nela. | O cliente adere ao clube e corta na mesma visita — o caso mais comum de venda no balcão. |
| T6 | Valor por uso do pacote = preço do pacote rateado entre os serviços pelo preço de tabela × quantidade (`catalog.allocate_combo_price`), dividido pela quantidade, arredondado para baixo. Vai no benefício como `value_cents` para a comissão (S08 T4). | Comissão de pacote paga o trabalho sobre o que o cliente pagou, não sobre a tabela. |
| T7 | Semana da regra "por semana" = segunda a domingo no fuso da unidade; "dia" idem. | Previsível para o cliente e para a recepção. |
| T8 | Uso conta **na comanda**, não no agendamento. A consulta de benefícios informa o saldo; a IA (S11) pode somar os agendamentos futuros dela mesma. | O agendamento pode não acontecer; consumir na hora certa evita estorno de saldo. |
| T9 | Adesão `pending` não paga em 7 dias (`pending_expiry_days`) é cancelada sozinha (motivo "não pago"). Pacote `pending_payment` não precisa: ele vive na comanda, e descartar/estornar a comanda o cancela. | Adesão registrada no balcão sem `ticket_id` (o cliente "vai pensar" ou pagar depois) não fica pendurada na lista nem trava a regra de um clube por vez (T2); a recepção não precisa limpar à mão. Não é cancelamento por inadimplência (nunca houve ciclo pago). |

## Business Rules

### Cadastro de clubes

- [ ] Campos: `name` (2–80, único sem maiúsculas), `description` (até 500), `price_cents` (> 0),
      `terms` (até 2000: regras mostradas ao cliente e lidas pela IA), `sellable_online` (a IA e o
      link podem oferecer), `active`.
- [ ] Benefícios (1–20): `included` para um serviço com `quantity_per_cycle` (1–60 ou `null` =
      ilimitado), ou `discount` com `discount_percent` (1–100) para um serviço, um produto, todos
      os serviços ou todos os produtos. Desconto específico vence o geral; serviço `included` não
      recebe desconto (já é coberto).
- [ ] Regras de uso (todas opcionais): `max_uses_per_day`, `max_uses_per_week`,
      `min_days_between_uses`, `allowed_weekdays` (ex.: clube "segunda a quinta", comum no
      BestBarbers), unidades permitidas (vazio = todas), barbeiros permitidos (vazio = todos). As
      regras de quantidade valem para usos `included`; desconto só respeita unidade, barbeiro e dia
      da semana.
- [ ] Mudar benefício ou regra vale para os próximos usos de todos os assinantes. Mudar preço
      (Q-S07-2): o dono escolhe `price_applies_to` — `new_only` (pré-selecionado; adesões existentes
      guardam o preço delas) ou `all_from` com `price_effective_from` (ciclos gerados a partir da
      data usam o preço novo; S12 avisa os assinantes antes do próximo ciclo).
- [ ] Apagar com adesão → `409`; inativar impede adesão nova e mantém as existentes.

### Cadastro de pacotes

- [ ] Campos: `name` (único), `description`, `price_cents` (> 0), `validity_days` (1–730),
      `sellable_online`, `active`; itens (1–10): serviço + `quantity` (1–50).
- [ ] Mudar o cadastro não altera pacote já vendido (snapshot em `client_package_items`).

### Adesão e ciclo

- [ ] `POST /client-memberships`: cliente ativo, clube ativo, cliente sem outra adesão não
      cancelada (`409` "Este cliente já tem o clube X"). Nasce `pending` com o ciclo 1 (valor =
      preço do clube, snapshot). Com `ticket_id`, a cobrança do ciclo 1 já entra na comanda.
- [ ] Primeiro pagamento (T1): fixa `anchor_day` e as datas do ciclo 1 a partir da data de
      `business_date` da comanda; adesão vira `active`.
- [ ] Worker diário: a adesão `active` ou `past_due` cujo ciclo termina em até 3 dias ganha o
      próximo ciclo (`due_date` = início) e publica `membership.charge_due`. Nunca existe mais de um
      ciclo não pago por adesão.
- [ ] Inadimplência (PD-36): ciclo vencido e não pago → `past_due`, **usando normalmente** durante a
      tolerância; passados `grace_days` (configuração, padrão 5) → `suspended` (uso bloqueado até
      pagar) e `membership.suspended`. **Nunca cancela sozinho** por inadimplência. Pagou →
      `active` (as datas do ciclo não mudam). `block_when_past_due` (desligado por padrão) é a
      opção mais rígida para quem quiser: bloqueia o uso já em `past_due`, sem tolerância
      (motivo `past_due_blocked`); o bloqueio depois da tolerância vale sempre.
- [ ] Cobrar: `POST /membership-cycles/{id}/charge` com `ticket_id` (comanda aberta do mesmo
      cliente, ou sem cliente — passa a ser dele) ou `unit_id` (abre comanda nova). Ciclo já numa
      comanda aberta → `409` "Esta mensalidade já está na comanda #N".
- [ ] `ticket.closed` com o item → ciclo `paid` (`paid_at`, `ticket_id`, `ticket_item_id`),
      status recalculado, `membership.charge_paid`. Idempotente.
- [ ] `ticket.voided` de comanda fechada com o item → ciclo volta a `pending` e o status é
      recalculado (pode cair em `past_due`/`suspended`).
- [ ] Isentar (`waive`): ciclo `waived` com motivo, conta como pago para uso; exige `finance:write`.

### Cancelamento

- [ ] `POST .../cancel` com `when: end_of_cycle` (padrão: usa até o fim do ciclo pago, não gera
      próximo; ciclo futuro já gerado e não pago é cancelado) ou `now` (encerra hoje; ciclo não pago
      é cancelado; pago não é devolvido — devolução é estorno da comanda, se for o caso). Motivo
      obrigatório (lista + texto livre). Publica `membership.cancelled` na data efetiva.
- [ ] Cancelamento agendado pode ser desfeito antes da data (`undo-cancel`).

### Venda e vida do pacote

- [ ] `POST /client-packages` com `ticket_id` ou `unit_id`: cria `pending_payment` com snapshot
      dos itens e valor por uso (T6) e põe o item `package_sale` na comanda. `ticket.closed` →
      `active`, `expires_at` = data da comanda + `validity_days`. Estorno → `cancelled` e usos
      revertidos.
- [ ] Saldo zerado → `exhausted`; worker diário: passou de `expires_at` → `expired`, saldo
      perdido (Q-S07-4). Prorrogar (`extend`) exige `finance:write`.
- [ ] Um cliente pode ter vários pacotes; o consumo usa o que **vence primeiro**, salvo escolha
      explícita na comanda.

### Consumo na comanda

- [ ] `GET /clients/{id}/eligibility?service_id|product_id&barber_id&unit_id&at&ticket_id` devolve
      as opções aplicáveis e, para o clube, o motivo quando não aplica (`not_member`,
      `suspended`, `past_due_blocked`, `cycle_unpaid`, `unit_not_allowed`, `barber_not_allowed`,
      `weekday_not_allowed`, `cycle_limit`, `day_limit`, `week_limit`, `min_interval`,
      `not_covered`) com mensagem em português.
- [ ] `POST /tickets/{tid}/items/{iid}/benefit {source: club|package, client_package_id?}`:
      comanda aberta com cliente; item `service` (included, desconto ou pacote) ou `product`
      (desconto); revalida tudo sob trava (T4); cria uso `reserved` e chama
      `apply_item_benefit` — `club_included` e `package` cobrem o preço inteiro; `club_discount`
      aplica o %. Não elegível → `409` com a mensagem do motivo.
- [ ] `DELETE` do benefício → uso `reverted` e `remove_item_benefit`.
- [ ] `ticket.closed` → usos da comanda `consumed`; `ticket.voided` → `reverted` (descarte de
      comanda aberta também). Idempotente.

### Consulta para a IA e para a ficha do cliente

- [ ] `GET /clients/{id}/benefits` (e `get_client_benefits` no `public.py`): clube (nome, status,
      ciclo atual, próximo vencimento, saldo por serviço — `null` = ilimitado —, descontos, regras
      em texto, motivo de bloqueio) e pacotes ativos (nome, validade, saldo por serviço).
- [ ] `list_offers` para a IA: clubes e pacotes `active` e `sellable_online`, com benefícios em
      texto.
- [ ] A IA só **lê** (`list_offers`, `get_client_benefits`): explica, registra o interesse na
      conversa e faz handoff com motivo `sale` ("venda de clube/pacote", PD-37). Não há função de
      escrita para ela no `public.py`; a equipe fecha a venda pelas rotas desta spec
      (`POST /client-memberships`, `POST /client-packages`), normalmente já na comanda (T5).

### Plano e permissões

- [ ] Sem o recurso `memberships` no plano: criar/editar clube e pacote, nova adesão e venda de pacote →
      `402` "Clubes e pacotes não estão no seu plano". O que já existe continua sendo cobrado e
      consumido (rebaixar o plano não tira benefício pago do cliente).

## Data Contract

```text
# Módulo memberships, tags "clubs", "packages", "memberships"
GET/POST /clubs · GET/PATCH/DELETE /clubs/{id}                 (benefits, unit_ids, barber_ids inline)
GET/POST /packages · GET/PATCH/DELETE /packages/{id}           (items inline)

ClubIn  {name, description?, price_cents, terms?, sellable_online = false, active = true,
         benefits: [{kind: included|discount, target: service|product|all_services|all_products,
                     service_id?, product_id?, quantity_per_cycle?, discount_percent?}],
         max_uses_per_day?, max_uses_per_week?, min_days_between_uses?, allowed_weekdays?: int[],
         unit_ids: uuid[] = [], barber_ids: uuid[] = []}
ClubPatch = ClubIn parcial + {price_applies_to?: new_only|all_from = new_only,   # all_from publica
                              membership.price_changed → aviso da S12
         price_effective_from?: date}        (só com price_cents; all_from exige a data)
ClubOut = ClubIn + {id, members_count, created_at, updated_at}
PackageIn {name, description?, price_cents, validity_days, sellable_online = false,
           active = true, items: [{service_id, quantity}]}
PackageOut = PackageIn + {id, list_price_cents, created_at, updated_at}

GET  /client-memberships?status=&club_id=&client_id=&q=&limit=&offset= → {items, total}
POST /client-memberships {client_id, club_id, unit_id, ticket_id?}  → 201 | 400 | 402 | 409
GET  /client-memberships/{id}                   → MembershipOut (com ciclos e uso do ciclo atual)
POST /client-memberships/{id}/cancel {when: end_of_cycle|now, reason_code, reason?} → 200 | 409
POST /client-memberships/{id}/undo-cancel       → 200 | 409

GET  /membership-cycles?charge_status=pending|paid|waived&overdue=&club_id=&due_from=&due_to=
                       &limit=&offset=          → {items: CycleOut[], total, sum_cents}
POST /membership-cycles/{id}/charge {ticket_id? | unit_id?} → 200 {ticket_id} | 409
POST /membership-cycles/{id}/waive {reason}     → 200 CycleOut | 403 | 409
DELETE /tickets/{ticket_id}/membership-charges/{cycle_id} → 204 | 409

GET  /client-packages?client_id=&status=&limit=&offset= → {items, total}
POST /client-packages {client_id, package_id, ticket_id? | unit_id?} → 201 {client_package, ticket_id}
                                                  | 400 | 402 | 409
GET  /client-packages/{id} · POST /client-packages/{id}/extend {expires_at}
POST /client-packages/{id}/cancel {reason}
DELETE /tickets/{ticket_id}/package-sales/{client_package_id} → 204 | 409

GET    /clients/{id}/benefits?at=                → ClientBenefitsOut
GET    /clients/{id}/eligibility?service_id=|product_id=&barber_id=&unit_id=&at=&ticket_id=
                                                 → {options: BenefitOption[], blocked: [{code, message}]}
POST   /tickets/{ticket_id}/items/{item_id}/benefit {source: club|package, client_package_id?}
                                                 → 200 {ticket_id} | 409
DELETE /tickets/{ticket_id}/items/{item_id}/benefit → 204 | 404

GET/PUT /membership-settings {grace_days (0–60), block_when_past_due, pending_expiry_days}

MembershipOut {id, client: {id, name, phone}, club_id, club_name, status, price_cents,
     anchor_day, started_on, origin, cancel_at, cancelled_at, cancel_reason_code, cancel_reason,
     current_cycle: CycleOut|null, cycles: CycleOut[],
     usage: [{service_id, name, used, limit|null}]}
CycleOut {id, client_membership_id, client_name, club_name, number, start_date, end_date,
     due_date, amount_cents, charge_status, overdue, paid_at, ticket_id, waived_reason,
     open_ticket_id}
ClientPackageOut {id, client_id, package_id, name, status, price_cents, purchased_on,
     expires_at, origin, items: [{service_id, name, quantity, used, remaining, unit_value_cents}]}
BenefitOption {source: club|package, ref_id, benefit_kind: club_included|club_discount|package,
     discount_cents, value_cents|null, remaining|null, expires_at|null, label}
```

### Eventos

```text
publica:  membership.charge_due   {cycle_id, client_membership_id, client_id, club_name,
                                   amount_cents, due_date}
          membership.charge_paid  {cycle_id, client_membership_id, client_id, amount_cents,
                                   ticket_id, paid_at}
          membership.suspended    {client_membership_id, client_id, club_name, overdue_since}
          membership.cancelled    {client_membership_id, client_id, club_name, effective_date,
                                   reason_code}
          membership.price_changed {club_id, new_price_cents, effective_from, membership_ids}
                                   (reajuste `all_from`; aviso aos assinantes pela S12)
consome:  ticket.closed, ticket.voided
```

### `memberships/public.py`

```text
get_client_benefits(session, client_id, at) -> ClientBenefits                      (S11, S13)
check_eligibility(session, client_id, service_id, barber_id, unit_id, at) -> Eligibility (S11, S03)
list_offers(session, online_only=True) -> list[Offer]                              (S11)
list_cycles_for_commission(session, ended_before, exclude_ids) -> [...]            (S08, modo revenue_share)
client_ids_with_active(session, kind=None) -> set[UUID]   # kind: club|package     (S12 segmentação)
iter_report_facts(session, since)                                                  (S14)
```

### Banco de dados

Migration de tenant `tNNNN_memberships`:

```text
clubs              id uuid pk · name varchar(80) · description varchar(500) null ·
                   price_cents integer > 0 · terms varchar(2000) null · sellable_online bool ·
                   max_uses_per_day smallint null · max_uses_per_week smallint null ·
                   min_days_between_uses smallint null · allowed_weekdays smallint[] null ·
                   active · created_at · updated_at · UNIQUE INDEX ON lower(name)
club_benefits      id uuid pk · club_id CASCADE · kind club_benefit_kind ('included','discount') ·
                   target club_benefit_target ('service','product','all_services','all_products') ·
                   service_id → services RESTRICT null · product_id → products RESTRICT null ·
                   quantity_per_cycle smallint null · discount_percent numeric(5,2) null
                   CHECK (kind='included' → target='service' AND discount_percent IS NULL)
club_units         club_id CASCADE · unit_id → units RESTRICT · pk (club_id, unit_id)
club_barbers       club_id CASCADE · barber_id → barbers RESTRICT · pk (club_id, barber_id)

packages           id uuid pk · name varchar(80) · description null · price_cents > 0 ·
                   validity_days smallint (1..730) · sellable_online · active · timestamps
package_items      id uuid pk · package_id CASCADE · service_id RESTRICT · quantity smallint
                   UNIQUE (package_id, service_id)

client_memberships id uuid pk · client_id → clients RESTRICT · club_id → clubs RESTRICT ·
                   home_unit_id → units RESTRICT · status membership_status ('pending','active',
                   'past_due','suspended','cancelled') · price_cents · anchor_day smallint null ·
                   started_on date null · origin membership_origin ('front_desk')  (só balcão: a IA não cria adesão, PD-37, e o link
                   não vende clube/pacote; nova origem entra por migration expand quando houver venda online) · cancel_at date null · cancelled_at null ·
                   cancel_reason_code varchar(30) null · cancel_reason varchar(300) null ·
                   created_at · created_by null
                   UNIQUE INDEX uq_membership_client ON (client_id) WHERE status <> 'cancelled'
membership_cycles  id uuid pk · client_membership_id CASCADE · number smallint ·
                   start_date null · end_date null · due_date · amount_cents ·
                   charge_status cycle_charge_status ('pending','paid','waived','cancelled') ·
                   paid_at null · ticket_id → tickets RESTRICT null · ticket_item_id uuid null ·
                   waived_reason null · waived_by null · created_at
                   UNIQUE (client_membership_id, number) · INDEX (charge_status, due_date)

client_packages    id uuid pk · client_id RESTRICT · package_id RESTRICT · name varchar(80) ·
                   status client_package_status ('pending_payment','active','exhausted',
                   'expired','cancelled') · price_cents · validity_days · purchased_on null ·
                   expires_at date null · origin membership_origin · ticket_id null ·
                   ticket_item_id null · created_at · INDEX (client_id, status)
client_package_items id uuid pk · client_package_id CASCADE · service_id RESTRICT ·
                   name varchar(80) · quantity smallint · unit_value_cents integer

membership_usages  id uuid pk · source usage_source ('club','package') ·
                   client_membership_id null · membership_cycle_id null · client_package_id null ·
                   benefit_kind ticket_benefit_kind · service_id null · product_id null ·
                   barber_id → barbers RESTRICT null · unit_id → units RESTRICT ·
                   ticket_id → tickets RESTRICT · ticket_item_id uuid ·
                   list_price_cents · discount_cents · value_cents null ·
                   status usage_status ('reserved','consumed','reverted') · used_at · local_date
                   UNIQUE INDEX ON (ticket_item_id) WHERE status <> 'reverted'
                   INDEX (membership_cycle_id, status) · INDEX (client_package_id, status)

membership_settings id smallint pk check (id = 1) · grace_days smallint default 5 ·
                   block_when_past_due bool default false · pending_expiry_days smallint default 7
```

## Permissões

Nenhuma permissão nova.

| Ação | Permissão | owner | manager | receptionist | barber |
|---|---|---|---|---|---|
| ver clubes e pacotes (cadastro) | `catalog:read` | todos | todos | todos | todos |
| criar/editar clubes e pacotes | `catalog:write` + todas as unidades | sim | só se vê todas | — | — |
| ver adesões, pacotes do cliente, benefícios | `client:read` | all | unit (todos, P3) | unit (todos) | own (clientes que atendeu) |
| aderir, cancelar, vender pacote | `client:write` | all | unit | unit | — |
| ver cobranças; cobrar na comanda; aplicar benefício | `ticket:read` / `ticket:write` | all | unit | unit | — |
| isentar ciclo, prorrogar ou cancelar pacote, configurações | `finance:write` | all | unit | — | — |

## Acceptance Criteria

- [ ] Módulo `memberships` com layout completo; importa `identity`, `catalog`, `clients`, `sales`
      só pelo `public.py` (o recurso do plano vem do `identity.public`, S15).
- [ ] Teste por regra de uso: ilimitado, N por ciclo, por dia, por semana (virada de domingo),
      intervalo mínimo, dia da semana, unidade, barbeiro, desconto específico × geral.
- [ ] Concorrência: duas comandas aplicando o último uso ao mesmo tempo → uma recebe `409`.
- [ ] Ciclo: ancoragem no dia 31, geração antecipada, `past_due` → `suspended` → pago → `active`,
      isenção, cancelamento no fim do ciclo e imediato, desfazer cancelamento, pendente expirada.
- [ ] Pacote: venda e uso na mesma comanda (T5), vencimento primeiro, expiração, estorno da venda.
- [ ] Eventos consumidos idempotentes; eventos publicados no outbox.
- [ ] `402` sem o recurso do plano; consumo do que já existe continua.
- [ ] Cruzamento entre duas barbearias; escopos.
- [ ] Snapshots, `make docs-api`, `make check` verde, memória atualizada.

## Dependencies

- **S06** — `add_managed_item`, `remove_managed_item`, `apply_item_benefit` (com `value_cents`),
  `remove_item_benefit`, `open_ticket`, `get_ticket`; eventos `ticket.closed`/`ticket.voided`.
- **S05** — `get_service`, `get_product`, `allocate_combo_price` (rateio genérico).
- **S15** — `require_feature(PlanFeature.MEMBERSHIPS)`, dependência FastAPI do `identity.public`
  que responde `402` (`code: feature_not_in_plan`).
- **S00** — outbox, assinatura de eventos, tarefas diárias.
- **clients** — `get_client` (a acrescentar, mesma necessidade do S06).
- Oferece para **S11** (IA, só leitura: `list_offers`, `get_client_benefits`, PD-37), **S13** (ficha), **S08** (rateio), **S12**
  (automações: `charge_due`, `suspended`, `cancelled`), **S14**.

## Notes

- **Gateway (PD-10).** Com cobrança recorrente no cartão, o worker do ciclo passa a criar o
  pagamento no provedor e o webhook fecha uma comanda automática com o item da mensalidade; a
  máquina de estados do ciclo não muda.
- **Fidelidade/multa** por cancelamento antecipado, **pausa** (férias), **clube família** e
  **upgrade com pró-rata**: fora desta spec.
- **Lembrete de pacote vencendo** é tarefa do S12 lendo `client_packages.expires_at`; se preferirem
  evento, `package.expiring` entra aqui.

### Perguntas em aberto

✅ **Q-S07-1 — O que acontece quando a mensalidade vence sem pagamento?**
1. Bloqueia o uso no dia seguinte ao vencimento.
2. Tolerância configurável (padrão 5 dias) usando normalmente; depois bloqueia até pagar. Nunca
   cancela sozinho.
3. Só sinaliza "em atraso" na comanda e na agenda; nunca bloqueia.
4. Como 2, e cancela sozinho após N dias bloqueado.

Recomendação: **2** — é o equilíbrio do mercado (BestBarbers usa tolerância), e "nunca cancela
sozinho" segue o espírito de PD-07: a recepção decide.

> Resolvido em 2026-11-06: opção 2 — tolerância configurável (padrão 5 dias) usando normalmente,
> depois bloqueia o uso até pagar; nunca cancela sozinho (PD-36).

✅ **Q-S07-2 — Reajuste do preço do clube atinge quem já é assinante?**
1. Não: cada adesão guarda o preço da adesão; o novo preço vale para quem entrar depois.
2. Sim, a partir do próximo ciclo de todos.
3. O dono escolhe no momento do reajuste (só novos, ou todos a partir de uma data, com aviso).

Recomendação: **3**, com "só novos" pré-selecionado. Ao escolher "todos", S12 manda o aviso no
WhatsApp antes do próximo ciclo.

> Resolvido em 2026-11-06: opção 3 — o dono escolhe no reajuste se atinge quem já assina, com "só
> novos" pré-selecionado (ROADMAP §7).

✅ **Q-S07-3 — Como a IA vende clube e pacote sem gateway?**
1. Só informa (preço, regras) e convida a aderir no balcão; nada fica registrado.
2. Registra adesão/pacote **pendente** (`origin = ai`) e avisa que o pagamento é na próxima
   visita; a recepção vê "vendas da IA aguardando pagamento"; sem pagamento em 7 dias, cancela.
3. Faz handoff para humano fechar a venda.

Recomendação: **2** — a venda vira dado (PD-25 mede a IA por isso), e a recepção cobra na primeira
comanda do cliente.

> Resolvido em 2026-11-06: opção 3, contra a recomendação — a IA explica e registra o interesse na
> conversa e faz handoff (motivo `sale`); a equipe fecha a venda no painel. Saem `origin = ai`,
> `create_pending_membership`/`create_pending_package` e a lista "vendas da IA aguardando
> pagamento"; a medida da IA (PD-25) passa a ser "interesses encaminhados", na S11/S14 (PD-37).

✅ **Q-S07-4 — Pacote vencido com saldo?**
1. Perde o saldo; o dono pode prorrogar manualmente antes ou depois de vencer.
2. Nunca vence.
3. Vence, mas o saldo vira crédito em reais.

Recomendação: **1**. É o que dá sentido à validade (PD-09); a prorrogação manual cobre o cliente
fiel que viajou.

> Resolvido em 2026-11-06: opção 1 — pacote vencido perde o saldo; prorrogação manual possível
> (ROADMAP §7).
