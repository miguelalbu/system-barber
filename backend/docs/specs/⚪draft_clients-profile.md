# Ficha do cliente: histórico, indicadores, consentimento e LGPD

**Priority:** high
**Status:** draft
**Espelho no frontend:** `frontend/docs/specs/⚪draft_frontend-client-profile.md`

## Overview

Hoje o cliente é só um cadastro (nome, telefone, e-mail, nascimento, observações). Esta spec transforma
o cadastro em **ficha**: o histórico de atendimentos e compras, os indicadores que a recepção e o dono
olham antes de atender (última visita, frequência média, gasto total, ticket médio, faltas, barbeiro
preferido), **tags**, o **consentimento de comunicação** (opt-out, PD-20) e os pedidos da **LGPD**
(exportar os dados do cliente, anonimizar sem quebrar o financeiro). Também resolve o problema clássico
de quem migra de agenda de papel: **clientes duplicados**, com sugestão e mescla.

O módulo `clients` é "baixo" no grafo (DEC-006, ROADMAP §3): não importa `scheduling`, `sales` nem
`memberships`. Por isso histórico e indicadores são um **read model do próprio `clients`, alimentado
por eventos** (S00), e as operações que atravessam módulos (exportar, anonimizar, mesclar) usam
**inversão de dependência**: os módulos de cima registram no `clients.public` um *handler de dados
do cliente*, chamado na mesma transação.

Como referência: Trinks e AppBarber mostram "última visita / frequência / ticket médio" no topo da
ficha e a linha do tempo de atendimentos abaixo; Booksy e Fresha somam "faltas" e "gasto total"; a
mescla de duplicados (Fresha, Avec) mantém um cadastro e move o histórico do outro para ele.

## Decisões de produto já tomadas

| Parâmetro | Valor |
|---|---|
| PD-03 | Cliente é da barbearia, não da unidade; telefone E.164 único (DEC-016 P2/P3). |
| PD-07 | Faltas (no-show) ficam no histórico do cliente. |
| PD-20 | Toda mensagem **iniciada pela barbearia** respeita o opt-out do cliente. |
| PD-30 | **Consentimento de marketing** (reativação, aniversário, campanhas): pode receber quem tem **ao menos um atendimento**; importados e contatos sem atendimento só com "sim" explícito. Mensagens de utilidade (lembrete, confirmação) valem para todo cliente com agendamento. Opt-out sempre respeitado. |
| PD-41 | **Contato do cliente para o barbeiro**: configurável, **padrão oculto** (barbeiro vê nome, histórico e indicadores). |
| PD-01/PD-02 | O cliente se identifica pelo telefone (WhatsApp, link com OTP) — o telefone é a chave da mescla. |
| Convenções §2 | Dinheiro em centavos; tempo em UTC com "dia" no fuso da unidade; snapshot no histórico; escopo `all/unit/own`. |
| Fora | Notas técnicas por atendimento ("máquina 2 nas laterais") ficam no agendamento (S03); pontos/fidelidade; pedido de LGPD feito pelo próprio cliente pelo WhatsApp (a equipe executa pelo painel). |

## Business Rules

### Histórico (read model `client_visits`)

- [ ] Uma **visita** é um atendimento realizado ou uma compra. Chave: `appointment:<id>` quando há
      agendamento, senão `ticket:<id>` (venda avulsa). Comanda fechada de um agendamento e o
      `appointment.completed` do mesmo agendamento caem **na mesma visita** (upsert pela chave).
- [ ] Falta (`appointment.no_show`) e cancelamento (`appointment.cancelled`) também entram, com
      `status` próprio, para a linha do tempo e os contadores; não contam como visita.
- [ ] Cada linha guarda snapshot: data/hora, unidade, barbeiro(s), resumo dos itens (nomes) e valor
      líquido — mudar cadastro depois não reescreve o passado. Como o evento só traz ids (S00: payload
      sem nome nem texto), os nomes são resolvidos **na ingestão** por `catalog.public` (serviço,
      produto, combo) e `identity.public` (barbeiro), módulos abaixo do `clients` no grafo.
