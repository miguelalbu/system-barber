# Dashboard e relatórios

**Priority:** medium
**Status:** draft
**Espelho no frontend:** `frontend/docs/specs/⚪draft_frontend-reports.md`


> ⚠️ **Em revisão:** o modelo de créditos de IA (PD-40/43/44) será substituído por custo de tokens
> por barbearia com chave própria ou administrada pela plataforma — ver o aviso no ROADMAP §1.
> Revisar as partes de créditos antes de implementar.
## Overview

O dashboard do painel é hoje um mock do protótipo. Esta spec cria o módulo `reports` (só leitura):
os **KPIs do dia** do dashboard e quatro relatórios — **faturamento**, **ocupação da agenda**,
**clientes e retenção** e **desempenho da IA** (PD-25) — com filtro por período, unidade e barbeiro,
comparação com o período anterior e exportação CSV.

A decisão central é **de onde vêm os números**. `reports` mantém um **read model em grão de linha**
(uma linha por agendamento, item de agendamento, comanda, item de comanda, pagamento e cobrança de
clube), alimentado pelos eventos de domínio (S00) com upsert pela chave natural. Os relatórios são
`GROUP BY` sobre essas tabelas, indexadas por `(local_date, unit_id)`. Duas coisas não vêm de evento,
porque não são fatos e sim cálculo sobre configuração ou dado de outro dono: a **capacidade** da
agenda (minutos disponíveis, do `scheduling`) e as **métricas da IA** (conversas, créditos
consumidos e custo estimado em US$, do `assistant`/`messaging`), lidas pelas funções públicas desses
módulos na hora da consulta.

Referência de mercado: o "Painel" do Trinks (faturamento do dia, ocupação, ticket médio) e os
relatórios da Fresha/Booksy (receita por profissional e por serviço, clientes novos × recorrentes,
taxa de retorno, faltas), com exportação para planilha.

## Decisões de produto já tomadas

| Parâmetro | Valor |
|---|---|
| PD-25 | Relatórios: faturamento, ocupação da agenda, clientes e retenção, desempenho da IA (conversas, agendamentos pela IA, handoff, abandono, custo). |
| PD-06/PD-07 | Origem do agendamento (IA, link, painel) e "não confirmado"/falta são dimensões dos relatórios. |
| PD-10 | Faturamento = pagamentos **registrados** (sem gateway); por forma de pagamento. |
| PD-14 | Resultado do mês (despesas, lucro) é do `finance` (S09); aqui só faturamento e produção. |
| PD-22 | Relatórios avançados ficam atrás do recurso de plano `advanced_reports` (S15; Q-S14-4, resolvida). |
| PD-37 | A IA não fecha venda de clube/pacote: registra o interesse e passa para a equipe (handoff `sale`). O relatório conta interesses encaminhados, não "vendas da IA". |
| PD-40 | IA por **créditos** (S15). |
| PD-43 | Crédito **proporcional ao custo real** de cada chamada ao modelo e de cada transcrição (`credits_per_usd`, milicréditos, reserva e acerto — S15). |
| PD-44 | O dono vê o consumo da IA **em créditos e o custo estimado em US$** (`cost_usd_micros`). |
| Convenções §2 | Centavos; dia no fuso da unidade; escopo `all/unit/own`. |

### Proposta desta spec: read model por eventos, não consulta aos módulos

| Opção | Prós | Contras |
|---|---|---|
| (1) Consultar as funções públicas de cada módulo (`scheduling.public.aggregate…`, `sales.public.revenue…`) | número sempre exato, sem tabela nova | cada módulo cresce SQL de relatório; o dashboard (aberto o dia todo por toda a equipe) faz `GROUP BY` nas tabelas quentes da operação; cruzar agenda × comanda × cliente vira N chamadas e junção em Python |
| (2) **Read model em grão de linha, por eventos** (escolhida) | uma consulta SQL por relatório, com junções locais; zero carga nas tabelas da operação; filtros livres (unidade × barbeiro × período) sem pré-agregar; evento repetido/fora de ordem resolvido por upsert | atraso de segundos (entrega do worker); precisa de recálculo para backfill |
| (3) Agregados diários pré-calculados | consulta trivial | combinação de filtros explode; estorno de comanda de dias atrás exige recalcular agregados; difícil de corrigir |

