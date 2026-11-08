# Eventos de domínio, outbox e worker

**Priority:** high
**Status:** draft
**Espelho no frontend:** não se aplica

## Overview

A partir da agenda, um fato num módulo precisa provocar reação em outros: o agendamento criado
agenda um lembrete (S12), a comanda fechada vira comissão (S08) e atualiza a "última visita" do
cliente (S13). Pela regra de dependência (DEC-006, ROADMAP §3) um módulo básico nunca importa um
mais alto, então a conversa "para cima" é por **evento de domínio**. Esta spec cria a
infraestrutura: **outbox transacional** (o evento é gravado na mesma transação do dado, então nunca
existe evento de dado que não foi salvo nem dado salvo sem evento), **entrega** a assinantes
idempotentes com nova tentativa e fila de falhas, **jobs avulsos com hora marcada** (`schedule_job`:
o lembrete 24 h antes, o envio de mensagem depois do commit, o "debounce" da IA, a importação em
segundo plano) e **tarefas periódicas** por barbearia (reativação, aniversário, cobrança do clube,
limpezas). Tudo roda num processo novo, o **`worker`**,
mesma imagem do `core-api`. Nenhuma rota HTTP nova: só infraestrutura e o contrato que os módulos
usam para publicar, assinar e agendar.

## Decisões de produto já tomadas

| Parâmetro | Valor |
|---|---|
| Comunicação entre módulos | Para cima, só por evento (ROADMAP §3); assinantes idempotentes |
| Processo | `worker` separado, mesma imagem; Redis já provisionado (ROADMAP §3, "Processos") |
| Usos previstos | Lembrete e "não confirmado" (PD-07), reativação, aniversário, avaliação (PD-20), cobrança do clube (PD-10), expiração de pacote, créditos de IA (lote mensal incluso, vencimento de lotes e expiração de reservas a cada 5 min — S15) |
| Isolamento | Schema por barbearia (DEC-011): o outbox mora no schema da barbearia, nunca no `public` |

### Decisões técnicas desta spec

| # | Decisão | Por quê |
|---|---|---|
| T1 | **Outbox por schema** (`outbox_events` em cada `tenant_<slug>`) | Mesma transação do dado sem tocar o `public`; o payload é dado da barbearia, e o `public` é só controle. |
| T2 | **Entrega por assinante** (`event_deliveries`, uma linha por evento × assinante) | Um assinante com erro tenta de novo sozinho, sem reexecutar os que já deram certo. |
| T3 | Handler roda **na mesma transação** que marca a entrega como feita | Para efeito só no banco, o resultado é "exatamente uma vez". Efeito externo (WhatsApp) é "pelo menos uma vez" e o assinante usa o `event_id` como chave de idempotência. |
| T4 | Despertar por **`pg_notify` na transação** + varredura periódica | O `NOTIFY` só sai no commit (transacional), então o worker acorda em milissegundos sem polling apertado em N schemas; a varredura cobre o worker que estava fora do ar. |
| T5 | Tarefas agendadas **por varredura do estado** ("tudo que venceu e ainda não foi feito"), com trava Redis por (tarefa, barbearia, janela) | Tarefa perdida (worker parado) se recupera sozinha na próxima janela; réplicas do worker dividem o trabalho sem líder. |
| T6 | Implementação própria (asyncio + `FOR UPDATE SKIP LOCKED` + redis-py), **sem** Celery/arq/saq | O necessário é pequeno; uma lib de fila traria um segundo lugar de verdade (a fila) além do banco. Regra "solução nativa antes de dependência". |
| T7 | Job avulso (`schedule_job`) é uma **linha no schema da barbearia** (`scheduled_jobs`), gravada na transação de quem agenda, com `dedupe_key` única | Agendar é transacional como publicar (rollback = sem job); a chave dá "no máximo um" mesmo com evento repetido. O worker mantém em memória só "próximo `run_at` por schema" (nome do schema e horário, nenhum dado), para acordar na hora certa (precisão de ~1 s, necessária ao debounce da IA). |