- [ ] `ticket.voided` zera o valor da visita vinda daquela comanda e, se a visita só existia pela
      comanda, marca `status = voided` (sai dos indicadores, fica na linha do tempo).
- [ ] Assinantes são idempotentes: evento repetido ou fora de ordem não duplica nem regride
      (upsert pela chave; campo `last_event_at` só avança).

### Indicadores (`client_stats`, `client_barber_stats`)

- [ ] Recalculados **a partir do `client_visits`** do cliente a cada evento aplicado (uma consulta
      agregada por cliente; nunca incremento cego), o que torna o recálculo idempotente.
- [ ] `first_visit_at`, `last_visit_at`, `visits_count` (visitas `completed`), `no_show_count`,
      `cancelled_count`, `total_spent_cents` (comandas + mensalidades de clube pagas),
      `tickets_count`, `avg_ticket_cents` = soma das comandas ÷ `tickets_count` (mensalidade fora),
      `avg_interval_days` = (última − primeira) ÷ (visitas − 1), só com 2+ visitas.
- [ ] **Barbeiro preferido**: o de mais visitas nos últimos 12 meses; empate → o mais recente.
      Visita com barbeiros em sequência (PD-05) conta para cada um.
- [ ] `client_barber_stats` ganha a linha já no `appointment.created` (visitas = 0): é ela que
      define o escopo `own` — o barbeiro vê os clientes que atendeu **ou tem agendados**. Isso
      completa a regra deixada em aberto pela DEC-016.
- [ ] **Valores só para quem vê dinheiro**: sem `finance:read`, `total_spent_cents`,
      `avg_ticket_cents` e `net_cents` das visitas saem `null`, e `sort=total_spent` é `403` — coerente
      com o mapa ("a recepção não vê faturamento"). Contagens (visitas, faltas) continuam visíveis.
- [ ] Comando de operador `python -m app.management.clients_stats --schema <s>` recalcula tudo do
      ledger (para backfill e depois de importação, S16).

### Tags

- [ ] Tag é cadastro da barbearia: `name` 1–30, único sem diferença de maiúsculas (`409`), `color`
      de uma paleta fixa (8 tokens). Até 20 tags por cliente (`422`).
- [ ] `PUT /clients/{id}/tags` substitui o conjunto. Apagar tag remove os vínculos (vínculo não é
      histórico).
- [ ] Lista de clientes filtra por tag (`tag_id`, várias = "tem todas").

### Comunicação e consentimento (PD-20, PD-30)

- [ ] Quatro registros, todos com data e origem: **opt-in de WhatsApp** (`whatsapp_opt_in_at` +
      `whatsapp_opt_in_source`: `inbound_message`, `booking_link`, `staff`, `import`, `keyword`),
      **consentimento explícito de marketing** — o "sim" da PD-30 (`marketing_consent_at` +
      `marketing_consent_source`: `booking_link`, `whatsapp`, `staff`) —, **opt-out de marketing**
      (`marketing_opt_out_at`) e **opt-out total** (`all_opt_out_at`).
- [ ] `get_contact_policy(client_id) -> ContactPolicy(opt_in, utility_allowed, marketing_allowed)` é a
      **única** pergunta que `automations` e `messaging` fazem antes de mensagem iniciada pela
      barbearia (PD-30):
      `utility_allowed` = o cliente **tem agendamento** (qualquer: há linha em `client_barber_stats`,
      criada no `appointment.created`, ou visita no ledger) e não tem opt-out total (lembrete,
      confirmação, aviso, avaliação);
      `marketing_allowed` = **sem opt-out algum** e (**ao menos um atendimento concluído no
      Navalha** — visita `completed` no `client_visits`; a visita-resumo `imported` da S16 (Q-S16-1)
      **não** conta, mesmo que entre em `visits_count` —, **ou** `marketing_consent_at` preenchido)
      (reativação, aniversário, campanha). Importado e contato do WhatsApp sem atendimento só recebem marketing com o "sim"
      explícito. `opt_in` = `whatsapp_opt_in_at` preenchido (informativo).
      Anonimizado ou lápide → tudo `False`.
