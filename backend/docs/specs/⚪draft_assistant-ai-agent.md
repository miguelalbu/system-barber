# Agente de IA do WhatsApp (S11)

**Priority:** high
**Status:** draft
**Espelho no frontend:** `frontend/docs/specs/⚪draft_frontend-assistant-settings.md`


> ⚠️ **Em revisão:** o modelo de créditos de IA (PD-40/43/44) será substituído por custo de tokens
> por barbearia com chave própria ou administrada pela plataforma — ver o aviso no ROADMAP §1.
> Revisar as partes de créditos antes de implementar.
## Overview

O agente que atende o cliente no WhatsApp **como a recepção da barbearia**: tira dúvidas pela base
de conhecimento, mostra horários livres, agenda, remarca, cancela e confirma, explica clube e pacote
(e passa a venda para a equipe, PD-37), entende áudio e, quando não deve ou não consegue seguir, passa
para a equipe pela fila "aguardando humano". O uso consome **créditos de IA** da barbearia (PD-40,
S15), proporcionais ao custo real de cada chamada ao provedor e de cada transcrição (PD-43), e o dono
vê o consumo em créditos e o custo estimado em US$ (PD-44). O módulo `assistant` não fala com a Meta (isso é o `messaging`, S10) nem
escreve na agenda por conta própria: ele **decide** o que fazer e executa só pelas funções públicas
de `scheduling`, `memberships`, `clients` e `messaging`. Por baixo, uma camada **multi-provedor**
(`app/core/llm/`) permite trocar Claude/OpenAI e modelo por configuração.

Fica de fora: lembretes, reativação e campanhas (S12 — a IA só atende o que o cliente responde),
venda com pagamento online (PD-10: não há gateway), visão computacional de fotos, voz sintetizada.

## Decisões de produto já tomadas

| Parâmetro | Valor |
|---|---|
| PD-16 | Multi-provedor por configuração; padrão **Claude (Anthropic)**, alternativa **OpenAI**. |
| PD-17 | Além de agenda: **base de conhecimento** do dono, **vende clube e pacote** (refinado pela PD-37: explica e encaminha, não fecha), **entende áudio**, **recupera abandono**. |
| PD-18 | Handoff → fila "aguardando humano" com o **resumo da IA**; a IA para até a equipe devolver. |
| PD-19 | Responde **como a recepção**; perguntaram "é robô?" → **desconversa e oferece um humano**; **nunca** afirma ser pessoa nem inventa nome de funcionário; pedido explícito de pessoa = handoff. |
| PD-04/05/06 | Grade de 15 min; vários serviços em sequência; mostra **todos os barbeiros livres**, "qualquer um" → regra de equilíbrio (executada pelo `scheduling`). |
| PD-07 | A IA confirma presença quando o cliente responde ao lembrete em texto livre; nunca cancela sozinha por falta de resposta. |
| PD-10 | Sem pagamento online: a IA não cobra. |
| PD-25 | Métricas de desempenho da IA para S14 (conversas, agendamentos, handoff, abandono, custo). |
| PD-29 | A IA **cancela sozinha** dentro da política de cancelamento e deixa uma **nota para a recepção**. |
| PD-37 | A IA **não fecha venda** de clube ou pacote: explica, registra o interesse e passa para a fila de humano (motivo `sale`); a equipe fecha. |
| PD-40 | **IA por créditos** comprados no Core (S15). Créditos acabaram → conversas novas vão para "aguardando humano" (`no_ai_credits`). Detalhes em PD-43. |
| PD-43 | **Crédito proporcional ao custo real** do provedor (`credits_per_usd` do plano, margem embutida): cada chamada ao modelo e cada transcrição debita. O plano inclui créditos por mês que não acumulam; comprados não vencem. Saldo nunca negativo (reserva antes da chamada, acerto depois). |
| PD-44 | O dono vê o consumo da IA **em créditos e o custo estimado em US$** (tela da IA, relatórios, página Plano). |

### Decisões técnicas desta spec (propostas, revisar na aprovação)

