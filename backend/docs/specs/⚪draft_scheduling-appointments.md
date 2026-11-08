# Agenda: disponibilidade e agendamentos

**Priority:** high
**Status:** draft
**Espelho no frontend:** `frontend/docs/specs/⚪draft_frontend-agenda.md`

## Overview

O coração do produto. Esta spec cria, no módulo `scheduling`, o **agendamento** (um cliente, um ou
mais serviços em sequência, cada um com seu barbeiro) e o **motor de disponibilidade** que a
recepção (painel), a IA do WhatsApp (S11) e o link público (S04) usam para achar horário livre. Cobre
o ciclo de vida inteiro — criar, remarcar, confirmar, "não confirmado", check-in, concluir, falta e
cancelar —, a garantia **no banco** de que um barbeiro nunca tem dois clientes no mesmo horário, as
funções públicas que os canais do cliente chamam e os eventos que alimentam lembrete, comanda,
comissão, ficha do cliente e relatórios.

Disponibilidade = tempo de trabalho efetivo do barbeiro (S02: jornada ∩ unidade − ausências) −
agendamentos que ocupam horário, recortado na grade de 15 min (PD-04) e nas políticas da barbearia
(S01).

## Decisões de produto já tomadas

| Código | Como vale aqui |
|---|---|
| PD-01 | Três origens: painel, IA no WhatsApp, link público (+ importação, PD-24) |
| PD-04 | Canais do cliente oferecem início em grade fixa de 15 min no fuso da unidade; o serviço ocupa a duração dele |
| PD-05 | Vários serviços em sequência, sem intervalo entre eles, com barbeiros iguais ou diferentes |
| PD-06 | Mostra **todos** os barbeiros livres; "qualquer um" → menos agendamentos no mês, depois menos no dia, depois ordem alfabética |
| PD-07 | Lembrete com Confirmar/Remarcar/Cancelar (S12); sem resposta até X h antes → **não confirmado** em destaque; **nunca cancela sozinho**; falta fica no histórico |
| PD-08 | Sem lista de espera e sem agendamento recorrente |
| PD-10 | Sem pagamento antecipado/sinal: nada de cobrança aqui |
| PD-18 | Cliente fora da janela de mudança → a IA passa para a recepção |
| PD-31 | Agendamento feito pelo cliente (IA/link) **nasce "agendado" e confirma pelo lembrete**; marcado já dentro do prazo do lembrete, nasce confirmado |
| PD-32 | Agendar para outra pessoa: campo **"para quem"** (`attendee_name`); o mesmo cliente pode ter horários simultâneos |
| DEC-016 P1 | Agendamento não se apaga: cancela. FKs para cliente, serviço, barbeiro e unidade com `RESTRICT` |

### Decisões técnicas desta spec

| # | Decisão |
|---|---|
| T1 | Um `appointment` (cliente, unidade, status) com N `appointment_items` (serviço + barbeiro + janela), até 5 itens. O status é do agendamento todo. |
| T2 | **Exclusion constraint** em `appointment_items`: `EXCLUDE USING gist (barber_id WITH =, tstzrange(starts_at, ends_at, '[)') WITH &&) WHERE (holds_slot)`, `DEFERRABLE INITIALLY IMMEDIATE`. Dois clientes no mesmo barbeiro e horário são impossíveis mesmo com duas requisições simultâneas; quem perde recebe `409`. Remarcação adia a checagem para o fim do comando (`SET CONSTRAINTS … DEFERRED` + `IMMEDIATE` antes de sair do service) para os itens do mesmo agendamento poderem trocar de lugar. |
| T3 | `holds_slot` (desnormalizado do status, atualizado na mesma transação) porque o `WHERE` de uma constraint só enxerga a própria linha: `false` em `cancelled` e `no_show`. |
| T4 | Extensão `btree_gist` criada por migration de **controle** (`CREATE EXTENSION IF NOT EXISTS btree_gist WITH SCHEMA public`, pelo migrator). A busca de opclass padrão não depende de `search_path`, e a checagem da constraint não exige `USAGE` do runtime no `public` — um teste prova isso com o role `navalha_app`. |
| T5 | Sem "segurar" horário enquanto o cliente decide (Booksy e Fresha também não seguram): a oferta é recalculada e o `409` vira "esse horário acabou de ser ocupado" + nova oferta. |
| T6 | Remarcar mantém o **mesmo id** (`reschedule_count`, evento com o horário anterior). Preço e duração do item que continua com o mesmo serviço mantêm o snapshot; serviço novo tira snapshot novo. |
| T7 | Painel pode marcar fora da grade (múltiplo de 5 min), no passado até 7 dias (lançar atendimento esquecido) e **fora da jornada/sobre bloqueio** com `allow_outside_hours = true` ("encaixe", como no Trinks). **Sobrepor outro agendamento do mesmo barbeiro, nunca** (T2). |
| T8 | Disponibilidade calculada sob demanda em Python (um dia = algumas dezenas de linhas); sem cache nesta fase. Se o p95 de `/availability` passar de 300 ms, entra cache Redis por `scheduling:avail:<schema>:<unit>:<date>` invalidado nas escritas. |
| T9 | A agenda do painel atualiza por polling (30 s, S03 frontend); sem SSE nesta fase. |

