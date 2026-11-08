# Canal WhatsApp e Central de conversas (S10)

**Priority:** high
**Status:** draft
**Espelho no frontend:** `frontend/docs/specs/⚪draft_frontend-inbox.md`

## Overview

Liga o número de WhatsApp da barbearia ao Navalha pela **Cloud API oficial da Meta, em
coexistência com o app WhatsApp Business** (PD-15): o dono continua usando o app no celular, no
mesmo número, e tudo — o que o cliente manda, o que a IA responde, o que a equipe responde pelo
painel **e pelo celular** — aparece na Central de conversas. Este módulo (`messaging`) é o **canal**:
conexão do número (Embedded Signup), webhook global com verificação de assinatura e roteamento por
`phone_number_id`, conversas e mensagens (texto, áudio, imagem, botões, status de entrega), janela
de 24 h, modelos (templates) da Meta, fila "aguardando humano" (PD-18), vínculo conversa ↔ cliente
e opt-out por palavra-chave. Ele **não decide o que responder**: a IA (S11, `assistant`) e as
automações (S12, `automations`) usam as funções públicas daqui para enviar, e reagem aos eventos que
este módulo publica.

Fica de fora: o agente de IA (S11), lembretes e campanhas (S12), o OTP do link (S04 usa o envio de
template daqui), notificação push (PD-18: não há), grupos, chamadas de voz, importação de histórico
além dos ~6 meses que a coexistência oferece (Q-S10-3) e a cobrança das mensagens da Meta (PD-28:
a barbearia paga direto à Meta).

## Decisões de produto já tomadas

| Parâmetro | Valor |
|---|---|
| PD-15 | Cloud API em **coexistência** com o app WhatsApp Business; o que a equipe responde no celular aparece no painel. |
| PD-18 | Handoff vai para a fila **"aguardando humano"** com o resumo da IA; a IA para até a equipe **devolver**. Sem push, sem aviso no WhatsApp pessoal, sem retomada automática. |
| PD-03 | Cliente é da barbearia; telefone E.164 único — é a chave que liga conversa e cliente. |
| PD-20 | Toda mensagem iniciada pela barbearia respeita o opt-out do cliente. |
| PD-21/22 | Recurso pago verifica o plano (S15) e responde **402**. |
| PD-28 | **Custo da Meta**: no início a barbearia paga direto à Meta com o cartão dela (Navalha como Tech Provider; o painel só estima); depois o Navalha vira Solution Partner e repassa pela fatura do Core. |
| PD-30 | Consentimento de marketing: pode receber quem tem ao menos um atendimento; importados e contatos sem atendimento só com "sim" explícito. Utilidade vale para todo cliente com agendamento. Opt-out sempre respeitado. (A regra mora na S13; aqui só se consulta `get_contact_policy`.) |
| PD-37 | A IA não fecha venda de clube/pacote: registra o interesse e faz handoff com motivo `sale` ("Venda de clube/pacote"). |
| PD-40 | IA por créditos: créditos acabaram → conversa nova vai para "aguardando humano" com motivo `no_ai_credits`. Quem debita é o `assistant` (S11/S15), não este módulo. |
| PD-42 | **Números de WhatsApp**: um geral e, opcionalmente, um por unidade, com quantidade limitada pelo plano (`whatsapp_numbers`, S15). |
| Desenho multi-tenant (doc §5, Camada 4) | App Secret e verify token **globais**; `public.whatsapp_number_routes` (`phone_number_id` UNIQUE → tenant) espelha o número do schema; token Meta por barbearia com **envelope encryption** (DEK por tenant). |

### Decisões técnicas desta spec (propostas, revisar na aprovação)

| # | Decisão | Por quê |
|---|---|---|
| T1 | Segredos do app Meta (`META_APP_ID`, `META_APP_SECRET`, `META_WEBHOOK_VERIFY_TOKEN`, `META_GRAPH_API_VERSION`, `META_ES_CONFIG_ID`) em **variável de ambiente**, não em tabela. | Um app só, regra "segredo vem do ambiente" (rules.md). O doc §5 aceita env como origem. |
| T2 | Envelope encryption entra **aqui** (primeiro consumidor): `app/core/crypto.py` (AES-256-GCM), KEK em `SECRETS_KEK`, DEK por barbearia em `public.tenants.dek_wrapped`. AAD = `tenant_id:tabela:coluna:id` (ciphertext não pode ser trocado de linha). | Camada 4. Reaproveitável por S11/S12. |
| T3 | Envio **sempre assíncrono**: a mensagem nasce `queued` na mesma transação, com um job do worker (S00) que chama a Graph API depois do commit. | Nada sai para a Meta de transação que pode dar rollback; retry com backoff num só lugar. |
| T4 | Mídia (áudio, imagem, documento) baixada pelo worker para **object storage S3-compatível privado**, chave `tenants/<tenant_id>/media/<uuid>`; o painel lê por rota autenticada do backend (nunca URL pública). Retenção de mídia: 180 dias. | Camada 5 (URL pública vazou no ClaraCRM); a URL da Meta expira em minutos e a mídia some de lá em 30 dias. |
| T5 | Atualização da Central por **polling** (TanStack Query) nesta versão; SSE/WebSocket por tenant depois. | Menos infraestrutura; a fila é pequena por barbearia. |

