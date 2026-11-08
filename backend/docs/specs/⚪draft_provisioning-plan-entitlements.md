# Planos do Navalha: limites e recursos

**Priority:** high
**Status:** draft
**Espelho no frontend:** `frontend/docs/specs/⚪draft_frontend-plan-limits.md`


> ⚠️ **Em revisão:** o modelo de créditos de IA (PD-40/43/44) será substituído por custo de tokens
> por barbearia com chave própria ou administrada pela plataforma — ver o aviso no ROADMAP §1.
> Revisar as partes de créditos antes de implementar.
## Overview

Hoje `public.tenants.plan` é um texto (`"basic"`) que nada lê. Esta spec dá significado a ele: o
control plane guarda um **catálogo de planos** com **recursos** (IA, clubes, campanhas, relatórios
avançados…) e **limites** (barbeiros ativos, unidades ativas, números de WhatsApp, mensagens de
campanha por mês…); o Core da plataforma escolhe o plano de cada barbearia (e exceções negociadas)
pelo `/core/*`; e a API passa a **verificar** o plano: recurso ausente → `402` com mensagem de
upgrade; limite atingido → `402` com o limite e o uso. O painel recebe o plano no `/auth/me` para
esconder ou travar o que não está contratado.

O uso da IA é medido em **créditos de IA** (PD-40, PD-43): a barbearia compra créditos (vendidos e
cobrados pelo Core), o plano inclui créditos por mês, e o `assistant` (S11) debita **proporcionalmente
ao custo real** de cada chamada ao provedor de LLM e de cada transcrição de áudio, convertido por
`credits_per_usd`. Esta spec guarda o **saldo, as reservas e o extrato** no control plane, em
milicréditos, recebe do Core os créditos comprados e os ajustes e oferece a **reserva antes da
chamada e o acerto depois** pelo `identity.public` — o saldo nunca fica negativo. Créditos acabaram →
conversas novas vão para "aguardando humano". O dono vê o consumo em créditos e o custo estimado em
US$ (PD-44).

O Navalha **não sabe preço nem cobra** (PD-21): o Core vende, cobra e, quando o cliente muda de plano,
compra créditos ou deixa de pagar, chama `PUT /core/tenants/{id}/plan`, `POST
/core/tenants/{id}/ai-credits` ou `POST /core/tenants/{id}/suspend` (já existe).

Referência de mercado: Trinks, AppBarber e BestBarbers vendem por **número de profissionais** e
liberam módulos (clube de assinatura, app/link, marketing) por plano; o padrão de UX é mostrar o
recurso travado com "disponível no plano X" em vez de sumir com ele.

## Decisões de produto já tomadas

| Parâmetro | Valor |
|---|---|
| PD-21 | Cobrança da barbearia mora no Core. O Navalha recebe só plano, limites, recursos, **créditos de IA comprados** e suspend/resume pelo `/core/*`. |
| PD-22 | Limites e recursos configuráveis, mantidos no control plane. **Nomes e valores dos planos ficam fora das specs** (são dado, não código). |
| PD-39 | **Downgrade** acima do limite: nada é desativado; só fica bloqueado criar/reativar até voltar ao limite. |
| PD-40 | **IA por créditos**: o uso da IA consome créditos que a barbearia compra (vendidos pelo Core, PD-21). Créditos acabaram → conversas novas vão para "aguardando humano". Detalhes em PD-43. |
| PD-43 | **Crédito proporcional ao custo real** do provedor (conversão `credits_per_usd` definida pelo Core por plano, margem embutida): cada chamada ao modelo e cada transcrição debita. O plano **inclui créditos por mês que não acumulam**; créditos **comprados não vencem**. Saldo nunca negativo (reserva antes da chamada, acerto depois). Resolve a Q-S15-6. |
| PD-44 | O dono vê o consumo da IA **em créditos e o custo estimado em US$** (relatórios, tela da IA, tela do plano). |
| PD-42 | **Números de WhatsApp**: um geral e, opcionalmente, um por unidade, com quantidade limitada pelo plano (`whatsapp_numbers`). |
| DEC-016 | Limite de barbeiros conta o **cadastro de barbeiros** ativos, não os logins. |
| DEC-013 | `suspended` → 403 "Assinatura inativa" continua igual; plano é outra coisa (o que está contratado), status é se pode usar. |
| Convenções §2 | Rota de recurso pago verifica o plano e responde **402** com mensagem de upgrade. |

### Propostas desta spec

