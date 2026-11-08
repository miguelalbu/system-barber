# Link público de agendamento (S04)

**Priority:** high
**Status:** draft
**Espelho no frontend:** `frontend/docs/specs/⚪draft_frontend-booking-page.md`

## Overview

A página pública da barbearia, no **subdomínio dela** (`<slug>.<BASE_DOMAIN>/agendar`, ou no domínio
próprio), para o cliente final agendar sozinho — o link que vai na bio do Instagram e no status do
WhatsApp. Fluxo: unidade → serviço(s) → barbeiro ou "qualquer um" → dia e horário → identificação
por **telefone + código no WhatsApp** (PD-02) → confirmado. Com a mesma identificação, o cliente vê
**"meus agendamentos"** e remarca ou cancela dentro da política. O módulo `booking` é fino: a regra de
agenda (grade, disponibilidade, "qualquer um", política) é do `scheduling` (S03); o envio do código é
do `messaging` (S10); o cliente é do `clients`. Aqui ficam a sessão do cliente, o OTP, a proteção
contra abuso, as configurações da página e o cartão de compartilhamento.

Fica de fora: pagamento/sinal (PD-10), lista de espera e recorrência (PD-08), clube/pacote pela
página (a venda é fechada no balcão; a IA só explica e passa para a equipe — PD-37), app do cliente
(PD-01), avaliações públicas.

## Decisões de produto já tomadas

| Parâmetro | Valor |
|---|---|
| PD-01 | Link público é canal oficial de agendamento, ao lado da IA no WhatsApp; sem app do cliente. |
| PD-02 | Identificação por **telefone + código (OTP) no WhatsApp**; sem senha. |
| PD-03 | Cliente é da barbearia; telefone E.164 único — o mesmo cliente da IA e do balcão. |
| PD-04/05 | Grade de 15 min; vários serviços em sequência, inclusive com barbeiros diferentes. |
| PD-06 | Mostra os barbeiros livres; "qualquer um" → barbeiro livre com menos agendamentos no mês (regra do `scheduling`). |
| PD-07 | Agendamento feito pelo cliente recebe lembrete com confirmação (S12). |
| PD-30 | Consentimento de marketing: quem agenda recebe mensagens de **utilidade** (lembrete, confirmação); marketing só com ao menos um atendimento ou "sim" explícito — a caixa "aceito receber promoções" da página é esse "sim". |
| PD-31 | Agendamento pelo link **nasce "agendado" e confirma pelo lembrete**; marcado já dentro do prazo do lembrete, nasce confirmado (regra do `scheduling`). |
| PD-32 | Campo **"para quem"** (`attendee_name`); o mesmo cliente pode ter horários simultâneos. |
| PD-42 | Um número de WhatsApp geral e, opcionalmente, um por unidade: o botão "falar no WhatsApp" usa o número da unidade escolhida e, sem ele, o geral. |
| DEC-002 | O tenant vem do domínio de acesso; nunca de body, query ou path. |

### Decisões técnicas desta spec (propostas, revisar na aprovação)

