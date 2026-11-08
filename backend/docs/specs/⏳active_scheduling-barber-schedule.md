# Jornada do barbeiro, turnos especiais, folgas e bloqueios

**Priority:** high
**Status:** active
**Espelho no frontend:** `frontend/docs/specs/⏳active_frontend-barber-schedule.md`

## Overview

Para oferecer horário (S03), o sistema precisa saber **quando cada barbeiro atende**. Esta spec cria
o módulo **`scheduling`** e, nele, a disponibilidade de trabalho do barbeiro:

1. **Jornada semanal** — os intervalos de cada dia da semana (o almoço é a lacuna entre dois
   intervalos: 09:00–12:00 e 13:00–19:00).
2. **Turno especial** — num dia específico, o barbeiro trabalha num horário diferente do habitual
   (só à tarde; sábado extra). Substitui a jornada naquele dia (modelo "editar só este dia" do
   Fresha e do Square).
3. **Ausências** — folga, férias, atestado (dias inteiros) e **bloqueio** pontual de horário
   ("reunião 15:00–16:00", "saiu mais cedo").

O tempo de trabalho efetivo de um barbeiro num dia é:
`(turno especial do dia, ou jornada semanal) ∩ horário aberto da unidade (S01) − ausências`.
A S03 subtrai daí os agendamentos para chegar nos horários livres.

O `Barber` continua no `identity` (DEC-007 reavaliada: movê-lo criaria ciclo, como a spec
`registry-basic-crud` já concluiu); o `scheduling` aponta para `barbers.id` por FK em string e lê
o barbeiro pelo `identity/public.py`.

## Decisões de produto já tomadas

| Parâmetro | Valor |
|---|---|
| Barbeiro × usuário | Cadastros separados; o barbeiro tem **uma unidade** (`barbers.unit_id`, DEC-016) |
| PD-34 | Barbeiro em **uma unidade por vez** (como hoje): para cobrir outra loja, muda-se a unidade do cadastro. Jornada por dia/unidade fica para depois, sem refazer nada (coluna `unit_id` nas tabelas de jornada, expand) |
| Fuso | Regras de dia e horário no fuso da unidade do barbeiro; banco em UTC (ROADMAP §2) |
| Grade | A jornada aceita minuto múltiplo de 5; a grade de 15 min (PD-04) é aplicada só na oferta de horário (S03) |
| Fora do planejamento | Lista de espera e recorrência de agendamento (PD-08) — bloqueio recorrente também fica de fora: para isso, mude a jornada |
| Escopo | Barbeiro (`own`) vê só a própria jornada e ausências (DEC-004) |

### Decisões técnicas desta spec

| # | Decisão |
|---|---|
| T1 | Jornada guardada como **intervalos** (até 3 por dia), não como "expediente + pausa": é o mesmo dado, sem caso especial; a tela converte. |
| T2 | Barbeiro **sem jornada salva segue o horário da unidade** (como o Booksy faz com a equipe nova). Salvar uma jornada com todos os dias vazios é recusado: para afastar, use ausência ou inative o barbeiro. |
| T3 | Ausência de dia inteiro é gravada como `timestamptz` da meia-noite local do primeiro dia à meia-noite local do dia seguinte ao último, com `all_day = true`; a resposta devolve também as datas. |
| T4 | Sem versão de jornada com "vale a partir de": mudar a jornada vale para todo o futuro; o que já estava marcado e ficar fora aparece destacado na agenda (S03). |
| T5 | Criar ausência sobre agendamentos existentes é permitido (mesma linha de Q-S01-3); a resposta lista os agendamentos afetados para a tela avisar. |

## Business Rules

### Jornada semanal

- [x] `PUT /barbers/{id}/schedule` substitui a semana: 7 dias, 0–3 intervalos cada; `starts_at <
      ends_at`, minutos múltiplos de 5, sem sobreposição nem intervalos encostados (`422`).
- [x] Semana inteira vazia → `422` "A jornada precisa de pelo menos um dia de trabalho. Para afastar
      o barbeiro, registre uma ausência ou inative o cadastro".
