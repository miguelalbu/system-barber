# Automações, avaliações e campanhas no WhatsApp (S12)

**Priority:** high
**Status:** draft
**Espelho no frontend:** `frontend/docs/specs/⚪draft_frontend-automations.md`

## Overview

Tudo o que a **barbearia inicia** no WhatsApp: aviso de agendamento feito/alterado pela equipe,
**lembrete com Confirmar/Remarcar/Cancelar** e o prazo de "não confirmado" (PD-07), **reativação**
de cliente sumido, **aniversário**, **avaliação pós-atendimento** e **campanhas manuais** para um
público filtrado. Como são mensagens fora da conversa iniciada pelo cliente, todas usam **modelo
aprovado pela Meta**, respeitam **opt-in/opt-out** (LGPD e política da Meta), **horário de silêncio**
e **limite de frequência**, e mostram **custo estimado**. O módulo `automations` decide **quem** recebe
**o quê** e **quando**; o envio é do `messaging` (S10) e o agendamento das tarefas é do worker (S00).

Fica de fora: a conversa que segue depois do toque num botão (é da IA, S11, ou da equipe), cupom de
desconto aplicado na comanda, e-mail/SMS, teste A/B de campanha.

## Decisões de produto já tomadas

| Parâmetro | Valor |
|---|---|
| PD-07 | Lembrete com **Confirmar/Remarcar/Cancelar**; sem resposta até X horas antes (configurável) → **"não confirmado"** em destaque para a recepção. **Nunca cancela sozinho.** |
| PD-20 | Lembrete com confirmação, **reativação** (padrão **40 dias**, ajustável), **aniversário**, **avaliação** (nota 1–5; link do Google para todos que responderam, nota baixa → alerta ao dono — PD-27) e **campanhas manuais** com template aprovado. Toda mensagem iniciada pela barbearia respeita o opt-out. |
| PD-27 | Avaliação: o **link do Google vai para todos que responderam**, qualquer nota; nota baixa continua gerando alerta ao dono. Substitui o "só nota alta" da PD-20 (*review gating*, proibido pelo Google). |
| PD-30 | **Consentimento de marketing** (reativação, aniversário, campanhas): pode receber quem tem **ao menos um atendimento**; importados e contatos sem atendimento só com "sim" explícito. Utilidade (aviso, lembrete, avaliação) vale para todo cliente com agendamento. Opt-out sempre respeitado. |
| PD-18 | Alerta sem push: aparece no painel. |
| PD-10 | Sem pagamento: campanha não vende com link de pagamento. |

### Decisões técnicas desta spec (propostas, revisar na aprovação)

| # | Decisão | Por quê |
|---|---|---|
| T1 | Toda mensagem automática vira uma linha em `automation_dispatches` com `dedupe_key` UNIQUE (`reminder:<appointment_id>:<start_at>`, `birthday:<client_id>:<ano>`, `reactivation:<client_id>:<data da última visita>`, `review:<appointment_id>`, `campaign:<id>:<client_id>`). | Worker e eventos entregam "pelo menos uma vez" (S00); a chave garante "no máximo um envio". |
| T2 | Tarefas com hora marcada são **agendadas por evento** (`appointment.created` → job no horário do lembrete) e **revalidam o estado ao rodar** (agendamento existe, mesmo horário, não cancelado, cliente sem opt-out). Remarcar muda a `dedupe_key`; o job velho encontra horário diferente e se descarta. | Hora exata sem varrer a agenda a cada minuto. |
| T3 | Reativação e aniversário rodam numa **tarefa por hora por barbearia** que só age na hora configurada (padrão 10:00) no fuso da unidade da última visita do cliente (ou da primeira unidade). | Um fuso por cliente sem cron por cliente. |
| T4 | Custo estimado = categoria do modelo × preço por mensagem da Meta para o Brasil (configuração da plataforma: `WHATSAPP_PRICE_MARKETING_USD`, `_UTILITY_USD`, `_AUTHENTICATION_USD`) × `USD_BRL_RATE`, guardado em centavos BRL no envio. Sempre rotulado "estimativa". | A conta real é da Meta (Q-S10-1); a barbearia precisa de ordem de grandeza antes de mandar campanha. |