| # | Decisão | Por quê |
|---|---|---|
| T1 | Sessão do cliente por **token opaco** em cookie `navalha_booking` (`HttpOnly`, `Secure`, `SameSite=Lax`, `Path=/api/booking`), guardado só como SHA-256 em `booking_sessions`, validade de 30 dias renovada a cada uso. Requisições que alteram estado exigem o header `X-Requested-With: navalha`. | Diferente do painel (ISS-001), o cliente final não precisa de token no `localStorage`; cookie HttpOnly no próprio host é mais seguro e o header customizado barra CSRF sem token extra. |
| T2 | OTP de 6 dígitos, validade de 10 min, guardado no Redis como hash (`booking:otp:<schema>:<phone>`), 5 tentativas por código. | PD-02; Redis já provisionado; chave particionada pelo tenant (Camada 5). |
| T3 | Rate limit em **Redis** (janela deslizante), chave sempre com o schema: por telefone (1 código/60 s, 5/h, 10/dia), por IP (10 códigos/h, 30 consultas de horário/min), por barbearia (200 códigos/h). Entra em `app/core/` como backend Redis do limitador atual. | O limitador de hoje é por processo; código de WhatsApp custa dinheiro e é alvo de abuso. |
| T4 | **Captcha** (Cloudflare Turnstile, modo gerenciado/invisível) só no pedido de código; desligável por `BOOKING_CAPTCHA_ENABLED`, chave em `TURNSTILE_SECRET_KEY`. | Protege o passo que gera custo sem atrito no resto do fluxo. |
| T5 | Ver serviços, barbeiros e horários **não** exige código; o código é pedido só para confirmar ou para "meus agendamentos". Sem reserva temporária do horário. | Menos atrito; corrida rara vira "esse horário acabou de ser ocupado" com novas opções. |
| T6 | Cartão de compartilhamento (Open Graph) servido pelo backend em `GET /booking/share` (HTML mínimo com título, descrição e imagem da barbearia); o servidor web encaminha robôs de prévia (WhatsApp, Instagram, Facebook, X, Telegram) que pedem `/agendar` para essa rota. | A SPA não roda JS para robôs; sem isso o link na bio aparece genérico. |

## Business Rules

### Página e catálogo

- [ ] Rotas públicas (sem JWT do painel) resolvem o tenant pelo host como as demais. Barbearia sem o
      recurso `public_booking` (S15, `has_feature`), com a página desligada ou não servível → 404
      "Agendamento online indisponível" (o cliente final não vê 402). Só aparecem unidades ativas com
      `online_booking = true` (S01).
- [ ] `GET /booking/shop` traz nome, **logo** (dono: esta spec — a S01 deixou logo para cá), `about`,
      `instagram` e `contact_phone` da barbearia (`identity.public.get_shop_settings`), unidades
      (`list_units(online_only=True)`: nome, endereço, telefone, fuso), texto de boas-vindas e a
      política do cliente da S01: `min_advance_minutes`, `max_advance_days`, `client_change_min_hours`.
- [ ] Logo enviado no painel (`PUT /booking/settings/logo`, PNG/JPEG/WebP até 1 MB, recortado em
      512×512) e guardado no bucket privado da S10 (`tenants/<id>/booking/logo`), servido por
      `GET /booking/logo` com cache.
- [ ] Serviços: só ativos, não ocultos em `booking_settings` e com ao menos um barbeiro ativo da
      unidade habilitado. Preço aparece se `show_prices` (padrão sim).
- [ ] Combos (Q-S05-1): os de `catalog.public.list_bookable_combos` (só serviços, ativos) cujos
      serviços passam na regra acima aparecem junto dos serviços, com o preço fechado e a duração
      somada. Escolher um combo preenche os itens na ordem do combo e envia `combo_id`; combo com
      produto nunca aparece.
- [ ] Barbeiros: ativos, da unidade, não ocultos, habilitados para **todos** os serviços escolhidos
      (ou, com barbeiros diferentes por serviço — PD-05 —, por item). "Qualquer um" aparece se
      `allow_any_barber` (padrão sim).
- [ ] Disponibilidade vem só de `scheduling.public` (grade de 15 min, expediente, jornada, bloqueios,
      antecedência mínima e máximo de dias); `booking` não calcula horário.

### Identificação (OTP no WhatsApp)