- [x] Intervalo fora do horário da unidade é aceito; a resposta traz `warnings` ("Terça 19:00–20:00
      fica fora do horário da unidade") e o efetivo é a interseção.
- [x] `GET` devolve `configured: false` e os dias da unidade quando o barbeiro nunca teve jornada
      (T2), e `weekly_minutes` (soma da semana efetiva, para a coluna "horas por semana").
- [x] Barbeiro inativo: jornada e ausências continuam legíveis e editáveis, mas ele não aparece na
      agenda nem na oferta de horário (S03).

### Turno especial (num dia)

- [x] `PUT /barbers/{id}/shift-overrides/{date}` define 1–3 intervalos para aquele dia (mesmas regras
      da jornada) e um `reason` opcional; substitui a jornada **só** naquele dia.
- [x] `DELETE` do mesmo dia volta à jornada semanal. Data no passado (fuso da unidade) → `422`.
- [x] Turno especial fora do horário da unidade segue T2/interseção: não abre a unidade. Para
      atender num dia em que a unidade está fechada, cadastre antes o horário especial da unidade
      (S01).

### Ausências e bloqueios

- [x] Tipos (`kind`): `day_off` (folga), `vacation` (férias), `sick_leave` (atestado) — sempre dias
      inteiros — e `block` (bloqueio de horário, dentro de um único dia local, até 24 h, minutos
      múltiplos de 5).
- [x] Dias inteiros: entrada `starts_on`/`ends_on` (inclusivo, até 180 dias); bloqueio: `starts_at`
      /`ends_at` (`timestamptz`).
- [x] Duas ausências do mesmo barbeiro não se sobrepõem → `409` "Já existe uma ausência nesse
      horário" (garantido no banco por exclusion constraint).
- [x] Ausência que termina no passado não é criada nem editada (`422`); apagar a passada é
      permitido só para dias inteiros (corrigir férias lançadas errado); bloqueio passado não se
      apaga (é o registro do porquê o horário ficou vazio).
- [x] `POST` e `PATCH` respondem `{time_off, affected_appointments: [{id, starts_at, client_name}]}`
      com os agendamentos ativos do barbeiro no período (vazio até a S03 existir).
- [x] `reason` opcional (até 200), visível só para a equipe; a IA diz apenas que o barbeiro "não
      atende nesse dia".

## Data Contract

```text
# Jornada — módulo scheduling, tag "scheduling"
GET  /schedules?unit_id=                         → 200 BarberScheduleOut[]  (barbeiros ativos no alcance)
GET  /barbers/{id}/schedule                      → 200 BarberScheduleOut | 404
PUT  /barbers/{id}/schedule   WeeklyScheduleIn   → 200 BarberScheduleOut | 403 | 404 | 422

WeeklyScheduleIn   {days: [{weekday: 1..7, intervals: [{starts_at: "HH:MM", ends_at: "HH:MM"}]}]}
BarberScheduleOut  {barber_id, unit_id, configured: bool, days: [...], weekly_minutes: int,
                    warnings: str[]}

# Turno especial
GET    /barbers/{id}/shift-overrides?from=&to=          → 200 ShiftOverrideOut[]
PUT    /barbers/{id}/shift-overrides/{date} ShiftOverrideIn → 200 ShiftOverrideOut | 403 | 404 | 422
DELETE /barbers/{id}/shift-overrides/{date}             → 204 | 403 | 404 | 422

ShiftOverrideIn   {intervals: [{starts_at, ends_at}] (1..3), reason?}
ShiftOverrideOut  {barber_id, date, intervals, reason, warnings: str[]}

# Ausências e bloqueios
GET    /time-off?unit_id=&barber_id=&from=&to=&kind=    → 200 TimeOffOut[]  (from/to obrigatórios, ≤ 366 dias)
POST   /time-off          TimeOffIn                     → 201 TimeOffResult | 403 | 404 | 409 | 422
PATCH  /time-off/{id}     TimeOffUpdate                 → 200 TimeOffResult | 403 | 404 | 409 | 422
DELETE /time-off/{id}                                   → 204 | 403 | 404 | 422

TimeOffIn      {barber_id, kind, starts_on?, ends_on?, starts_at?, ends_at?, reason?}
               (dias inteiros: starts_on/ends_on; block: starts_at/ends_at)
TimeOffUpdate  {mesmos campos menos barber_id e kind, opcionais}
TimeOffOut     {id, barber_id, kind, all_day, starts_at, ends_at, starts_on, ends_on, reason,
                created_by_user_id, created_at}
TimeOffResult  {time_off: TimeOffOut, affected_appointments: [{id, starts_at, client_name}]}

# Tempo de trabalho efetivo (a agenda S03 usa internamente; exposto para a tela de escala)
GET  /working-time?unit_id=&from=&to=     (≤ 31 dias)
     → 200 {timezone, barbers: [{barber_id, days: [{date, intervals: [{starts_at, ends_at}] (UTC),
                                 source: "weekly" | "unit_default" | "override",
                                 time_off: [{id, kind, starts_at, ends_at}]}]}]}

Erros: {"detail": "<mensagem em português>"}.
```

### Funções públicas (`scheduling/public.py`)

```text
capacity_minutes(session, *, unit_id, start: date, end: date, barber_ids=None, by_day=False)
    -> dict[UUID, int]  |  com by_day=True: dict[(UUID, date), int]   # S14: série diária e mapa de calor
    # S14 (ocupação da agenda): minutos de trabalho efetivo (jornada − ausências − fechamentos)
barbers_without_hours(session) -> list[UUID]
    # S16 (primeiros passos): barbeiros ativos sem jornada salva (seguem o horário da unidade, T2)
```

Internamente, `service/working_time.py` (`effective_intervals(session, barber_ids, start, end)`) é
a função que S03 usa para a disponibilidade; ela lê `identity.public.get_unit_calendar` (S01) e
`identity.public.get_barber`/lista de barbeiros.

### Banco de dados

Migration de tenant `t000N_barber_schedule` (expand: tabelas novas):

```text
barber_work_hours     id uuid pk · barber_id → barbers.id ON DELETE CASCADE · weekday smallint
                      check (1..7) · starts_at time · ends_at time · check (starts_at < ends_at)
                      INDEX (barber_id, weekday)
barber_shift_overrides id uuid pk · barber_id → barbers.id ON DELETE CASCADE · on_date date ·
                      starts_at time · ends_at time · reason varchar(120) null ·
                      created_by_user_id uuid null → users.id ON DELETE SET NULL · created_at
                      check (starts_at < ends_at) · INDEX (barber_id, on_date)
barber_time_off       id uuid pk · barber_id → barbers.id ON DELETE CASCADE ·
                      kind enum time_off_kind(day_off, vacation, sick_leave, block) ·
                      all_day bool · starts_at timestamptz · ends_at timestamptz ·
                      reason varchar(200) null ·
                      created_by_user_id uuid null → users.id ON DELETE SET NULL · created_at · updated_at
                      check (ends_at > starts_at)
                      EXCLUDE USING gist (barber_id WITH =, tstzrange(starts_at, ends_at, '[)') WITH &&)
                        name ex_time_off_overlap   (btree_gist — migration de controle da S03)
```

`CASCADE` para o barbeiro: jornada e ausência são configuração, não histórico financeiro; o que
impede apagar um barbeiro com passado são os agendamentos (S03, `RESTRICT`).
Novo contrato no import-linter: `scheduling` entra no contrato de camadas; importa `identity`,
`catalog` e `clients` só pelo `public.py`.

## Permissões

Nenhuma permissão nova.

| Rota | Permissão | owner | manager | receptionist | barber |
|---|---|---|---|---|---|
| `GET` jornada, turnos, ausências, `/working-time` | `appointment:read` | todos | barbeiros das suas unidades | idem | só os próprios |
| `PUT` jornada, turno especial | `team:manage` | sim | suas unidades | — | — |
| ausência `day_off`, `vacation`, `sick_leave` (criar/editar/apagar) | `team:manage` | sim | suas unidades | — | — |
| ausência `block` | `appointment:create` | sim | suas unidades | suas unidades | só a própria (Q-S02-3) |

Fora do alcance → `404` (barbeiro de outra unidade não "existe" para quem não o vê).

## Acceptance Criteria

- [x] Módulo `scheduling` com o layout completo, no `model_registry`, no `main.py` e no contrato de
      camadas; `test_module_layout` e `lint-imports` verdes.
- [x] Migration aplicada em `tenant_template` e em toda barbearia; `alembic check` limpo.
- [x] `effective_intervals` testado: jornada + unidade (interseção), barbeiro sem jornada (T2), turno
      especial, folga, férias atravessando mês, bloqueio no meio do intervalo, exceção `closed` da
      unidade, fuso diferente de São Paulo, troca de horário de verão de outro fuso.
- [x] `tests/test_scheduling/test_schedule.py`, `test_time_off.py`: uma prova por regra, os escopos
      (gerente de uma unidade, recepção, barbeiro próprio e alheio) e o **cruzamento entre duas
      barbearias**.
- [x] Snapshots e `make docs-api` com só o que esta spec descreve.
- [x] `make check` verde; `progress.md`, `issues.md`, DEC nova (módulo `scheduling`, T1–T5, DEC-007
      reavaliada e mantida).

## Dependencies

- S01 (`identity-units-hours`) — `get_unit_calendar`; sem ela, a interseção com a unidade não existe.
- `✅completed_registry-basic-crud.md` — `barbers`.
- S03 preenche `affected_appointments` e é a principal consumidora.
- S14 (`reports`) — **oferecido**: `capacity_minutes` para a ocupação.
- S16 (`imports`) — **oferecido**: `barbers_without_hours` para o checklist de primeiros passos.

## Notes

### Implementação (2026-11-07)

- Tudo implementado e testado: 13 testes em `tests/test_scheduling/` (`test_schedule.py`,
  `test_time_off.py`, `test_working_time.py`), incluindo escopos, cruzamento entre duas barbearias,
  fuso de Nova York na virada do horário de verão e férias atravessando o mês.
- `affected_appointments` volta sempre vazio até a S03 (como previsto).
- O `identity.public` ganhou `BarberInfo`, `get_barber_info`, `list_barber_infos` e
  `get_unit_week` (semana regular da unidade, sem exceções) para o `scheduling` não ler tabelas
  alheias.
- O tipo `ClockTime` ("HH:MM", passo de 5 min) desceu para `app/core/clock.py`, usado pelo horário
  da unidade (S01) e pela jornada.
- `GET /working-time` exige `unit_id` (a resposta tem um fuso só).
- Interseção com a unidade usa o calendário efetivo (exceções incluídas); o `weekly_minutes` e os
  `warnings` da jornada usam a semana regular da unidade.

- **Coluna "horas por semana"** do protótipo de barbeiros volta pela `weekly_minutes`.
- **Escala impressa / exportar** fica para depois.
- **Duração de serviço por barbeiro** (barbeiro mais lento) é catálogo, não jornada — ver Q-S03-3.

### Perguntas em aberto

- ✅ **Q-S02-1 — Barbeiro em mais de uma unidade.** (a) Uma unidade por vez (como hoje): para cobrir
  outra loja, muda-se a unidade do barbeiro. (b) Jornada por dia e unidade (seg/qua no Centro,
  sex/sáb na Zona Sul), com a unidade do cadastro sendo a "principal" para escopo e comissão.
  **Recomendação: (a) agora** — a maioria tem uma unidade; (b) entra depois com uma coluna
  `unit_id` em `barber_work_hours`/`barber_shift_overrides` (expand) e muda o escopo `unit` de
  barbeiros, por isso merece a própria decisão.
  > Resolvido em 2026-11-06: (a) — uma unidade por vez; jornada por dia/unidade fica para depois,
  > sem refazer nada (PD-34).
- ✅ **Q-S02-2 — Turno especial num dia.** (a) Não ter; diferença pontual vira bloqueio. (b) Ter, só
  dentro do horário da unidade (como está acima). (c) Ter, podendo abrir a unidade naquele dia.
  **Recomendação: (b)** — sábado extra e "só à tarde" são comuns; abrir a unidade é decisão do dono
  (horário especial da unidade, S01).
  > Resolvido em 2026-11-06: (b) — turno especial num dia, só dentro do horário da unidade
  > (ROADMAP §7).
- ✅ **Q-S02-3 — O barbeiro bloqueia a própria agenda pelo celular?** (a) Não, só gerência e recepção.
  (b) Sim, só bloqueio pontual de horário. (c) Sim, inclusive folgas. **Recomendação: (b)** — evita
  cliente marcado quando ele sabe que vai sair; folga e férias continuam com a gerência.
  > Resolvido em 2026-11-06: (b) — o barbeiro bloqueia horários pontuais da própria agenda; folgas
  > só a gerência (ROADMAP §7).