## Business Rules

### Publicar

- [ ] `publish(session, type, payload, *, aggregate_id, actor)` grava em `outbox_events` usando a
      **sessão da requisição** (mesma transação). Rollback da transação = evento não existe.
- [ ] Na mesma transação, `SELECT pg_notify('navalha_outbox', <schema>)`: o payload do `NOTIFY` é
      só o nome do schema (nenhum dado da barbearia sai do banco por aí).
- [ ] Todo tipo de evento é declarado num catálogo (`EventType`) com o schema Pydantic do payload e
      uma `version`; publicar tipo desconhecido ou payload inválido é erro de programação (exceção,
      não 4xx).
- [ ] Payload leva **ids e o mínimo de estado** (horários, status, valores); nunca nome, telefone ou
      texto livre do cliente — quem precisa lê pelo `public.py` do dono do dado. Evento guardado não
      vira cópia de dado pessoal (LGPD).

### Entregar

- [ ] O **dispatcher** de um schema pega eventos com `dispatched_at IS NULL` em ordem de `seq`
      (`FOR UPDATE SKIP LOCKED`, lote de 100), cria uma `event_deliveries` por assinante registrado
      para o tipo (`ON CONFLICT DO NOTHING`) e marca `dispatched_at`. Evento sem assinante só é
      marcado.
- [ ] O **deliverer** pega entregas `pending` com `next_attempt_at <= now()` (`SKIP LOCKED`, lote
      de 50) e roda o handler num `SAVEPOINT` da sessão do schema; sucesso → `done` + `done_at` no
      mesmo commit.
- [ ] Erro no handler: desfaz o savepoint, `attempts += 1`, `last_error` (truncado em 2000, sem
      stack de dado pessoal), `next_attempt_at` com espera exponencial (30 s, 2 min, 10 min, 1 h,
      6 h, 6 h…). Ao chegar em `EVENT_MAX_ATTEMPTS` (padrão 8) → `failed` e log `ERROR`; não trava
      as outras entregas.
- [ ] Duas réplicas do worker nunca executam a mesma entrega ao mesmo tempo (`SKIP LOCKED`); a mesma
      entrega executada duas vezes (crash depois do efeito externo, antes do commit) é tolerada
      porque o assinante é idempotente.
- [ ] **Ordem não é garantida** entre eventos do mesmo agregado. O assinante decide pelo estado atual
      lido do dono do dado (ex.: lembrete de agendamento que já foi cancelado não sai), nunca só pelo
      payload.
- [ ] Reprocessar uma entrega `failed` é comando de operador:
      `python -m app.management.events retry --tenant <slug> [--delivery <id> | --subscriber <nome>]`.
- [ ] Limpeza: entregas `done`, jobs `done`/`cancelled` e eventos totalmente entregues com mais de
      30 dias são apagados pela
      tarefa `platform.purge_outbox` (diária). `failed` fica até alguém reprocessar ou descartar.

### Jobs avulsos (`schedule_job`)

- [ ] `schedule_job(session, name, *, run_at, payload, dedupe_key=None)` grava em `scheduled_jobs` na
      transação de quem chama (+ `pg_notify`); `run_at <= now` = executar assim que possível
      (substitui o "enqueue"). `name` é um handler registrado (`JOB_HANDLERS` no `public.py` do
      módulo); nome desconhecido é erro de programação.
- [ ] `dedupe_key` repetida não cria outro job (`ON CONFLICT DO NOTHING`) e devolve o existente;
      `cancel_job(session, dedupe_key)` passa um job `pending` para `cancelled` (job já rodando ou
      feito não muda).
- [ ] Execução igual à da entrega de evento: `FOR UPDATE SKIP LOCKED` nos vencidos, handler num
      `SAVEPOINT`, `done` no mesmo commit, espera exponencial e `failed` em `EVENT_MAX_ATTEMPTS`.
- [ ] O handler **revalida o estado** ao rodar (o agendamento ainda existe, no mesmo horário…) e
      termina sem efeito quando o motivo do job acabou — é assim que remarcação e cancelamento
      "desagendam" sem precisar achar o job.
