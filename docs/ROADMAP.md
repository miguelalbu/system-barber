# Roadmap — Navalha

Planejamento do produto inteiro, feito antes do código para não ir e voltar em funcionalidade.
Cada item abaixo vira uma spec `⚪draft_` em `backend/docs/specs/` (e o espelho em
`frontend/docs/specs/` quando tem tela). Este arquivo guarda **o que vale para todas as specs**:
as decisões de produto, a ordem, quem é dono de cada dado e como os módulos conversam.

> Fonte da verdade continua a mesma: código → specs → decisões → instruções. Este roadmap é a
> visão de conjunto; quando uma spec detalhar algo diferente daqui, a spec vence e este arquivo é
> corrigido.

Atualizado: 2026-11-06.

---

## 1. Decisões de produto (rodadas de perguntas de 2026-11-06)

Não reabrir na implementação. Cada spec cita as que usa pelo código `PD-NN`.

### Canais e clientes

| Código | Decisão |
|---|---|
| PD-01 | O cliente final agenda por **WhatsApp com IA** e por **link público de agendamento** (página da barbearia). Sem app do cliente. A equipe também agenda pelo painel. |
| PD-02 | No link público o cliente se identifica pelo **telefone + código (OTP) enviado no WhatsApp**. Sem senha. |
| PD-03 | O cliente pertence à barbearia, não à unidade (já valia, DEC-016 P3). Telefone E.164 único. |

### Agenda

| Código | Decisão |
|---|---|
| PD-04 | Horários oferecidos numa **grade fixa de 15 min** (09:00, 09:15…); o serviço ocupa a duração dele. |
| PD-05 | **Vários serviços em sequência** num agendamento, inclusive com barbeiros diferentes em sequência. |
| PD-06 | A IA (e o link) **mostra todos os barbeiros livres** no horário. Cliente escolhe um → marca com ele. Cliente diz "qualquer um" → marca com o barbeiro livre que tem **menos agendamentos no mês corrente** (equilíbrio). Empate → menos agendamentos no dia; depois ordem alfabética. |
| PD-07 | Contra falta: **lembrete com Confirmar/Remarcar/Cancelar**. Sem resposta até X horas antes (configurável), o agendamento fica **"não confirmado"** em destaque para a recepção decidir. Nunca cancela sozinho. Faltas (no-show) ficam no histórico do cliente. |
| PD-08 | **Fora do planejamento agora:** lista de espera e agendamento recorrente. |

### Produtos do cliente final

| Código | Decisão |
|---|---|
| PD-09 | Três produtos: **Clube** (assinatura mensal: serviços ilimitados ou N por ciclo, e/ou desconto), **Pacote** (pré-pago: N serviços por um preço, com validade) e **Combo** (serviços — e produtos — juntos com preço fechado, vendido avulso). O menu Cadastros troca "Clubes e combos" + "Planos" por **Clubes**, **Pacotes** e **Combos**. |
| PD-10 | **Sem gateway de pagamento por enquanto.** O sistema só **registra** pagamentos feitos fora (dinheiro, Pix, cartão na maquininha). A mensalidade do clube é cobrança registrada manualmente (o sistema gera a cobrança do ciclo e a recepção dá baixa). Gateway é um passo futuro — modelar pagamentos para que ele entre sem refazer nada. |
| PD-11 | **Sem estoque por agora.** Produto existe como item de venda na comanda (preço, comissão), sem quantidade. |

### Dinheiro e equipe

| Código | Decisão |
|---|---|
| PD-12 | Barbeiros são **só comissionados** (sem aluguel de cadeira, sem salão-parceiro). |
| PD-13 | Regras de comissão, **todas ligáveis/desligáveis e ajustáveis pela barbearia**: % padrão do barbeiro com exceção por serviço; desconto da taxa do cartão antes de calcular; comissão sobre produto; comissão em atendimento de assinante do clube. |
| PD-14 | Financeiro: **comanda**, **caixa diário** (abertura, fechamento, sangria, reforço) e **despesas / contas a pagar** (resultado do mês). Fora: vales/adiantamentos, NFS-e. |

### WhatsApp e IA