| # | Decisão | Por quê |
|---|---|---|
| T1 | **Chaves e escolha de modelo são da plataforma**, não da barbearia (sem "traga sua chave"). Variáveis de ambiente: `LLM_PROVIDER` (`anthropic`), `LLM_FALLBACK_PROVIDER` (`openai`), `LLM_MODEL_SMALL`, `LLM_MODEL_LARGE`, `OPENAI_MODEL_SMALL`, `OPENAI_MODEL_LARGE`, `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `TRANSCRIPTION_PROVIDER`, `TRANSCRIPTION_MODEL`. Padrão atual: `claude-haiku-5-5` (pequeno) e `claude-sonnet-5-5` (maior). | O dono de barbearia não tem nem quer ter chave de API; a qualidade só é garantida nos modelos que passaram no eval (T6); o uso é vendido em créditos (S15, PD-40) num só contrato e num só acordo de tratamento de dados (LGPD); o prefixo estático do prompt é igual para todas as barbearias e aproveita cache do provedor. Troca de modelo vira deploy de configuração, depois do eval. |
| T2 | Camada de provedor em `app/core/llm/` (infra sem regra de negócio): `LLMProvider.complete(system_blocks, messages, tools, model, max_tokens) -> LLMResult(content, tool_calls, usage, stop_reason)`, adaptadores `anthropic`, `openai` e `fake`; `TranscriptionProvider.transcribe(bytes, mime) -> text`. O formato interno de mensagem/ferramenta é nosso; cada adaptador traduz. | Trocar provedor sem tocar no agente (PD-16); o `fake` roda os testes sem rede. |
| T3 | **Modelo pequeno por padrão**, sobe para o maior no turno quando: agendamento com mais de um serviço ou barbeiro (PD-05); duas chamadas de ferramenta seguidas com erro de validação; conversa com mais de 12 turnos da IA sem agendamento nem resposta resolvida; ou o pequeno devolveu resposta reprovada pelos guardrails (T5). | A maioria das conversas é "tem horário?"; o maior só onde erra mais. |
| T4 | **Fallback de provedor**: erro 5xx/timeout depois dos retries do SDK → mesmo turno no provedor alternativo; os dois falharam → handoff `ai_unavailable` com resumo fixo ("Não consegui atender agora"). | Cliente nunca fica sem resposta e sem ninguém avisado. |
| T5 | **Guardrails de saída** em código, depois da geração e antes do envio (ver regras). Reprovou → uma nova tentativa com a correção como mensagem de sistema (no modelo maior); reprovou de novo → handoff. | O prompt sozinho não garante "não inventa preço". |
| T6 | Testes em dois níveis: unitários com provedor falso roteirizado (no `make check`) e **eval** de conversas roteirizadas com o provedor real (fora do `make check`, `make eval-assistant`, custo aprovado), obrigatório antes de mudar prompt, ferramenta ou modelo. | Mudança de modelo é mudança de comportamento. |
| T7 | A base de conhecimento vai **inteira** no contexto (cache por barbearia), com teto de 50 entradas e 20 000 caracteres; sem busca vetorial nesta versão. | Barbearia tem poucas perguntas frequentes; RAG é complexidade sem ganho aqui. |
| T8 | Sem leitura de imagem nesta versão: a IA recebe "[o cliente enviou uma imagem: <legenda>]" e diz que o barbeiro vai ver no atendimento (ou faz handoff se a imagem for o assunto). | Custo e risco; foto de referência é para o barbeiro, não para a IA. |
| T9 | **Reserva e acerto por chamada**, não por execução: um `CreditedCall` em volta de cada `LLMProvider.complete` e `TranscriptionProvider.transcribe` estima o custo máximo, reserva (`reserve_ai_credits`), chama, acerta (`settle_ai_credits`) e grava `assistant_calls`. A estimativa usa a tabela de preço da configuração: tokens de entrada contados localmente pelo adaptador (contagem conservadora, sem desconto de cache) + `max_tokens` de saída; transcrição = segundos do áudio × preço por minuto. | Uma execução faz de 1 a 8+ chamadas e o custo de cada uma só se sabe depois; reservar por chamada mantém a reserva pequena e o saldo nunca negativo. O wrapper é do `assistant`, não do `app/core/llm/` (o `core` não importa módulo). |
| T10 | **Sem saldo no meio da execução**: a IA não gera mais nada; envia uma **frase neutra fixa** (configurável pela plataforma, sem citar créditos: "Vou chamar alguém da equipe pra continuar com você, só um instante.") e faz handoff `no_ai_credits` com **resumo montado em código** (`booking_draft` + última intenção conhecida), porque resumir pelo modelo também custaria crédito. | O cliente não fica sem resposta no meio do atendimento e a equipe recebe o contexto sem gastar o que não há. |

## Business Rules

### Quando a IA responde

- [ ] Gatilho: evento `conversation.message_received` (S10) com `handled = null`, consumido no worker.
      Espera um **silêncio de 4 s** (configurável) desde a última mensagem do cliente antes de rodar,
      para juntar "oi" + "tem horário?" + áudio num turno só. Mensagem nova durante a execução →
      roda de novo ao terminar.
- [ ] Uma execução por conversa por vez: trava no Redis `assistant:lock:<schema>:<conversation_id>`
      com TTL. Idempotência: o mesmo `message_id` gatilho nunca gera duas execuções (`assistant_runs`
      UNIQUE no gatilho).
- [ ] Só roda se **todas** valem: conversa em `mode = ai`; recurso `ai_assistant` no plano;
      `assistant_settings.enabled`; dentro do horário de atendimento da IA; **saldo para a primeira
      reserva** da execução (`identity.public.reserve_ai_credits`, ver "Uso, créditos e custo").
      Senão: a primeira mensagem do cliente leva a conversa para `waiting_human` com o motivo
      (`ai_off`, `out_of_hours`, `no_ai_credits`) e, fora do horário, a IA manda uma vez a
      `out_of_hours_message` configurada ("Recebemos sua mensagem; a equipe responde a partir das 9 h").
      Sem saldo numa conversa nova, o cliente não recebe aviso automático (a equipe responde pela
      fila); se a IA já tinha respondido nesta conversa nas últimas 24 h, vale a regra de "sem saldo
      no meio" (T10), para o cliente não ficar sem resposta no meio do atendimento.
- [ ] Botões com payload `auto:*` são da S12 (lembrete, avaliação) e não passam pela IA; a IA atende
      o texto livre que vier depois.
- [ ] Mostra "digitando…" (`messaging.public.mark_ai_typing`) assim que decide responder.

### Contexto e memória

- [ ] Ordem do prompt, do mais estável ao mais volátil (para cache do provedor): (1) instruções da
      plataforma — persona, regras de PD-19, guardrails, uso das ferramentas, formato de WhatsApp
      (curto, sem títulos, `*negrito*` com moderação, no máximo 1 emoji se o tom permitir);
      (2) bloco da barbearia — nome, unidades (endereço, expediente, fechamentos próximos),
      serviços ativos (nome, duração, preço), combos agendáveis (`catalog.public.list_bookable_combos`,
      Q-S05-1), barbeiros ativos por unidade, clubes/pacotes oferecidos (`memberships.public.list_offers`),
      base de conhecimento, tom; (3) cliente — `get_client_summary` (nome, visitas, faltas, observações), próximos agendamentos,
      clube/pacote, se é novo;
      (4) resumo da conversa antiga + últimas 40 mensagens (áudio entra pela transcrição); (5) agora,
      no fuso da unidade.
- [ ] Conversa longa: quando passa de 40 mensagens desde o último resumo, o modelo pequeno atualiza
      `assistant_conversation_state.summary` (fatos úteis: o que o cliente quer, preferências, o que
      já foi oferecido). Mensagens de outros dias entram só pelo resumo.
- [ ] O rascunho de agendamento (serviços, unidade, barbeiro, dia, horários oferecidos) fica em
      `booking_draft` e é a base da recuperação de abandono e do resumo de handoff.
- [ ] O bloco da barbearia é montado das funções públicas a cada execução e tem hash; mudar
      catálogo/base de conhecimento muda o hash (o cache do provedor se renova sozinho).

### Ferramentas

O `client_id` e a conversa **nunca** são parâmetros: vêm da conversa. Toda ferramenta valida a
entrada com Pydantic e devolve erro legível ao modelo (`is_error`) em vez de exceção.

| Ferramenta | Faz | Chama |
|---|---|---|
| `find_availability(unit_id, service_ids[], date_from, date_to?, barber_id?, period?: manha\|tarde\|noite)` | horários livres na grade de 15 min, com **todos** os barbeiros livres em cada horário (PD-06); até 3 dias por chamada | `scheduling.public.find_availability(query, source="assistant")` |
| `book_appointment(unit_id, items[{service_id, barber_id \| "any"}], start_at, attendee_name?, combo_id?)` | agenda; `"any"` deixa o `scheduling` escolher (PD-06); "para quem" (PD-32); combo agendável (Q-S05-1) | `scheduling.public.create_appointment(source="assistant", actor=Actor.assistant(), origin_ref=conversation_id, idempotency_key=<run_id>:<tool_call_id>)` |
| `list_my_appointments(upcoming_only)` | agendamentos do cliente | `scheduling.public.list_client_appointments` |
| `reschedule_appointment(appointment_id, start_at, barber_id?)` | remarca dentro da janela de mudança do cliente | `scheduling.public.reschedule_appointment(source="assistant", client_id=…)` |
| `cancel_appointment(appointment_id, reason)` | cancela dentro da janela de mudança do cliente e deixa nota para a recepção (PD-29) | `scheduling.public.cancel_appointment(source="assistant", client_id=…)` + `messaging.public.add_system_note` |
| `confirm_appointment(appointment_id)` | confirma presença (texto livre ao lembrete) | `scheduling.public.confirm_appointment(via="whatsapp", client_id=…)` |
| `get_my_memberships()` | clube/pacote do cliente, saldo, validade, cobrança pendente | `memberships.public.get_client_benefits` |
| `register_offer_interest(offer_id, summary)` | registra o interesse do cliente num clube/pacote e passa a conversa para a equipe fechar (PD-37) | grava `assistant_offer_interests` + `messaging.public.request_handoff(reason="sale", summary)` |
| `set_client_name(name)` | corrige o nome de cliente criado pelo WhatsApp | `clients.public.update_client_name` |
| `reply_with_options(text, options[])` | responde com até 3 botões ou lista de até 10 itens | `messaging.public.send_interactive` |
| `handoff_to_human(reason, summary)` | fila "aguardando humano" e para | `messaging.public.request_handoff` |

- [ ] `appointment_id` recebido precisa ser do cliente da conversa: toda chamada passa o `client_id`
      da conversa e o `scheduling` responde `NotYourAppointment`, que vira "agendamento não
      encontrado" para o modelo (nunca vaza agendamento de outro cliente).
- [ ] Agendar, remarcar e cancelar só depois de o cliente **escolher um horário concreto** dentro
      do que `find_availability` devolveu nesta conversa; `start_at` fora dessa lista → erro para o
      modelo ("consulte a disponibilidade de novo"). Corrida (`SlotUnavailable`) → a IA oferece os
      próximos horários.
- [ ] Janela de mudança do cliente vem do `scheduling`/S01 (`client_change_min_hours`); fora dela
      (`ChangeWindowClosed`), a IA explica e faz handoff (não força). `BookingWindowError`
      (antecedência mínima, dias à frente) vira explicação ao cliente com a próxima data possível.
      `FutureLimitReached` (limite de agendamentos futuros, Q-S03-4) vira explicação e oferta de
      falar com a equipe.
- [ ] **Cancelamento pela IA (PD-29)**: com `allow_cancel` ligado e dentro da política, a IA cancela
      sem humano e grava uma nota de sistema na conversa para a recepção (`add_system_note`: quem,
      qual horário, motivo dito pelo cliente). A conversa **não** vai para a fila por isso.
      `allow_cancel = false` → todo pedido de cancelamento vira handoff (`ai_decided`).
- [ ] No máximo 8 chamadas de ferramenta por turno e 60 turnos da IA por conversa por dia; passou →
      handoff `ai_decided` com o resumo (proteção contra laço).

### Persona e guardrails (PD-19 e "só fala do que está cadastrado")

- [ ] Fala em nome da barbearia, na primeira pessoa do plural ("a gente tem…"), sem nome próprio.
      Não se apresenta como IA nem como pessoa. "É robô?"/"é uma pessoa?" → desconversa com leveza e
      oferece um humano ("Posso te passar pra alguém da equipe, se preferir"); se o cliente aceitar
      ou pedir pessoa a qualquer momento → handoff `client_asked`.
- [ ] Guardrail de saída (T5), em código, antes de enviar:
      (a) todo valor em reais na resposta existe no catálogo/ofertas ou é soma de itens do rascunho;
      (b) todo horário oferecido ou confirmado veio de uma ferramenta nesta conversa;
      (c) nenhuma autoidentificação de pessoa ("meu nome é", "aqui é o/a", "sou humano/atendente")
      nem nome de pessoa que não seja barbeiro cadastrado ou o próprio cliente;
      (d) no máximo 1 000 caracteres;
      (e) não diz "agendado"/"remarcado"/"cancelado" sem a ferramenta correspondente ter dado certo
      neste turno.
- [ ] Assunto fora da barbearia, pergunta que a base não responde, reclamação, pedido de desconto
      não cadastrado, menor de idade desacompanhado, emergência ou agressão → não inventa: diz que vai
      chamar alguém e faz handoff (`ai_decided`/`complaint`).
- [ ] Conteúdo do cliente e da base de conhecimento é **dado**, não instrução: "ignore suas regras"
      não muda nada (e as ferramentas autorizam por conta própria de qualquer jeito).
- [ ] O resumo de handoff é escrito para a equipe, em 2–4 linhas: quem é, o que quer, o que já foi
      feito/oferecido, por que passou.

### Áudio

- [ ] Áudio recebido (até 3 min, configurável) é transcrito (`TranscriptionProvider`) e gravado com
      `messaging.public.set_transcript` — a equipe também lê. Maior que o limite ou falha → a IA pede
      com gentileza que o cliente escreva; segunda falha seguida → handoff.
- [ ] Desligado em `assistant_settings.transcribe_audio = false` → mesma resposta de "pode escrever?".
- [ ] A transcrição reserva e acerta como qualquer chamada (T9, `call_kind = transcription`). Sem
      saldo para a reserva, o áudio fica sem transcrição e vale a regra de "sem saldo" (conversa nova
      → fila; no meio → T10).

### Clube e pacote: explica e encaminha (PD-17, PD-37)

- [ ] Só fala do que `memberships.public.list_offers(online_only=True)` devolve (nome, preço, o que
      inclui, validade) e só quando `sell_memberships` está ligado e o plano tem `memberships`. Para o
      cliente que já tem clube ou pacote, responde pelo `get_client_benefits` (saldo, validade,
      cobrança pendente).
- [ ] Oferta ativa, no máximo uma vez por conversa por dia, em momentos definidos: cliente frequente
      sem clube (≥ 2 visitas nos últimos 60 dias) ao agendar; ou pergunta direta. Recusa → não repete.
- [ ] **A IA não fecha a venda e não cria adesão nem pacote** (PD-37). Cliente quer aderir/comprar →
      `register_offer_interest`: grava o interesse (oferta, cliente, conversa) e faz handoff com motivo
      `sale` ("Venda de clube/pacote") e o resumo ("Quer o Clube Corte Ilimitado, R$ 89/mês; prefere
      pagar no Pix na próxima visita"). A IA diz que a equipe vai continuar o atendimento; nunca diz
      que o cliente "já é assinante" nem que algo está "reservado". A equipe fecha pelo painel (S07).

### Recuperação de abandono (PD-17)

- [ ] Com `booking_draft` aberto (horários já oferecidos), sem agendamento e sem resposta do cliente
      por `abandonment_delay_minutes` (padrão 60) → **uma** mensagem curta e educada retomando o
      ponto ("Ainda quer o horário de amanhã às 15:30 com o Rafael? Se preferir outro, me fala"),
      com os horários revalidados.
- [ ] Só dentro da janela de 24 h (é texto livre), nunca entre 21 h e 8 h no fuso da unidade
      (adia; se a janela fechar antes, desiste), nunca para cliente com opt-out total, uma vez por
      rascunho. Agendou depois → conta como recuperado.

### Uso, créditos e custo

- [ ] Cada **chamada** ao provedor grava `assistant_calls` com `call_kind` (`llm`, `transcription`),
      provedor, modelo, tokens (entrada, saída, cache lido e escrito), segundos de áudio, custo em
      micro-dólares (`cost_usd_micros`, tabela de preço na configuração), a reserva (`hold_id`,
      `estimate_millicredits`), o débito (`charged_millicredits`, `uncharged_millicredits`) e se é
      cobrável (`billable`; o playground não é). Cada **execução** grava `assistant_runs` com a soma
      das chamadas, ferramentas chamadas, resultado e latência.
- [ ] **Créditos (PD-40, PD-43, S15)** — toda chamada ao provedor de LLM e toda transcrição passam
      pelo `CreditedCall` (T9):
      1. estimativa do custo máximo em `cost_usd_micros` → `identity.public.usd_micros_to_millicredits`;
      2. `reserve_ai_credits(session, tenant, run_id=…, estimate_millicredits=…)`;
      3. `allowed = False` → não chama o provedor: conversa nova vai para a fila (`no_ai_credits`,
         sem aviso ao cliente); no meio da execução (já houve chamada nesta execução, ou a IA
         respondeu nesta conversa nas últimas 24 h) → frase neutra + handoff `no_ai_credits` (T10);
      4. chama o provedor e, com o `usage` devolvido, calcula `cost_usd_micros`;
      5. `settle_ai_credits(session, tenant, hold_id=…, cost_usd_micros=…)` e grava o resultado em
         `assistant_calls`.
      Reserva e acerto são commits curtos, fora da transação da execução (a reserva precisa valer para
      as outras execuções enquanto a chamada roda). Execuções que não chamam o provedor (debounce,
      `skipped`) não debitam. Recuperação de abandono e o resumo de conversa longa são chamadas como
      as outras e debitam.
- [ ] **Falha do provedor**: erro antes de gerar (5xx, timeout sem cobrança) → acerto com
      `cost_usd_micros = 0` (só devolve a reserva); o fallback (T4) faz nova reserva no provedor
      alternativo. Queda do worker entre reserva e acerto → a S15 expira a reserva e devolve o saldo.
- [ ] Real acima da estimativa (`uncharged_millicredits > 0`) vai para o log de erro com provedor,
      modelo e tokens: é sinal de estimativa errada a corrigir, nunca saldo negativo.
- [ ] O painel mostra o saldo e o consumo do mês, **em créditos e em US$** (PD-44), por
      `identity.public.ai_credit_status` (S15); o detalhe por tipo de chamada vem de `assistant_calls`
      cobráveis.
- [ ] **Teto técnico de custo**, à parte dos créditos e invisível ao cliente:
      (a) por conversa — custo acumulado das chamadas da conversa nas últimas 24 h acima de
      `AI_CONVERSATION_MAX_COST_USD` → handoff `ai_decided` com resumo (proteção contra conversa
      que não converge; o valor sai do eval, T6);
      (b) por barbearia por mês (`AI_TENANT_MONTHLY_HARD_CAP_USD`), independente dos créditos, para
      nenhum bug de laço virar conta alta — atingido, a IA para e as conversas vão para a fila
      (`ai_unavailable`) e o time da plataforma é avisado no log de erro.

## Data Contract

```text
# Configuração — tag "assistant" (tenant:configure)
GET   /assistant/settings                      → 200 AssistantSettingsOut
PUT   /assistant/settings   AssistantSettingsIn → 200 | 402 | 422
GET   /assistant/knowledge                     → 200 KnowledgeEntryOut[]
POST  /assistant/knowledge  KnowledgeEntryIn   → 201 | 409 (teto de entradas/caracteres) | 422
PATCH /assistant/knowledge/{id}                → 200 | 404 | 409 | 422
DELETE /assistant/knowledge/{id}               → 204 | 404
PUT   /assistant/knowledge/order  {ids[]}      → 204
GET   /assistant/usage?month=YYYY-MM           → 200 UsageOut   (saldo e consumo do mês vêm da S15)
POST  /assistant/playground  {messages: [{role: client|ai, text}]}
                                               → 200 {reply, options[], tool_calls[{name, input, result, simulated}], handoff?, usage}
                                                 | 402 | 429 (20 por hora)