- [ ] Depois de processar um schema, o worker lê `min(run_at)` dos `pending` e agenda o próximo
      despertar daquele schema; a varredura de `OUTBOX_SWEEP_SECONDS` cobre o que escapar.

### Tarefas periódicas

- [ ] Cada módulo declara tarefas em `app/modules/<m>/jobs/` como `PeriodicTask(name, every,
      handler)`, com `name` `<modulo>.<acao>` e `every` em minutos (1–1440) ou `daily_at` (hora local
      da **unidade** — o handler recebe `now` em UTC e resolve o fuso; a tarefa diária roda a cada
      hora e cada unidade age quando chega a hora dela).
- [ ] Janela = `floor(now / every)`. Antes de rodar uma (tarefa, barbearia, janela), o worker faz
      `SET platform:task:<name>:<schema>:<janela> NX EX <every+60s>` no Redis; só quem pega a trava
      roda. Réplicas dividem as barbearias sem líder.
- [ ] O handler é **por varredura** e idempotente: age sobre tudo que venceu até `now` e ainda não
      foi feito (marcas no próprio dado, ex.: `reminder_sent_at`). Janela perdida não precisa ser
      "recuperada": a próxima pega o atraso.
- [ ] Cada execução roda numa `tenant_session(schema)` própria com timeout (`TASK_TIMEOUT_SECONDS`,
      padrão 120); erro numa barbearia é logado e não afeta as outras.
- [ ] Redis fora do ar: tarefas periódicas param (log `ERROR` a cada janela); entrega de eventos e os jobs avulsos
      continuam (não dependem do Redis).

### Quais barbearias

- [ ] O worker lê do control plane as barbearias **servíveis** (mesma regra do `assert_servable`:
      `status = active` e `schema_version` não atrasada), com cache de 60 s. `suspended`,
      `provisioning`, `failed`, `archived` e schema atrasado (migração em curso) ficam de fora — o
      outbox delas espera e é entregue quando voltarem; o assinante, pela regra acima, ignora o que
      perdeu o sentido (lembrete de horário que já passou).
- [ ] Barbearias processadas com concorrência limitada (`WORKER_TENANT_CONCURRENCY`, padrão 8),
      sempre via `tenant_session(schema)` (`schema_translate_map`) — **nunca** `SET search_path`.
- [ ] O despertar por `NOTIFY` só aceita schema que está na lista de servíveis e passa por
      `assert_safe_schema_name`; nome desconhecido é ignorado com log.
- [ ] Varredura de segurança: a cada `OUTBOX_SWEEP_SECONDS` (padrão 30) o dispatcher/deliverer passa
      por todas as servíveis (consulta barata: índice parcial nas linhas pendentes).

## Data Contract

Sem rota HTTP. O contrato é a API interna que os módulos usam (em `app/core/events/`) e as tabelas.

```text
# Publicar (qualquer service, dentro da transação da requisição)
from app.core.events import publish, Actor
await publish(session, "appointment.created", AppointmentEvent(...),
              aggregate_id=appt.id, actor=Actor.staff(ctx.user.id))

Actor           {kind: staff | client | assistant | system, user_id?: uuid}
EventEnvelope   {id, seq, type, version, occurred_at, aggregate_id, actor, payload: dict}

# Assinar (no public.py do módulo assinante, coletado pelo worker)
SUBSCRIBERS = [Subscriber(name="clients.update_indicators",
                          events=["appointment.completed", "appointment.no_show"],
                          handler=update_indicators)]
async def update_indicators(session: AsyncSession, event: EventEnvelope, ctx: JobContext) -> None

# Job avulso (na transação de quem agenda)
from app.core.events import schedule_job, cancel_job
await schedule_job(session, "automations.send_reminder", run_at=start - timedelta(hours=24),
                   payload={"appointment_id": str(appt.id)},
                   dedupe_key=f"reminder:{appt.id}:{appt.starts_at.isoformat()}")
JOB_HANDLERS = {"automations.send_reminder": send_reminder}     # no public.py do módulo
async def send_reminder(session: AsyncSession, payload: dict, ctx: JobContext) -> None

# Tarefa periódica
PERIODIC_TASKS = [PeriodicTask(name="clients.reactivation_scan", every=60, handler=...)]
async def handler(session: AsyncSession, ctx: JobContext) -> None
JobContext      {tenant_id, schema, now (UTC, injetável nos testes)}

# Operador
python -m app.management.worker                  # processo longo (compose: serviço worker)
python -m app.management.worker --once [--tenant <slug>]   # um ciclo e sai (testes, operação)
python -m app.management.events retry|discard --tenant <slug> [--delivery <id>|--subscriber <n>]
python -m app.management.events stats            # pendentes/falhas por barbearia
```