| # | Parâmetro | Proposta | Por quê |
|---|---|---|---|
| E1 | Onde guardar | Catálogo `public.plans` + o plano e as exceções na própria linha de `public.tenants`. | O registry já lê `tenants` a cada request (ISS-016): o plano vem junto, sem consulta extra. Exceção por cliente ("barbearia X ganhou IA no plano básico") sem criar um plano por cliente. |
| E2 | Onde mora o código | **Model e verificação no `identity`**; o `provisioning` só expõe as rotas `/core/*` que escrevem pelo `identity.public`. | Todo módulo de domínio depende do `identity` e o `identity` cria barbeiros e unidades (precisa checar o limite). Se a verificação morasse no `provisioning`, o `identity` teria de importá-lo — ciclo (`provisioning → identity`). |
| E3 | Multi-unidade | É o limite `max_units` (1 = sem multi-unidade), não um recurso separado. | Dois controles para a mesma coisa divergem. |
| E4 | Uso mensal | Contador por métrica e mês no schema da barbearia, incrementado de forma atômica por quem consome (hoje só `campaign_messages_per_month`). | Exato, barato e sem depender de evento. |
| E5 | Créditos de IA | **Conta, lotes, reservas e extrato no control plane** (`public.ai_credit_*`), não no schema da barbearia. Saldo disponível = soma do que resta nos lotes válidos; reserva e débito travam a linha da conta (`FOR UPDATE`) e consomem os lotes do que vence primeiro para o que não vence. | O crédito é dinheiro que o Core vendeu: o Core precisa ler e lançar sem conhecer o schema da barbearia, e o extrato precisa sobreviver a qualquer operação no tenant. Lotes permitem créditos inclusos que não acumulam e comprados com ou sem validade sem mudar código. |
| E6 | Política dos créditos | `plans.ai_credit_policy` (jsonb) com sobrescrita chave a chave em `tenants.ai_credit_policy_overrides`: `credits_per_usd` (numeric, obrigatório em plano com `ai_assistant`), `monthly_included` (créditos, padrão 0), `included_rollover` (false), `purchased_expiry_days` (null = não vence), `low_balance_threshold` (créditos, padrão 20). | O Core muda conversão, inclusos e validade por plano ou por barbearia sem deploy (PD-43). |
| E7 | Unidade guardada | **Milicréditos** em `bigint` (`*_millicredits`; 1 crédito = 1000). A tela mostra crédito com até 1 casa decimal. | Uma chamada barata custa fração de crédito; inteiro evita erro de ponto flutuante no saldo e no `CHECK (>= 0)`. |
| E8 | Débito proporcional | Por chamada ao provedor (LLM ou transcrição): `ceil(cost_usd_micros × credits_per_usd / 1000)` milicréditos (= `cost_usd_micros/1e6 × credits_per_usd × 1000`). Arredonda para cima, por chamada. | Uma regra só para modelo e áudio; a margem está no `credits_per_usd`; arredondar para cima nunca deixa uma chamada de graça. |
| E9 | Reserva e acerto | Antes da chamada, **reserva** o custo máximo (`hold`), tirado dos lotes; depois, o **acerto** devolve a reserva (`release`) e debita o real (`consume`) na mesma transação. A reserva guarda o `credits_per_usd` vigente e vence em `AI_CREDIT_HOLD_TTL_MINUTES` (padrão 15). | Custo real só se conhece depois da chamada; reservar o máximo antes é o que garante saldo nunca negativo com execuções simultâneas. Congelar a conversão na reserva evita que uma mudança de política no meio da chamada mude o preço dela. |
| E10 | Uma linha por operação no extrato | Cada lançamento é uma linha com `allocations` (`[{lot_id, amount_millicredits}]`) em vez de uma linha por lote tocado. | Reserva, acerto e consumo tocam vários lotes; uma linha por operação deixa `cost_usd_micros` e `run_id` sem duplicar na soma. |

## Business Rules

### Catálogo e plano efetivo

- [ ] Recursos são um enum fechado no código (`PlanFeature`), com as chaves que as specs S01–S14
      já usam: `whatsapp` (S10), `ai_assistant` (S11), `online_booking` (S04), `memberships` (S07: clubes e
      pacotes), `automations` (S12: lembretes, reativação, aniversário, avaliação), `campaigns`
      (S12), `advanced_reports` (S14). Chave desconhecida no `/core/*` → `422`.
- [ ] Limites são um enum fechado (`PlanLimit`): `max_barbers` e `max_units` (contam só os
      **ativos**), `whatsapp_numbers` (S10: um geral e, opcionalmente, um por unidade — PD-42) e
      `campaign_messages_per_month` (S12). Valor inteiro ≥ 0 ou `null` = ilimitado. Limite ausente no
      plano = ilimitado. **O uso da IA não é limite do plano**: é saldo de créditos (PD-40, seção
      abaixo); o recurso `ai_assistant` continua dizendo se o plano tem IA.
- [ ] Plano efetivo = recursos do plano **+** `feature_overrides.add` **−** `feature_overrides.remove`;
      limites do plano sobrescritos chave a chave por `limit_overrides`; política de créditos do plano
      sobrescrita chave a chave por `ai_credit_policy_overrides`.
- [ ] `POST /core/tenants` passa a validar `plan` contra o catálogo (`400` "Plano desconhecido"); o
      padrão `"basic"` deixa de existir no schema de entrada (o Core sempre informa). Toda barbearia
      nasce com a conta de créditos (`ai_credit_accounts`, saldo 0).
- [ ] Plano (ou override) com `ai_assistant` e sem `credits_per_usd > 0` efetivo → `422`
      "Defina a conversão de créditos de IA do plano".
- [ ] Plano em uso não pode ser apagado (`409`); mudar recursos/limites de um plano vale na hora
      para todas as barbearias dele (sem cache — ou cache invalidado na escrita, ISS-016).
- [ ] Toda escrita no catálogo, no plano de uma barbearia e nos créditos fica no `core_audit_log`
      (já é assim para `/core/*`), com o antes e o depois no `payload`.

### Verificação de recurso

- [ ] `require_feature(tenant, PlanFeature.X)` (função que levanta `PaymentRequired`) e
      `feature_required(PlanFeature.X)` (a mesma coisa como dependência FastAPI), ambas no
      `identity.public`, usadas nas rotas do recurso (ex.: configurar IA, criar clube, disparar campanha, relatórios avançados).
      Ausente → `402` `{"detail": "Seu plano não inclui <recurso>. Fale com a gente para mudar de
      plano.", "code": "feature_not_in_plan", "feature": "<chave>"}`.
- [ ] Rotas de **leitura de dado já existente** não são bloqueadas (ex.: lista de clubes e adesões
      antigas depois de um downgrade continua legível) — só criar/ativar/configurar.
- [ ] Trabalho em segundo plano (worker: IA respondendo, automações, campanhas) chama
      `has_feature(tenant, X)` antes de agir e **não age** sem o recurso (sem erro ao cliente final).

### Verificação de limite