- [ ] "Sim" explícito: `record_marketing_consent(session, client_id, source)` — caixa "Quero receber
      novidades e promoções" no link (S04), resposta "sim" a um convite no WhatsApp ou a recepção
      marca "cliente autorizou" (`staff`). Nunca vem da importação.
- [ ] **"SAIR"** pelo WhatsApp (detectado pelo `messaging`, Q-S12-2): grava na hora
      `record_opt_out(..., scope="marketing", source="whatsapp")` (padrão seguro) e o `messaging`
      responde com dois botões, **"Só promoções"** / **"Tudo"**; "Tudo" grava
      `record_opt_out(..., scope="all", source="whatsapp")`. **"VOLTAR"** chama
      `record_opt_in(..., source="keyword")`, que limpa `marketing_opt_out_at` e `all_opt_out_at`.
      Resposta a conversa aberta pelo cliente nunca é bloqueada (não é mensagem iniciada pela
      barbearia). Mensagem recebida do cliente registra opt-in `inbound_message` se ainda não houver
      (isso **não** é consentimento de marketing).
- [ ] Toda mudança grava `client_audit_log` (quem, quando, origem) — prova para a LGPD — e publica
      `client.opted_out {client_id, scope}` quando é opt-out (S12 cancela envios agendados).

### LGPD

- [ ] **Exportar**: `GET /clients/{id}/export` devolve um JSON com cadastro, tags, consentimentos,
      visitas e o que cada handler registrado contribuir (agendamentos, comandas, adesões, conversas).
      Grava `exported` no log.
- [ ] **Anonimizar**: irreversível. Nome → "Cliente anonimizado", telefone → marcador único
      `anon-<11 hex>` (libera o número real para um cadastro novo), e-mail/nascimento/observações →
      `null`, tags removidas, consentimentos `opted_out`, `anonymized_at` preenchido. Visitas e
      valores **ficam** (histórico financeiro intacto); só o texto livre delas é limpo.
- [ ] Antes de anonimizar, cada handler pode recusar (`409` com a mensagem dele): agendamento futuro
      ("Cancele os agendamentos futuros antes"), adesão de clube ativa etc. Depois, cada handler limpa
      o próprio dado pessoal (ex.: conversas apagam o conteúdo das mensagens; comanda troca o nome
      do snapshot). Tudo numa transação.
- [ ] Exige `confirm` igual ao telefone atual do cliente (dígitos) — evita anonimizar o cliente errado.

### Duplicados e mescla

- [ ] `GET /clients/duplicates` sugere pares com mesmo e-mail, ou mesmo nome normalizado (minúsculas,
      espaços colapsados) e mesma data de nascimento ou mesmo nome e telefones que diferem só no
      nono dígito. Até 50 pares, ignorando pares já descartados (`client_duplicate_dismissals`).
- [ ] `POST /clients/{id}/merge {source_id}`: o `{id}` (destino) fica; o `source` vira **lápide**
      (`merged_into_id = id`, `active = false`), mantém o telefone reservado e some das listas.
      `find_client_by_phone` segue a lápide até o destino — o WhatsApp do número antigo cai no
      cliente certo.
- [ ] Campos do destino vazios são preenchidos pelos da origem; tags somadas; consentimento fica o
      mais restritivo; `client_visits` e `client_barber_stats` movidos; indicadores recalculados.
- [ ] Cada handler re-aponta as próprias FKs (`appointments.client_id`, `tickets.client_id`,
      adesões, conversas) na mesma transação; conflito de regra deles → `409` e nada muda.
- [ ] Os dois cadastros são travados (`SELECT … FOR UPDATE`, em ordem de id). Mesclar consigo mesmo,
      com lápide ou com anonimizado → `400`.

## Data Contract