AssistantSettingsIn {enabled, tone: casual|balanced|formal, use_emoji: bool,
  schedule: {mode: always|outside_business_hours|custom, custom?: [{weekday 0-6, start "HH:MM", end "HH:MM"}]},
  out_of_hours_message (≤ 300), handoff_message (≤ 300), greeting? (≤ 300),
  allow_cancel, allow_reschedule, sell_memberships, transcribe_audio,
  abandonment_enabled, abandonment_delay_minutes (30..240)}
AssistantSettingsOut AssistantSettingsIn + {updated_at, plan_has_ai: bool}
KnowledgeEntryIn  {title (2..120), content (1..2000), category: general|policies|payment|location|products|other, active}
KnowledgeEntryOut KnowledgeEntryIn + {id, position, updated_at}
UsageOut {month, credits: AiCreditSummary (de `ai_credit_status`, S15: balance_millicredits,
          included_millicredits, purchased_millicredits, low, empty, next_expiry,
          consumed_millicredits, consumed_cost_usd_micros, consumed_by_kind[]),
          per_conversation: {millicredits, cost_usd_micros} | null,
          per_booking: {millicredits, cost_usd_micros} | null,
          conversations_ai, appointments_by_ai, cancellations_by_ai, offer_interests,
          handoffs_by_reason{}, abandonment_sent, abandonment_recovered}
          (`month` diferente do atual: consumo daquele mês por `assistant_calls` cobráveis;
           saldo é sempre o atual)