- [ ] Limites de estoque (`max_barbers`, `max_units`, `whatsapp_numbers`): `assert_within_limit(session,
      tenant, PlanLimit.X)` antes de criar um registro ativo **ou reativar** um inativo (barbeiro:
      `POST /barbers` e `PATCH` `active false→true`; unidade: criação/reativação da S01; número:
      conectar, S10). Atingido → `402` `{"detail": "Seu plano permite até N barbeiros ativos. Inative
      um barbeiro ou mude de plano.", "code": "plan_limit_reached", "limit": "max_barbers", "max": N,
      "used": N}`.
- [ ] A contagem e a inserção acontecem na mesma transação com trava
      (`pg_advisory_xact_lock(hash('plan_limit:max_barbers'))` no schema) — dois cadastros
      simultâneos não passam do limite.
- [ ] Limite mensal (`campaign_messages_per_month`): `consume_quota(session, tenant, PlanLimit.X, amount=1) ->
      QuotaResult{used, max, allowed}` faz `INSERT … ON CONFLICT DO UPDATE SET used = used + :n
      WHERE used + :n <= :max RETURNING used` em `plan_usage`. Sem linha → `allowed = False`.
      O mês é o do fuso da unidade mais antiga ativa.
- [ ] O que acontece quando a cota mensal acaba é decidido pelo consumidor: campanha → o disparo é
      recusado antes de começar com `402` se não couber inteiro (S12).

### Créditos de IA (PD-40, PD-43, PD-44)

- [ ] **Unidade.** Tudo é guardado em **milicréditos** inteiros (`*_millicredits`, `bigint`; 1 crédito
      = 1000). A política (`monthly_included`, `low_balance_threshold`) é escrita em créditos e
      convertida ×1000 ao usar. A tela mostra crédito com até 1 casa decimal (saldo arredondado para
      baixo).
- [ ] **Conta e saldo.** Cada barbearia tem uma linha em `public.ai_credit_accounts` com
      `balance_millicredits` (saldo **disponível**, ≥ 0, nunca negativo) e `held_millicredits` (soma
      das reservas abertas). O disponível é a soma de `remaining_millicredits` dos lotes não vencidos
      e é mantido na conta a cada lançamento, na mesma transação.
- [ ] **Lotes** (`public.ai_credit_lots`), de três tipos:
      `purchased` (comprado no Core), `included` (crédito mensal do plano, se `monthly_included > 0`)
      e `adjustment` (ajuste positivo do Core: cortesia, compensação). Cada lote tem
      `granted_millicredits`, `remaining_millicredits` e `expires_at` (null = não vence).
- [ ] **Ordem dos lotes** (reserva, débito e ajuste negativo): `expires_at` mais próximo primeiro,
      depois os que não vencem; empate pelo mais antigo. Tudo com a conta travada
      (`SELECT … FOR UPDATE` em `ai_credit_accounts`).
- [ ] **Extrato** (`public.ai_credit_ledger`): todo movimento vira **uma linha imutável por operação**
      com `kind` (`purchase`, `included_grant`, `adjustment`, `hold`, `release`, `consume`,
      `expire`), `amount_millicredits` (+/−), `balance_after_millicredits` (disponível depois),
      `allocations` (`[{lot_id, amount_millicredits}]`, os lotes tocados), a referência (`core_ref`,
      `hold_id`, `run_id`), e, no `consume`, `cost_usd_micros` e `call_kind` (`llm` ou
      `transcription`). O extrato é a prova para o Core e para o dono; nada é apagado nem editado.
- [ ] **Crédito comprado e ajuste vêm do Core** por `POST /core/tenants/{id}/ai-credits` (`kind`
      `purchase` ou `adjustment`, valor em `amount_millicredits`). `core_ref` é obrigatório e
      idempotente: o mesmo `core_ref` com o mesmo corpo devolve `200` com o lançamento original; com
      corpo diferente, `409`. Compra sem `expires_at` usa `purchased_expiry_days` da política (padrão
      null = **não vence**, PD-43). Ajuste negativo consome lotes como um débito; maior que o saldo
      disponível → `409` "Saldo insuficiente para o ajuste".
- [ ] **Crédito mensal incluso** (só se `monthly_included > 0`): tarefa periódica global do worker
      (S00) no dia 1, no fuso da unidade mais antiga ativa, cria o lote `included` do mês com
      `monthly_included × 1000` (`UNIQUE (tenant_id, period)` torna a tarefa idempotente). Sem
      `included_rollover` (padrão, PD-43), o lote vence no fim do mês e **não acumula**; com ele, não
      vence.
- [ ] **Vencimento de lote**: a mesma tarefa periódica (de hora em hora) zera os lotes com
      `expires_at` no passado e `remaining_millicredits > 0`, lançando `expire` no extrato e baixando
      o disponível. Parte reservada de um lote não vence enquanto a reserva está aberta; se voltar
      (`release`) a um lote já vencido, vence na mesma transação (`expire`).
- [ ] **Conversão** (E8): `usd_micros_to_millicredits(tenant, cost_usd_micros) = ceil(cost_usd_micros
      × credits_per_usd / 1000)` com o `credits_per_usd` efetivo. Custo 0 → 0. A mesma função serve
      à S11 para converter a estimativa da reserva.
- [ ] **Reserva** pelo `assistant` (S11), antes de **cada** chamada ao provedor de LLM e de cada
      transcrição: `reserve_ai_credits(session, tenant, *, run_id, estimate_millicredits) ->
      HoldResult{allowed, hold_id | None, balance_millicredits}`.
      1. Trava a conta.
      2. Com `balance_millicredits ≥ estimate_millicredits`, tira a estimativa dos lotes na ordem,
         cria a reserva (`ai_credit_holds`: `run_id`, valor, lotes tocados, `credits_per_usd`
         congelado, `expires_at = now + AI_CREDIT_HOLD_TTL_MINUTES`), lança `hold` (−estimativa) e
         soma em `held_millicredits` — `allowed = True`.
      3. Saldo insuficiente → `allowed = False`, nada é gravado.
      A estimativa é o **custo máximo** da chamada (S11: tokens de entrada contados + `max_tokens` ×
      preço do modelo, sem desconto de cache; transcrição: segundos do áudio × preço).