| Código | Decisão |
|---|---|
| PD-15 | API oficial da Meta em **coexistência**: o dono continua com o app WhatsApp Business no celular, no mesmo número; o que a equipe responde no celular aparece no painel. |
| PD-16 | IA **multi-provedor**: uma camada própria troca de provedor/modelo por configuração (padrão: Claude, da Anthropic; alternativa: OpenAI). |
| PD-17 | Além de agendar/remarcar/cancelar, a IA: responde pela **base de conhecimento** editada pelo dono; **vende clube e pacotes**; **entende áudio** (transcrição); **recupera abandono** (lembrete educado a quem começou a agendar e sumiu). |
| PD-18 | Handoff para humano: a conversa vai para a **fila "aguardando humano" na Central de conversas**, com o resumo da IA, e a IA para de responder até a equipe devolver. Sem push, sem aviso no WhatsApp pessoal, sem retomada automática. |
| PD-19 | A IA **responde como a recepção** (não se apresenta como IA). Se perguntarem "é robô?", **desconversa e oferece um humano**. Limite: a IA nunca afirma ser uma pessoa nem inventa nome de funcionário. Pedido explícito de falar com pessoa = handoff. |
| PD-20 | Automações: lembrete com confirmação (PD-07), **reativação de inativo** (padrão 40 dias, ajustável), **aniversário**, **avaliação pós-atendimento** (nota 1–5; link do Google para todos que responderam, nota baixa → alerta ao dono — PD-27) e **campanhas manuais** com template aprovado pela Meta. Toda mensagem iniciada pela barbearia respeita opt-out do cliente. |

### Plataforma

| Código | Decisão |
|---|---|
| PD-21 | **A cobrança da barbearia mora no Core da plataforma.** O Navalha recebe pelo `/core/*` só plano, limites, recursos e suspend/resume. Nunca toca no dinheiro da assinatura. |
| PD-22 | Planos do Navalha com **limites e recursos configuráveis** (máx. de barbeiros, máx. de unidades, IA, clubes, multi-unidade…), mantidos no control plane. Nomes e valores ficam fora das specs. |
| PD-23 | **Venda assistida**: o time cria a barbearia pelo Core. No painel, só um **assistente de primeiros passos** (unidade, horários, serviços, barbeiros, WhatsApp). Sem cadastro self-service na landing. |
| PD-24 | **Importação por planilha** CSV/Excel (clientes, serviços, agendamentos futuros), com prévia e relatório de erros. |
| PD-25 | Relatórios: **faturamento**, **ocupação da agenda**, **clientes e retenção**, **desempenho da IA** (conversas, agendamentos pela IA, handoff, abandono, custo). |
| PD-26 | O barbeiro usa o **painel responsivo instalável (PWA)**: agenda do dia, próximo cliente, minhas comissões. Sem app nativo. |

### Segunda rodada (2026-11-06, depois das specs escritas)