Escala que justifica (2) sem (3): uma barbearia grande faz ~200 atendimentos/dia → ~75 mil
agendamentos e ~150 mil itens por ano por schema; `GROUP BY` indexado por data nisso responde em
milissegundos.

## Business Rules

### Ingestão (read model)

- [ ] Cada assinante faz upsert pela chave natural (`appointment_id`, `ticket_id`,
      `(ticket_id, item_id)`, `(ticket_id, payment_id)`, `cycle_id`) e só aplica o evento se o
      `occurred_at` do envelope for **mais novo** que o `source_updated_at` guardado (fora de ordem
      não regride). Os itens de um agendamento são **substituídos inteiros** a cada evento dele (o
      payload da S03 traz a lista completa; não há id de item).
- [ ] O evento só traz ids (S00). Nomes de serviço, produto, combo e forma de pagamento são
      resolvidos **na ingestão** por `catalog.public` e gravados no fato (snapshot: renomear o serviço
      depois não reescreve o relatório).
- [ ] `local_date` é calculado na ingestão pelo fuso da unidade do fato (`identity.public`).
- [ ] `ticket.voided` marca a comanda `voided`: some do faturamento, fica na exportação com o status.
- [ ] `appointment.no_show_reverted` (S03) volta o status do fato; `client.merged` re-aponta `client_id` da origem para o destino; `client.anonymized` não muda
      nada (o read model não guarda dado pessoal, só ids).
- [ ] `python -m app.management.reports_rebuild --schema <s> [--since AAAA-MM-DD]` reconstrói o read
      model puxando dos `public.iter_report_facts(...)` de `scheduling`, `sales` e `memberships`.

### Definições (iguais na tela, no CSV e nos testes)

- [ ] **Faturamento** reconhecido na **data de fechamento da comanda** (Q-S14-2). Bruto = soma dos
      itens antes de desconto; líquido = bruto − descontos; ticket médio = líquido ÷ comandas fechadas.
      Mensalidade de clube entra pela data de pagamento, em linha separada ("Clubes").
- [ ] **Produção por barbeiro** = líquido dos itens atribuídos a ele (serviço e produto); item sem
      barbeiro vai para "Sem barbeiro".
- [ ] **Ocupação** = minutos agendados ÷ minutos de capacidade, por barbeiro e dia. Agendados =
      itens de agendamento não cancelados (falta **conta** como ocupado: o horário foi perdido).
      Capacidade = jornada − folgas − bloqueios − fechamentos (`scheduling.public.capacity_minutes`, S02, por barbeiro e dia).
      Capacidade zero → ocupação "—", nunca divisão por zero.
- [ ] **Taxa de falta** = faltas ÷ (concluídos + faltas). **"Não confirmados"** = agendamentos que
      chegaram ao horário sem confirmação (PD-07).
- [ ] **Clientes**: novo = primeira visita no período; recorrente = visitou no período e antes dele;
      **ativo** = visita nos últimos N dias, **inativo** = sem visita há mais de N dias, com N =
      limite de reativação das automações (PD-20, padrão 40; Q-S14-3); **retenção** = % dos clientes
      com visita no período anterior que voltaram no período.
- [ ] **IA**: conversas iniciadas pelo cliente no período; resolvidas só pela IA; handoff (PD-18) e
      taxa; agendamentos criados pela IA (`origin = assistant`) e o faturamento deles (comandas desses
      agendamentos); abandono = começou a agendar e não concluiu; recuperados = abandono que virou
      agendamento depois do lembrete (PD-17); interesses em clube/pacote encaminhados à equipe
      (`assistant_offer_interests`, handoff `sale` — PD-37); **consumo** (PD-43, PD-44) em
      **créditos** (`*_millicredits`) e em **custo estimado em US$** (`cost_usd_micros`): no período
      e na série, médio por conversa, médio por agendamento feito pela IA e por tipo de chamada
      (`llm` = conversa, `transcription` = transcrição de áudio). Só chamadas cobráveis (o playground
      não entra). Média por conversa = consumo ÷ conversas atendidas pela IA; por agendamento =
      consumo das conversas que geraram agendamento ÷ agendamentos pela IA (`null` sem agendamento).