- [ ] **Acerto** depois da chamada: `settle_ai_credits(session, tenant, *, hold_id, cost_usd_micros)
      -> SettleResult{charged_millicredits, uncharged_millicredits, balance_millicredits}`, numa
      transação: trava a conta; devolve a reserva inteira aos lotes de onde saiu (`release`,
      +reserva); calcula o real com o `credits_per_usd` congelado na reserva e debita dos lotes na
      ordem (`consume`, −real, com `cost_usd_micros`, `run_id` e `call_kind`); fecha a reserva
      (`settled`). Custo 0 (provedor falhou sem cobrar) → só `release`. Idempotente por `hold_id`:
      acertar de novo devolve o mesmo resultado sem lançar.
- [ ] **Real maior que a reserva** (estimativa errada): o `consume` é limitado à reserva; a diferença
      sai em `uncharged_millicredits`, fica como custo da plataforma e vai para o log de erro (a S11
      corrige a estimativa). O saldo nunca fica negativo.
- [ ] **Reserva sem acerto** (queda do worker, timeout): a tarefa periódica dos créditos (a cada 5 min)
      fecha as reservas com `expires_at` no passado como `expired`, lança `release` e devolve o valor
      ao disponível. O custo que o provedor tenha cobrado fica com a plataforma (log). Acerto que chega
      depois de a reserva expirar debita o real do disponível, limitado a ele (nunca negativo), e
      registra o que faltou em `uncharged_millicredits`.
- [ ] Reserva e acerto rodam na sessão do chamador (o `public` é qualificado explicitamente; não muda
      o `schema_translate_map`). Duas execuções simultâneas nunca deixam o saldo negativo: a soma das
      reservas abertas nunca passa do disponível no momento de cada reserva.
- [ ] **Sem saldo para a reserva**: decisão do consumidor (S11). Conversa nova → "aguardando humano"
      com motivo `no_ai_credits` (S10, PD-18); no meio de uma execução → a IA encerra com uma frase
      neutra e faz handoff `no_ai_credits`. Créditos voltam → conversas novas voltam a ser da IA (as
      que já estão na fila seguem com a equipe até ela devolver, PD-18).
- [ ] **Avisos ao dono** (só no painel, sem push — PD-18): `ai_credit_status` devolve `low = true`
      quando `balance_millicredits ≤ low_balance_threshold × 1000` e `empty = true` quando o disponível
      é menor que 1 crédito (`< 1000`; não cobre uma reserva típica); o painel mostra a faixa.
- [ ] **Consumo do mês** (PD-44): soma dos `consume` do mês no fuso da unidade mais antiga ativa, em
      milicréditos e em `cost_usd_micros`, separado por `call_kind`. É o mesmo número que a S11 e a S14
      mostram.
- [ ] Suspensão (DEC-013) e mudança de plano **não mexem no saldo**: créditos comprados são da
      barbearia. Perder o recurso `ai_assistant` desliga a IA, mas o saldo continua e volta a valer
      quando o recurso voltar. Mudar `credits_per_usd` vale para as reservas seguintes.
- [ ] O **teto técnico de custo** da S11 (por conversa e por barbearia/mês) continua como proteção à
      parte, independente do saldo. O playground da S11 não reserva nem debita.

### Mudança de plano (upgrade e downgrade)

- [ ] `PUT /core/tenants/{id}/plan` responde com o plano efetivo, o uso e a lista `over_limit`
      (`[{limit, max, used}]`) — o Core avisa o vendedor antes de confirmar um downgrade.
- [ ] **Nada é apagado nem inativado automaticamente** num downgrade (PD-39): acima do limite, a
      barbearia só fica impedida de criar/reativar até voltar ao limite; o painel mostra o aviso.
- [ ] Recurso removido: dado continua guardado e legível; configurações ficam somente leitura;
      trabalho em segundo plano para. Adesões de clube ativas seguem até o fim do ciclo pago, sem
      renovação nem venda nova (Q-S15-2, S07).

### Leitura pela barbearia

- [ ] `GET /auth/me` ganha `plan {code, name, features[], limits{}}` (efetivo, sem uso) — todo
      usuário precisa para montar a navegação.
- [ ] `GET /tenant/plan` (dono) devolve plano, recursos, limites e **uso atual** (barbeiros ativos,
      unidades ativas, números de WhatsApp conectados e mensagens de campanha do mês), o **resumo dos
      créditos de IA** (`ai_credits`: `AiCreditSummary`, com saldo, inclusos, comprados, reservado,
      `low`, `empty`, próximo vencimento e consumo do mês em milicréditos e em `cost_usd_micros`) e
      `upgrade_url` (`PLAN_UPGRADE_URL`, variável de ambiente; ver Q-S15-4).
- [ ] `GET /tenant/ai-credits` (dono) devolve o resumo, a política efetiva e o **extrato** paginado
      (mais recente primeiro, filtro por `kind`). No extrato da barbearia, `hold` e `release` não
      aparecem (são reserva técnica e se anulam) e os `consume` vêm **agrupados por dia** (fuso da
      unidade mais antiga ativa) com milicréditos, `cost_usd_micros` e número de chamadas, separados
      por `call_kind`; compra, crédito do plano, ajuste e vencimento vêm um a um. Comprar créditos
      leva ao `upgrade_url` (o Navalha não vende).

## Data Contract