```text
# Ficha — módulo clients, tag "clients"
GET    /clients/{id}/profile                        → 200 ClientProfileOut | 404
GET    /clients/{id}/history?limit=20&before=       → 200 {items: VisitOut[], next_before} | 404
PUT    /clients/{id}/tags        {tag_ids[]}        → 200 TagOut[] | 400 | 404 | 422
PATCH  /clients/{id}/communication  CommunicationIn → 200 CommunicationOut | 404
GET    /clients/{id}/export                         → 200 application/json (anexo) | 403 | 404
POST   /clients/{id}/anonymize   {confirm}          → 200 ClientOut | 400 | 403 | 404 | 409
GET    /clients/duplicates?limit=50                 → 200 DuplicatePairOut[]
POST   /clients/duplicates/dismiss {a_id, b_id}     → 204
POST   /clients/{id}/merge       {source_id}        → 200 ClientProfileOut | 400 | 403 | 404 | 409

# Tags
GET    /client-tags                                 → 200 TagOut[] (com clients_count)
POST   /client-tags              {name, color}      → 201 TagOut | 409 | 422
PATCH  /client-tags/{id}         {name?, color?}    → 200 TagOut | 404 | 409
DELETE /client-tags/{id}                            → 204 | 404

# Mudança aditiva em rota existente
GET    /clients  + ?tag_id=…&sort=name|last_visit|total_spent|visits&order=asc|desc
                 + ?last_visit_before=YYYY-MM-DD  (inativos)
ClientOut + {tag_ids[], last_visit_at, visits_count, anonymized_at}   (lápides nunca aparecem)

ClientProfileOut  {client: ClientOut, stats: StatsOut, tags: TagOut[], communication: CommunicationOut,
                   preferred_barber: {id, name} | null}
StatsOut          {first_visit_at, last_visit_at, days_since_last_visit, visits_count, no_show_count,
                   cancelled_count, total_spent_cents, avg_ticket_cents, avg_interval_days,
                   expected_return_on (last + intervalo, data local) }
VisitOut          {key, occurred_at, local_date, unit_id, status: completed|no_show|cancelled|voided,
                   barbers: [{id, name}], items: [{kind: service|product|combo|package|membership,
                   name}], net_cents, appointment_id, ticket_id}
CommunicationIn   {whatsapp_opt_in?: bool, marketing_consent?: bool, marketing_opt_out?: bool,
                   all_opt_out?: bool}
                  (mudança pelo painel grava origem `staff`)
CommunicationOut  {whatsapp_opt_in_at, whatsapp_opt_in_source, marketing_consent_at,
                   marketing_consent_source, marketing_opt_out_at, all_opt_out_at,
                   utility_allowed, marketing_allowed}
ClientOut (barbeiro) phone e email mascarados (`(11) 9••••-4321`, `j•••@gmail.com`) quando
                  `shop_settings.barber_sees_client_contact = false` (padrão, PD-41)
TagOut            {id, name, color, clients_count}
DuplicatePairOut  {a: ClientOut, b: ClientOut, reason: same_email|same_name_birth|similar_phone}

Erros: {"detail": "<mensagem em português>"}. Barbeiro (own) recebe 404 para cliente fora do escopo.
```

### Banco de dados

Migration de tenant (próxima revisão `tNNNN_client_profile`, só expand):