| Código | Decisão | Specs |
|---|---|---|
| PD-27 | Avaliação: o **link do Google vai para todos que responderam**; nota baixa continua gerando alerta ao dono. Substitui o "só nota alta" da PD-20 (seria *review gating*, proibido pelo Google). | S12 |
| PD-28 | **Custo da Meta**: no início a barbearia paga direto à Meta com o cartão dela (Navalha como Tech Provider); depois o Navalha vira Solution Partner e repassa pela fatura do Core. | S10 |
| PD-29 | A IA **cancela sozinha** dentro da política de cancelamento e deixa uma **nota para a recepção**. | S11 |
| PD-30 | **Consentimento de marketing** (reativação, aniversário, campanhas): pode receber quem tem **ao menos um atendimento**; importados e contatos sem atendimento só com "sim" explícito. Mensagens de utilidade (lembrete, confirmação) valem para todo cliente com agendamento. Opt-out sempre respeitado. | S12, S13 |
| PD-31 | Agendamento feito pelo cliente (IA/link) **nasce "agendado" e confirma pelo lembrete**; se for marcado já dentro do prazo do lembrete, nasce confirmado. | S03 |
| PD-32 | Agendar para outra pessoa: campo **"para quem"** (`attendee_name`); o mesmo cliente pode ter horários simultâneos. | S03 |
| PD-33 | **Expediente e feriados** da unidade: dono em todas; gerente nas unidades dele (permissão nova `unit:configure`). | S01 |
| PD-34 | Barbeiro em **uma unidade por vez** (como hoje); jornada por dia/unidade fica para depois, sem refazer nada. | S02 |
| PD-35 | **Comissão de atendimento de assinante: a barbearia escolhe o modo** (rateio da mensalidade, valor fixo por atendimento, % do preço de tabela ou sem comissão). Sem padrão imposto: o modo é escolhido ao ligar a regra. | S08, S07 |
| PD-36 | Mensalidade do clube vencida: **tolerância configurável (padrão 5 dias) e depois bloqueia o uso** até pagar. Nunca cancela sozinho. | S07 |
| PD-37 | A IA **não fecha venda** de clube ou pacote: explica, registra o interesse e **passa para a fila de humano**; a equipe fecha. | S11, S07 |
| PD-38 | **Gorjeta** na comanda, por barbeiro, fora da receita, repassada **integral** no fechamento (a barbearia absorve a taxa do cartão sobre ela). | S06, S08 |
| PD-39 | **Downgrade** acima do limite: nada é desativado; só fica bloqueado criar/reativar até voltar ao limite. | S15 |
| PD-40 | **IA por créditos**: o uso da IA consome créditos que a barbearia compra (vendidos pelo Core, PD-21). Créditos acabaram → conversas novas vão para "aguardando humano". Detalhes em PD-43. | S11, S15 |
| PD-41 | **Contato do cliente para o barbeiro**: configurável, **padrão oculto** (barbeiro vê nome e histórico). | S13 |
| PD-42 | **Números de WhatsApp**: um geral e, opcionalmente, um por unidade, com quantidade limitada pelo plano (`whatsapp_numbers`). | S10, S15 |
| PD-43 | **Crédito de IA proporcional ao custo real** do provedor (conversão `credits_per_usd` definida pelo Core por plano, margem embutida): cada chamada ao modelo e cada transcrição debita. O plano **inclui créditos por mês que não acumulam**; créditos **comprados não vencem**. Saldo nunca negativo (reserva antes da chamada, acerto depois). | S11, S15 |
| PD-44 | O dono vê o consumo da IA **em créditos e o custo estimado em US$** (relatórios, tela da IA, tela do plano). | S11, S14, S15 |

> ⚠️ **Em revisão (2026-11-06) — PD-16, PD-40, PD-43, PD-44.** O dono esclareceu que o custo da IA
> será **de cada barbearia, direto do consumo de tokens no provedor (OpenAI)**, com **chave/token por
> barbearia** para cada uma controlar o próprio gasto. Ainda não decidido: a barbearia **coloca a
> própria chave** nas configurações (BYOK) ou **a plataforma administra** uma chave/projeto por
> barbearia e controla os gastos. Isso substitui o modelo de créditos comprados no Core; S11, S14 e
> S15 (partes de créditos) serão revistas antes de implementar. Não afeta as Fases 1 e 2.

---

## 2. Convenções que valem para todas as specs

- **Dinheiro** em centavos inteiros (`*_cents`), BRL. **Percentual** em `Numeric(5,2)`. Exceções:
  custo de IA em micro-dólares (`cost_usd_micros`), porque os provedores cobram em dólar (S11), e
  créditos de IA em milicréditos (`*_millicredits`, S15).
- **Tempo**: tudo em UTC no banco (`timestamptz`); a unidade tem `timezone` (já existe, padrão
  `America/Sao_Paulo`) e regras de horário (expediente, grade de 15 min, "dia") são calculadas no
  fuso da unidade.
- **Apagar**: só sem histórico; com histórico, inativar (DEC-016 P1). FKs de histórico com
  `ON DELETE RESTRICT`, `IntegrityError` → 409.
- **Snapshot no histórico**: agendamento e comanda copiam nome/preço/duração/comissão do momento —
  mudar o cadastro depois não reescreve o passado.