```text
# Control plane (X-Core-Key, fora do /docs público; entra no core_openapi.json)
GET    /core/plans                          tenant:read       → PlanDef[]
PUT    /core/plans/{code}    PlanDefIn      tenant:provision  → 200 PlanDef (upsert) | 422
DELETE /core/plans/{code}                   tenant:provision  → 204 | 404 | 409
GET    /core/tenants/{id}/plan              tenant:read       → TenantPlanOut
PUT    /core/tenants/{id}/plan TenantPlanIn tenant:provision  → 200 TenantPlanOut | 400 | 404 | 422
POST   /core/tenants   ProvisionIn.plan: obrigatório, validado no catálogo → 400 "Plano desconhecido"
CoreTenantOut + {plan_name}
GET    /core/tenants/{id}/ai-credits?cursor=&kind=   tenant:read      → AiCreditAccountOut
POST   /core/tenants/{id}/ai-credits AiCreditGrantIn tenant:provision → 201 AiCreditEntryOut
                                                     | 200 (mesmo core_ref, mesmo corpo) | 404 | 409 | 422

PlanDefIn      {name (2–60), features: PlanFeature[], limits: {PlanLimit: int|null},
                ai_credit_policy?: AiCreditPolicy (parcial; o que faltar usa o padrão)}
PlanDef        PlanDefIn + {code, tenants_count, updated_at}
TenantPlanIn   {plan: code, feature_overrides?: {add: [], remove: []},
                limit_overrides?: {PlanLimit: int|null}, ai_credit_policy_overrides?: AiCreditPolicy}
TenantPlanOut  {tenant_id, plan, plan_name, features[], limits{}, feature_overrides, limit_overrides,
                ai_credit_policy (efetiva), ai_credit_policy_overrides,
                usage: {PlanLimit: int}, over_limit: [{limit, max, used}], ai_credits: AiCreditSummary}
AiCreditPolicy {credits_per_usd: decimal > 0 (até 4 casas; obrigatório com ai_assistant),
                monthly_included: int ≥ 0 (créditos), included_rollover: bool (padrão false),
                purchased_expiry_days: int ≥ 1 | null (padrão null), low_balance_threshold: int ≥ 0
                (créditos, padrão 20)}
AiCreditGrantIn {kind: purchase|adjustment, amount_millicredits: int (purchase > 0; adjustment ≠ 0),
                 core_ref: str (1–80), expires_at?: datetime (só purchase), note?: str (≤ 200)}
AiCreditSummary {balance_millicredits, included_millicredits, purchased_millicredits,
                 held_millicredits, low, empty,
                 next_expiry: {amount_millicredits, expires_at} | null,
                 month: "YYYY-MM", consumed_millicredits, consumed_cost_usd_micros,
                 consumed_by_kind: [{call_kind: llm|transcription, millicredits, cost_usd_micros, calls}]}
AiCreditEntryOut {id, created_at, kind, amount_millicredits, balance_after_millicredits,
                  allocations: [{lot_id, amount_millicredits}], core_ref | null, hold_id | null,
                  run_id | null, call_kind | null, cost_usd_micros | null, note | null}
AiCreditAccountOut AiCreditSummary + {policy: AiCreditPolicy, lots: [{id, kind, granted_millicredits,
                   remaining_millicredits, expires_at, period}],
                   open_holds: [{id, run_id, amount_millicredits, expires_at}],
                   entries: AiCreditEntryOut[] (completo, com hold/release), next_cursor | null}

# Barbearia
GET    /auth/me        MeOut + {plan: {code, name, features[], limits{}}}
GET    /tenant/plan    subscription:manage → 200 TenantPlanUsageOut
       TenantPlanUsageOut {code, name, features[], limits{}, usage{}, period: "YYYY-MM",
                           ai_credits: AiCreditSummary, upgrade_url | null}
GET    /tenant/ai-credits?cursor=&kind=   subscription:manage → 200 TenantAiCreditsOut
       kind ∈ purchase|included_grant|adjustment|consume|expire (hold/release → 422)
       TenantAiCreditsOut AiCreditSummary + {policy: AiCreditPolicy,
                          entries: [{date (local) | created_at, kind, amount_millicredits,
                                     balance_after_millicredits, note | null,
                                     call_kind | null, cost_usd_micros | null, calls | null}],
                          next_cursor | null}
       (`consume` agrupado por dia e `call_kind`, com balance_after_millicredits do último lançamento do dia;
        sem `hold`/`release`; não expõe `core_ref`, `hold_id`, `run_id` nem lotes)

# Erro 402 (novo PaymentRequired em app/core/exceptions.py; o handler único passa a
# serializar campos extras além de "detail")
{"detail": str, "code": "feature_not_in_plan", "feature": PlanFeature}
{"detail": str, "code": "plan_limit_reached", "limit": PlanLimit, "max": int, "used": int}
```

### Banco de dados

Control (`alembic/control`, próxima `cNNNN_plans`, com `GRANT SELECT` ao runtime em `plans` e
`SELECT` nas colunas novas de `tenants` — `APP_GRANTS`):

```text
plans      code varchar(40) pk (slug: ^[a-z][a-z0-9_-]{1,39}$) · name varchar(60) ·
           features text[] not null default '{}' · limits jsonb not null default '{}' ·
           ai_credit_policy jsonb not null default '{}' · created_at · updated_at
tenants    + plan → FK plans.code ON UPDATE CASCADE ON DELETE RESTRICT  (coluna já existe)
           + feature_overrides jsonb not null default '{"add": [], "remove": []}'
           + limit_overrides jsonb not null default '{}'
           + ai_credit_policy_overrides jsonb not null default '{}'
           + plan_changed_at timestamptz null
```

A migration cria `plans`, insere **um plano por valor distinto já usado em `tenants.plan`**, com todos
os recursos e sem limites (nada muda para as barbearias que já existem), e só então cria a FK.
Dev: `python -m app.management.plans seed-dev` cria planos de exemplo (fora do contrato).