## Business Rules

### Criar

- [ ] Entrada: unidade, cliente, início, itens (`service_id` + `barber_id` ou `null` = qualquer
      barbeiro), observação (até 500), `attendee_name` ("para quem", até 120, opcional — PD-32),
      `confirmed` (só painel: "cliente já confirmou").
- [ ] Itens em sequência: item *n+1* começa no fim do item *n*; `ends_at` do agendamento = fim do
      último item. Duração de cada item = `duration_minutes` do serviço.
- [ ] Serviço ativo, barbeiro ativo, da **mesma unidade** do agendamento e habilitado para o serviço
      (`barber_services`); cliente ativo; unidade ativa. Violação → `400` com mensagem específica
      ("Diego não faz Barba", "Serviço inativo"…).
- [ ] `barber_id = null` resolve pela regra PD-06 entre os livres e habilitados na janela do item:
      menos itens não cancelados no **mês** (mês local da data do agendamento), depois no dia,
      depois `lower(name)`. Vários itens "qualquer um": prefere **um barbeiro só** que esteja livre
      para todos eles (mesma regra de equilíbrio); se nenhum estiver, resolve item a item.
- [ ] Sem `allow_outside_hours`, toda janela precisa caber no tempo de trabalho efetivo (S02) →
      senão `409` "Diego não atende nesse horário". Canais do cliente nunca têm essa opção.
- [ ] Mesmo barbeiro e horário ocupados → `409` "Esse horário acabou de ser ocupado. Escolha outro."
      (exclusion constraint, `23P01`).
- [ ] Mesmo cliente com outro agendamento ativo sobreposto → `409` "Este cliente já tem um
      agendamento nesse horário" — exceto quando um dos dois tem `attendee_name` (PD-32: o pai marca
      para os dois filhos no mesmo horário com barbeiros diferentes).
- [ ] Status inicial `scheduled`; `confirmed` quando o painel envia `confirmed = true` ou quando um
      canal do cliente marca dentro do prazo de confirmação (`starts_at − now <
      confirmation_deadline_hours`: não haveria tempo de confirmar). Fora desse caso, agendamento
      feito pelo cliente (IA/link) nasce `scheduled` e confirma pelo lembrete (PD-31); `confirmed_via`
      do que já nasce confirmado = canal de origem (`whatsapp` ou `booking_link`).
- [ ] Snapshot por item: `service_name`, `duration_minutes`, `price_cents` do momento.
- [ ] **Combo** (Q-S05-1): `combo_id` opcional. Só combo ativo e só de serviços
      (`catalog.public.get_combo(...).bookable`) → senão `400` "Este combo não pode ser agendado".
      Os serviços do combo viram os itens em sequência, na ordem do combo (`items` traz só o
      `barber_id` de cada posição, ou `null`); o `price_cents` de cada item é o rateio de
      `catalog.public.allocate_combo_price`; o agendamento guarda `combo_id`, `combo_name` e
      `combo_price_cents` (snapshot). A comanda aberta do agendamento agrupa os itens no combo (S06).
      Os canais do cliente oferecem os combos de `list_bookable_combos`.