- **Todo dinheiro passa pela comanda** (S06): mensalidade de clube e venda de pacote são itens de
  comanda. Caixa, taxas, comissão e relatórios têm um caminho só.
- **Escopo**: toda lista e toda rota aplicam `all/unit/own` (DEC-004). Barbeiro (`own`) só vê o
  que é dele.
- **Tabelas de barbearia** herdam `TenantBase`, sem `tenant_id`, migrations no conjunto
  `alembic/tenant`, só expand/contract (DEC-011).
- **Permissões**: reaproveitar as 19 que existem. Novas propostas pelas specs, cada uma justificada
  na sua spec: `cash:operate` (S09 — a recepção opera o caixa sem ver despesas/resultado),
  `client:manage` (S13 — exportar, anonimizar e mesclar clientes), `unit:configure` (S01 —
  expediente e feriados; dono `all`, gerente `unit`, PD-33).
- **Plano**: rota de recurso pago verifica o plano pelo `identity.public` (S15) e responde **402**
  com corpo `{detail, code, feature | limit, max, used}` (muda o handler de `app/core/exceptions.py`).
- **Telefone**: a normalização E.164 desce de `clients/phone.py` para `app/core/phone.py` (S01
  valida o telefone da unidade).
- **Textos** ao usuário em português; identificadores em inglês.

---

## 3. Arquitetura-alvo: módulos, donos de dado e conversa entre módulos

### Módulos do backend

| Módulo | Dono de | Specs |
|---|---|---|
| `identity` (existe) | usuários, convites, sessões, RBAC, **unidades** (+ expediente, fechamentos), **configurações da barbearia** (`shop_settings`: políticas de agendamento, limite de agendamentos futuros, `barber_sees_client_contact`), **barbeiros**, **leitura e verificação do plano** (o `provisioning` só escreve) | S01, S15, S17 |
| `provisioning` (existe) | control plane `/core/*`, **escrita do plano, dos limites e dos créditos de IA** vinda do Core (tabelas `plans`, `ai_credit_accounts`, `ai_credit_lots`, `ai_credit_holds`, `ai_credit_ledger` no `public`; reserva e acerto pelo `identity.public`) | S15 |
| `catalog` (existe) | serviços, **produtos**, **combos**, **formas de pagamento e taxas** | S05 |
| `clients` (existe) | clientes, **perfil e indicadores** (read model próprio, por eventos), tags, **consentimento** (`record_marketing_consent`) **e opt-out** (por escopo), LGPD (exportar, anonimizar, mesclar) | S13 |
| `scheduling` (novo) | **jornada do barbeiro**, folgas, bloqueios, **agendamentos**, **disponibilidade** | S02, S03 |
| `booking` (novo) | **link público**: página da barbearia, sessão do cliente por OTP | S04 |
| `sales` (novo) | **comanda** (itens — inclusive mensalidade de clube e venda de pacote —, descontos, gorjeta, pagamentos registrados) | S06 |
| `memberships` (novo) | **clubes**, **pacotes**, adesões, ciclos e cobranças, saldo de uso | S07 |
| `commissions` (novo) | regras de comissão, lançamentos, **fechamento** por período | S08 |
| `finance` (novo) | **caixa diário**, **despesas e contas a pagar**, resultado do mês | S09 |
| `messaging` (novo) | conta WhatsApp, webhook, **conversas**, mensagens, mídia, templates, fila de handoff, notas de sistema (`add_system_note`) | S10 |
| `assistant` (novo) | **agente de IA**: persona, base de conhecimento, ferramentas, interesses em clube/pacote encaminhados, chamadas ao provedor (`assistant_calls`), reserva/acerto de créditos e custo | S11 |
| `automations` (novo) | lembretes, reativação, aniversário, avaliação, **campanhas** (lê o consentimento do `clients`) | S12 |
| `reports` (novo) | **dashboard e relatórios** (read model próprio, por eventos; só leitura) | S14 |
| `imports` (novo) | **primeiros passos** e **importação por planilha** (cria registros pelos `public.py` dos donos) | S16 |

Infra nova em `app/core/`: `events` (S00), `phone.py`, `crypto.py` (envelope encryption, S10),
`llm/` (provedores de IA, S11), limitador de tentativas no Redis (S04, S17).