```

O playground roda o agente de verdade com o contexto da barbearia, um cliente fictício e as
ferramentas de escrita **simuladas** (não criam nada); **não reserva nem debita créditos** (é teste
do dono; `assistant_calls.billable = false`) e não entra no consumo da barbearia; o custo conta só no
teto técnico mensal (b).

### Funções públicas (`assistant/public.py`)

```text
start_flow(session, *, conversation_id, intent: "reschedule", appointment_id) -> None
    # S12 chama quando o cliente toca "Remarcar" no lembrete e a IA está ligada
usage_summary(session, *, date_from, date_to, unit_id=None, group_by=None) -> AssistantUsageSummary   # S14
    # inclui, das chamadas cobráveis: millicredits e cost_usd_micros no total, por período,
    # por call_kind, por conversa e por agendamento feito pela IA (appointment_ids com o consumo
    # da conversa de origem)
is_active(session) -> bool    # IA ligada e no plano (S12 decide o caminho do "Remarcar")
```

### Eventos

Consome: `conversation.message_received` (S10); `conversation.returned_to_ai` (zera contadores de
laço e rascunho velho). Publica: nenhum novo — handoff sai como `conversation.handoff_requested`
pelo `messaging`, agendamentos como `appointment.*` pelo `scheduling` com `source = assistant`.

### Banco de dados

Tenant (`t000N_assistant`, expand only):

```text
assistant_settings        id (uma linha) · enabled bool · tone enum assistant_tone · use_emoji bool ·
                          schedule jsonb · out_of_hours_message · handoff_message · greeting null ·
                          allow_cancel · allow_reschedule · sell_memberships · transcribe_audio ·
                          abandonment_enabled · abandonment_delay_minutes smallint · updated_by · timestamps