## Business Rules

### Regras comuns a toda mensagem iniciada pela barbearia

- [ ] Recurso no plano (S15, `identity.public.require_feature`/`has_feature`): aviso de agendamento e
      lembrete só exigem `whatsapp`; reativação, aniversário e avaliação exigem `automations`;
      campanhas exigem `campaigns` e consomem a cota `campaign_messages_per_month` pelo tamanho do
      público ao agendar (`quota_status` na prévia, `consume_quota(amount = n)` no agendamento; sem
      cota → 402 `plan_limit_reached`). Sem número conectado → nada é enviado e o `dispatch` fica
      `skipped` (`no_whatsapp`).
- [ ] Antes de enviar: `clients.public.get_contact_policy(client_id)` (lê `utility_allowed` ou `marketing_allowed` conforme o propósito) (`utility` para aviso,
      lembrete e avaliação; `marketing` para o resto) — negado → `skipped` com o motivo. Regra
      (PD-30, dona é a S13): **utilidade** para todo cliente com agendamento e sem opt-out total;
      **marketing** só para quem tem ao menos um atendimento concluído ou o "sim" explícito
      (`marketing_consent_at`), e sem opt-out algum — importado e contato do WhatsApp sem
      atendimento ficam `skipped` (`no_consent`) até dizer "sim". Opt-out conforme o escopo gravado
      (`marketing` ou `all`, Q-S12-2). Cliente inativo → `skipped`.
- [ ] **Horário de silêncio** (padrão 20:00–09:00 no fuso da unidade, configurável, mínimo 8 h):
      marketing nunca sai dentro dele (espera a abertura); lembrete que cairia dentro dele é
      **antecipado** para o último horário permitido antes (nunca atrasado).
- [ ] **Frequência** (só marketing: reativação, aniversário, campanha): no máximo
      `marketing_max_per_7d` (padrão 2) e `marketing_max_per_30d` (padrão 4) por cliente; excedeu →
      `skipped` (`frequency_cap`). Utilidade (lembrete, aviso, avaliação) não conta nem é barrada.
- [ ] Erro da Meta de limite por usuário (marketing) ou de "usuário parou marketing" → `skipped` com
      o motivo, sem retry; o segundo caso grava o opt-out de marketing
      (`clients.public.record_opt_out(scope="marketing", source="whatsapp")`).
- [ ] Toda mensagem automática usa o modelo da `purpose` correspondente com status `approved`;
      enquanto não houver um aprovado, a automação fica "Aguardando aprovação do modelo" e nada sai.
- [ ] Variáveis preenchidas dos dados reais (primeiro nome do cliente, serviço, barbeiro, data/hora
      no fuso da unidade, nome da barbearia, unidade). Nunca texto livre da IA dentro de um modelo.

### Aviso de agendamento feito pela equipe

- [ ] `appointment.created`/`.rescheduled`/`.cancelled` com `source = panel` → aviso `utility`
      (ligado por padrão, desligável). Agendamento feito pelo próprio cliente (IA ou link) não recebe
      aviso — ele já viu a confirmação no canal que usou.
- [ ] Criado pela equipe **dentro** da antecedência do lembrete → o aviso já sai no formato do
      lembrete (com os três botões), e não há lembrete separado.

### Lembrete e confirmação (PD-07)

- [ ] Configuração: `hours_before` (padrão 24; 2–72), que precisa ser maior que o
      `confirmation_deadline_hours` da barbearia (S01, `shop_settings`, padrão 3 — o prazo é dela, não
      daqui). Lembrete sai `hours_before` antes do início. Lembrete aceito pela Meta (`sent`) →
      `scheduling.public.record_reminder_sent(appointment_id, at)`.
- [ ] Modelo `appointment_reminder` com botões de resposta rápida: **Confirmar**, **Remarcar**,
      **Cancelar** (payloads `auto:confirm:<dispatch_id>`, `auto:reschedule:<id>`, `auto:cancel:<id>`).