Control (`alembic/control`, próxima `cNNNN_ai_credits`; `APP_GRANTS`: `SELECT, UPDATE` em
`ai_credit_accounts` e `ai_credit_lots`, `SELECT, INSERT, UPDATE` em `ai_credit_holds`, `SELECT,
INSERT` em `ai_credit_ledger` — o runtime reserva e acerta; `INSERT` de conta e lote só pelo
provisionamento e pelo worker, que usam o mesmo role):

```text
ai_credit_accounts  tenant_id uuid pk → tenants.id ON DELETE RESTRICT ·
                    balance_millicredits bigint not null default 0 CHECK (balance_millicredits >= 0) ·
                    held_millicredits bigint not null default 0 CHECK (held_millicredits >= 0) ·
                    updated_at
ai_credit_lots      id uuid pk · tenant_id → tenants.id ON DELETE RESTRICT ·
                    kind ai_credit_lot_kind ('purchased','included','adjustment') ·
                    granted_millicredits bigint CHECK (granted_millicredits > 0) ·
                    remaining_millicredits bigint
                      CHECK (remaining_millicredits BETWEEN 0 AND granted_millicredits) ·
                    expires_at timestamptz null · period char(7) null (só included) ·
                    core_ref varchar(80) null · created_at ·
                    UNIQUE (tenant_id, core_ref) · UNIQUE (tenant_id, period) WHERE kind = 'included' ·
                    INDEX (tenant_id, expires_at) WHERE remaining_millicredits > 0
ai_credit_holds     id uuid pk · tenant_id → tenants.id ON DELETE RESTRICT · run_id uuid ·
                    amount_millicredits bigint CHECK (amount_millicredits > 0) ·
                    allocations jsonb not null ([{lot_id, amount_millicredits}]) ·
                    credits_per_usd numeric(12,4) not null (congelado) ·
                    status ai_credit_hold_status ('open','settled','expired') ·
                    charged_millicredits bigint null · uncharged_millicredits bigint null ·
                    cost_usd_micros bigint null · expires_at timestamptz · created_at · settled_at null ·
                    INDEX (expires_at) WHERE status = 'open' · INDEX (tenant_id, run_id)
ai_credit_ledger    id bigserial pk · tenant_id → tenants.id ON DELETE RESTRICT ·
                    kind ai_credit_entry_kind ('purchase','included_grant','adjustment',
                                               'hold','release','consume','expire') ·
                    amount_millicredits bigint CHECK (amount_millicredits <> 0) ·
                    balance_after_millicredits bigint CHECK (balance_after_millicredits >= 0) ·
                    allocations jsonb not null ([{lot_id, amount_millicredits}]) ·
                    core_ref varchar(80) null · hold_id → ai_credit_holds.id RESTRICT null ·
                    run_id uuid null · call_kind ai_call_kind ('llm','transcription') null ·
                    cost_usd_micros bigint null (só consume) · note varchar(200) null ·
                    request_hash char(64) null (idempotência do core_ref) · created_at ·
                    INDEX (tenant_id, created_at DESC) · INDEX (tenant_id, kind, created_at)
                    WHERE kind = 'consume'
```

`run_id` aponta para `assistant_runs` no schema da barbearia (sem FK: o control plane não referencia
tenant). Saldo disponível + `held_millicredits` = soma de `remaining_millicredits` dos lotes válidos
+ soma das reservas abertas — conferido nos testes depois de cada operação.

A migration cria uma conta (saldo 0) para cada barbearia existente; `POST /core/tenants` cria a da
nova na mesma transação.

Tenant (`alembic/tenant`, próxima `tNNNN_plan_usage`):

```text
plan_usage  metric varchar(40) · period char(7) ('YYYY-MM') · used integer not null default 0 ·
            updated_at · PRIMARY KEY (metric, period)
```

### `identity.public` (oferecido)

```text
PlanFeature, PlanLimit (enums) · PaymentRequired (exceção)
require_feature(tenant, feature) -> None      # levanta PaymentRequired (402 feature_not_in_plan)
feature_required(feature) -> Depends           # a mesma verificação como dependência de rota
get_limit(tenant, limit) -> int | None         # None = ilimitado (S10, S11 já assumem este nome)
has_feature(tenant, feature) -> bool           # worker e lógica condicional
effective_plan(tenant) -> EffectivePlan        # features, limits, ai_credit_policy
assert_within_limit(session, tenant, limit)    # 402 plan_limit_reached; trava + contagem
consume_quota(session, tenant, limit, amount=1) -> QuotaResult
quota_status(session, tenant, limit) -> QuotaResult   # sem consumir (ex.: prévia de campanha)
usd_micros_to_millicredits(tenant, cost_usd_micros) -> int   # ceil(cost × credits_per_usd / 1000)
reserve_ai_credits(session, tenant, *, run_id, estimate_millicredits)
    -> HoldResult{allowed, hold_id | None, balance_millicredits}
settle_ai_credits(session, tenant, *, hold_id, cost_usd_micros)
    -> SettleResult{charged_millicredits, uncharged_millicredits, balance_millicredits}
ai_credit_status(session, tenant) -> AiCreditSummary  # sem reservar; saldo + consumo do mês (S11, página Plano)
expire_ai_credit_holds(session, *, now) -> int         # tarefa periódica (S00), a cada 5 min
upsert_plan / delete_plan / set_tenant_plan / tenant_plan_usage   # usados pelo provisioning
grant_ai_credits / ai_credit_account                 # usados pelo provisioning (/core/*)
```

## Permissões