## Business Rules

### Conexão do número (Embedded Signup, coexistência)

- [ ] Conectar exige `tenant:configure` e o recurso `whatsapp` no plano
      (`require_feature(PlanFeature.WHATSAPP)`, 402 sem ele). Limite de números por barbearia:
      `whatsapp_numbers` (S15, PD-42), contando os números não `disconnected`, com
      `assert_within_limit` → 402 `plan_limit_reached` (`limit: "whatsapp_numbers"`).
- [ ] Desenho dos números (PD-42): **no máximo um número geral** (`unit_id = null`, atende a
      barbearia toda) e **no máximo um por unidade**. Conectar ou mudar a unidade (`PATCH`) para uma
      unidade que já tem número, ou criar um segundo geral → 409 "Esta unidade já tem um número
      conectado" / "A barbearia já tem um número geral". O primeiro número conectado nasce geral por
      padrão; a barbearia de uma unidade só fica com ele.
- [ ] Cobrança da Meta (PD-28): no Embedded Signup a barbearia cadastra a forma de pagamento **na
      conta WhatsApp dela** (Navalha como Tech Provider); o Navalha não cobra nem repassa mensagens.
      O painel só **estima** o custo pelo `pricing_category` das mensagens enviadas (S12). Quando o
      Navalha virar Solution Partner, o repasse entra pela fatura do Core sem mudar este contrato.
- [ ] O frontend roda o Embedded Signup da Meta no fluxo de **coexistência** (onboarding de número
      do app WhatsApp Business) e envia ao backend `code`, `waba_id` e `phone_number_id`. O backend
      troca o `code` pelo token do negócio, assina o app na WABA (`subscribed_apps`), lê o número
      (E.164, nome verificado, qualidade) e grava `whatsapp_numbers` + `public.whatsapp_number_routes`
      **na mesma operação lógica**: rota primeiro (o `UNIQUE` barra número de outra barbearia → 409
      "Este número já está conectado a outra conta Navalha"), depois o número; falha no segundo passo
      apaga a rota (compensação), e um teste prova que as duas nunca divergem.
- [ ] O token da Meta é gravado só cifrado com a DEK da barbearia (T2) e nunca sai em resposta, log
      ou evento.
- [ ] Um número pode ser ligado a uma unidade (`unit_id`) ou atender a barbearia toda (`null`); a
      unidade define o escopo `unit` das conversas dele (ver Permissões). Roteamento: conversa que
      chega pelo número de uma unidade nasce com `conversations.unit_id` = unidade do número; pelo
      número geral nasce com `unit_id = null` (a equipe ou a IA definem a unidade ao agendar).
      Mensagem iniciada pela barbearia (`send_template` com `unit_id`) sai pelo número da unidade e,
      se ela não tiver, pelo geral.
- [ ] Desconectar (`DELETE`) remove a rota, desassina o app quando for o último número da WABA, marca
      o número `disconnected` e **mantém** conversas e mensagens. Reconectar o mesmo número reaproveita
      o registro.
- [ ] Na conexão, os **modelos do sistema** (tabela em Data Contract) são submetidos à Meta na WABA da
      barbearia, em `pt_BR`. Já existentes com o mesmo nome são adotados, não duplicados.

### Webhook global

- [ ] `GET /webhooks/meta` responde o `hub.challenge` só com `hub.mode=subscribe` e `hub.verify_token`
      igual ao global (comparação em tempo constante); senão 403.
- [ ] `POST /webhooks/meta` valida `X-Hub-Signature-256` (HMAC-SHA256 do corpo **cru** com o App
      Secret) **antes** de qualquer parse; inválida ou ausente → 401, nada é processado.
- [ ] A rota fica fora da resolução de tenant por host (é a única exceção à DEC-002, documentada): o
      tenant vem **só** de `whatsapp_number_routes` pelo `metadata.phone_number_id` (mensagens,
      status, echoes) ou pelo `waba_id` (status de template, qualidade, conta). Número desconhecido →
      200 e log de aviso (a Meta não deve reenviar para sempre), nunca erro.
- [ ] O webhook responde 200 rápido: grava mensagens/status na sessão do tenant, publica eventos no
      outbox e deixa download de mídia e respostas para o worker. Um lote com entradas de várias
      barbearias abre uma sessão por tenant.
- [ ] Idempotência: `messages.wamid` é UNIQUE; webhook repetido não duplica mensagem nem evento.
      Status só avança (`sent → delivered → read`; `failed` vale de qualquer estado) — status atrasado
      fora de ordem é ignorado.