Regra de dependência (DEC-006): um módulo chama outro **só pelo `public.py`**, sem ciclos. Ordem
de baixo para cima:

```text
identity ← catalog ← clients ← scheduling ← sales ← memberships ← commissions ← finance
                                    ↑    ↑                ↑
                         messaging ← assistant ← automations       booking (→ scheduling, messaging)
                         reports e imports leem/escrevem pelos public.py de todos
```

Quando um módulo de baixo precisa de algo de um de cima, há **dois mecanismos** (nunca import):

1. **Evento de domínio** (S00) — reação assíncrona. Ex.: `clients` atualiza "última visita"
   quando a comanda fecha.
2. **Registro por inversão** — o módulo de cima registra uma função no de baixo, ligada em
   `main.py`, para chamadas **síncronas na mesma transação**. Ex.: `finance` registra no `sales` o
   resolvedor da sessão de caixa aberta (S09); `scheduling`, `sales`, `memberships` e `messaging`
   registram no `clients` o handler de dados do cliente para exportar/anonimizar/mesclar (S13).
   *Vira DEC quando a primeira for implementada.*

### Eventos de domínio (S00)

Publicados na **mesma transação** do dado (outbox por schema) e entregues por um worker. Payload só
com ids, horários, status e valores — nunca nome ou telefone. Assinantes idempotentes.

| Evento | Publicado por | Interessados |
|---|---|---|
| `appointment.created` / `.rescheduled` / `.cancelled` | scheduling | automations (lembrete, confirmação), clients, reports |
| `appointment.confirmed` / `.unconfirmed` | scheduling | reports (painel lê direto) |
| `appointment.completed` / `.no_show` / `.no_show_reverted` | scheduling | clients (indicadores), automations (avaliação), reports |
| `ticket.closed` / `ticket.voided` | sales | commissions, clients, memberships (consumo), reports |
| `membership.charge_due` / `.charge_paid` / `.suspended` / `.cancelled` / `.price_changed` | memberships | automations, reports |
| `client.created` / `.merged` / `.anonymized` / `.opted_out` | clients | automations, messaging, reports |
| `conversation.message_received` / `.handoff_requested` / `.assumed` / `.returned_to_ai` / `.resolved` | messaging | assistant, automations, reports |
| `message.delivery_updated`, `whatsapp.number_status_changed` | messaging | automations, painel |
| `review.received` / `review.low_received` | automations | reports, messaging (nota baixa → fila) |

Chamadas diretas que **não** são eventos: a comanda conclui o agendamento
(`scheduling.public.complete_appointment`); a S12 marca "não confirmado"
(`scheduling.public.mark_unconfirmed`); o caixa é resolvido de forma síncrona (registro por
inversão). `finance` não consome eventos: a receita vem por consulta ao `sales`.

### Processos e infraestrutura

- Hoje: `core-api` e `migrate`. Com S00 entra o **`worker`** (mesma imagem): entrega o outbox
  (acordado por `LISTEN/NOTIFY` do Postgres + varredura a cada 30 s), roda jobs avulsos
  (`schedule_job` com `dedupe_key`) e tarefas periódicas (lembretes, reativação, aniversário,
  cobranças de clube, expiração de pacote). Sem biblioteca de fila.
- **Redis**: travas das tarefas periódicas, OTP e limites de tentativa (S04, S17), revogação de
  sessão (S17).
- **Postgres**: extensão `btree_gist` (exclusion constraint da agenda, S03), criada por migration de
  controle.
- **Bucket S3 privado** (MinIO em dev) para mídia do WhatsApp (S10).
- **Meta**: app com Embedded Signup, Navalha cadastrado como Tech Provider (S10). `POST
  /webhooks/meta` é a **única rota cujo tenant vem do `phone_number_id`**, não do host — exceção à
  DEC-002, vira DEC.
- **Cloudflare Turnstile** no pedido de código do link público (S04).
- **Número de WhatsApp da plataforma** (`PLATFORM_WHATSAPP_*`): manda o código do link público
  quando a barbearia ainda não conectou o dela (`messaging.public.send_platform_otp`, Q-S04-1).