- [ ] Toque em **Confirmar** → `scheduling.public.confirm_appointment(via = "whatsapp", actor =
      Actor.client, client_id)` e
      resposta "Confirmado! Te esperamos <dia> às <hora>." Já cancelado/remarcado → resposta
      explicando e nada muda.
- [ ] **Cancelar** → pergunta de confirmação com botões "Sim, cancelar"/"Não" (`auto:cancel_yes:<id>`);
      no "sim", `scheduling.public.cancel_appointment(channel = "assistant", client_id)`; fora da janela
      de mudança (`ChangeWindowClosed`) → explica e leva a conversa para `waiting_human`
      (`reschedule_request`).
- [ ] **Remarcar** → com a IA ativa (`assistant.public.is_active`), `assistant.public.start_flow`
      (a IA oferece horários); sem IA → resposta "Certo! Alguém da equipe já te chama para remarcar" e
      `waiting_human` (`reschedule_request`).
- [ ] Texto livre em vez de botão fica com a IA (ela tem `confirm_appointment`) ou com a equipe.
- [ ] Prazo: **é do `scheduling`** (tarefa `scheduling.mark_unconfirmed`, S03), que marca
      "não confirmado" só quem tem `reminder_sent_at`. Por isso este módulo só chama
      `record_reminder_sent` quando a Meta aceitou o envio; lembrete pulado ou com falha não grava, e o
      agendamento fica "agendado" (ver Notes). **Nunca cancela** (PD-07).
- [ ] Agendamento criado depois do horário do lembrete e antes do prazo: lembrete sai na hora (se o
      horário de silêncio permitir). Criado depois do prazo: sem lembrete e sem "não confirmado".

### Reativação (PD-20)

- [ ] Cliente com ao menos 1 atendimento concluído, última visita há `inactive_days` (padrão 40;
      15–365) ou mais, sem agendamento futuro → um envio do modelo `reactivation` por episódio de
      inatividade (a chave usa a data da última visita: só volta a valer depois de uma nova visita).
- [ ] Até `max_per_run` (padrão 50) por dia, os mais antigos primeiro, para não estourar limite de
      envio da Meta nem a agenda da semana.
- [ ] Resposta do cliente é conversa normal (IA ou equipe); agendou em até 14 dias → conta como
      reativado (métrica).

### Aniversário (PD-20)

- [ ] Clientes com `birth_date` no dia (29/02 vira 28/02 em ano não bissexto), enviado na hora
      configurada; `days_before` opcional (0–7, padrão 0). Um por ano.
- [ ] O texto do presente/condição faz parte do modelo (aprovado pela Meta); mudar o texto envia
      versão nova do modelo.

### Avaliação pós-atendimento (PD-20)

- [ ] `appointment.completed` → envio do modelo `review_request` `delay_minutes` depois (padrão 120;
      30–1440), respeitando o horário de silêncio (adia para a abertura; passou de 24 h, desiste).
      No máximo uma pesquisa por cliente a cada `min_days_between` (padrão 30).
- [ ] O modelo pergunta a nota de 1 a 5 com botões de resposta rápida (`auto:review:<id>:<1..5>`);
      se o limite de botões da Meta não permitir 5, usa lista interativa ou resposta numérica em
      texto (a conferir).
- [ ] Nota grava `reviews` (ligada a agendamento, cliente, barbeiro e unidade). Texto que o cliente
      mandar em até 1 h depois da nota vira o comentário.
- [ ] **Toda nota** (1 a 5) → mensagem de agradecimento com o **link do Google da unidade** (texto
      livre: a janela abriu com a resposta) — PD-27; nunca condicionar o link à nota (*review
      gating*). Sem link cadastrado → só agradece. `google_link_sent` registra o envio.