- [ ] Campos assinados: `messages`, `smb_message_echoes`, `message_template_status_update`,
      `phone_number_quality_update`, `account_update`, `history` e `smb_app_state_sync` (Q-S10-3).

### Histórico do app (Q-S10-3)

- [ ] Na conexão em coexistência, o histórico que a Meta oferece (até ~6 meses) é importado pelo
      worker a partir do webhook `history`: mensagens gravadas com `wamid` (idempotente), `status`
      final e data original, sem abrir janela de 24 h.
- [ ] A conversa importada só é **ligada a cliente que já existe** (`find_client_by_phone`); contato
      sem cliente fica com `client_id = null` e **não cria cliente** (não enche o cadastro com contatos
      pessoais do dono). Mensagem importada não grava opt-in, não publica
      `conversation.message_received` (a IA e as automações não reagem a ela) e não mexe em
      `unread_count`.

### Conversas e mensagens

- [ ] Uma conversa por contato por número: `UNIQUE (whatsapp_number_id, contact_phone)`. Ela é
      permanente (o histórico inteiro do contato); o que muda é `status` (`open`/`resolved`) e `mode`.
- [ ] `mode`: `ai` (a IA responde), `waiting_human` (fila PD-18; ninguém respondeu ainda),
      `human` (alguém da equipe assumiu). Transições:
      `ai → waiting_human` (handoff da IA, pedido explícito do cliente, IA desligada/fora do horário,
      sem créditos de IA — PD-40, motivo `no_ai_credits`; venda de clube/pacote — PD-37, motivo
      `sale`); `waiting_human|ai → human` (equipe assume no painel, ou responde pelo
      celular — echo); `human|waiting_human → ai` só por **"Devolver para a IA"** (PD-18) ou ao
      **resolver** a conversa (a próxima mensagem do cliente recomeça com a IA, se ligada).
- [ ] Mensagem nova do cliente numa conversa `resolved` reabre (`open`), mantendo o `mode` corrente.
- [ ] Toda mensagem recebida: normaliza o telefone (`clients.public.normalize_phone`) e procura o
      cliente com `find_client_by_phone` (segue a lápide de cliente mesclado, S13); se não há, **cria**
      com `create_client(source = whatsapp)` (nome = nome do perfil do WhatsApp, ou "Cliente WhatsApp"
      + 4 últimos dígitos) e liga `client_id`. Corrida entre dois webhooks do mesmo número novo: o 409
      do telefone único vira "busca e liga". A primeira mensagem do cliente grava opt-in de origem
      `inbound_message` se ainda não houver (`record_opt_in`, S13).
- [ ] A equipe pode religar a conversa a outro cliente (`PUT /conversations/{id}/client`) — ex.: o
      cliente cadastrado com outro número; não muda o telefone de ninguém.
- [ ] Tipos suportados na entrada: texto, áudio/voz, imagem, vídeo, documento, figurinha, localização,
      contato, reação, resposta de botão (`button`/`interactive.button_reply`/`list_reply`).
      Desconhecido vira `unsupported` com o texto "Tipo de mensagem não suportado" no painel.
- [ ] Mídia recebida: o worker baixa (T4) e só então publica `conversation.message_received` para
      áudio (a IA precisa do arquivo para transcrever); para os outros tipos o evento sai na hora.
- [ ] Echo da coexistência (`smb_message_echoes`): vira mensagem `outbound`, `author = phone_app`,
      já `sent`; **não** abre a janela de 24 h; leva a conversa para `human` (a IA para ali), com
      `assigned_user_id = null` e `human_via_phone_at` = horário do echo (Q-S10-4).