| Rota | Permissão | owner | manager | receptionist | barber |
|---|---|---|---|---|---|
| `GET /auth/me` (campo `plan`) | autenticado | sim | sim | sim | sim |
| `GET /tenant/plan` | `subscription:manage` (já existe, só dono) | all | — | — | — |
| `GET /tenant/ai-credits` | `subscription:manage` | all | — | — | — |
| `/core/plans*`, `/core/tenants/{id}/plan`, `/core/tenants/{id}/ai-credits` | escopos `X-Core-Key` (`tenant:read`, `tenant:provision`) | — | — | — | — |

Nenhuma permissão nova: `subscription:manage` existe desde o mapa inicial justamente para isto.

## Acceptance Criteria

- [ ] Migrations de controle e tenant aplicadas; barbearias existentes continuam com tudo liberado e
      com conta de créditos de saldo 0.
- [ ] `tests/test_provisioning/`: CRUD do catálogo, plano em uso não apaga, override soma/remove,
      chave desconhecida `422`, auditoria com antes/depois, `over_limit` num downgrade.
- [ ] `tests/test_provisioning/`: lançar compra e ajuste de créditos; `core_ref` repetido com o mesmo
      corpo → `200` sem lançar de novo, com corpo diferente → `409`; ajuste negativo maior que o saldo
      → `409`; compra sem `expires_at` respeita `purchased_expiry_days`; auditoria.
- [ ] `tests/test_identity/`: `402` de recurso e de limite com o corpo completo; reativar barbeiro
      acima do limite recusado; duas criações concorrentes no limite → uma passa; `consume_quota`
      concorrente nunca passa do máximo; `/auth/me` com o plano efetivo; cruzamento entre duas
      barbearias (uso de A não conta em B).
- [ ] `tests/test_identity/` (créditos): conversão `ceil(cost_usd_micros × credits_per_usd / 1000)`
      (custo 0 → 0, arredondamento para cima, `credits_per_usd` com casas decimais); reserva e débito
      consomem primeiro o lote que vence antes; reserva sem saldo → `allowed = False` sem lançamento;
      acerto lança `release` + `consume` com `cost_usd_micros`, `run_id` e `call_kind` e usa o
      `credits_per_usd` congelado na reserva; acerto repetido não lança de novo; real maior que a
      reserva limitado a ela com `uncharged_millicredits`; reserva expirada devolvida pela tarefa
      periódica e acerto atrasado limitado ao disponível; reservas concorrentes nunca deixam o saldo
      negativo (último crédito: uma reserva passa, a outra recebe `allowed = False`); `release` para
      lote já vencido vence na mesma transação; lote `included` do mês criado uma vez só e vencido no
      fim do mês sem `included_rollover`; compra sem `expires_at` não vence; lote vencido zerado com
      `expire` no extrato; disponível + reservado = soma dos lotes válidos + reservas abertas depois
      de cada operação; plano com `ai_assistant` sem `credits_per_usd` → `422`; extrato da barbearia
      sem `hold`/`release` e com `consume` agrupado por dia; créditos de A nunca reservados por B.
- [ ] `PERMISSIONS_MAP.md` inalterado; `core_openapi.json`, `openapi.json`, `routes.json` e
      `db_schema.json` com o diff lido; `make docs-api`.
- [ ] `PLAN_UPGRADE_URL` e `AI_CREDIT_HOLD_TTL_MINUTES` (padrão 15) em `.env.example` e
      `docs/ENVIRONMENT_VARIABLES.md`.
- [ ] Testes em `tests/test_identity/` e `tests/test_provisioning/` cobrindo as regras acima
- [ ] Snapshots de contrato revisados (`UPDATE_CONTRACT_SNAPSHOTS=1` só se a mudança for intencional)

## Dependencies

- `✅completed_identity-schema-per-tenant.md` (control plane, `core_audit_log`, registry de tenants).
- `⚪draft_platform-events-jobs.md` (S00): tarefas periódicas globais do crédito mensal incluso, do
  vencimento de lotes (de hora em hora) e da expiração de reservas (a cada 5 min).
- Consumidores que **devem** chamar a verificação (cada spec declara a rota):
  S01 (`assert_within_limit(MAX_UNITS)` ao criar/reativar unidade), S04
  (`ONLINE_BOOKING`), S07 (`MEMBERSHIPS` em criar clube/pacote/adesão), S10 (`WHATSAPP` +
  `assert_within_limit(WHATSAPP_NUMBERS)` em conectar número), S11 (`AI_ASSISTANT` +
  `usd_micros_to_millicredits`, `reserve_ai_credits` antes e `settle_ai_credits` depois de cada
  chamada ao provedor de LLM e de cada transcrição, `ai_credit_status` no painel), S12
  (`AUTOMATIONS`, `CAMPAIGNS` + `consume_quota(CAMPAIGN_MESSAGES_PER_MONTH, amount=n)`), S14
  (`ADVANCED_REPORTS`; consumo em créditos e em US$ pelo `usage_summary` da S11, que grava o
  resultado de cada acerto).
- O Core da plataforma: chama `PUT /core/plans/{code}` e `PUT /core/tenants/{id}/plan`; mostra
  `over_limit` antes de um downgrade; vende créditos de IA e os lança por `POST
  /core/tenants/{id}/ai-credits` com o id da venda como `core_ref`.

## Notes