- **Mesmo host para painel e API** (`/api`) — pré-requisito do cookie httpOnly da S17.
- **Dependências novas a aprovar** quando a spec for implementada: SDKs `anthropic` e `openai`
  (S11), cliente S3 (S10), `openpyxl` (S16).

### Features do frontend

| Feature | Rotas | Specs |
|---|---|---|
| `registry` (existe) | `/app/cadastros/*` — Unidades, Barbeiros, Serviços, **Produtos**, **Combos**, **Clubes**, **Pacotes**, **Formas de pagamento** | S01, S05, S07 |
| `scheduling` (existe, mock) | `/app/agenda` real, `/app/agenda/escala`, `/app/agenda/ausencias`, `/app/meu-dia` (barbeiro) | S02, S03, S18 |
| `booking` (nova) | no host da barbearia: `/agendar`, `/agendar/meus-agendamentos` (`/` redireciona; a landing fica só no domínio raiz) | S04 |
| `sales` (nova) | `/app/comandas` | S06 |
| `memberships` (nova) | `/app/assinaturas` (adesões, cobranças, saldos) | S07 |
| `customers` (existe) | `/app/clientes` + ficha do cliente | S13 |
| `finance` (existe, placeholder) | `/app/financeiro/{caixa,despesas,resultado,comissoes,comissoes/regras}`, `/app/minhas-comissoes` | S08, S09 |
| `conversations` (existe, mock) | `/app/conversas` real + fila de handoff | S10 |
| `settings` (nova, nasce na S01) | `/app/configuracoes/{barbearia,agendamento,whatsapp,ia,automacoes,agendamento-online}` | S01, S04, S10, S11, S12 |
| `plan` (nova) | `/app/configuracoes/plano` (uso × limite) | S15 |
| `marketing` (nova) | `/app/marketing/{campanhas,avaliacoes}` | S12 |
| `dashboard` (existe, mock) | `/app/dashboard`, `/app/relatorios/:aba` | S14 |
| `onboarding` (nova) | `/app/primeiros-passos`, `/app/importar` | S16 |
| `auth` (existe) | `/app/minha-conta`, `/esqueci-senha`, `/redefinir-senha/:token` | S17 |
| shell | PWA, layout de celular, navegação por permissão (ISS-005) | S18 |

---

## 4. Mapa das specs e ordem

`B` = spec no backend, `F` = espelho no frontend. Ordem = ordem sugerida de implementação; cada
fase entrega algo usável sozinha.

### Fase 1 — Operação do dia (substitui a agenda de papel)

| ID | Spec | B | F | Depende de |
|---|---|---|---|---|
| S00 | Eventos de domínio, outbox e worker | `platform-events-jobs` | — | — |
| S01 | Unidades, expediente e fechamentos; configurações da barbearia | `identity-units-hours` | `frontend-units-settings` | (S15 só para o 402; antes dela, sem limite) |
| S02 | Jornada do barbeiro, folgas e bloqueios | `scheduling-barber-schedule` | `frontend-barber-schedule` | S01 |
| S03 | Agenda: disponibilidade e agendamentos | `scheduling-appointments` | `frontend-agenda` | S00, S01, S02 |
| S05 | Produtos, combos e formas de pagamento | `catalog-products-combos` | `frontend-products-combos` | — |
| S06 | Comanda e pagamentos registrados | `sales-tickets` | `frontend-tickets` | S03, S05 |
| S13 | Ficha do cliente: histórico, indicadores, LGPD | `clients-profile` | `frontend-client-profile` | S00, S03, S06 |

### Fase 2 — Dinheiro

| ID | Spec | B | F | Depende de |
|---|---|---|---|---|
| S08 | Comissões e fechamento (regras 1–3; o modo de assinante, PD-35, espera a S07) | `commissions-rules-closing` | `frontend-commissions` | S06 |
| S09 | Caixa diário, despesas e resultado | `finance-cash-expenses` | `frontend-cash-expenses` | S06, S08 |
| S07 | Clubes e pacotes | `memberships-clubs-packages` | `frontend-clubs-packages` | S05, S06, S15 |