### Banco de dados

Migration de tenant `t000N_outbox` (expand: só tabelas novas):

```text
outbox_events    id uuid pk · seq bigint identity unique · type varchar(80) · version smallint ·
                 aggregate_id uuid null · actor_kind varchar(16) · actor_user_id uuid null ·
                 payload jsonb · occurred_at timestamptz default now() ·
                 dispatched_at timestamptz null
                 INDEX ix_outbox_pending (seq) WHERE dispatched_at IS NULL
                 INDEX ix_outbox_aggregate (aggregate_id, seq)

event_deliveries id uuid pk · event_id → outbox_events.id ON DELETE CASCADE ·
                 subscriber varchar(80) · status enum delivery_status(pending, done, failed) ·
                 attempts smallint default 0 · next_attempt_at timestamptz default now() ·
                 last_error varchar(2000) null · done_at timestamptz null · created_at
                 UNIQUE (event_id, subscriber)
                 INDEX ix_delivery_due (next_attempt_at) WHERE status = 'pending'

scheduled_jobs   id uuid pk · name varchar(80) · payload jsonb · run_at timestamptz ·
                 dedupe_key varchar(200) null UNIQUE ·
                 status enum job_run_status(pending, done, failed, cancelled) ·
                 attempts smallint default 0 · last_error varchar(2000) null ·
                 created_at · done_at timestamptz null
                 INDEX ix_job_due (run_at) WHERE status = 'pending'
```

O enum do job no tenant chama `job_run_status` para não colidir com `job_status` do
`provisioning_jobs` (que está no `public`, mas o nome igual confunde quem lê o banco).

Sem tabela nova no `public`. Sem `GRANT` novo (default privileges do provisionamento).
Chaves Redis: `platform:task:<name>:<schema>:<janela>` (TTL = janela + 60 s) e
`platform:worker:<hostname>:heartbeat` (TTL 30 s). Prefixo `platform:` e TTL sempre (DEC-006).

### Onde mora o código

```text
app/core/events/        model.py (OutboxEvent, EventDelivery — TenantBase) · publish.py ·
                        registry.py (EventType, Subscriber, PeriodicTask, JobContext, Actor) ·
                        dispatch.py · deliver.py · scheduler.py   — infraestrutura sem regra de negócio
app/management/worker.py   junta SUBSCRIBERS/PERIODIC_TASKS dos public.py, lê as barbearias
                           servíveis por identity.public, roda os loops (LISTEN, varredura, agenda)
app/management/events.py   comandos de operador
```

`core` continua sem importar módulo: quem conhece os módulos é o `management/worker.py`, que já usa
módulos só pelo `public.py`. O `model_registry` passa a importar `app.core.events.model` (DEC-008).
O `identity/public.py` ganha `list_servable_tenants() -> list[ServableTenant(id, slug, schema)]`.

### Variáveis de ambiente novas

`EVENT_MAX_ATTEMPTS` (8), `OUTBOX_SWEEP_SECONDS` (30), `WORKER_TENANT_CONCURRENCY` (8),
`TASK_TIMEOUT_SECONDS` (120) — em `.env.example` e `docs/ENVIRONMENT_VARIABLES.md`.