- [ ] **Plano (Q-S14-4):** sem `advanced_reports`, a barbearia tem o dashboard e os relatórios de
      **faturamento** e **ocupação** por **mês de calendário** (um mês por vez, sem `compare`, sem
      `group_by` diferente de `day`). Período livre, comparação,
      **clientes**, **IA** e **CSV** exigem `advanced_reports` → `402 feature_not_in_plan`.

### Consultas

- [ ] Período em datas locais (`date_from`, `date_to`, inclusivas), no máximo 366 dias (`422`).
      `group_by` = `day | week | month` (semana começa na segunda).
- [ ] `compare=true` devolve o mesmo bloco de totais do período anterior de mesmo tamanho.
- [ ] Escopo: `unit` limita às unidades do usuário (filtro `unit_id` fora delas → `403`); `own`
      força `barber_id` = o barbeiro do token e ignora o filtro.
- [ ] Dinheiro só sai para quem tem `finance:read`; nos relatórios que não são de faturamento, os
      campos em centavos vêm `null` sem ela (mesma regra da S13). No relatório de IA, créditos e custo
      em US$ seguem a mesma regra: `null` sem `finance:read` (a recepção não vê).
- [ ] Dashboard: KPIs de **hoje** na unidade selecionada (ou todas): agendamentos (e quantos não
      confirmados), ocupação, faturamento e ticket médio (com `finance:read`), faltas evitadas
      (confirmações por lembrete em 7 dias), série dos últimos 14 dias. Lista "próximos agendamentos"
      e "conversas aguardando" **não** são deste módulo: o frontend lê do `scheduling` e do
      `messaging`, que são tempo real.
- [ ] Resposta traz `generated_at` e `freshness_seconds` (idade do último evento aplicado), para a
      tela dizer "atualizado há N s".

### Exportação CSV

- [ ] `GET /reports/<relatório>/export` com os mesmos filtros devolve `text/csv` em streaming, uma
      linha por fato (comanda, agendamento, cliente, conversa), separador `;`, UTF-8 com BOM, valores
      em reais com vírgula (`1234,56`) e datas `dd/mm/aaaa` — abre direto no Excel em português. No
      CSV de IA (uma linha por conversa), créditos com 1 casa (`12,3`) e custo em US$ com 4 casas
      (`0,0123`), colunas separadas por tipo (conversa, transcrição).
- [ ] Máximo 100 mil linhas (`422` "Reduza o período"); colunas de dinheiro omitidas sem
      `finance:read`; CSV exporta ids e nomes, **nunca telefone/e-mail** (LGPD: exportação de dado
      pessoal é a da S13).

## Data Contract