- [ ] `Idempotency-Key` (header no painel, argumento nas funções públicas): repetir a chave devolve o
      agendamento já criado, sem duplicar (clique duplo, ferramenta da IA reexecutada).
- [ ] Publica `appointment.created`.

### Regras extras dos canais do cliente (IA e link)

- [ ] Início na grade de 15 min do fuso da unidade; `starts_at ≥ now + min_advance_minutes`; data
      ≤ hoje + `max_advance_days`; unidade com `online_booking`. Fora disso → `BookingWindowError`
      (`422` no link) com a mensagem para o cliente.
- [ ] O horário pedido precisa estar na oferta atual (`find_availability`); senão `409` como acima.
- [ ] Cliente só vê, remarca e cancela **os próprios** agendamentos (o canal passa o `client_id`
      autenticado: telefone do WhatsApp ou OTP do link).
- [ ] Remarcar/cancelar só até `starts_at − client_change_min_hours`; depois → `ChangeWindowClosed`
      ("Para mudar com menos de 2 h, fale com a recepção") e a IA faz o handoff (PD-18).
- [ ] Limite de agendamentos futuros por cliente nos canais do cliente (Q-S03-4):
      `max_future_appointments_per_client` de `shop_settings` (S01, padrão 3) conta os agendamentos
      ativos (`scheduled`, `confirmed`, `unconfirmed`, `checked_in`) com início no futuro; atingido →
      `FutureLimitReached` (`409` no link: "Você já tem 3 horários marcados. Para marcar mais, fale
      com a barbearia") e a IA oferece a recepção. O painel não tem limite.

### Remarcar e editar

- [ ] `reschedule`: novo início e, opcionalmente, nova lista de itens; mesmas validações da criação
      (ignorando o próprio agendamento na disponibilidade). Permitido em `scheduled`, `confirmed`,
      `unconfirmed`. Status volta a `scheduled` (painel pode mandar `confirmed = true`; cliente segue
      PD-31), `unconfirmed_reason` zera, `reschedule_count += 1`; S12 agenda novo lembrete pelo
      evento.
- [ ] Publica `appointment.rescheduled` com `previous_starts_at` e os barbeiros anteriores.
- [ ] `PATCH` muda só `notes`, `attendee_name` e `client_id` (corrigir cliente errado), nos mesmos
      status; não publica evento de horário.

### Ciclo de vida

| Ação | De | Para | Quando | Evento |
|---|---|---|---|---|
| confirmar | `scheduled`, `unconfirmed` | `confirmed` | antes do fim | `appointment.confirmed` |
| marcar não confirmado (S12) | `scheduled` | `unconfirmed` | `now ≥ starts_at − confirmation_deadline_hours` | `appointment.unconfirmed` |
| check-in | `scheduled`, `confirmed`, `unconfirmed` | `checked_in` | de 1 h antes até o fim do dia local | — |
| concluir | os três acima + `checked_in` | `completed` | `now ≥ starts_at` | `appointment.completed` |
| falta | `scheduled`, `confirmed`, `unconfirmed` | `no_show` | `now ≥ starts_at + late_tolerance_minutes` | `appointment.no_show` |
| desfazer falta | `no_show` | `confirmed` | até o fim do dia local seguinte; horário ainda livre | `appointment.no_show_reverted` |
| cancelar | os quatro ativos | `cancelled` | antes de concluir | `appointment.cancelled` |

- [ ] Transição fora da tabela → `409` "Não é possível <ação> um agendamento <status em português>".
- [ ] Cancelar guarda `cancelled_by_kind` (`staff`, `client`, `system`), `cancel_reason` (até 200) e
      libera o horário (`holds_slot = false`). **Nada cancela sozinho** (PD-07): `system` só existe
      para a importação desfazer o que importou.
- [ ] Confirmar guarda `confirmed_at` e `confirmed_via` (`staff`, `whatsapp`, `booking_link`).
- [ ] "Não confirmado" é marcado por `mark_unconfirmed(reason)`, chamado pelo job de prazo da S12
      (que é quem sabe se houve lembrete): `reason` = `no_response` ou `reminder_not_delivered`,
      guardado em `unconfirmed_reason`. Sem WhatsApp conectado, S12 não agenda nada e não existe
      "não confirmado". Idempotente: agendamento que já não está `scheduled` (confirmado, cancelado,
      remarcado para outro horário) → nada a fazer, sem erro.
- [ ] Agendamento passado ainda em `scheduled/confirmed/unconfirmed/checked_in` não muda sozinho; a
      agenda o mostra como "sem baixa" (flag `overdue`).
- [ ] Concluir pela comanda: `complete_appointment` (função pública, idempotente) chamada pela S06 na
      transação que fecha a comanda (S06 T8; `sales` está acima de `scheduling`, então é chamada
      direta, não evento). Já `completed` = nada a fazer. "Concluir" na agenda continua existindo
      para quem não usa comanda (Q-S03-2).

### Leitura e escopo

- [ ] `own` (barbeiro): vê e altera só agendamentos com algum item dele; cria só com ele mesmo em
      todos os itens ("qualquer um" resolve para ele). `unit`: unidades do usuário. Fora → `404`.
- [ ] Lista e agenda trazem o cliente (id, nome, telefone) lido por `clients.public`, não por
      snapshot: anonimização LGPD (S13) reflete na agenda.
- [ ] `flags` calculadas na leitura: `outside_hours`, `barber_inactive`, `unit_closed`, `overdue`.

## Data Contract

```text
# Agenda e agendamentos — módulo scheduling, tag "appointments"
GET  /agenda?unit_id=&from=&to=&barber_ids=&status=    (from/to datas, ≤ 7 dias)  → 200 AgendaOut
GET  /appointments?unit_id=&client_id=&barber_id=&status=&origin=&from=&to=&limit=50&offset=0
                                                       → 200 {items: AppointmentOut[], total}
     (from/to obrigatórios sem client_id; intervalo ≤ 366 dias; ordem starts_at)
GET  /appointments/{id}                                → 200 AppointmentOut | 404
POST /appointments        AppointmentIn  [Idempotency-Key] → 201 AppointmentOut | 400 | 403 | 409 | 422
PATCH /appointments/{id}  AppointmentUpdate            → 200 | 400 | 404 | 409
POST /appointments/{id}/reschedule  RescheduleIn       → 200 | 400 | 404 | 409 | 422
POST /appointments/{id}/confirm                        → 200 | 404 | 409
POST /appointments/{id}/check-in                       → 200 | 404 | 409
POST /appointments/{id}/complete                       → 200 | 404 | 409
POST /appointments/{id}/no-show                        → 200 | 404 | 409
POST /appointments/{id}/revert-no-show                 → 200 | 404 | 409
POST /appointments/{id}/cancel      {reason?}          → 200 | 403 | 404 | 409

# Disponibilidade (POST porque a consulta é uma lista estruturada de itens; não grava nada)
POST /availability        AvailabilityQuery            → 200 AvailabilityOut | 400 | 404
POST /availability/days   AvailabilityDaysQuery        → 200 {days: [{date, first_slot, slots_count}]}

AppointmentIn     {unit_id, client_id, starts_at, items: [{service_id, barber_id|null}] (1..5),
                   combo_id?, notes?, attendee_name?, confirmed? = false, allow_outside_hours? = false}
                   (com combo_id, items segue a ordem dos serviços do combo)
AppointmentUpdate {notes?, attendee_name?, client_id?}
RescheduleIn      {starts_at, items?, confirmed? = false, allow_outside_hours? = false}
AvailabilityQuery {unit_id, date, items: [{service_id, barber_id?}], exclude_appointment_id?}
AvailabilityDaysQuery {unit_id, from, to (≤ 62 dias), items}
AvailabilityOut   {date, timezone, slots: [{starts_at, ends_at,
                    items: [{service_id, starts_at, ends_at, barber_ids: uuid[],
                             suggested_barber_id}]}]}
                   (barber_ids na ordem PD-06; o painel recebe a grade de 15 min também)

AppointmentOut    {id, unit_id, status, origin, origin_ref, starts_at, ends_at,
                   client: {id, name, phone}, attendee_name,
                   combo: {id, name, price_cents} | null,
                   items: [{id, position, service_id, service_name, barber_id, barber_name,
                            starts_at, ends_at, duration_minutes, price_cents}],
                   total_price_cents, notes, confirmed_at, confirmed_via, checked_in_at,
                   completed_at, no_show_at, cancelled_at, cancelled_by_kind, cancel_reason,
                   unconfirmed_reason, reschedule_count, created_by_user_id, flags: str[],
                   created_at, updated_at}
AgendaOut         {unit: {id, name, timezone},
                   days: [{date, unit_intervals: [{starts_at, ends_at}], closed_reason}],
                   barbers: [{id, name, initials, active,
                              days: [{date, intervals, source, time_off: [{id, kind, starts_at, ends_at, reason}]}]}],
                   appointments: AppointmentOut[]}

Erros: {"detail": "<mensagem em português>"}.
```

### Funções públicas (`scheduling/public.py`) — S04, S06, S11, S12, S16

```text
AppointmentSource = panel | assistant | booking_link | import     (= coluna origin)
Actor             (de app.core.events, S00)
# `source` decide as regras: assistant/booking_link aplicam as "regras extras dos canais do cliente"
# (grade, antecedência, horizonte, janela de mudança) — não há flag separada para isso.

find_availability(session, *, unit_id, items: list[SlotItem(service_id, barber_id | None)],
                  date_from, date_to=None (≤ 7 dias), source, now,
                  exclude_appointment_id=None) -> list[AvailableSlot]
    AvailableSlot {starts_at, ends_at, items: [{service_id, starts_at, ends_at, barber_ids,
                   suggested_barber_id}]}
find_available_days(session, *, unit_id, items, date_from, date_to, source, now) -> list[DayAvailability]
create_appointment(session, *, unit_id, client_id, items, starts_at, source, actor, notes=None,
                   attendee_name=None, combo_id=None, origin_ref=None, confirmed=False, idempotency_key=None)
                   -> AppointmentView
reschedule_appointment(session, *, appointment_id, starts_at, items=None, source, actor,
                       client_id=None) -> AppointmentView
cancel_appointment(session, *, appointment_id, source, actor, client_id=None, reason=None)
                   -> AppointmentView
confirm_appointment(session, *, appointment_id, via, actor, client_id=None) -> AppointmentView
complete_appointment(session, *, appointment_id, actor) -> AppointmentView     # S06, idempotente
mark_unconfirmed(session, *, appointment_id, reason) -> None                     # S12, idempotente
get_appointment(session, appointment_id) -> AppointmentView | None
list_client_appointments(session, *, client_id, when: upcoming | past, limit=10) -> list[AppointmentView]
client_change_deadline(session, appointment_id) -> datetime       # "pode cancelar até…"
client_ids_with_future_appointment(session) -> set[UUID]          # S12 (não reativar quem já marcou)
client_ids_served(session, *, barber_id=None, service_id=None) -> set[UUID]   # S10 (escopo own), S12
Exceções: SlotUnavailable (Conflict), BookingWindowError (BadRequest), ChangeWindowClosed (Conflict),
          FutureLimitReached (Conflict), InvalidTransition (Conflict), NotYourAppointment (NotFound)
```

`client_ids_served` lê `appointment_items` concluídos; para listas grandes, a S13 mantém a
projeção `client_barber_stats` por evento — esta função é para uso pontual.

### Eventos publicados (S00)

Payload comum `AppointmentEvent`: `appointment_id, unit_id, client_id, status, origin, starts_at,
ends_at, items: [{service_id, barber_id, starts_at, ends_at, price_cents}]`, e o `actor` no
envelope. Sem nome ou telefone (S00).

| Evento | Extra no payload | Interessados (ROADMAP §3) |
|---|---|---|
| `appointment.created` | — | S12 (lembrete), S10 (confirmação), S13, S14 |
| `appointment.rescheduled` | `previous_starts_at`, `previous_barber_ids` | S12, S10, S14 |
| `appointment.cancelled` | `cancelled_by_kind`, `reason` | S12, S10, S13, S14 |
| `appointment.confirmed` / `.unconfirmed` | `confirmed_via` | painel, S14 |
| `appointment.completed` / `.no_show` | — | S13, S12 (avaliação), S14 |
| `appointment.no_show_reverted` | — | S13, S14 (**novo**, não está no ROADMAP) |

Nenhum evento consumido: a conclusão pela comanda é chamada direta (`complete_appointment`), e o
"não confirmado" é chamada direta da S12 (`mark_unconfirmed`).

### Banco de dados

Migration de **controle** `c000N_btree_gist` (T4) e de tenant `t000N_appointments` (expand):

```text
appointments       id uuid pk · unit_id → units.id RESTRICT · client_id → clients.id RESTRICT ·
                   status enum appointment_status(scheduled, confirmed, unconfirmed, checked_in,
                     completed, cancelled, no_show) ·
                   origin enum appointment_origin(panel, assistant, booking_link, import) ·
                   origin_ref uuid null (conversa S10 / sessão do link S04; sem FK) ·
                   starts_at timestamptz · ends_at timestamptz · check (ends_at > starts_at) ·
                   attendee_name varchar(120) null · notes varchar(500) null ·
                   combo_id → combos.id RESTRICT null · combo_name varchar(80) null ·
                   combo_price_cents integer null ·
                   idempotency_key varchar(80) null UNIQUE ·
                   confirmed_at · checked_in_at · completed_at · no_show_at ·
                   cancelled_at  (timestamptz null) ·
                   unconfirmed_reason enum unconfirmed_reason(no_response, reminder_not_delivered) null ·
                   confirmed_via enum confirmation_channel(staff, whatsapp, booking_link) null ·
                   cancelled_by_kind enum actor_kind(staff, client, system) null ·
                   cancel_reason varchar(200) null · reschedule_count smallint default 0 ·
                   created_by_user_id → users.id SET NULL null · created_at · updated_at
                   INDEX (unit_id, starts_at) · INDEX (client_id, starts_at)
appointment_items  id uuid pk · appointment_id → appointments.id CASCADE · position smallint
                   check (0..4) · service_id → services.id RESTRICT · barber_id → barbers.id RESTRICT ·
                   starts_at · ends_at · check (ends_at > starts_at) ·
                   service_name varchar(80) · duration_minutes smallint · price_cents integer ·
                   holds_slot bool not null default true
                   UNIQUE (appointment_id, position) · INDEX (barber_id, starts_at)
                   EXCLUDE USING gist (barber_id WITH =, tstzrange(starts_at, ends_at, '[)') WITH &&)
                     WHERE (holds_slot) DEFERRABLE INITIALLY IMMEDIATE
                     name ex_appointment_item_barber_time
```

O `RESTRICT` em `clients`, `services`, `barbers` e `units` é o que faz o `DELETE` desses cadastros
responder `409` (DEC-016 P1) sem código novo.

## Permissões

Nenhuma permissão nova.

| Rota | Permissão | owner | manager | receptionist | barber |
|---|---|---|---|---|---|
| `GET /agenda`, `/appointments*`, `POST /availability*` | `appointment:read` | todos | suas unidades | suas unidades | os seus |
| `POST /appointments` | `appointment:create` | sim | suas unidades | suas unidades | só com ele |
| `PATCH`, reschedule, confirm, check-in, complete, no-show, revert | `appointment:update` | sim | suas unidades | suas unidades | os seus (sem trocar de barbeiro) |
| `cancel` | `appointment:cancel` | sim | suas unidades | suas unidades | — |

## Acceptance Criteria

- [ ] Migrations aplicadas (controle e tenant); `alembic check` limpo; teste prova que o runtime
      (`navalha_app`, sem `USAGE` no `public`) insere item e recebe a violação da exclusion.
- [ ] **Concorrência**: duas sessões reservam o mesmo barbeiro e horário ao mesmo tempo
      (`asyncio.gather`, conexões distintas) → exatamente um `201` e um `409`; reservas encostadas
      (10:00–10:30 e 10:30–11:00) passam; cancelar libera o horário.
- [ ] Disponibilidade testada: grade 15 min no fuso da unidade, multi-serviço com barbeiros
      diferentes, "qualquer um" com desempate PD-06 (mês, dia, nome) e preferência por um barbeiro
      só, antecedência, horizonte, exceção da unidade, folga, bloqueio, item atravessando a pausa do
      almoço (não oferecido), `exclude_appointment_id` na remarcação.
- [ ] Ciclo de vida: cada linha da tabela de transições, os `409` das proibidas, janelas de tempo
      com relógio injetado; `mark_unconfirmed` e `complete_appointment` idempotentes (segunda
      chamada não muda nada nem publica de novo).
- [ ] Canais do cliente: grade, janela de mudança (`ChangeWindowClosed`), cliente alheio, idempotência.
- [ ] Eventos: cada ação publica o evento da tabela na mesma transação (rollback = sem evento).
- [ ] `tests/test_scheduling/`: escopos (gerente, recepção, barbeiro com item próprio e alheio) e
      **cruzamento entre duas barbearias** (agendamento, agenda e disponibilidade de A invisíveis em B).
- [ ] `clients` com escopo `own` passa a listar os clientes atendidos pelo barbeiro (ver
      Dependencies, S13).
- [ ] Snapshots, `make docs-api`, `make check` verde; `progress.md`, `issues.md`, DEC nova (T1–T9).

## Dependencies

- S00 — `publish` e `Actor` (só publica; não assina nem agenda nada).
- S01 — `get_unit_calendar`, `get_shop_settings` (antecedência, horizonte, prazo de confirmação,
  janela de mudança, tolerância, `max_future_appointments_per_client`), `online_booking`.
- S02 — `effective_intervals` (tempo de trabalho efetivo), no mesmo módulo.
- `catalog.public` — **acrescentar**: `get_services(session, ids)` e
  `barbers_for_services(session, service_ids) -> dict[service_id, set[barber_id]]`.
- `clients.public` — **acrescentar**: `get_clients(session, ids)`; `identity.public` — **acrescentar**:
  `list_barbers(session, unit_id, active_only)`.
- S06 (`sales`) — **oferecido**: `get_appointment` (abrir comanda do agendamento) e
  `complete_appointment` (fechar a comanda conclui, S06 T8).
- S12 (`automations`) — **assumido**: agenda o lembrete e o job de prazo ao receber
  `appointment.created/.rescheduled` (`schedule_job`, S00) e chama `mark_unconfirmed(reason)` no
  prazo; a resposta "Confirmar/Remarcar/Cancelar" chega por S10 e vira `confirm_appointment(via =
  whatsapp)` / `cancel_appointment(source = assistant)`. O prazo (`confirmation_deadline_hours`)
  é lido de `identity.public.get_shop_settings` (S01), não de uma configuração própria da S12.
- S13 (`clients`) — **assumido**: mantém por evento a relação cliente ↔ barbeiro atendido para o
  escopo `own` do `client:read` (o `clients` não pode importar `scheduling`).
- S10 (`messaging`) — **oferecido**: `client_ids_served(barber_id=…)` para o escopo `own` das conversas.
- S11, S04 e S16 — consumidores de `find_availability`, `create_appointment` (S16 com
  `source = import`), `reschedule_appointment`, `cancel_appointment`, `list_client_appointments`.

## Notes

- **Pai e filho no mesmo telefone** é comum em barbearia; por isso `attendee_name` (PD-32).
- **Sobreposição proposital** (barba enquanto a tinta age): fora — T2 proíbe sempre. Se o dono
  pedir, vira "serviço com tempo de pausa" no catálogo, não exceção da constraint.
- **Mês da agenda** e visão por semana são leitura do mesmo `/agenda`; relatório de ocupação é S14.

### Perguntas em aberto

- ✅ **Q-S03-1 — Agendamento feito pelo próprio cliente (IA/link) já nasce confirmado?**
  (a) Não: nasce "agendado" e a confirmação vem pelo lembrete; marcado dentro do prazo de
  confirmação já nasce confirmado. (b) Sim, sempre; o lembrete só lembra. (c) Configurável.
  **Recomendação: (a)** — a maioria dos agendamentos virá da IA; se nascerem confirmados, o
  "não confirmado" (PD-07) quase nunca aparece e perde o efeito contra falta.
  > Resolvido em 2026-11-06: (a) — nasce "agendado" e confirma pelo lembrete; marcado já dentro do
  > prazo do lembrete nasce confirmado (PD-31).
- ✅ **Q-S03-2 — Concluir: pela agenda ou pela comanda?** (a) Independentes: "Concluir" na agenda e
  comanda à parte. (b) Fechar a comanda conclui o agendamento sozinho, e "Concluir" na agenda
  continua para quem não usa comanda. (c) Só a comanda conclui. **Recomendação: (b)** — é o fluxo
  do Trinks/AppBarber (check-in → comanda → concluído) sem obrigar quem ainda não usa comanda. A
  spec da comanda (S06, T8) já foi escrita assumindo (b).
  > Resolvido em 2026-11-06: (b) — fechar a comanda conclui o agendamento; "Concluir" na agenda
  > continua existindo (ROADMAP §7).
- ✅ **Q-S03-3 — Duração (e preço) por barbeiro.** (a) Não: a duração do serviço vale para todos.
  (b) Duração própria por barbeiro (barbeiro mais lento). (c) Duração e preço por barbeiro (barbeiro
  "master" mais caro). **Recomendação: (a) agora** — entra depois como sobrescrita em
  `barber_services` sem mudar este contrato; (c) mexe em comissão e na IA.
  > Resolvido em 2026-11-06: (a) — sem duração ou preço por barbeiro agora (ROADMAP §7).
- ✅ **Q-S03-4 — Limite de agendamentos futuros por cliente na IA/link.** (a) Sem limite. (b) Um por
  vez. (c) Configurável, padrão 3. **Recomendação: (c)** — evita brincadeira/abuso pelo link sem
  travar o pai que marca para dois filhos; a equipe no painel não tem limite. Vira um campo em
  `shop_settings` (S01).
  > Resolvido em 2026-11-06: (c) — configurável, padrão 3, no campo
  > `max_future_appointments_per_client` de `shop_settings` (S01) (ROADMAP §7).
- ✅ **Q-S03-5 — Agendar para outra pessoa pelo mesmo telefone (filho).** (a) Não: cada pessoa com
  telefone próprio. (b) Campo "para quem" (`attendee_name`) e o mesmo cliente pode ter horários
  simultâneos com barbeiros diferentes. (c) Dependentes cadastrados na ficha do cliente (S13).
  **Recomendação: (b) agora** — resolve o caso comum sem cadastro novo; (c) pode vir com a ficha.
  > Resolvido em 2026-11-06: (b) — campo "para quem" (`attendee_name`); o mesmo cliente pode ter
  > horários simultâneos (PD-32).
- ✅ **Q-S03-6 — Intervalo entre atendimentos (limpeza).** (a) Nenhum: a grade de 15 min já sobra
  folga. (b) "Tempo extra depois" por serviço, que ocupa a agenda sem aparecer para o cliente.
  (c) Um intervalo fixo da barbearia. **Recomendação: (a) agora**, com (b) como evolução (é o
  "processing/buffer time" do Booksy e do Fresha).
  > Resolvido em 2026-11-06: (a) — sem intervalo entre atendimentos agora; "tempo extra" por
  > serviço é evolução (ROADMAP §7).