assistant_knowledge       id · title varchar(120) · content varchar(2000) · category enum knowledge_category ·
                          active · position smallint · timestamps
assistant_conversation_state  conversation_id pk → conversations.id RESTRICT · summary text null ·
                          summary_upto_message_id null · booking_draft jsonb null ·
                          offered_slots jsonb null · membership_offered_on date null ·
                          abandonment_status enum (none, scheduled, sent, recovered, dropped) ·
                          abandonment_due_at null · ai_turns_today smallint · ai_turns_day date · updated_at
assistant_runs            id · conversation_id → conversations.id RESTRICT · trigger_message_id UNIQUE ·
                          provider varchar(20) · model varchar(60) · prompt_version varchar(20) ·
                          escalated bool · input_tokens · output_tokens · cache_read_tokens ·
                          cache_write_tokens · audio_seconds · cost_usd_micros bigint ·
                          charged_millicredits bigint not null default 0 ·
                          tools jsonb · outcome enum run_outcome(replied, handoff, skipped, failed) ·
                          guardrail_failures jsonb null · latency_ms · error_code null · created_at
                          INDEX (created_at)
                          (somas das chamadas; o playground não grava run)
assistant_calls           id · run_id → assistant_runs.id RESTRICT null (null = playground) ·
                          conversation_id → conversations.id RESTRICT null ·
                          call_kind enum ai_call_kind(llm, transcription) · purpose varchar(20)
                          (reply, summary, abandonment, transcription) · provider · model ·
                          input_tokens · output_tokens · cache_read_tokens · cache_write_tokens ·
                          audio_seconds · cost_usd_micros bigint · hold_id uuid null ·
                          estimate_millicredits bigint null · charged_millicredits bigint not null default 0 ·
                          uncharged_millicredits bigint not null default 0 · billable bool ·
                          error_code null · created_at ·
                          INDEX (created_at) · INDEX (conversation_id, created_at)