```text
# Módulo reports, tag "reports". Filtros comuns (F):
#   date_from, date_to (YYYY-MM-DD), unit_id[]?, barber_id[]?, group_by=day|week|month, compare=false
GET /reports/dashboard?unit_id=           → 200 DashboardOut
GET /reports/revenue?F                    → 200 RevenueReportOut   | 402 | 403 | 422
GET /reports/occupancy?F                  → 200 OccupancyReportOut | 402 | 403 | 422
GET /reports/clients?F                    → 200 ClientsReportOut   | 402 | 403 | 422
GET /reports/ai?F                         → 200 AiReportOut        | 402 | 403 | 422
GET /reports/{revenue|occupancy|clients|ai}/export?F  → 200 text/csv | 402 | 403 | 422

DashboardOut       {date, generated_at, freshness_seconds,
                    appointments: {total, unconfirmed, completed, no_show},
                    occupancy_pct | null, revenue_cents | null, avg_ticket_cents | null,
                    reminders_confirmed_7d, series_14d: [{date, appointments, revenue_cents|null}]}
Totals (revenue)   {gross_cents, discount_cents, net_cents, tickets, avg_ticket_cents,
                    services_cents, products_cents, memberships_cents}
RevenueReportOut   {totals, previous: totals|null, series: [{period, net_cents, tickets}],
                    by_payment_method: [{method_id, name, amount_cents, count}],
                    by_barber: [{barber_id, name, net_cents, services, products}],
                    top_services: [{name, count, net_cents}], top_products: [...]}
OccupancyReportOut {totals: {capacity_minutes, booked_minutes, occupancy_pct, appointments,
                    no_shows, no_show_rate, cancellations, unconfirmed}, previous, series,
                    by_barber: [{barber_id, name, capacity_minutes, booked_minutes, occupancy_pct}],
                    heatmap: [{weekday 0-6, hour, occupancy_pct}],
                    by_origin: [{origin: panel|assistant|booking_link|import, appointments}]}
ClientsReportOut   {totals: {active, inactive, new, returning, retention_pct, avg_interval_days,
                    no_show_rate}, previous, series: [{period, new, returning}],
                    top_clients: [{client_id, name, visits, net_cents|null}]}
AiUsage            {millicredits, cost_usd_micros}            (null inteiro sem finance:read)
AiReportOut        {totals: {conversations, ai_only, handoffs, handoff_rate, appointments_by_ai,
                    revenue_by_ai_cents|null, abandoned, recovered, offer_interests,
                    consumed: AiUsage|null, per_conversation: AiUsage|null,
                    per_booking: AiUsage|null,
                    by_kind: [{call_kind: llm|transcription, millicredits, cost_usd_micros, calls}]|null},
                    previous,
                    series: [{period, conversations, appointments_by_ai, consumed: AiUsage|null}],
                    handoff_reasons: [{reason, count}]}
Erros: {"detail"}; 402 = recurso fora do plano (corpo da S15).
```

### Banco de dados

Migration de tenant (próxima `tNNNN_reports`), tabelas com prefixo `rpt_` (só o `reports` escreve;
sem FK para outros módulos — é read model, sobrevive a qualquer ordem de eventos):

```text
rpt_appointments       appointment_id uuid pk · unit_id · client_id null · local_date date ·
                       starts_at timestamptz · status varchar(12) · origin varchar(12)
                       (panel, assistant, booking_link, import) · confirmed_via varchar(20) null ·
                       source_updated_at timestamptz · INDEX (local_date, unit_id) · INDEX (client_id)
rpt_appointment_items  (appointment_id, seq) pk · barber_id · service_id · service_name ·
                       starts_at · duration_minutes smallint · price_cents int · local_date ·
                       INDEX (local_date, barber_id)
rpt_tickets            ticket_id uuid pk · unit_id · client_id null · appointment_id null ·
                       local_date · closed_at · status varchar(8) (closed, voided) · gross_cents ·
                       discount_cents · net_cents · source_updated_at · INDEX (local_date, unit_id)
rpt_ticket_lines       (ticket_id, item_id) pk · kind varchar(12) · item_id null · item_name ·
                       barber_id null · quantity smallint · net_cents · INDEX (ticket_id)
rpt_payments           (ticket_id, payment_id) pk · method_id · method_name · amount_cents
rpt_membership_charges cycle_id pk · client_id · unit_id null · local_date · amount_cents ·
                       status varchar(10)
rpt_state              singleton: last_event_at timestamptz (para freshness_seconds)
```

### Eventos consumidos (S00)

`appointment.created/.rescheduled/.cancelled/.confirmed/.unconfirmed/.no_show/.completed`,
`ticket.closed/.voided`, `membership.charge_paid/.cancelled`, `client.merged`.

## Permissões