- [ ] Nota **≤ `low_threshold`** (padrão 3) → o agradecimento tem tom neutro ("Obrigado por contar;
      vamos melhorar", seguido do link) e gera **alerta**: avaliação com `alert_status = open`,
      publicada em `review.low_received`, entra na lista de avaliações com contador de alertas e a
      conversa vai para `waiting_human` (`low_review`) — Q-S12-3.

### Campanhas manuais (PD-20)

- [ ] Rascunho com nome, modelo (`purpose = campaign`, aprovado), valores das variáveis fixas e o
      **público** por filtro: unidade da última visita, última visita entre/sem visita há N dias,
      número de visitas, já atendido por barbeiro X, usou serviço Y, tem/não tem clube ou pacote ativo,
      aniversariantes do mês, clientes novos (primeira visita há até N dias).
- [ ] **Prévia** antes de agendar: total elegível, excluídos por motivo (opt-out, sem consentimento, limite
      de frequência, sem WhatsApp), amostra de 10 nomes e **custo estimado** (T4).
- [ ] Agendar para agora ou data/hora fora do horário de silêncio (409 "Escolha um horário entre
      09:00 e 20:00"). Público vazio → 409. O público é **congelado** no início do envio (quem entra
      depois não recebe); regras de opt-out/frequência são reavaliadas cliente a cliente no envio.
- [ ] Envio em lotes respeitando a vazão do número (padrão 10 msg/s; menor em coexistência);
      cancelar interrompe o que não saiu. Estatística: enviados, entregues, lidos, falhas, respostas
      (mensagem do cliente em até 72 h) e agendamentos em até 7 dias.
- [ ] No máximo 1 campanha **enviando** por vez por barbearia.

### Opt-in e opt-out (LGPD)

- [ ] O registro é do `clients` (S13): `whatsapp_opt_in_at` + `whatsapp_opt_in_source`
      (`inbound_message`, `booking_link`, `staff`, `import`, `keyword`), `marketing_consent_at` +
      `marketing_consent_source` (o "sim" explícito da PD-30: `booking_link`, `whatsapp`, `staff`),
      `marketing_opt_out_at` e `all_opt_out_at`. Este módulo só lê (`get_contact_policy`) e, no caso
      do erro da Meta acima, grava pelo `clients.public.record_opt_out`.
- [ ] Todo modelo de marketing leva rodapé "Responda SAIR para não receber mais" ou o botão de
      opt-out de marketing da Meta.
- [ ] **"SAIR"** (Q-S12-2) é tratado pelo `messaging` (S10): grava na hora
      `record_opt_out(scope="marketing", source="whatsapp")` (padrão seguro) e responde com dois
      botões, **"Só promoções"** / **"Tudo"**; "Tudo" grava `scope="all"` (para também lembretes e
      avisos). **"VOLTAR"** → `record_opt_in(source="keyword")`, que limpa os opt-outs.
      `client.opted_out` (com `scope`) cancela os envios agendados atingidos: `marketing` cancela
      reativação, aniversário e campanha; `all` cancela também lembrete, aviso e avaliação.

### Aviso de reajuste do clube (S07)

- [ ] Reajuste com `price_applies_to = all_from` (S07, Q-S07-2) agenda uma mensagem de **utilidade**
      para cada assinante ativo do clube (template `membership_price_change`: valor novo e data de
      início), enviada assim que o reajuste é salvo. Assinante sem WhatsApp válido aparece numa
      lista para a recepção avisar por outro meio. Consome `membership.price_changed` (evento novo da
      S07: `club_id`, `new_price_cents`, `effective_from`, `membership_ids`).

## Data Contract

```text
# Automações — tag "automations" (tenant:configure)
GET  /automations                              → 200 AutomationOut[]
PUT  /automations/{kind}  {enabled, config}    → 200 AutomationOut | 402 | 422
PUT  /automations/{kind}/message  {body, buttons?, footer?} → 201 TemplateOut (nova versão, pending) | 400 | 502
GET  /automations/settings                     → 200 AutomationSettings
PUT  /automations/settings  AutomationSettings → 200 | 422
GET  /automations/dispatches?kind=&status=&client_id=&from=&to=&limit=&offset=
                                               → 200 {items: DispatchOut[], total}
GET  /automations/costs?month=YYYY-MM          → 200 {by_kind: {kind: {sent, estimated_cents}}, total_estimated_cents}

kind = appointment_updates | reminder | reactivation | birthday | review
AutomationOut {kind, enabled, config, template: {id, status, body} | null, waiting_template: bool,
               last_30d: {sent, skipped, failed, responded}}
config por kind: reminder {hours_before} · reactivation {inactive_days,
  max_per_run, send_hour} · birthday {days_before, send_hour} · review {delay_minutes, min_days_between,
  low_threshold} (sem `high_threshold`: o link vai para toda nota, PD-27) · appointment_updates {on_create, on_reschedule, on_cancel}
AutomationSettings {quiet_start "HH:MM", quiet_end "HH:MM", marketing_max_per_7d, marketing_max_per_30d,
                    review_links: [{unit_id, google_url}]}
DispatchOut {id, kind, client {id, name}, appointment_id, campaign_id, status, skip_reason,
             scheduled_for, sent_at, response, estimated_cents}
skip_reason = opted_out_marketing | opted_out_all | no_consent | frequency_cap | no_whatsapp |
              inactive_client | template_not_approved | meta_user_limit | meta_marketing_stopped

# Avaliações — tag "reviews"
GET  /reviews?score_max=&alert=open|handled&unit_id=&barber_id=&from=&to=&limit=&offset=
                                               → 200 {items: ReviewOut[], total}       (client:read)
GET  /reviews/summary?from=&to=&unit_id=       → 200 {average, count, by_score{}, by_barber[]} (client:read)
POST /reviews/{id}/handle  {note?}             → 200 ReviewOut | 404                    (client:write)
ReviewOut {id, score, comment, client {id, name}, barber {id, name}, unit_id, appointment_id,
           google_link_sent, alert_status, handled_by, handled_note, created_at}

# Campanhas — tag "campaigns" (tenant:configure)
GET   /campaigns?status=                       → 200 CampaignOut[]
POST  /campaigns  CampaignIn                   → 201 | 402 | 422
GET   /campaigns/{id}                          → 200 CampaignOut (com estatística)
PATCH /campaigns/{id}  CampaignIn              → 200 | 409 (já enviada) | 422
DELETE /campaigns/{id}                         → 204 | 409 (já enviada)
POST  /campaigns/audience-preview  {filter}    → 200 {eligible, excluded: {opted_out, no_consent,
                                                  frequency_cap, no_whatsapp}, sample[], estimated_cents}
POST  /campaigns/{id}/schedule  {send_at | null} → 200 | 402 | 409
POST  /campaigns/{id}/cancel                   → 200 | 409
GET   /campaigns/{id}/recipients?status=&limit=&offset= → 200 {items, total}
CampaignIn {name, template_id, variables{}, filter: AudienceFilter}
AudienceFilter {unit_id?, last_visit_from?, last_visit_to?, no_visit_days?, min_visits?, max_visits?,
                barber_id?, service_id?, membership: any|active|none, birthday_month?, new_within_days?}
CampaignOut CampaignIn + {id, status: draft|scheduled|sending|sent|cancelled, send_at,
            recipients_count, stats {sent, delivered, read, failed, replied, booked}, estimated_cents}
```

### Eventos

Consome: `appointment.created/.rescheduled/.cancelled/.completed` (S03);
`conversation.message_received` com `button_payload` `auto:*` (S10); `message.delivery_updated`
(S10, atualiza o `dispatch`); `client.opted_out` com `scope` (S13: `marketing` cancela envios
agendados de marketing; `all` cancela todos).
Publica: `review.received` `{review_id, score, barber_id, unit_id}` e `review.low_received` (mesmo
payload) — interessados: reports (S14) e painel.

### Banco de dados

Tenant (`t000N_automations`, expand only):

```text
automation_settings   id (uma linha) · quiet_start time · quiet_end time · marketing_max_per_7d smallint ·
                      marketing_max_per_30d smallint · updated_by · timestamps
automation_rules      id · kind enum automation_kind UNIQUE · enabled bool · config jsonb · updated_by · timestamps
review_links          unit_id pk → units.id CASCADE · google_url varchar(500)
automation_dispatches id · kind enum dispatch_kind(appointment_updates, reminder, reactivation, birthday,
                      review, campaign) · dedupe_key varchar(120) UNIQUE · client_id → clients.id RESTRICT ·
                      appointment_id → appointments.id SET NULL null · campaign_id → campaigns.id RESTRICT null ·
                      message_id → messages.id SET NULL null ·
                      status enum dispatch_status(scheduled, sent, delivered, read, skipped, failed, cancelled) ·
                      skip_reason varchar(30) null · scheduled_for · sent_at null · response varchar(30) null ·
                      estimated_cents int default 0 · timestamps
                      INDEX (client_id, kind, sent_at) · INDEX (status, scheduled_for)
reviews               id · appointment_id → appointments.id RESTRICT UNIQUE · client_id → clients.id RESTRICT ·
                      barber_id → barbers.id RESTRICT · unit_id → units.id RESTRICT ·
                      score smallint check (1..5) · comment varchar(1000) null · google_link_sent bool ·
                      alert_status enum review_alert(none, open, handled) · handled_by → users.id null ·
                      handled_note varchar(500) null · timestamps
campaigns             id · name varchar(120) · template_id → message_templates.id RESTRICT · variables jsonb ·
                      filter jsonb · status enum campaign_status · send_at null · started_at null ·
                      finished_at null · recipients_count int · estimated_cents int · created_by → users.id · timestamps
campaign_recipients   id · campaign_id → campaigns.id CASCADE · client_id → clients.id RESTRICT ·
                      dispatch_id → automation_dispatches.id null · UNIQUE (campaign_id, client_id)
```

Linhas de `automation_rules` e `automation_settings` nascem com os padrões quando o módulo é
migrado (dado inicial da migration) e quando a barbearia é provisionada.

## Permissões

Sem permissão nova nesta versão: campanhas só com `tenant:configure` (dono) — Q-S12-4.

| Ação | Permissão | owner | manager | receptionist | barber |
|---|---|---|---|---|---|
| configurar automações, ver envios e custos | `tenant:configure` | sim | — | — | — |
| criar, agendar e cancelar campanhas | `tenant:configure` | sim | — | — | — |
| ver avaliações e resumo | `client:read` | todas | suas unidades | suas unidades | `own`: as dele |
| marcar alerta como tratado | `client:write` | sim | suas unidades | suas unidades | — |

## Acceptance Criteria

- [ ] Módulo `automations` com layout completo + `jobs/` (lembrete, prazo, diária, avaliação,
      campanha); importa `messaging`, `assistant`, `scheduling`, `memberships`, `clients` e `identity`
      só pelo `public.py`.
- [ ] Testes de cada regra com relógio controlado: lembrete na hora, antecipado pelo silêncio,
      remarcado (job velho descartado), cancelado; `record_reminder_sent` só com envio aceito;
      botões Confirmar/Cancelar/Remarcar (com e sem IA); reativação uma vez por episódio; aniversário
      29/02; avaliação: link do Google para toda nota (5 e 1) e alerta só na baixa; limite de
      frequência; opt-out `marketing` × `all` (lembrete sai no primeiro, não no segundo); marketing
      para importado sem atendimento só com `marketing_consent_at`; prévia e
      envio de campanha com congelamento do público; idempotência pela `dedupe_key` (evento duplicado);
      **duas barbearias**.
- [ ] Modelos do sistema com textos-padrão em `pt_BR` (abaixo) submetidos pela S10 na conexão.
- [ ] Migrations aplicadas; `alembic check` limpo; variáveis de preço no `.env.example` e em
      `docs/ENVIRONMENT_VARIABLES.md`.
- [ ] Testes em `tests/test_automations/` cobrindo as regras acima
- [ ] Snapshots de contrato revisados (`UPDATE_CONTRACT_SNAPSHOTS=1` só se a mudança for intencional)

Textos-padrão propostos (editáveis pelo dono, cada edição é uma nova versão do modelo):

```text
appointment_reminder  Oi, {{nome_cliente}}! Lembrete do seu horário na {{barbearia}}: {{servico}} com
                      {{barbeiro}}, {{data}} às {{hora}}. Pode confirmar?   [Confirmar] [Remarcar] [Cancelar]
appointment_created   Oi, {{nome_cliente}}! Seu horário na {{barbearia}} está marcado: {{servico}} com
                      {{barbeiro}}, {{data}} às {{hora}}.
reactivation          Oi, {{nome_cliente}}! Faz um tempinho que você não aparece na {{barbearia}}.
                      Bora marcar? É só responder aqui.   Responda SAIR para não receber mais.
birthday              Feliz aniversário, {{nome_cliente}}! A {{barbearia}} preparou um presente: <texto do dono>.
review_request        Oi, {{nome_cliente}}! Como foi seu atendimento com {{barbeiro}} hoje? Toque numa nota de 1 a 5.
```

## Dependencies

- **S10** (`messaging`) — `send_template`, `send_text`, `send_interactive`, `request_handoff`;
  eventos `conversation.message_received` e `message.delivery_updated`; modelos por `purpose`.
- **S11** (`assistant`) — `is_active`, `start_flow(intent="reschedule")`.
- **S03** (`scheduling`) — eventos `appointment.*` (payload com `origin`, `starts_at`, `items` com
  `barber_id`); `get_appointment`, `confirm_appointment(via, actor, client_id)`,
  `cancel_appointment(channel, actor, client_id, reason)`, `record_reminder_sent`, exceção
  `ChangeWindowClosed`; a tarefa `scheduling.mark_unconfirmed` é deles. **Assumido a mais:**
  `client_ids_with_future_appointment(session) -> set[UUID]` (reativação).
- **S01** — `identity.public.get_shop_settings()` (`confirmation_deadline_hours`), `list_units`
  (fuso).
- **S13** (`clients`) — `get_contact_policy(session, client_id)`, `record_opt_out(session,
  client_id, scope, source)`,
  `query_audience(session, AudienceFilter)` — o filtro (S13) já tem unidade da última visita,
  `min_visits`/`max_visits`, `first_visit_from/to`, `served_by_barber_id`, `used_service_id`,
  `birthday_md`, `tag_ids` e `purpose` —, `get_client_summary`; eventos `client.opted_out`,
  `client.merged`, `client.anonymized`. **Ainda a pedir à S13:** `last_visit_unit_id` no resumo.
- **S07** (`memberships`) — **assumido a mais:** `client_ids_with_active(session, kind=None) ->
  set[UUID]` (filtro "tem clube/pacote").
- **S15** — `require_feature`/`has_feature` (`WHATSAPP`, `AUTOMATIONS`, `CAMPAIGNS`), `quota_status` e
  `consume_quota(CAMPAIGN_MESSAGES_PER_MONTH)` em `identity.public`.
- **S00** — `schedule_job`/`cancel_job` com `dedupe_key` (o próprio exemplo da S00 é
  `automations.send_reminder`), `PeriodicTask` por barbearia, `SUBSCRIBERS` idempotentes.
- Oferece: eventos `review.received` / `review.low_received`; S14 lê `automation_dispatches`,
  `reviews` e `campaigns` por funções de leitura em `automations.public`
  (`reminder_stats`, `review_stats`, `campaign_stats`, `reactivation_stats`).

## Notes

- **Política de avaliações do Google:** pedir avaliação no Google **só para quem deu nota alta**
  ("review gating") é proibido pelas regras do Google. Resolvido pela PD-27: o link vai para todos
  que responderam (Q-S12-5).
- **A conferir na documentação da Meta:** se opt-in precisa ser explícito e por canal para
  utilidade e marketing; número máximo de botões de resposta rápida em modelo; se pedido de avaliação
  é classificado como utilidade ou marketing; botão de opt-out de marketing; limites de envio de
  marketing por usuário; preço vigente por categoria no Brasil.
- Campanha "volta às aulas"/"Dia dos Pais" é só campanha manual com filtro; não há calendário de
  datas comemorativas automático.
- **Lembrete que falhou** (sem WhatsApp, opt-out, erro da Meta): pela regra da S03 o agendamento não
  vira "não confirmado". Sugestão à S03: um indicador "sem lembrete" na agenda, para a recepção ligar.

### Perguntas em aberto

- ✅ **Q-S12-1 (= Q-S13-1) — Quem pode receber mensagem iniciada pela barbearia (opt-in)?** A Meta
  exige opt-in. A S13 recomenda: marketing permitido para quem já teve ao menos uma visita, e só com
  opt-in para importado sem visita e contato do WhatsApp sem atendimento. Visto do canal:
  (a) Só quem tem opt-in **explícito** registrado (marcado no link, respondeu "SIM" a um convite, ou a
  recepção marcou "cliente autorizou"); (b) todos com telefone, salvo opt-out; (c) opt-in implícito
  para quem escreveu à barbearia ou agendou pelo link (com aviso na tela), explícito marcado pela
  recepção para os demais, e importados só depois de autorizar. **Recomendação: (c) da S13 para
  marketing**, e utilidade (aviso e lembrete) para todo cliente com agendamento — quem marcou horário
  deu o número para isso; responder uma só pergunta para os dois módulos.
  > Resolvido em 2026-11-06: marketing para quem tem ao menos um atendimento; importados e contatos
  > sem atendimento só com "sim" explícito (`marketing_consent_at`); utilidade para todo cliente com
  > agendamento; opt-out sempre respeitado (PD-30).
- ✅ **Q-S12-2 — O que "SAIR" desliga?** (a) Só marketing (reativação, aniversário, campanha), mantendo
  lembretes e avisos do próprio agendamento; (b) tudo; (c) pergunta ao cliente com dois botões
  ("Só promoções" / "Tudo"). **Recomendação: (c)** — quem não quer promoção quase sempre ainda quer o
  lembrete, e o lembrete é o que reduz falta. (A S13 hoje assume (a); decidir aqui vale para as duas.)
  > Resolvido em 2026-11-06: (c) — "SAIR" grava opt-out de marketing na hora e pergunta com dois
  > botões ("Só promoções" / "Tudo"); "Tudo" grava `scope = all`. Vale também para a S13 (ROADMAP §7).
- ✅ **Q-S12-3 — Como a nota baixa chega ao dono?** (a) Lista de avaliações com contador de alertas;
  (b) (a) + a conversa vai para "Aguardando humano" com motivo "Avaliação baixa"; (c) (a) + e-mail ao
  dono. **Recomendação: (b)** — coloca a recuperação do cliente na fila de quem já responde, sem
  push (PD-18).
  > Resolvido em 2026-11-06: (b) — lista com contador de alertas e a conversa vai para "aguardando
  > humano" (`low_review`) (ROADMAP §7).
- ✅ **Q-S12-4 — O gerente pode criar e mandar campanhas?** (a) Não, só o dono (`tenant:configure`,
  como está); (b) sim, com permissão nova `campaign:send` (owner `all`, manager `unit`, filtrando o
  público pelas unidades dele). **Recomendação: (a) agora** — campanha gasta dinheiro e expõe o
  número a bloqueios; (b) quando houver pedido de rede com gerente por unidade.
  > Resolvido em 2026-11-06: (a) — campanhas só com `tenant:configure` (dono) agora (ROADMAP §7).
- ✅ **Q-S12-5 — Link do Google só para nota alta (PD-20) ou para todos?** (a) Como PD-20: só nota alta
  (risco de violar a política do Google); (b) link para todos que responderam, com a nota baixa
  também gerando o alerta de recuperação; (c) para todos, mas a nota baixa recebe primeiro o contato
  da equipe e o link só depois de tratada. **Recomendação: (b)** — mantém o alerta, que é o valor
  de PD-20, sem o risco de perder as avaliações do Google.
  > Resolvido em 2026-11-06: (b) — link do Google para todos que responderam; nota baixa continua
  > gerando alerta (PD-27).