```text
clients                  + merged_into_id uuid null → clients.id ON DELETE RESTRICT
                         + anonymized_at timestamptz null
                         + whatsapp_opt_in_at timestamptz null · whatsapp_opt_in_source varchar(20) null
                         + marketing_consent_at timestamptz null · marketing_consent_source varchar(20) null
                         + marketing_opt_out_at timestamptz null · all_opt_out_at timestamptz null
                         INDEX (merged_into_id) · CHECK (merged_into_id <> id)

client_visits            id uuid pk · client_id → clients.id ON DELETE RESTRICT ·
                         visit_key varchar(60) UNIQUE · appointment_id uuid null · ticket_id uuid null ·
                         unit_id uuid · occurred_at timestamptz · local_date date ·
                         status varchar(12) CHECK in (completed, no_show, cancelled, voided) ·
                         barber_ids uuid[] · summary jsonb (itens, nomes dos barbeiros) ·
                         net_cents integer default 0 · last_event_at timestamptz · created_at · updated_at
                         INDEX (client_id, occurred_at desc)
                         (ids de agendamento/comanda sem FK: o dono deles é outro módulo, mais alto)

client_stats             client_id uuid pk → clients.id ON DELETE CASCADE · first_visit_at · last_visit_at ·
                         visits_count int · no_show_count int · cancelled_count int ·
                         last_visit_unit_id uuid null ·
                         total_spent_cents bigint · tickets_count int · avg_ticket_cents int null ·
                         avg_interval_days numeric(6,1) null · preferred_barber_id uuid null · updated_at
                         INDEX (last_visit_at)   (cascata: estatística é derivada, não histórico)

client_barber_stats      (client_id, barber_id) pk · visits int · last_visit_at null · first_seen_at
                         INDEX (barber_id)

client_tags              id uuid pk · name varchar(30) · color varchar(20) · created_at
                         UNIQUE INDEX on lower(name)
client_tag_links         (client_id → clients CASCADE, tag_id → client_tags CASCADE) pk · INDEX (tag_id)

client_audit_log         id uuid pk · client_id uuid (sem FK: sobrevive à mescla) ·
                         action varchar(30) (consent_changed, exported, anonymized, merged_into,
                         merged_from) · actor_user_id uuid null · source varchar(20)
                         (panel, whatsapp, keyword, booking, import, system) · details jsonb (sem dado pessoal) ·
                         created_at · INDEX (client_id, created_at)

client_duplicate_dismissals (a_id, b_id) pk, a_id < b_id · created_at
```

### Eventos consumidos (S00)

| Evento | O que faz |
|---|---|
| `appointment.created` / `.rescheduled` | garante `client_barber_stats` (escopo `own`) |
| `appointment.completed` | upsert da visita `completed`; recalcula |
| `appointment.no_show` / `.cancelled` | upsert da visita com o status; recalcula |
| `appointment.no_show_reverted` (novo na S03) | volta a visita para `scheduled`/fora dos contadores; recalcula |
| `ticket.closed` | upsert da visita (chave do agendamento, ou da comanda); valor e itens |
| `ticket.voided` | zera o valor; `voided` se a visita só existia pela comanda |
| `membership.charge_paid` | soma em `total_spent_cents` (linha `membership` no ledger, chave `charge:<id>`) |

Assinatura no formato da S00: `SUBSCRIBERS = [Subscriber(name="clients.apply_visit", events=[…],
handler=…)]` no `clients/public.py`.

Publica (já previsto no ROADMAP): `client.created` (com `source`: `panel`, `whatsapp`, `booking`,
`import`), `client.updated` — e passa a publicar `client.merged {target_id, source_id}`,
`client.anonymized {client_id}` e `client.opted_out {client_id, scope}`.

### `clients.public` (oferecido)

```text
find_client_by_phone(session, phone) -> ClientRef | None          # segue a lápide; ÚNICA busca por telefone
create_client(..., source)                                         # já existe; ganha source
get_client(session, id) / get_clients(session, ids) -> ClientRef  # nome, telefone, anonimizado (S03, S06)
update_client_name(session, client_id, name)                       # IA corrige nome vindo do WhatsApp (S11)
get_contact_policy(session, client_id) -> ContactPolicy(opt_in, utility_allowed, marketing_allowed)
record_opt_in(session, client_id, source)                          # VOLTAR (`keyword`) limpa os opt-outs
record_marketing_consent(session, client_id, source)               # "sim" explícito (PD-30): S04, S10, painel
record_opt_out(session, client_id, scope: "marketing" | "all", source)
query_audience(session, filter: AudienceFilter) -> AsyncIterator[UUID]   # S12, sobre client_stats
  AudienceFilter {unit_id?, last_visit_from?, last_visit_to?, no_visit_days?, min_visits?,
                  max_visits?, first_visit_from?, first_visit_to?, tag_ids?, birthday_md?,
                  served_by_barber_id?, used_service_id?, purpose: utility | marketing}
  # devolve só quem pode receber pelo propósito (get_contact_policy); filtros pedidos pela S12
client_ids_served_by(session, barber_id) -> set[UUID]              # escopo own (S03, S10)
get_client_summary(session, client_id) -> ClientSummary   # nome, tags, stats, observações: IA (S11)
register_client_data_handler(handler: ClientDataHandler) -> None
  ClientDataHandler (Protocol): name; export(session, client_id) -> dict;
    check_anonymize(session, client_id) -> None (levanta Conflict); anonymize(session, client_id);
    merge(session, source_id, target_id) -> None
```