- [ ] `POST /booking/otp/request` normaliza o telefone (`clients.public.normalize_phone`; inválido
      → 422 "Telefone inválido"), confere captcha e limites (429 "Muitas tentativas. Tente de novo em
      N minutos", com `Retry-After`) e envia o modelo de **autenticação** (`purpose = otp`) por
      `messaging.public.send_template(origin = "otp")`. A resposta é sempre igual exista ou não o
      cliente (não revela quem é cliente).
- [ ] O texto do código **nunca** é gravado: a mensagem fica no histórico como "Código de acesso
      enviado" (a equipe não vê o código na Central). Falha da Meta → 503 "Não conseguimos enviar o
      código agora. Tente de novo em instantes".
- [ ] **Sem WhatsApp conectado** (Q-S04-1): o link funciona e o código sai de um **número da
      plataforma Navalha** (`messaging.public.send_platform_otp(phone, shop_name, code)`, modelo de
      autenticação genérico "Seu código para agendar na <Barbearia> é …", custo da plataforma). Nada
      é gravado na Central da barbearia; os limites de T3 (inclusive por barbearia) valem igual.
- [ ] `POST /booking/otp/verify`: código certo → cria a sessão (T1) e responde se o cliente já existe
      e o nome dele; errado → 400 "Código inválido" (tentativas restantes no corpo); expirado ou
      tentativas esgotadas → 410 "Código expirado. Peça um novo". Código usado é apagado.
- [ ] Novo pedido de código invalida o anterior.
- [ ] Consentimento (PD-30): agendar pelo link grava o opt-in de WhatsApp para utilidade
      (`clients.public.record_opt_in(session, client_id, source = "booking_link")`, se ainda não
      houver) — quem marcou horário deu o número para receber lembrete e confirmação. A caixa
      **"Aceito receber promoções da barbearia no WhatsApp"** (`accept_marketing`, desmarcada por
      padrão) é o "sim" explícito de marketing: marcada →
      `clients.public.record_marketing_consent(session, client_id, source = "booking_link")`.
      Desmarcada não grava opt-out nem apaga consentimento anterior.
- [ ] Sessão revogada em `POST /booking/logout`; revogada também quando o telefone do cliente muda
      no cadastro (evento `client.updated` com telefone novo) ou o cliente é anonimizado.

### Agendar

- [ ] `POST /booking/appointments` exige sessão. Cliente procurado com `find_client_by_phone`;
      inexistente → criado por `create_client(source = "booking_link")` com o `name` enviado
      (obrigatório nesse caso, 2–120).
- [ ] Chama `scheduling.public.create_appointment(source = "booking_link", actor = Actor.client(id),
      idempotency_key = <sessão>:<hash do pedido>)` (clique duplo não duplica); `SlotUnavailable` → 409
      "Esse horário acabou de ser ocupado" + até 6 horários próximos no corpo; `BookingWindowError` →
      422 com a mensagem do `scheduling`.
- [ ] Status inicial (PD-31, decidido pelo `scheduling`): `scheduled`, que confirma pelo lembrete;
      marcado já dentro do prazo do lembrete (`confirmation_deadline_hours`), nasce `confirmed` com
      `confirmed_via = booking_link`. A tela de sucesso mostra o status que veio.
- [ ] Limites: agendamentos futuros por cliente configurável, padrão 3 (Q-S03-4; campo da S01,
      aplicado pelo `scheduling` nos canais do cliente; a mensagem dele aparece como veio); 5 criações
      por sessão por dia (aqui); bloqueio por faltas configurável e **desligado por padrão**
      (Q-S04-2, `block_after_no_shows = null`; ligado, N faltas nos últimos 90 dias → 422 "Para
      agendar, fale com a barbearia pelo WhatsApp" + link `wa.me`; faltas lidas de
      `clients.public.get_client_summary`).
- [ ] Observação do cliente opcional (até 300 caracteres) e "para quem é o horário"
      (`attendee_name`, até 120, PD-32), gravados no agendamento. Com `attendee_name`, o mesmo cliente
      pode ter horários simultâneos (pai que marca para dois filhos; regra do `scheduling`).
- [ ] Resposta traz o resumo (serviços, barbeiro(s) — o escolhido pelo "qualquer um" incluído —,
      unidade, endereço, início/fim, total) e o link para adicionar à agenda do celular (`.ics` em
      `GET /booking/me/appointments/{id}/calendar.ics`).

### Meus agendamentos

- [ ] Lista futuros e os últimos 10 passados do cliente da sessão (`list_client_appointments`), com
      status e se ainda pode remarcar/cancelar pela política.
- [ ] Remarcar (`POST .../reschedule`) e cancelar (`POST .../cancel`) passam por `scheduling.public`
      com `source = "booking_link"` e o `client_id` da sessão; `ChangeWindowClosed` → 409 com a
      mensagem do `scheduling` + link `wa.me` do número da barbearia, se houver. `can_reschedule`/
      `can_cancel` vêm de `client_change_deadline`.
- [ ] Agendamento de outro cliente (`NotYourAppointment`) → 404 (nunca 403, para não revelar
      existência).

### Configuração (painel)

- [ ] `GET/PUT /booking/settings` com `tenant:configure`; sem o recurso no plano → 402.
- [ ] Ocultar serviço/barbeiro só afeta a página (a IA e o balcão continuam vendo).

## Data Contract

```text
# Público — tag "booking", sem JWT; tenant pelo host; cookie navalha_booking quando indicado
GET  /booking/shop                                   → 200 ShopOut | 404
GET  /booking/services?unit_id=                      → 200 PublicServiceOut[]
GET  /booking/combos?unit_id=                        → 200 PublicComboOut[]   (Q-S05-1)
GET  /booking/barbers?unit_id=&service_ids=a,b       → 200 PublicBarberOut[]
GET  /booking/availability/days?unit_id=&items=&from=&to= → 200 [{date, available: bool}]  (até 31 dias)
GET  /booking/availability?unit_id=&items=&date=     → 200 {date, slots: [{start_at, end_at,
                                                         barbers: [{id, name}]}]}
     items = JSON compacto [{"service_id": "...", "barber_id": "..." | null}] (ordem = sequência, PD-05)
POST /booking/otp/request  {phone, captcha_token?}   → 202 {expires_in, resend_in} | 422 | 429 | 503
POST /booking/otp/verify   {phone, code}
                                                     → 200 {client: {exists, name | null}} + Set-Cookie
                                                       | 400 {detail, attempts_left} | 410 | 429
GET  /booking/me                       (cookie)      → 200 {name, phone} | 401
POST /booking/logout                   (cookie)      → 204
POST /booking/appointments             (cookie)  {unit_id, items, start_at, name?, notes?, attendee_name?,
                                                  combo_id?, accept_marketing?: bool = false}
                                                     → 201 PublicAppointmentOut | 401 | 409 | 422
GET  /booking/me/appointments?when=upcoming|past (cookie) → 200 PublicAppointmentOut[]
POST /booking/me/appointments/{id}/reschedule (cookie) {start_at, items?} → 200 | 404 | 409
POST /booking/me/appointments/{id}/cancel (cookie) {reason?} → 200 | 404 | 409
GET  /booking/me/appointments/{id}/calendar.ics (cookie) → 200 text/calendar | 404
GET  /booking/share                                  → 200 text/html (Open Graph) | 404

ShopOut {name, logo_url, about, instagram, welcome_text, whatsapp_url | null (número geral),
         units: [{id, name, address, phone, timezone, whatsapp_url | null (número da unidade, senão
         o geral — PD-42)}], policy: {min_advance_minutes, max_advance_days,
         client_change_min_hours}, show_prices, allow_any_barber}
PublicServiceOut {id, name, description, duration_minutes, price_cents | null}
PublicComboOut   {id, name, service_ids[] (ordem do combo), duration_minutes, price_cents | null}
PublicBarberOut  {id, name, initials, service_ids[]}
PublicAppointmentOut {id, status (scheduled|confirmed|unconfirmed|…), attendee_name | null,
         unit {id, name, address}, items: [{service_name, barber_name, start_at, end_at}], start_at,
         end_at, total_cents | null, can_reschedule, can_cancel}

# Painel — tag "booking" (tenant:configure)
GET  /booking/settings                               → 200 BookingSettings
PUT  /booking/settings  BookingSettings              → 200 | 402 | 422
PUT  /booking/settings/logo  (multipart, file)       → 200 {logo_url} | 402 | 413 | 422
DELETE /booking/settings/logo                        → 204
GET  /booking/logo                     (público)     → 200 image/* | 404
BookingSettings {enabled, welcome_text (≤ 500), hidden_service_ids[], hidden_barber_ids[],
                 allow_any_barber, show_prices, block_after_no_shows (null | 1..10),
                 public_url (só leitura)}
```

Mutação pública sem `X-Requested-With: navalha` → 403 "Requisição inválida". Sessão ausente ou
expirada → 401 "Confirme seu telefone para continuar".

### Funções públicas e eventos

`booking/public.py`: nenhuma função por enquanto (ninguém depende do `booking`). Não publica evento
próprio: o agendamento sai como `appointment.created` do `scheduling` com `source = booking_link`.
Consome `client.updated` (telefone mudou), `client.merged` (sessões da origem passam ao destino) e
`client.anonymized` (revoga sessões).

### Banco de dados

Tenant (`t000N_booking`, expand only):

```text
booking_settings  id (uma linha) · enabled bool default true · welcome_text varchar(500) null ·
                  hidden_service_ids uuid[] · hidden_barber_ids uuid[] · allow_any_barber bool ·
                  show_prices bool · block_after_no_shows smallint null · logo_key varchar(255) null ·
                  updated_by → users.id null · timestamps
booking_sessions  id · token_hash char(64) UNIQUE · client_id → clients.id RESTRICT · phone varchar(16) ·
                  created_at · last_seen_at · expires_at · revoked_at null · ip_hash char(64) ·
                  user_agent varchar(200) null
                  INDEX (client_id)
```

Redis: `booking:otp:<schema>:<phone>` (TTL 10 min), `booking:rl:<schema>:<tipo>:<chave>` (TTL da
janela). Nada de dado de barbearia em memória de processo.

## Permissões

As rotas públicas não usam o RBAC do painel: a autorização é "a sessão do cliente só vê o que é do
próprio `client_id`". Sem permissão nova.

| Ação | Permissão | owner | manager | receptionist | barber |
|---|---|---|---|---|---|
| configurar a página | `tenant:configure` | sim | — | — | — |

## Acceptance Criteria

- [ ] Módulo `booking` com layout completo + `cache/` (OTP e limites); importa `scheduling`,
      `clients`, `messaging`, `catalog`, `identity`, `provisioning` só pelo `public.py`.
- [ ] Rotas públicas marcadas como públicas no snapshot de rotas (sem `require(...)`), com teste de
      que nenhuma devolve dado de outro cliente nem de outra barbearia (**duas barbearias**, mesmo
      telefone nas duas: sessões e agendamentos não se cruzam).
- [ ] Testes: OTP (certo, errado, esgotado, expirado, reenvio invalida o anterior, resposta igual
      para telefone novo e existente, código não gravado na mensagem); limites por telefone, IP e
      barbearia; captcha; CSRF (sem header → 403); criação de cliente novo; corrida de horário (409 com
      sugestões); máximo de futuros; política de remarcar/cancelar; serviço/barbeiro oculto;
      página desligada e plano sem o recurso → 404; sem número conectado o código sai pelo número da
      plataforma; agendar grava opt-in `booking_link` e, só com `accept_marketing`, o consentimento de
      marketing; status inicial `scheduled` ou `confirmed` dentro do prazo do lembrete;
      `attendee_name` permite dois horários simultâneos do mesmo cliente; bloqueio por faltas desligado
      por padrão.
- [ ] `GET /booking/share` com título "<Barbearia> — agende seu horário", descrição e imagem.
- [ ] Variáveis novas (`BOOKING_CAPTCHA_ENABLED`, `TURNSTILE_SECRET_KEY`, `BOOKING_SESSION_DAYS`) no
      `.env.example` e em `docs/ENVIRONMENT_VARIABLES.md`.
- [ ] Testes em `tests/test_booking/` cobrindo as regras acima
- [ ] Snapshots de contrato revisados (`UPDATE_CONTRACT_SNAPSHOTS=1` só se a mudança for intencional)

## Dependencies

- **S03** (`scheduling`) — `find_availability`/`find_available_days(query, *, source =
  "booking_link", now)`, `create_appointment`, `reschedule_appointment`, `cancel_appointment`,
  `list_client_appointments`, `client_change_deadline`, `get_appointment`; exceções
  `SlotUnavailable`, `BookingWindowError`, `ChangeWindowClosed`, `NotYourAppointment`; campo
  `attendee_name` (PD-32), `combo_id` (Q-S05-1) e status inicial pela PD-31.
- **S05** (`catalog`) — `list_bookable_combos` (Q-S05-1). **Assumido a mais:** `SlotUnavailable` com até
  6 alternativas.
- **S10** (`messaging`) — `send_template(purpose="otp", phone=..., origin="otp")` com o texto
  mascarado no histórico; `send_platform_otp(phone, shop_name, code)` quando a barbearia não tem
  número conectado (Q-S04-1); modelo de autenticação aprovado na conexão; `whatsapp_url` do número
  geral e por unidade (PD-42); bucket privado (logo).
- **S13** — `clients.public.find_client_by_phone`, `create_client(source)`, `normalize_phone`,
  `get_client_summary` (faltas), `record_opt_in(session, client_id, source)` e
  `record_marketing_consent(session, client_id, source)` (PD-30); eventos `client.updated`,
  `client.merged`, `client.anonymized`.
- **S01** — `identity.public.get_shop_settings` (contato, `about`, `instagram`, políticas),
  `list_units(online_only=True)`.
- **S15** — `identity.public.has_feature(PlanFeature.ONLINE_BOOKING)` nas rotas públicas e
  `require_feature` nas do painel.
- **S00** — consumo de evento (revogar sessões).
- Infra: Turnstile (conta Cloudflare); regra no servidor web de produção para robôs de prévia (T6).

## Notes

- **A conferir na documentação da Meta:** formato do modelo de autenticação (texto fixo, botão de
  copiar código, validade informada), preço por mensagem de autenticação no Brasil e limites de envio
  por número.
- **A conferir com a infra de produção:** quem serve o `index.html` (para o T6) e se o domínio
  próprio (`custom_domain`) tem certificado para o cookie `Secure`.
- Em desenvolvimento (localhost) a página roda em `/agendar` com o slug guardado como no login, e o
  cookie vai sem `Secure`.
- Proteção extra possível depois: bloqueio de telefones descartáveis/virtuais e limite por ASN.

### Perguntas em aberto

- ✅ **Q-S04-1 — Barbearia sem WhatsApp conectado pode ter link de agendamento?** (a) Não: o link só
  liga com o WhatsApp conectado; (b) sim, e o código sai de um **número da plataforma Navalha**
  (modelo de autenticação genérico, custo da plataforma); (c) sim, sem código (só nome e telefone),
  aceitando o risco de agendamento falso. **Recomendação: (b)** — o link é o canal do plano sem IA e
  não deve depender da conexão; custo por código é baixo e o limite por barbearia (T3) segura abuso.
  > Resolvido em 2026-11-06: (b) — sem WhatsApp conectado, o código do link sai de um número da
  > plataforma Navalha (ROADMAP §7).
- ✅ **Q-S04-2 — Cliente com faltas pode agendar pelo link?** (a) Sim, sem restrição; (b) bloqueia
  depois de N faltas nos últimos 90 dias (configurável) com "Para agendar, fale com a barbearia pelo
  WhatsApp"; (c) permite, mas o agendamento já nasce "não confirmado" para a recepção decidir.
  **Recomendação: (b)**, desligado por padrão (`block_after_no_shows = null`) — quem sofre com falta
  liga; quem não sofre não perde cliente.
  > Resolvido em 2026-11-06: (b) — bloqueio após N faltas configurável, desligado por padrão
  > (ROADMAP §7).
- ✅ Agendar para outra pessoa no mesmo telefone (pai para filho) e limite de agendamentos futuros
  são perguntas da S03 (Q-S03-5 e Q-S03-4); esta spec só repassa os campos.
  > Resolvido em 2026-11-06: campo "para quem" (`attendee_name`), com horários simultâneos do mesmo
  > cliente (PD-32); limite de futuros configurável, padrão 3 (ROADMAP §7).