### Fase 3 — WhatsApp e IA

| ID | Spec | B | F | Depende de |
|---|---|---|---|---|
| S15 | Planos do Navalha: limites e recursos | `provisioning-plan-entitlements` | `frontend-plan-limits` | — |
| S10 | Canal WhatsApp e Central de conversas | `messaging-whatsapp-inbox` | `frontend-inbox` | S00, S13, S15 |
| S11 | Agente de IA | `assistant-ai-agent` | `frontend-assistant-settings` | S03, S07, S10, S15 |
| S04 | Link público de agendamento | `booking-public-link` | `frontend-booking-page` | S01, S03, S10 (OTP), S13, S15 |
| S12 | Automações e campanhas | `automations-messages-campaigns` | `frontend-automations` | S00, S03, S10, S11, S13 |

### Fase 4 — Gestão e plataforma

| ID | Spec | B | F | Depende de |
|---|---|---|---|---|
| S14 | Dashboard e relatórios | `reports-dashboard` | `frontend-reports` | S03, S06, S07, S11 |
| S16 | Primeiros passos e importação | `imports-onboarding` | `frontend-onboarding-import` | S01–S06 |
| S17 | Endurecer a autenticação | `identity-auth-hardening` | `frontend-auth-hardening` | — |
| S18 | Painel no celular (PWA) e navegação por permissão | — | `frontend-pwa-mobile` | S03, S08 |

Nome do arquivo: `⚪draft_<B>.md` no backend e `⚪draft_<F>.md` no frontend. Todas escritas em
2026-11-06; nomes de funções e eventos entre specs alinhados no mesmo dia.

---

## 5. Divergências com a landing (corrigir o texto quando o produto chegar lá)

- "Controle de estoque" — fora por agora (PD-11).
- "Integração com a maquininha" e "Clubes com cobrança recorrente" — sem gateway por agora
  (PD-10); a cobrança do clube é registrada manualmente.
- Botão "Começar teste" no plano Básico — não há self-service (PD-23).
- "Barbeiros ilimitados" / "até 4 profissionais" — limites vêm do plano configurável (PD-22).
- FAQ "cobrado sem margem" (custo da Meta) — depende de quem paga a Meta (Q-S10-1).
- "Lembrete por WhatsApp (envio manual)" no Básico — pela S15, lembrete automático depende só do
  recurso `whatsapp`.

---

## 6. Riscos para conferir cedo

- **PD-19 (IA como a recepção):** conferir na hora de implementar se a política vigente da Meta
  para IA no WhatsApp Business ou o Código de Defesa do Consumidor exigem avisar que o atendimento
  é automatizado.
- **PD-20 (link do Google só para nota alta):** pedir avaliação só a quem gostou ("review gating")
  vai contra a política do Google — ver Q-S12-5.
- **`btree_gist` com o role de runtime** sem `USAGE` no `public` — critério de aceite da S03.
- **Apagar unidade** com `user_units` em CASCADE tornaria um usuário restrito àquela unidade em
  "vê todas" — a S01 recusa com 409; registrar como issue.

---

## 7. Perguntas das specs resolvidas pela recomendação (2026-11-06)

O dono não respondeu uma a uma; vale a recomendação da spec. **Revisáveis** — para mudar, diga o ID.