## Permissões

Uma permissão nova, `client:manage` — exportar, anonimizar e mesclar são ações **irreversíveis ou
de dado pessoal em massa**; `client:write` é da recepção (cadastra no balcão) e `tenant:configure` é
configuração da barbearia, não pedido de titular. Entra no enum, no mapa e no `PERMISSIONS_MAP.md`.

| Rota / ação | Permissão | owner | manager | receptionist | barber |
|---|---|---|---|---|---|
| ficha, histórico, `GET /client-tags` | `client:read` | todos | todos (P3) | todos | os que atendeu/tem agendados |
| tags no cliente, comunicação, CRUD de tags | `client:write` | sim | sim | sim | — |
| duplicados (ver, descartar) | `client:write` | sim | sim | sim | — |
| exportar, anonimizar, mesclar | `client:manage` (nova) | all | unit (= todos, P3) | — | — |

**Contato para o barbeiro (PD-41):** com `shop_settings.barber_sees_client_contact = false` (padrão;
o campo mora no `shop_settings` do `identity`, S01, lido por `identity.public.get_shop_settings()`),
quem tem só escopo `own` em `client:read` recebe telefone e e-mail **mascarados** em toda rota de
cliente (lista e ficha); vê nome, histórico, tags,
observações e indicadores. Ligado → vê o contato completo. Owner, manager e recepção sempre veem.

## Acceptance Criteria

- [ ] Migration aplicada (`make migrate`), `alembic check` limpo; `client:manage` no mapa e no doc.
- [ ] Assinantes registrados no worker (S00) e testados com evento repetido e fora de ordem.
- [ ] `tests/test_clients/`: um teste por regra; cruzamento entre duas barbearias (ficha, tags,
      mescla e exportação de A invisíveis em B); escopo `own` com e sem agendamento.
- [ ] Mescla testada com um handler falso que re-aponta e um que recusa (rollback total).
- [ ] Anonimização: o telefone real fica livre para novo cadastro; visitas e valores permanecem.
- [ ] `get_contact_policy` testado (PD-30): cliente com só agendamento futuro → utilidade sim,
      marketing não; com um atendimento → marketing sim; importado sem atendimento → marketing só
      depois de `record_marketing_consent`; opt-out `marketing` mantém utilidade; `all` bloqueia
      tudo; VOLTAR limpa os dois.
- [ ] Barbeiro (`own`) recebe contato mascarado com `barber_sees_client_contact = false` e completo com
      `true` (PD-41).
- [ ] Snapshots (`openapi.json`, `routes.json`, `db_schema.json`) com o diff lido; `make docs-api`.
- [ ] Testes em `tests/test_clients/` cobrindo as regras acima
- [ ] Snapshots de contrato revisados (`UPDATE_CONTRACT_SNAPSHOTS=1` só se a mudança for intencional)

## Dependencies

- **S00** (`platform-events-jobs`): `publish(session, type, payload, *, aggregate_id, actor)` e
  `SUBSCRIBERS`/`Subscriber` no `public.py`; envelope com `occurred_at`; entrega pelo menos uma vez.
- **S03** (`scheduling`) publica `appointment.*` com o `AppointmentEvent` dela (`appointment_id,
  unit_id, client_id, status, origin, starts_at, ends_at, items: [{service_id, barber_id,
  starts_at, ends_at, price_cents}]`) e `appointment.no_show_reverted`; registra
  `ClientDataHandler` (re-apontar, recusar anonimizar com agendamento futuro, limpar notas).
- **S06** (`sales`) publica `ticket.closed` (`ticket_id, unit_id, client_id, appointment_id,
  closed_at, total_cents, items: [{item_id, kind, service_id, product_id, combo_id, barber_id,
  net_cents}]`) e `ticket.voided` (`ticket_id, was_closed, item_ids`); registra handler.