- [ ] Pausa pelo celular (Q-S10-4): cada echo agenda (`schedule_job`, `dedupe_key =
      phone_pause:<conversation_id>`) a verificação para **12 h** depois do último echo. Se até lá não
      houve outra mensagem da equipe (painel ou celular) e a conversa continua `human` sem responsável
      no painel, ela é **resolvida sozinha** (nota de sistema "Resolvida após 12 h sem resposta da
      equipe pelo celular"); a próxima mensagem do cliente recomeça com a IA, se ligada. Alguém que
      assume no painel cancela essa regra (`human_via_phone_at = null`). Não é retomada de handoff:
      conversa que veio da fila (PD-18) só volta à IA por "Devolver" ou "Resolver".
- [ ] Saída: texto, mídia (imagem/documento), interativo (até 3 botões de resposta ou lista de até 10
      linhas, limites da Meta) e template. Toda saída nasce `queued` (T3) e avança por webhook.
      Falha da Meta grava `error_code` + mensagem e, se for permanente, `failed` sem retry.
- [ ] **Janela de 24 h**: texto livre/interativo só com `now < last_inbound_at + 24h`. Fora dela, só
      template aprovado → 409 "Fora da janela de 24 h: use um modelo aprovado". A resposta da conversa
      traz `window_expires_at` para o painel.
- [ ] Responder pelo painel exige `conversation:reply` e `mode = human` com o próprio usuário como
      responsável; em `ai`/`waiting_human` → 409 "Assuma a conversa para responder". Assumir conversa
      de outro atendente é permitido e registra quem assumiu (nota de sistema na conversa).
- [ ] Abrir a conversa no painel zera `unread_count` e marca como lida na Meta (visto azul) a última
      mensagem recebida.
- [ ] Mensagem de sistema (`author = system`, não enviada ao cliente) registra no histórico:
      assumiu, devolveu, resolveu, handoff (com o resumo da IA), agendamento criado pela IA e
      **cancelamento feito pela IA** (nota para a recepção, PD-29 — S11 grava por `add_system_note`).

### Opt-out

- [ ] Texto recebido que, aparado e sem acento/caixa, seja exatamente `SAIR`, `PARAR`, `STOP` ou
      `DESCADASTRAR`, ou o botão de opt-out de um template de marketing → grava **na hora**
      `clients.public.record_opt_out(session, client_id, scope = "marketing", source = "whatsapp")`
      e responde com mensagem interativa de **dois botões** (Q-S12-2): "Pronto, você não vai mais
      receber nossas promoções. Quer parar também os lembretes dos seus horários?" com
      [Só promoções] (payload `opt_out_marketing`) e [Tudo] (payload `opt_out_all`).
- [ ] Clique em **"Só promoções"** mantém o opt-out de marketing e responde "Combinado: só os avisos
      dos seus horários continuam. Para voltar a receber promoções, responda VOLTAR." Clique em
      **"Tudo"** grava `record_opt_out(..., scope = "all", source = "whatsapp")` e responde "Pronto,
      você não vai mais receber nossas mensagens. Para voltar, responda VOLTAR." Sem clique, vale o
      opt-out de marketing já gravado.
- [ ] A palavra-chave e o clique nos botões publicam o evento marcado `handled = "opt_out"` (a IA
      não responde a eles). `VOLTAR` → `clients.public.record_opt_in(session, client_id, source =
      "keyword")`, que limpa os dois opt-outs, e responde "Pronto, você voltou a receber nossas
      mensagens."
- [ ] `send_template` com `category = marketing` ou `utility` iniciado pela barbearia (`origin` ≠
      `conversation`) pergunta `clients.public.get_contact_policy(client_id)` (lê `utility_allowed` ou `marketing_allowed` conforme o propósito) e recusa com
      `OptedOut`; quem chama registra como "pulado". A regra de quem pode receber (PD-30: marketing
      só para quem tem ao menos um atendimento ou disse "sim" explícito; utilidade para todo cliente
      com agendamento) é da S13; este módulo não a repete.
      O template de autenticação (OTP pedido pelo próprio cliente) não é bloqueado.
- [ ] Mensagem com `origin = otp` é gravada **sem o código** (texto "Código de acesso enviado") e não
      cria cliente; a equipe nunca vê o código na Central.

### Modelos (templates)

- [ ] Cadastro, submissão e acompanhamento de modelos por WABA: `draft → pending → approved |
      rejected`, depois `paused`/`disabled` conforme a Meta. Status chega por webhook e também por
      `POST /whatsapp/templates/sync`.
- [ ] Variáveis **nomeadas** (`{{nome_cliente}}`), com exemplo obrigatório; o envio valida que todas
      foram preenchidas (400 "Preencha a variável X").
- [ ] Modelo aprovado não é editado: editar cria uma nova versão (`<nome>_v2`) e a anterior segue em
      uso até a nova ser aprovada (quem consome — S12 — escolhe pela `purpose`, não pelo nome).
- [ ] Categoria é sugerida por nós, mas a Meta pode reclassificar (ex.: utilidade → marketing); a
      categoria gravada é a que a Meta devolveu, porque é ela que define custo e opt-out.

## Data Contract

```text
# Conexão — tag "whatsapp" (tenant:configure, salvo indicação)
GET    /whatsapp/signup-config                 → 200 {app_id, config_id, graph_api_version}
GET    /whatsapp/numbers                       → 200 WhatsappNumberOut[]   (conversation:read também lê)
POST   /whatsapp/numbers  {code, waba_id, phone_number_id, unit_id?}
                                               → 201 WhatsappNumberOut | 400 | 402 (whatsapp_numbers) | 409 | 502PATCH  /whatsapp/numbers/{id}  {unit_id}       → 200 | 404 | 409 (unidade já tem número / já há geral) | 422
DELETE /whatsapp/numbers/{id}                  → 204 | 404

WhatsappNumberOut {id, display_phone, verified_name, unit_id, status, coexistence,
                   quality_rating, messaging_limit_tier, connected_at, last_error}

# Modelos — tag "whatsapp"
GET    /whatsapp/templates?purpose=&status=    → 200 TemplateOut[]  (conversation:reply ou tenant:configure)
POST   /whatsapp/templates  TemplateIn         → 201 TemplateOut (pending) | 400 | 402 | 409 | 502
DELETE /whatsapp/templates/{id}                → 204 | 404 | 409 (modelo do sistema)
POST   /whatsapp/templates/sync                → 200 TemplateOut[]

TemplateIn  {name (a-z0-9_), category, language="pt_BR", purpose="custom"|"campaign",
             header?: {type: text|image, text?}, body, footer?, buttons?: [{type: quick_reply|url,
             text, url?}], examples: {var: valor}}
TemplateOut {id, name, language, category, purpose, status, rejection_reason, body, variables[],
             buttons[], system: bool, created_at, updated_at}

# Central — tag "conversations"
GET  /conversations?queue=all|waiting_human|mine|ai|resolved&q=&unit_id=&limit=30&cursor=
                                               → 200 {items: ConversationSummary[], next_cursor}
GET  /conversations/counts                     → 200 {waiting_human, unread}
GET  /conversations/{id}                       → 200 ConversationOut | 404
GET  /conversations/{id}/messages?before=&limit=50 → 200 {items: MessageOut[], next_cursor}
POST /conversations/{id}/messages  OutgoingIn  → 202 MessageOut | 400 | 402 | 409 | 422
POST /conversations/{id}/assume                → 200 ConversationOut | 404
POST /conversations/{id}/return-to-ai          → 200 | 402 | 409 ("A IA está desligada")
POST /conversations/{id}/resolve               → 200 | 404
POST /conversations/{id}/read                  → 204
PUT  /conversations/{id}/client  {client_id}   → 200 | 400 | 404
GET  /conversations/{id}/messages/{message_id}/media → 200 (stream, Content-Type da mídia) | 404 | 410 (expirada)

ConversationSummary {id, contact_name, contact_phone, client_id, unit_id, status, mode,
                     assigned_user {id, name} | null, last_message_preview, last_message_at,
                     unread_count, handoff_reason}
ConversationOut     ConversationSummary + {window_expires_at, handoff_summary,
                     handoff_requested_at, opt_out_scope: null|"marketing"|"all",
                     human_via_phone_at | null, whatsapp_number {id, display_phone, unit_id}}
MessageOut {id, direction, author: client|ai|staff|phone_app|automation|system, author_user_name,
            type, text, transcript, media {mime_type, size_bytes, available} | null,
            interactive | null, template_name | null, status, error_message, created_at}
OutgoingIn {kind: "text", text (1..4096)} | {kind: "template", template_id, variables{}}
           | {kind: "media", upload_id, caption?}   (upload: POST /conversations/{id}/uploads, 16 MB)

# Webhook — tag "webhooks", fora do /docs público, sem tenant por host
GET  /webhooks/meta?hub.mode&hub.verify_token&hub.challenge → 200 text | 403
POST /webhooks/meta   (X-Hub-Signature-256)    → 200 | 401

Erros: {"detail": "<mensagem em português>"}. 502 "O WhatsApp não respondeu; tente de novo" quando a
Graph API falha numa chamada síncrona (conexão, criação de modelo).
```

### Funções públicas (`messaging/public.py`)

```text
send_text(session, *, conversation_id, text, author: Author, author_user_id=None,
          origin: Origin = "conversation", origin_ref: str | None = None) -> MessageRef
send_interactive(session, *, conversation_id, body, buttons: list[Button] | None,
                 list_rows: list[ListRow] | None, author, origin, origin_ref) -> MessageRef
send_template(session, *, client_id | phone, purpose | template_id, variables: dict,
              origin: Origin, origin_ref: str | None, unit_id: UUID | None = None) -> MessageRef
    # escolhe o número (o da unidade, senão o geral), cria a conversa se não existir
    # levanta WindowClosed, OptedOut, NoWhatsappNumber, TemplateNotApproved, FeatureUnavailable
send_platform_otp(*, phone, shop_name, code) -> None
    # OTP do link (S04, Q-S04-1) quando a barbearia não tem número conectado: sai do número da
    # plataforma Navalha (PLATFORM_WHATSAPP_PHONE_NUMBER_ID / PLATFORM_WHATSAPP_TOKEN, env), modelo de
    # autenticação genérico; não cria conversa nem mensagem na barbearia
is_window_open(session, conversation_id) -> bool
get_conversation_context(session, conversation_id, *, limit=40) -> ConversationContext
    # mensagens (texto/transcrição/tipo), modo, client_id, unit_id, janela
get_media(session, message_id) -> bytes + mime        # para a transcrição (S11)
set_transcript(session, message_id, text) -> None
request_handoff(session, *, conversation_id, reason: HandoffReason, summary: str) -> None
add_system_note(session, *, conversation_id, text, origin_ref: str | None = None) -> MessageRef
    # mensagem author = system, não enviada ao cliente; ex.: "A IA cancelou o horário de
    # sex 15:30 com o Rafael a pedido do cliente" (S11, PD-29)
mark_ai_typing(session, conversation_id) -> None       # "digitando…" + visto azul
Origin  = conversation | automation | campaign | otp | system
Author  = ai | staff | automation | system
HandoffReason = client_asked | ai_decided | ai_unavailable | ai_off | out_of_hours |
                no_ai_credits | sale | complaint | low_review | reschedule_request
    # no_ai_credits = "Sem créditos de IA" (PD-40); sale = "Venda de clube/pacote" (PD-37)
```

### Eventos

| Evento | Quando | Payload |
|---|---|---|
| `conversation.message_received` | mensagem do cliente gravada (áudio: depois do download); não sai para mensagem importada do histórico | `conversation_id, message_id, client_id, type, button_payload, handled` (`null` \| `"opt_out"`) |
| `conversation.handoff_requested` | entrou em `waiting_human` | `conversation_id, client_id, reason` (o resumo, texto livre, fica na conversa e não vai no evento — regra do S00) |
| `conversation.assumed` / `.returned_to_ai` / `.resolved` | ações da equipe (ou echo) | `conversation_id, user_id \| null` |
| `message.delivery_updated` | status de saída com `origin` ≠ `conversation` mudou | `message_id, origin, origin_ref, status, error_code` |
| `whatsapp.number_status_changed` | conectado, desconectado, qualidade caiu | `number_id, status, quality_rating` |

Registra um `ClientDataHandler` no `clients.public` (S13): **exportar** devolve conversas e mensagens
do cliente; **anonimizar** apaga texto, transcrição e mídia das mensagens e o nome do contato,
mantendo tipos e datas para relatórios; **mesclar** re-aponta `conversations.client_id` da origem
para o destino.

### Banco de dados

Controle (`alembic/control`, `c000N_whatsapp_routes`, com `GRANT SELECT, INSERT, DELETE` ao runtime):

```text
whatsapp_number_routes  phone_number_id varchar(32) pk · tenant_id uuid → tenants.id ON DELETE CASCADE ·
                        waba_id varchar(32) · created_at       INDEX (waba_id)
tenants                 + dek_wrapped bytea null · + dek_kek_id varchar(16) null
```

Tenant (`alembic/tenant`, `t000N_messaging`, expand only):

```text
whatsapp_numbers   id · phone_number_id varchar(32) UNIQUE · waba_id varchar(32) · display_phone varchar(16) ·
                   verified_name varchar(120) · unit_id → units.id ON DELETE SET NULL null ·
                   status enum whatsapp_number_status(connecting, connected, disconnected, error) ·
                   coexistence bool · access_token_enc text · token_expires_at null ·
                   quality_rating varchar(16) null · messaging_limit_tier varchar(16) null ·
                   connected_at · disconnected_at null · last_error varchar(500) null · timestamps
                   UNIQUE (unit_id) WHERE unit_id IS NOT NULL AND status <> 'disconnected' ·
                   UNIQUE ((true)) WHERE unit_id IS NULL AND status <> 'disconnected'   (um geral, PD-42)
conversations      id · whatsapp_number_id → whatsapp_numbers.id RESTRICT · contact_phone varchar(16) ·
                   contact_name varchar(120) null · client_id → clients.id RESTRICT null ·
                   unit_id → units.id SET NULL null · status enum conversation_status(open, resolved) ·
                   mode enum conversation_mode(ai, waiting_human, human) ·
                   assigned_user_id → users.id SET NULL null · handoff_reason varchar(32) null ·
                   handoff_summary text null · handoff_requested_at null · last_inbound_at null ·
                   human_via_phone_at timestamptz null (Q-S10-4) ·
                   last_message_at · last_message_preview varchar(200) · unread_count int default 0 ·
                   timestamps
                   UNIQUE (whatsapp_number_id, contact_phone) · INDEX (mode, last_message_at) ·
                   INDEX (client_id)
messages           id · conversation_id → conversations.id RESTRICT ·
                   direction enum message_direction(inbound, outbound) ·
                   author enum message_author(client, ai, staff, phone_app, automation, system) ·
                   author_user_id → users.id SET NULL null · type enum message_type(...) ·
                   text text null · transcript text null · interactive jsonb null ·
                   template_id → message_templates.id SET NULL null · wamid varchar(128) UNIQUE null ·
                   reply_to_wamid varchar(128) null ·
                   status enum message_status(received, queued, sent, delivered, read, failed) ·
                   error_code int null · error_message varchar(300) null ·
                   media_key varchar(255) null · media_mime varchar(100) null · media_size int null ·
                   media_expires_at null · origin enum message_origin(...) · origin_ref varchar(80) null ·
                   pricing_category varchar(20) null · imported bool default false (Q-S10-3) ·
                   sent_at/delivered_at/read_at null · created_at
                   INDEX (conversation_id, created_at desc)
message_templates  id · waba_id varchar(32) · name varchar(512) · language varchar(10) ·
                   category enum template_category(marketing, utility, authentication) ·
                   purpose varchar(40) · system bool · components jsonb · variables jsonb ·
                   status enum template_status(draft, pending, approved, rejected, paused, disabled) ·
                   rejection_reason varchar(300) null · meta_template_id varchar(40) null ·
                   created_by → users.id SET NULL null · timestamps
                   UNIQUE (waba_id, name, language) · INDEX (purpose, status)
```

Modelos do sistema submetidos na conexão (texto final definido pela spec dona):

| `purpose` | Categoria | Dono |
|---|---|---|
| `otp` | authentication | S04 |
| `appointment_reminder` (botões Confirmar/Remarcar/Cancelar), `appointment_created` | utility | S12 |
| `review_request` | utility (a Meta pode reclassificar) | S12 |
| `reactivation`, `birthday` | marketing | S12 |
| `reopen_conversation` ("Oi {{nome_cliente}}, sobre sua mensagem…") | utility | S10 — a equipe usa para responder fora da janela |

## Permissões

Sem permissão nova.

| Ação | Permissão | owner | manager | receptionist | barber |
|---|---|---|---|---|---|
| ver Central e mensagens | `conversation:read` | todas | conversas das suas unidades + de números sem unidade | idem manager | `own`: conversas de clientes que ele já atendeu (relação da S13), só leitura |
| responder, assumir, devolver, resolver, religar cliente | `conversation:reply` | sim | suas unidades | suas unidades | — |
| listar modelos (para responder fora da janela) | `conversation:reply` | sim | sim | sim | — |
| conectar/desconectar número, criar/apagar modelos | `tenant:configure` | sim | — | — | — |

## Acceptance Criteria

- [ ] Módulo `messaging` com o layout completo + `jobs/` (envio, download de mídia, sync de
      modelos); `messaging` importa `identity`, `clients` e `scheduling` só pelo
      `public.py`; nada abaixo importa `messaging`. Contratos do `lint-imports` atualizados.
- [ ] `app/core/crypto.py` (T2) com teste: cifra/decifra, AAD errado falha, DEK de A não abre B.
- [ ] Migrations `c000N` e `t000N` aplicadas; `alembic check` limpo nos dois conjuntos.
- [ ] Testes do webhook com payloads gravados da Meta (fixtures): assinatura inválida → 401;
      roteamento para a barbearia certa entre **duas barbearias**; número desconhecido → 200 sem
      efeito; repetição não duplica; status fora de ordem ignorado; echo leva a `human`.
- [ ] Teste de que rota e número não divergem (falha simulada no meio da conexão).
- [ ] Testes de janela de 24 h, opt-out por palavra-chave (SAIR grava marketing na hora; botão
      "Tudo" grava `all`; VOLTAR limpa), criação/ligação de cliente (com corrida), transições de
      `mode` e o 409 de responder sem assumir.
- [ ] Testes de números (PD-42): limite `whatsapp_numbers` → 402; segundo número geral ou segundo
      número na mesma unidade → 409; conversa nasce com a unidade do número; `send_template` com
      `unit_id` sai pelo número da unidade e, sem ele, pelo geral.
- [ ] Teste do histórico importado (Q-S10-3): liga só a cliente existente, não cria cliente, não
      publica evento. Teste da pausa pelo celular (Q-S10-4): 12 h sem mensagem da equipe → resolvida;
      assumir no painel cancela.
- [ ] Cliente HTTP da Graph API isolado e substituído por um falso nos testes (nenhum teste chama a
      Meta).
- [ ] Variáveis novas em `.env.example` e `docs/ENVIRONMENT_VARIABLES.md`; dependências novas
      (`httpx`, `cryptography`, cliente S3) aprovadas e registradas.
- [ ] Snapshots revisados; `make docs-api`; `make check` verde.
- [ ] Testes em `tests/test_messaging/` cobrindo as regras acima
- [ ] Snapshots de contrato revisados (`UPDATE_CONTRACT_SNAPSHOTS=1` só se a mudança for intencional)

## Dependencies

- **S00** (`platform-events-jobs`) — `app.core.events.publish(session, type, payload, *,
  aggregate_id, actor)` no outbox da transação; `SUBSCRIBERS`/`JOB_HANDLERS` no `public.py`;
  `schedule_job(session, name, *, run_at, payload, dedupe_key=None)` (job com `run_at <= now` roda no
  próximo ciclo, ~1 s) e `cancel_job`; `Actor.assistant()`/`Actor.staff(id)`/`Actor.system()`.
- **S13** (`clients-profile`) — `clients.public`: `find_client_by_phone`, `create_client(source)`,
  `normalize_phone`, `get_contact_policy(session, client_id)`, `record_opt_out(session, client_id,
  scope: "marketing"|"all", source)`, `record_opt_in(session, client_id, source)` (fonte `keyword`
  para o VOLTAR), `register_client_data_handler`. O "sim" explícito de marketing
  (`record_marketing_consent`, PD-30) não é chamado por este módulo: vem do link (S04), das
  automações (S12) ou da recepção (S13).
- **S15** (`provisioning-plan-entitlements`) — `identity.public.require_feature(PlanFeature.WHATSAPP)`
  (402) e `assert_within_limit(WHATSAPP_NUMBERS)` (limite `whatsapp_numbers`, PD-42). Os créditos de
  IA (`reserve_ai_credits`/`settle_ai_credits`, `ai_credit_status`, PD-40/PD-43) são do `assistant`; este módulo só recebe o
  `request_handoff(reason = "no_ai_credits")`.
- **S03/S13** — escopo `own` do barbeiro: assumido `client_ids_served_by(session, barber_id)` na
  relação cliente ↔ barbeiro que a S13 mantém por evento (a S03 delegou essa relação à S13).
- **S01** — unidades (já existem).
- Infra nova: bucket S3-compatível privado (MinIO no compose de dev); app Meta com Embedded Signup
  configurado e o Navalha cadastrado como **Tech Provider**.
- Oferece a S11, S12 e S04: as funções públicas e os eventos acima.

## Notes

- **A conferir na documentação oficial da Meta na implementação:** fluxo de Embedded Signup para
  coexistência (`featureType`, campos devolvidos, se o número dispensa `/register`), países
  suportados e o requisito de abrir o app a cada ~14 dias para não perder a coexistência; nomes dos
  campos de webhook `smb_message_echoes`/`smb_app_state_sync`/`history`; vazão de números em
  coexistência (menor que a padrão); variáveis nomeadas em templates; limites de botões; códigos de
  erro (131047 janela, 131049 limite de marketing por usuário, 131050 usuário parou marketing);
  modelo de preço por mensagem e categorias vigentes; política de uso de IA no WhatsApp Business
  (assistente específico do negócio é permitido; assistente de uso geral não).
- **Coexistência e o celular:** o que a equipe faz no app (apagar, editar mensagem, chamadas,
  grupos) não tem espelho completo na API; o painel mostra só o que chega por echo.
- **Quem paga a Meta** (PD-28): no início, a barbearia, com o cartão dela na conta WhatsApp
  (Navalha Tech Provider); o painel só estima custo (S12). O FAQ da landing ("cobrado sem margem")
  precisa ser corrigido até o Navalha virar Solution Partner e repassar pelo Core.
- O token do Embedded Signup é de usuário de sistema do negócio e não expira na prática; se a Meta
  devolver token com validade, `token_expires_at` alimenta um alerta em `whatsapp.number_status_changed`.

### Perguntas em aberto

- ✅ **Q-S10-1 — Quem paga as mensagens da Meta?** (a) A barbearia cadastra o próprio cartão na conta
  WhatsApp dela (Navalha como Tech Provider; o painel só estima); (b) o Navalha vira Solution Partner,
  paga a Meta e repassa pelo Core (como promete a landing, "sem margem"); (c) começa com (a) e migra
  para (b) quando o volume justificar. **Recomendação: (c)** — (a) não exige linha de crédito nem
  conciliação agora; corrigir o FAQ da landing até lá.
  > Resolvido em 2026-11-06: (c) — no início a barbearia paga direto à Meta com o cartão dela
  > (Navalha Tech Provider, painel só estima); depois Solution Partner com repasse pela fatura do
  > Core (PD-28).
- ✅ **Q-S10-2 — Um número por barbearia ou por unidade?** (a) Um número para a barbearia toda;
  (b) um por unidade, obrigatório; (c) flexível: um geral e, opcionalmente, um por unidade, com o
  total limitado pelo plano. **Recomendação: (c)** — o modelo já suporta; a maioria tem um número só.
  > Resolvido em 2026-11-06: (c) — um número geral e, opcionalmente, um por unidade, com o total
  > limitado por `whatsapp_numbers` (PD-42).
- ✅ **Q-S10-3 — Importar o histórico do app na conexão?** A coexistência permite trazer até ~6 meses
  de conversas. (a) Não importar; (b) importar mensagens e ligar só a clientes que já existem (sem
  criar cliente por contato antigo); (c) importar tudo e criar clientes. **Recomendação: (b)** —
  dá contexto à equipe e à IA sem encher o cadastro com contatos pessoais do dono.
  > Resolvido em 2026-11-06: (b) — importa o histórico do app (até ~6 meses) e liga só a clientes
  > que já existem (ROADMAP §7).
- ✅ **Q-S10-4 — Quando alguém responde pelo celular, por quanto tempo a IA fica parada naquela
  conversa?** (a) Até alguém clicar "Devolver para a IA" ou "Resolver" (igual ao handoff);
  (b) até 12 h sem mensagem da equipe, e então a conversa é resolvida sozinha; (c) a IA nem para.
  **Recomendação: (b)** — o dono que responde no celular raramente abre o painel para devolver; sem
  isso a IA ficaria muda para aquele cliente para sempre. Não é retomada de handoff (PD-18 continua
  valendo para a fila).
  > Resolvido em 2026-11-06: (b) — resposta pelo celular pausa a IA até 12 h sem mensagem da equipe;
  > depois a conversa se resolve sozinha (ROADMAP §7).