## Permissões

Nenhuma rota, nenhuma permissão. O worker não tem usuário: age como `Actor.system()`. Os comandos
de operador usam a credencial de banco, como `core_key` e `migrate`.

## Acceptance Criteria

- [ ] `app/core/events/` com publish, registry, dispatch, deliver e scheduler; `lint-imports` verde
      (core não importa módulo).
- [ ] Serviço `worker` no `backend/docker-compose.yml` (mesma imagem, depende de `migrate`
      concluído, `db` e `redis` saudáveis); `make up` sobe os três processos.
- [ ] Migration `t000N_outbox` aplicada em `tenant_template` e em todas as barbearias; `alembic
      check` limpo.
- [ ] Helpers de teste em `tests/conftest.py`: `drain_events(schema)` (dispatch + deliver até
      esvaziar, síncrono) e `run_task(name, schema, now=...)` com relógio injetado. Nenhum teste
      depende do worker rodando. `run_jobs(schema, now=...)` executa os jobs avulsos vencidos.
- [ ] Jobs avulsos: rollback de quem agenda = sem job; `dedupe_key` repetida não duplica;
      `cancel_job` só afeta `pending`; job futuro não roda antes do `run_at` (relógio injetado);
      erro → nova tentativa com espera → `failed`.
- [ ] `tests/test_platform/`: publicar dentro de transação que faz rollback não gera evento; `NOTIFY`
      só chega depois do commit; assinante com erro tenta de novo com espera e vira `failed` no
      limite, sem bloquear os outros assinantes do mesmo evento; dois dispatchers concorrentes não
      duplicam entrega; entrega repetida não duplica efeito de assinante de banco; tarefa com a mesma
      janela roda uma vez só com duas "réplicas"; barbearia suspensa e schema atrasado são pulados.
- [ ] Teste de **cruzamento entre duas barbearias**: evento publicado em A só é entregue com a sessão
      de A; o handler nunca recebe sessão de B; trava Redis de A não bloqueia B.
- [ ] `docs/ENVIRONMENT_VARIABLES.md`, `.env.example`, `README.md` (processos) atualizados.
- [ ] DEC nova em `memory/decisions.md` (T1–T6) e `progress.md`.
- [ ] Snapshot `db_schema.json` regenerado com o diff lido (só as três tabelas).

## Dependencies

- `✅completed_identity-schema-per-tenant.md` — `tenant_session`, `assert_servable`,
  `schema_version`.
- Redis do compose (já existe, hoje sem uso).
- Consumidores desta spec: S03 (publica `appointment.*`), S06, S07, S08, S13, S14 (eventos);
  S10 (envio assíncrono), S11 (debounce e abandono), S12 (lembrete, prazo de confirmação,
  avaliação), S16 (importação em segundo plano) via `schedule_job`; S07, S08, S09, S12, S17
  (tarefas periódicas e limpezas).

## Notes

- **Por que não um outbox global no `public`.** Daria uma consulta só para o dispatcher, mas
  colocaria payload de barbearia no `public` (proibido por DEC-011) e exigiria `tenant_id` + filtro
  manual em todo assinante. O custo do outbox por schema é a varredura em N schemas, resolvido pelo
  `NOTIFY` + índice parcial.
- **Escala.** Com milhares de barbearias, a varredura de 30 s vira o gargalo antes do resto; aí entra
  uma tabela de controle `outbox_dirty(tenant_id)` (sem payload) alimentada pelo `NOTIFY`. Não é
  necessário agora.
- **Tempo real no painel** (agenda atualizando sozinha) não usa o outbox nesta fase: o frontend faz
  polling (S03). Um canal SSE alimentado por um assinante é passo futuro.
- **Teste de relógio.** Nada no `core/events` chama `datetime.now()` direto: o `now` vem do
  `JobContext`, para os testes de lembrete e "não confirmado" serem determinísticos.

### Perguntas em aberto

Nenhuma decisão de produto pendente nesta spec: tudo aqui é técnico e foi decidido acima (T1–T6).