| ID | Resolução |
|---|---|
| Q-S01-2 | O sistema sugere os feriados nacionais do ano; o dono marca quais fecha. |
| Q-S01-3 | Fechamento num dia com agendamentos: permitido, com os agendamentos destacados na agenda (aviso automático aos clientes quando a S12 existir). |
| Q-S01-4 | Políticas de agendamento valem para a barbearia inteira. |
| Q-S01-5 | Padrões: antecedência mínima 60 min, horizonte 30 dias, "não confirmado" 3 h antes, cliente muda sozinho até 2 h antes, tolerância de atraso 10 min. |
| Q-S02-2 | Turno especial num dia: sim, dentro do horário da unidade. |
| Q-S02-3 | O barbeiro bloqueia horários pontuais da própria agenda; folgas só gerência. |
| Q-S03-2 | Fechar a comanda conclui o agendamento; "Concluir" na agenda continua existindo. |
| Q-S03-3 | Sem duração ou preço por barbeiro agora. |
| Q-S03-4 | Limite de agendamentos futuros por cliente na IA/link: configurável, padrão 3. |
| Q-S03-6 | Sem intervalo entre atendimentos agora ("tempo extra" por serviço é evolução). |
| Q-S05-1 | IA e link agendam só combos de serviços. |
| Q-S05-2 | A barbearia absorve a taxa do cartão (sem acréscimo no parcelado). |
| Q-S06-2 | Desconto livre para a recepção, com motivo obrigatório e relatório por usuário. |
| Q-S06-3 | Sem "fiado". |
| Q-S06-4 | Só gerente e dono estornam comanda fechada. |
| Q-S07-2 | No reajuste do clube o dono escolhe se atinge quem já assina ("só novos" pré-selecionado). |
| Q-S07-4 | Pacote vencido perde o saldo; prorrogação manual possível. |
| Q-S08-2 | Ajuste manual em lançamento de comissão, com motivo, só `finance:write` (não é vale). |
| Q-S08-3 | Sem comissão sobre venda de clube/pacote. |
| Q-S09-1 | Fechar comanda exige caixa aberto (configurável, ligado por padrão). |
| Q-S09-2 | Fechamento cego para a recepção (configurável). |
| Q-S09-3 | Despesa entra no resultado por competência. |
| Q-S10-3 | Importa o histórico do app (até ~6 meses) e liga só a clientes que já existem. |
| Q-S10-4 | Resposta pelo celular pausa a IA até 12 h sem mensagem da equipe; depois a conversa se resolve sozinha. |
| Q-S11-3 | IA ligada 24 h por padrão, com a equipe podendo assumir a qualquer momento. |
| Q-S12-2 | "SAIR" pergunta ao cliente, com dois botões, se quer parar só as promoções ou tudo. |
| Q-S12-3 | Nota baixa: lista com contador e a conversa vai para "aguardando humano". |
| Q-S12-4 | Campanhas só com `tenant:configure` (dono) agora. |
| Q-S04-1 | Sem WhatsApp conectado, o código do link sai de um número da plataforma Navalha. |
| Q-S04-2 | Bloqueio no link após N faltas: configurável, desligado por padrão. |
| Q-S13-3 | Só dono e gerente mesclam clientes duplicados. |
| Q-S14-1 | Barbeiro vê só os relatórios dele (ocupação e produção). |
| Q-S14-2 | Faturamento conta na data de fechamento da comanda. |
| Q-S14-3 | "Inativo" usa o mesmo limite da reativação (40 dias, ajustável). |
| Q-S14-4 | Básico: dashboard + faturamento e ocupação do mês. `advanced_reports`: período livre, comparação, retenção, IA e CSV. |
| Q-S15-2 | Plano perde clubes com assinantes ativos: seguem até o fim do ciclo pago. |
| Q-S15-3 | Créditos de IA acabaram: conversas novas vão para "aguardando humano" (PD-40). |
| Q-S15-4 | "Mudar de plano" leva ao portal do Core; até ele existir, ao WhatsApp do comercial. |
| Q-S15-5 | Recurso fora do plano: travado (com convite a mudar de plano) para o dono, escondido para a equipe. |
| Q-S16-1 | Importação traz o resumo do histórico (última visita, nº de visitas, total gasto). |
| Q-S16-2 | Agendamento importado não pede confirmação; lembretes normais. |
| Q-S16-3 | Só o dono faz os primeiros passos. |
| Q-S17-1 | Recuperação de senha por e-mail e por link gerado pelo dono/gerente. |
| Q-S17-2 | Caixa "Manter conectado" (30 dias ou até fechar o navegador, máx. 12 h). |
| Q-S17-3 | Sem 2FA agora; app autenticador opcional em spec própria. |
| Q-S18-1 | App instalado se chama "Navalha" agora; nome e logo da barbearia quando houver logo. |
| Q-S18-2 | Sem push agora (só aviso dentro do app); Web Push em spec própria. |

Q-S15-6 (créditos de IA) foi respondida pelo dono: PD-43 e PD-44.