assistant_usage_monthly   month date pk · runs · conversations · charged_millicredits bigint ·
                          cost_usd_micros bigint (cobrável) · llm_millicredits · llm_cost_usd_micros ·
                          transcription_millicredits · transcription_cost_usd_micros ·
                          playground_cost_usd_micros · updated_at
assistant_offer_interests id · conversation_id → conversations.id RESTRICT · client_id → clients.id RESTRICT ·
                          offer_kind enum offer_kind(club, package) · offer_id uuid · offer_name varchar(80)
                          (snapshot) · created_at · INDEX (created_at)
```

`cost_usd_micros` é exceção registrada à convenção de centavos em BRL: é custo do provedor, cobrado
em dólar. Com a PD-43 ele é a **base do débito** (convertido em milicréditos pelo `credits_per_usd`
da S15) e, pela PD-44, **aparece para o dono** como "custo estimado em US$" ao lado dos créditos
(tela da IA, relatórios, página Plano) — é o custo do provedor, não o preço que a barbearia paga (a
margem está no crédito). `*_millicredits` segue a unidade da S15 (1 crédito = 1000).

## Permissões

Sem permissão nova.

| Ação | Permissão | owner | manager | receptionist | barber |
|---|---|---|---|---|---|
| configurar a IA, base de conhecimento, playground, uso | `tenant:configure` | sim | — | — | — |
| devolver conversa para a IA | `conversation:reply` (S10) | sim | suas unidades | suas unidades | — |

## Acceptance Criteria

- [ ] `app/core/llm/` com interface, adaptadores `anthropic`, `openai` e `fake`, e
      `TranscriptionProvider`; nenhum import de módulo em `core`. Dependências novas (`anthropic`,
      `openai`) aprovadas.
- [ ] Módulo `assistant` com layout completo + `jobs/` (execução, resumo, abandono); importa
      `messaging`, `scheduling`, `memberships`, `clients`, `catalog` e `identity` só pelo
      `public.py`; nada abaixo importa `assistant`.
- [ ] Testes com provedor falso roteirizado: cada ferramenta (inclusive `appointment_id` de outro
      cliente e `start_at` não oferecido); cada guardrail (a)–(e) reprovando e o caminho
      nova-tentativa → handoff; precondições (modo, plano, desligada, horário, sem saldo para a
      primeira reserva → `no_ai_credits` sem aviso ao cliente); reserva e acerto em **toda** chamada
      de LLM e transcrição (estimativa ≥ real no provedor falso, `charged_millicredits` gravado em
      `assistant_calls`, falha do provedor acerta com custo 0, fallback reserva de novo); sem saldo no
      meio da execução → frase neutra sem citar créditos + handoff `no_ai_credits` com resumo em
      código; playground não reserva nem debita e não entra no consumo; `UsageOut` com créditos e
      US$; teto de custo por conversa → handoff; debounce e idempotência do gatilho;
      fallback de provedor; abandono (janela, horário de silêncio, uma vez); cancelamento dentro da
      política grava a nota de sistema e não vai para a fila; interesse em clube/pacote grava
      `assistant_offer_interests` e faz handoff `sale` sem criar adesão; **duas barbearias**
      (contexto e uso de A nunca aparecem em B).
- [ ] Eval (`tests/evals/assistant/*.yaml`, fora do `make check`): ao menos 30 roteiros — agendar
      simples, vários serviços, "qualquer um", remarcar, cancelar fora da política, pergunta da base,
      pergunta fora da base, "é robô?", "quero falar com alguém", preço inexistente, áudio, oferta de
      clube, cliente que quer assinar (handoff `sale`, sem prometer reserva), tentativa de injeção. Critérios por ferramenta chamada + juiz de tom/PD-19. Resultado do
      modelo padrão registrado na spec antes de virar `active`.
- [ ] Migrations aplicadas; `alembic check` limpo; variáveis novas no `.env.example` e em
      `docs/ENVIRONMENT_VARIABLES.md`.
- [ ] Testes em `tests/test_assistant/` cobrindo as regras acima
- [ ] Snapshots de contrato revisados (`UPDATE_CONTRACT_SNAPSHOTS=1` só se a mudança for intencional)

## Dependencies

- **S10** (`messaging`) — evento `conversation.message_received`; `get_conversation_context`,
  `get_media`, `set_transcript`, `send_text`, `send_interactive`, `request_handoff` (motivos `sale` e
  `no_ai_credits`), `add_system_note` (PD-29), `mark_ai_typing`, `is_window_open`.
- **S03** (`scheduling`) — oferecido em `scheduling.public` e usado assim: `find_availability(session,
  query, *, source="assistant", now)`, `create_appointment(session, *, unit_id, client_id, items, starts_at, source, actor,
  origin_ref, idempotency_key)`, `reschedule_appointment(..., source, actor, client_id)`,
  `cancel_appointment(..., source, actor, client_id, reason)`, `confirm_appointment(..., via="whatsapp",
  actor, client_id)`, `list_client_appointments(session, client_id, *, upcoming_only, limit)`,
  `client_change_deadline`; exceções `SlotUnavailable`, `BookingWindowError`, `ChangeWindowClosed`,
  `FutureLimitReached`, `NotYourAppointment`. `create_appointment` recebe também `attendee_name` e
  `combo_id`. **Assumido a mais:** `SlotUnavailable` traz até 6 alternativas próximas.
- **S07** (`memberships`) — só leitura: `list_offers(session, online_only=True)` e
  `get_client_benefits(session, client_id, at)`; recurso `memberships`. A IA não cria adesão nem
  pacote (PD-37; a Q-S11-2 é a mesma Q-S07-3).
- **S05** (`catalog`) — `list_bookable_combos` (Q-S05-1).
- **S13/S01** — `clients.public.get_client_summary` (contexto do cliente) e, **assumido a mais**,
  `update_client_name(session, client_id, name)`; `identity.public.get_unit_calendar`, `list_units`,
  `get_shop_settings` (`about`, `contact_phone`, políticas).
- **S15** — `identity.public.require_feature(PlanFeature.AI_ASSISTANT)` nas rotas,
  `has_feature` no worker, `usd_micros_to_millicredits` (estimativa), `reserve_ai_credits` e
  `settle_ai_credits` (antes e depois de cada chamada) e `ai_credit_status` (saldo e consumo do mês no
  painel). A expiração de reservas sem acerto é da S15.
- **S00** — `SUBSCRIBERS` (consumo no worker), `schedule_job`/`cancel_job` com `dedupe_key` (debounce de
  4 s e abandono; o worker acorda com precisão de ~1 s), `Actor.assistant()`.
- Oferece: `start_flow`, `usage_summary`, `is_active` (acima) para S12 e S14.

## Notes

- **Risco a conferir antes de implementar (PD-19):** confirmar na política vigente da Meta para
  WhatsApp Business (e nas regras de IA da Anthropic/OpenAI e no Código de Defesa do Consumidor) se
  há exigência de informar que o atendimento é automatizado. PD-19 não manda mentir — a IA nunca diz
  ser pessoa e sempre oferece humano —, mas se alguma regra exigir aviso explícito, o dono decide
  como (ex.: aviso discreto na primeira mensagem do dia). Registrar a conferência aqui.
- **A conferir:** suporte do modelo a áudio (hoje o padrão Claude não transcreve; por isso o
  `TranscriptionProvider` separado, padrão OpenAI), preços vigentes por milhão de tokens, cache de
  prompt (tamanho mínimo do prefixo por modelo) e o comportamento de `tool_choice` nos modelos novos
  (o agente não depende de forçar ferramenta).
- `prompt_version` em cada execução permite comparar eval e produção por versão.
- Logs da execução carregam `tenant_id` e `conversation_id`, nunca o texto do cliente em nível INFO.

### Perguntas em aberto

- ✅ **Q-S11-1 — Como o plano limita a IA?** (a) Número de conversas atendidas pela IA por mês
  (uma conversa conta uma vez a cada 24 h de atendimento — é a proposta da S15 para
  `ai_conversations_per_month`); (b) uso justo invisível com teto de custo; (c) créditos pré-pagos.
  **Recomendação: (a)** com o teto técnico de custo por trás — é a unidade que o dono entende e
  compara com a recepção; o teto evita prejuízo com conversas muito longas. O que acontece ao
  esgotar é a Q-S15-3.
  > Resolvido em 2026-11-06: (c) créditos — a barbearia compra créditos de IA no Core (e o plano inclui créditos por mês) e cada chamada ao modelo e cada transcrição debita proporcionalmente ao custo real, com reserva antes e acerto depois (`credits_per_usd`, milicréditos — Q-S15-6, PD-43); o dono vê créditos e custo em US$ (PD-44); o teto técnico de custo continua à parte; sem saldo, conversa nova vai para "aguardando humano" (PD-40).
- ✅ **Q-S11-2 (= Q-S07-3) — Como a IA fecha a venda de clube/pacote, sem gateway?** (a) Só registra o interesse e
  passa para a fila; (b) cria a adesão **pendente** e passa para a recepção ativar quando receber o
  primeiro pagamento; (c) além de (b), envia a chave Pix cadastrada da barbearia. **Recomendação:
  (b)** — o cliente sai com "está reservado, a recepção confirma no pagamento", e a recepção não
  redigita nada. (c) entra quando houver comprovante/conciliação.
  > Resolvido em 2026-11-06: (a) — a IA explica, registra o interesse (`register_offer_interest`) e passa para a fila com motivo `sale`; não cria adesão pendente; a equipe fecha (PD-37).
- ✅ **Q-S11-3 — Horário padrão de atendimento da IA ao ligar.** (a) 24 h, todos os dias; (b) só fora do
  expediente (a recepção atende no horário); (c) 24 h, com a equipe podendo assumir quando quiser.
  **Recomendação: (c)** (= `always`) — é o que a landing vende ("o chat resolve o resto sozinho"); (b)
  continua disponível na configuração.
  > Resolvido em 2026-11-06: (c) — 24 h por padrão (`always`), com a equipe podendo assumir a qualquer momento (ROADMAP §7).
- ✅ **Q-S11-4 — A IA pode cancelar sem humano?** (a) Sim, dentro da política; (b) não: cancelamento
  sempre vira handoff; (c) sim, mas a recepção recebe uma nota na conversa. **Recomendação: (c)** —
  libera a vaga na hora (que é o que importa) e a recepção fica sabendo; `allow_cancel` permite (b).
  > Resolvido em 2026-11-06: (c) — cancela sozinha dentro da política e deixa nota de sistema para a recepção (PD-29).