- **Import certo.** As verificações de plano são importadas de `identity.public` (E2), não de
  `provisioning.public`, que continua sem consumidor de domínio. Nomes canônicos (alinhados entre as
  specs em 2026-11-06, revistos com a PD-40): recursos `whatsapp`, `ai_assistant`, `online_booking`,
  `memberships`, `automations`, `campaigns`, `advanced_reports`; limites `max_barbers`, `max_units`,
  `whatsapp_numbers`, `campaign_messages_per_month`. O limite `ai_monthly_usage` (e a "cota de
  conversas de IA por mês") **saiu** com a PD-40, e o débito de 1 crédito por conversa numa janela de
  24 h (`credits_per_conversation`, `conversation_window_hours`, `consume_ai_credit`) **saiu** com a
  PD-43: o uso da IA é `reserve_ai_credits`/`settle_ai_credits`/`ai_credit_status`.
- O contador próprio da S11 (`assistant_calls`, `assistant_usage_monthly`) guarda tokens,
  `cost_usd_micros` e os milicréditos de cada acerto, para o teto técnico e os relatórios (S14); não é
  ele que libera ou trava a IA — quem decide é a reserva.
- Fonte da verdade do saldo é o extrato do control plane. O consumo do mês da página Plano vem dele
  (`ai_credit_status`); o detalhe por conversa e agendamento vem da S11. Os dois batem porque a S11
  grava o `charged_millicredits` devolvido pelo acerto.
- Trial: não há conceito aqui; se o Core vender período de teste, ele escolhe um plano e suspende
  ao fim (e pode lançar créditos de cortesia como `adjustment`). O Navalha não conta dias.
- Cache do plano: se o ISS-016 ganhar cache do registry, o `set_tenant_plan` invalida a entrada.
- Débito no control plane a partir do worker de uma barbearia: a linha da conta é a trava; não há
  trava global. A tarefa periódica dos lotes roda com a trava das tarefas periódicas no Redis (S00).

### Perguntas em aberto

- ✅ **Q-S15-1 — Downgrade com dados acima do limite (ex.: 6 barbeiros ativos, plano novo permite 4).**
  (a) nada é desativado; só não cria nem reativa até ficar dentro do limite; (b) o dono escolhe quais
  ficam ativos em até 7 dias, depois o sistema inativa os mais recentes; (c) o Core recusa o downgrade
  enquanto houver excesso.
  **Recomendação: (a)** com aviso permanente para o dono — nunca derruba a agenda de um barbeiro com
  clientes marcados; o Core já recebe `over_limit` para negociar.
  > Resolvido em 2026-11-06: (a) — nada é desativado; só fica bloqueado criar/reativar até voltar ao limite (PD-39).
- ✅ **Q-S15-2 — Recurso `memberships` removido com assinantes ativos.**
  (a) adesões ativas seguem até o fim do ciclo pago, sem renovação nem venda nova; (b) seguem
  indefinidamente, só sem venda nova; (c) param na hora.
  **Recomendação: (a)** — honra o que o cliente final pagou e encerra o produto de forma previsível.
  > Resolvido em 2026-11-06: (a) — seguem até o fim do ciclo pago, sem renovação nem venda nova (ROADMAP §7).
- ✅ **Q-S15-3 — Cota mensal de IA esgotada no meio do mês.**
  (a) a IA para e a conversa nova cai em "aguardando humano" (PD-18) com motivo "limite do plano";
  (b) a IA continua e o excedente é informado ao Core para cobrança; (c) a IA continua só para
  clientes com agendamento em andamento.
  **Recomendação: (a)** agora, com aviso ao dono a 80% e 100% — (b) é o caminho quando o Core
  souber cobrar excedente.
  > Resolvido em 2026-11-06: não há mais cota mensal — a IA usa créditos (inclusos no plano e comprados), debitados proporcionalmente ao custo de cada chamada; sem saldo para a reserva, conversa nova vai para "aguardando humano" com motivo `no_ai_credits` e, no meio de uma execução, a IA encerra com frase neutra e faz handoff `no_ai_credits`; o dono vê aviso de saldo baixo e de saldo zerado (PD-40, PD-43 | ROADMAP §7).
- ✅ **Q-S15-4 — Para onde leva o botão "Mudar de plano"?**
  (a) portal do cliente no Core (`PLAN_UPGRADE_URL`); (b) WhatsApp do comercial; (c) só texto
  "fale com o suporte".
  **Recomendação: (a)** quando o portal existir, com (b) como valor da mesma variável até lá.
  > Resolvido em 2026-11-06: (a) quando o portal existir; até lá, `PLAN_UPGRADE_URL` aponta para o WhatsApp do comercial (ROADMAP §7). Vale também para "Comprar créditos".
- ✅ **Q-S15-6 — Créditos de IA: o que gasta um crédito, o plano inclui créditos e créditos vencem?**
  A PD-40 decidiu o modelo (créditos comprados no Core) e deixou isto em aberto. Tudo é parâmetro de
  `ai_credit_policy` (E6) — a resposta muda dado, não código (exceto 1b/1c).
  1. **Unidade de consumo:** (a) 1 crédito = 1 conversa de IA numa janela de 24 h (a mesma conversa
     volta a custar depois de 24 h); (b) 1 crédito por resposta da IA; (c) proporcional ao custo do
     provedor (tokens). (b) e (c) mudam o ponto de débito na S11.
  2. **Créditos inclusos no plano:** (a) nenhum, só créditos comprados; (b) o plano inclui N créditos
     por mês, que **não acumulam** (vencem no fim do mês); (c) inclui N por mês, acumulando.
  3. **Validade dos créditos comprados:** (a) não vencem; (b) vencem em 12 meses; (c) vencem com o
     ciclo do plano.
  **Recomendação: 1(a), 2(b), 3(a)** — conversa é a unidade que o dono entende e compara com a
  recepção, e o teto técnico de custo da S11 protege a conversa longa; crédito mensal incluso deixa o
  plano "com IA" funcionando desde o primeiro dia sem compra, e não acumular evita passivo crescente;
  crédito pago que vence gera atrito e chamado de suporte. Padrões da política até a resposta:
  `credits_per_conversation = 1`, `conversation_window_hours = 24`, `monthly_included = 0` (o Core
  define por plano), `included_rollover = false`, `purchased_expiry_days = null`.
  > Resolvido em 2026-11-06: 1(c) proporcional ao custo (credits_per_usd, milicréditos, reserva e acerto), 2(b), 3(a) (PD-43); custo em US$ visível ao dono (PD-44).