- **S07** (`memberships`) publica `membership.charge_paid {cycle_id, client_membership_id,
  client_id, amount_cents, …}` (chave da visita-ledger: `charge:<cycle_id>`); handler recusa
  anonimizar com adesão ativa.
- **S10** (`messaging`) usa `find_client_by_phone` (não busca por telefone por conta própria — a
  lápide da mescla depende disso), `record_opt_in`, `record_opt_out(scope, source)` e
  `record_marketing_consent`, e consome `client.anonymized`. **S04** grava `record_opt_in`
  (`booking_link`) e, com a caixa marcada, `record_marketing_consent` (`booking_link`).
- **S01** (`identity`): `get_shop_settings()` com o campo novo `barber_sees_client_contact bool
  default false` (PD-41) — **a acrescentar na S01**.
  **S12** usa `get_contact_policy`, `query_audience` e consome `client.opted_out`.
- Oferece a `reports` (S14) e `imports` (S16): `client_stats` via `get_client_summary` e o comando
  de recálculo.

## Notes

- **Por que read model e não consulta ao `scheduling`/`sales`?** `clients` está abaixo deles no
  grafo; importar para cima cria ciclo. O ledger também deixa a ficha abrir com uma consulta só.
- O telefone de lápide fica reservado para sempre; "desfazer mescla" não existe (o histórico já foi
  movido). Se pedirem, é cadastro novo.
- `avg_interval_days` ignora visitas no mesmo dia (cortou e voltou para barba): conta dias distintos.
- Busca com acento continua no ISS-020; a detecção de duplicados usa a mesma normalização.

### Perguntas em aberto

- ✅ **Q-S13-1 — Consentimento de marketing do cliente que nunca disse nada.** É a mesma decisão da
  Q-S12-1 (automações); responder uma vez só, que vale para as duas specs.
  (a) opt-out: todo cliente pode receber reativação/aniversário/campanha até pedir para sair;
  (b) opt-in estrito: só quem marcou "aceito receber" (link, IA ou balcão);
  (c) relação existente: permitido para quem já teve **ao menos uma visita**; importado sem visita e
  lead do WhatsApp sem atendimento só com opt-in.
  **Recomendação: (c)** — é o "interesse legítimo" da LGPD para cliente da casa, mantém o alcance das
  automações e reduz risco de denúncia na Meta (que pune envio a quem não conhece a empresa). Toda
  mensagem de marketing leva "Responda SAIR para não receber".
  > Resolvido em 2026-11-06: (c) — marketing para quem tem ao menos um atendimento; importados e
  > contatos sem atendimento só com "sim" explícito (`marketing_consent_at`); utilidade para todo
  > cliente com agendamento; opt-out sempre respeitado. "SAIR" pergunta "Só promoções" / "Tudo"
  > (Q-S12-2) (PD-30).
- ✅ **Q-S13-2 — O barbeiro vê o telefone e o e-mail do cliente?**
  (a) sim, ficha completa; (b) não: nome, histórico e indicadores, contato mascarado
  (`(11) 9••••-4321`); (c) configurável pela barbearia, padrão mascarado.
  **Recomendação: (c)** — o medo de o barbeiro "levar a clientela" é real no mercado, mas há casas em
  que o barbeiro confirma pelo próprio WhatsApp.
  > Resolvido em 2026-11-06: (c) — configuração `barber_sees_client_contact` no `shop_settings`,
  > padrão oculto: o barbeiro vê nome, histórico e indicadores, com o contato mascarado (PD-41).
- ✅ **Q-S13-3 — Quem mescla duplicados?**
  (a) só dono/gerente (`client:manage`); (b) também a recepção, que é quem mais encontra duplicado.
  **Recomendação: (a)** no lançamento — a mescla é irreversível; a recepção vê a sugestão e avisa.
  > Resolvido em 2026-11-06: (a) — só dono e gerente mesclam (`client:manage`) (ROADMAP §7).