Nenhuma permissão nova: cada relatório pede a permissão do dado que mostra (DEC-004 — "a recepção vê o
faturamento do dia" é uma linha no mapa, não um endpoint).

| Rota | Permissão | owner | manager | receptionist | barber |
|---|---|---|---|---|---|
| `GET /reports/dashboard` | `appointment:read` (+ `finance:read` para valores) | all | unit | unit, sem valores | own, sem valores (o frontend leva o barbeiro para "Meu dia") |
| `revenue` | `finance:read` | all | unit | — | — |
| `occupancy` | `appointment:read` | all | unit | unit | own (Q-S14-1) |
| `clients` | `client:read` + escopo ≠ `own` | all | unit (clientes que visitaram as unidades dele) | unit, sem valores | — |
| `ai` | `conversation:reply` (+ `finance:read` para créditos e US$) | all | unit | unit, sem créditos nem US$ | — |
| `by_barber` em `revenue` (produção) | `commission:read` | all | unit | — | own via S08/S18 |

## Acceptance Criteria

- [ ] Módulo `reports` com layout completo; importa os outros só pelo `public.py`; ninguém importa
      `reports` (contrato do import-linter).
- [ ] Assinantes testados com evento duplicado, fora de ordem e estorno.
- [ ] `tests/test_reports/`: cada definição acima com dados montados à mão (inclusive capacidade
      zero, falta, item sem barbeiro, período cruzando meia-noite em fuso diferente); escopo `unit` e
      `own`; `null` sem `finance:read` (inclusive créditos e US$ da IA); consumo da IA em milicréditos
      e `cost_usd_micros` por período, por conversa, por agendamento e por tipo (`llm`,
      `transcription`), sem o playground; cruzamento entre duas barbearias; sem `advanced_reports`, só
      mês de calendário em faturamento e ocupação e `402` em clientes, IA, comparação e CSV.
- [ ] CSV aberto no Excel/LibreOffice em pt-BR sem assistente de importação.
- [ ] Consulta de 12 meses sobre 100 mil agendamentos sintéticos abaixo de 300 ms (teste marcado
      `slow`, fora do portão padrão).
- [ ] Testes em `tests/test_reports/` cobrindo as regras acima
- [ ] Snapshots de contrato revisados (`UPDATE_CONTRACT_SNAPSHOTS=1` só se a mudança for intencional)

## Dependencies

- **S00**: `SUBSCRIBERS`/`Subscriber` no `reports/public.py`; envelope com `occurred_at`.
- **S03** (`scheduling`): `AppointmentEvent` (`appointment_id, unit_id, client_id, status, origin,
  starts_at, ends_at, items: [{service_id, barber_id, starts_at, ends_at, price_cents}]`),
  `confirmed_via` no `.confirmed`, e `appointment.no_show_reverted`. **Pedido:**
  `iter_report_facts(session, since)` para o rebuild.
- **S02**: `capacity_minutes(session, *, unit_id, start, end, barber_ids=None, by_day=False)`. **Pedido:** variante
  por dia (`by_day=True -> dict[(date, barber_id), int]`) — a série e o mapa de calor precisam do
  dia, e o mapa de calor precisa dos intervalos (`working_intervals(...)`).
- **S06** (`sales`): `ticket.closed` (`items[]` com `item_id, kind, service_id, product_id, combo_id,
  barber_id, net_cents`; `payments[]` com `payment_id, payment_method_id, method_kind,
  amount_cents`; `subtotal_cents, discount_cents, total_cents`) e `ticket.voided`. **Pedido:**
  `iter_report_facts`.
- **S07** (`memberships`): `membership.charge_paid/.cancelled`; **pedido:** `iter_report_facts`.
- **S11** (`assistant`): `usage_summary(session, *, date_from, date_to, unit_id=None) ->
  AssistantUsageSummary` — **pedido:** aceitar `group_by` e devolver também `ai_only`,
  `handoffs_by_reason`, `abandonment_sent/recovered`, `appointment_ids` (para cruzar com o
  faturamento), `offer_interests` e o consumo das chamadas cobráveis (`assistant_calls`:
  `charged_millicredits` e `cost_usd_micros`) no total, por período, por `call_kind`, por conversa e
  por agendamento (PD-43, PD-44). **S10**: `GET /conversations?queue=waiting_human` para o
  dashboard (rota dela).
- **S12** (`automations`): `inactive_after_days(session) -> int` (PD-20).
- **S13** (`clients`): eventos `client.merged`.
- **S15**: `require_feature(PlanFeature.ADVANCED_REPORTS)` conforme Q-S14-4.
- Oferece: nada para outros módulos (topo do grafo).

## Notes

- Custo da IA: a barbearia paga a IA em créditos, debitados proporcionalmente ao custo do provedor
  (PD-43); o relatório mostra os **dois números** (PD-44): créditos consumidos (o que sai do saldo) e
  custo estimado em US$ (`cost_usd_micros` da S11, o custo do provedor sem a margem). `cost_usd_micros`
  é a exceção à convenção de centavos em BRL (ROADMAP §2); a tela formata em dólar. Créditos
  comprados, saldo e extrato ficam na página Plano (S15).
- Créditos e US$ ficam atrás de `finance:read` (mesma regra do dinheiro): a recepção vê o desempenho
  da IA sem o custo.
- O read model não guarda nome de cliente, telefone nem e-mail — só ids. O nome sai de
  `clients.public` na hora (top clientes), o que mantém a anonimização da S13 automática aqui.
- Ocupação de agendamento com barbeiros em sequência (PD-05) é por item: cada barbeiro ocupa só a
  parte dele.
- Atraso esperado do read model: o tempo de entrega do worker (segundos). Se um dia o dashboard
  precisar ser instantâneo, os KPIs de "hoje" podem ler direto do `scheduling` sem mudar o contrato.

### Perguntas em aberto

- ✅ **Q-S14-1 — O barbeiro vê relatórios?**
  (a) não: só "Meu dia" e as comissões (S18/S08); (b) os **dele**: ocupação e produção (serviços e
  valor que gerou), sem faturamento da casa; (c) tudo da unidade.
  **Recomendação: (b)** — é o que motiva o comissionado (Trinks e AppBarber mostram "minha produção")
  e não expõe a receita da casa.
  > Resolvido em 2026-11-06: (b) — o barbeiro vê os dele: ocupação e produção, sem faturamento da casa (ROADMAP §7).
- ✅ **Q-S14-2 — Em que data o faturamento conta?**
  (a) data de fechamento da comanda (o dinheiro entrou); (b) data do atendimento; (c) mostrar as duas
  com seletor.
  **Recomendação: (a)** — bate com o caixa diário (S09) e com o extrato da maquininha; atendimento e
  fechamento quase sempre caem no mesmo dia.
  > Resolvido em 2026-11-06: (a) — data de fechamento da comanda (ROADMAP §7).
- ✅ **Q-S14-3 — Quando um cliente é "inativo" nos relatórios?**
  (a) o mesmo limite da reativação automática (PD-20, padrão 40 dias, ajustável); (b) fixo 90 dias;
  (c) limite próprio dos relatórios.
  **Recomendação: (a)** — um número só no produto: o cliente que o relatório chama de inativo é
  exatamente quem a automação vai tentar reativar.
  > Resolvido em 2026-11-06: (a) — o mesmo limite da reativação (40 dias, ajustável) (ROADMAP §7).
- ✅ **Q-S14-4 — O que fica atrás do recurso de plano `advanced_reports`?**
  (a) nada: relatórios em todos os planos; (b) dashboard + faturamento e ocupação do mês em todos;
  período livre, comparação, clientes/retenção, IA e CSV no avançado; (c) só o dashboard fora do
  avançado.
  **Recomendação: (b)** — o básico responde "como foi o mês"; o avançado é argumento de upgrade.
  > Resolvido em 2026-11-06: (b) — básico: dashboard + faturamento e ocupação do mês; `advanced_reports`: período livre, comparação, clientes/retenção, IA e CSV (ROADMAP §7).
