<!-- Gerado por backend/tools/api_docs.py a partir do OpenAPI. Não edite à mão: rode `make docs-api`. -->

# Escala e ausências

Jornada semanal dos barbeiros, turnos especiais de um dia, folgas, férias, atestados e bloqueios de horário, e o tempo de trabalho efetivo que a agenda usa.

Erros seguem o formato `{"detail": "<mensagem em português>"}`; validação de entrada responde `422` com a lista de problemas.

## Rotas

- [`GET /barbers/{barber_id}/schedule`](#get-barbersbarber_idschedule) — Weekly schedule
- [`PUT /barbers/{barber_id}/schedule`](#put-barbersbarber_idschedule) — Replace the week
- [`GET /barbers/{barber_id}/shift-overrides`](#get-barbersbarber_idshift-overrides) — Special shifts
- [`PUT /barbers/{barber_id}/shift-overrides/{on_date}`](#put-barbersbarber_idshift-overrideson_date) — Special shift on a day
- [`DELETE /barbers/{barber_id}/shift-overrides/{on_date}`](#delete-barbersbarber_idshift-overrideson_date) — Back to the weekly schedule
- [`GET /schedules`](#get-schedules) — Schedule grid
- [`GET /time-off`](#get-time-off) — Time off and blocks in a period
- [`POST /time-off`](#post-time-off) — Add time off
- [`PATCH /time-off/{time_off_id}`](#patch-time-offtime_off_id) — Edit time off
- [`DELETE /time-off/{time_off_id}`](#delete-time-offtime_off_id) — Remove time off
- [`GET /working-time`](#get-working-time) — Effective working time

## Endpoints

### GET /barbers/{barber_id}/schedule

**Weekly schedule**

`configured: false` → no schedule saved; the unit's hours apply.

- **Acesso:** permissão `appointment:read`
- **Parâmetros:**

  | Nome | Onde | Obrigatório | Tipo |
  |---|---|---|---|
  | `barber_id` | path | sim | `string` (uuid) |
  | `x-tenant-slug` (só em dev) | header | não | `string` \| `null` |

- **Respostas:**
  - `200` Successful Response → [`BarberScheduleOut`](#barberscheduleout)
  - `422` Validation Error → [`HTTPValidationError`](#httpvalidationerror)

### PUT /barbers/{barber_id}/schedule

**Replace the week**

7 days, 0–3 intervals each (lunch is the gap). A whole empty week is refused.

- **Acesso:** permissão `team:manage`
- **Parâmetros:**

  | Nome | Onde | Obrigatório | Tipo |
  |---|---|---|---|
  | `barber_id` | path | sim | `string` (uuid) |
  | `x-tenant-slug` (só em dev) | header | não | `string` \| `null` |

- **Corpo:** [`WeeklyScheduleIn`](#weeklyschedulein)
- **Respostas:**
  - `200` Successful Response → [`BarberScheduleOut`](#barberscheduleout)
  - `422` Validation Error → [`HTTPValidationError`](#httpvalidationerror)

### GET /barbers/{barber_id}/shift-overrides

**Special shifts**

- **Acesso:** permissão `appointment:read`
- **Parâmetros:**

  | Nome | Onde | Obrigatório | Tipo |
  |---|---|---|---|
  | `barber_id` | path | sim | `string` (uuid) |
  | `from` | query | não | `string` (date) \| `null` |
  | `to` | query | não | `string` (date) \| `null` |
  | `x-tenant-slug` (só em dev) | header | não | `string` \| `null` |

- **Respostas:**
  - `200` Successful Response → [`ShiftOverrideOut`](#shiftoverrideout)[]
  - `422` Validation Error → [`HTTPValidationError`](#httpvalidationerror)

### PUT /barbers/{barber_id}/shift-overrides/{on_date}

**Special shift on a day**

Replaces the weekly schedule on that day only; never opens the unit.

- **Acesso:** permissão `team:manage`
- **Parâmetros:**

  | Nome | Onde | Obrigatório | Tipo |
  |---|---|---|---|
  | `barber_id` | path | sim | `string` (uuid) |
  | `on_date` | path | sim | `string` (date) |
  | `x-tenant-slug` (só em dev) | header | não | `string` \| `null` |

- **Corpo:** [`ShiftOverrideIn`](#shiftoverridein)
- **Respostas:**
  - `200` Successful Response → [`ShiftOverrideOut`](#shiftoverrideout)
  - `422` Validation Error → [`HTTPValidationError`](#httpvalidationerror)

### DELETE /barbers/{barber_id}/shift-overrides/{on_date}

**Back to the weekly schedule**

- **Acesso:** permissão `team:manage`
- **Parâmetros:**

  | Nome | Onde | Obrigatório | Tipo |
  |---|---|---|---|
  | `barber_id` | path | sim | `string` (uuid) |
  | `on_date` | path | sim | `string` (date) |
  | `x-tenant-slug` (só em dev) | header | não | `string` \| `null` |

- **Respostas:**
  - `204` Successful Response
  - `422` Validation Error → [`HTTPValidationError`](#httpvalidationerror)

### GET /schedules

**Schedule grid**

One row per active barber in reach.

- **Acesso:** permissão `appointment:read`
- **Parâmetros:**

  | Nome | Onde | Obrigatório | Tipo |
  |---|---|---|---|
  | `unit_id` | query | não | `string` (uuid) \| `null` |
  | `x-tenant-slug` (só em dev) | header | não | `string` \| `null` |

- **Respostas:**
  - `200` Successful Response → [`BarberScheduleOut`](#barberscheduleout)[]
  - `422` Validation Error → [`HTTPValidationError`](#httpvalidationerror)

### GET /time-off

**Time off and blocks in a period**

Up to 366 days.

- **Acesso:** permissão `appointment:read`
- **Parâmetros:**

  | Nome | Onde | Obrigatório | Tipo |
  |---|---|---|---|
  | `from` | query | sim | `string` (date) |
  | `to` | query | sim | `string` (date) |
  | `unit_id` | query | não | `string` (uuid) \| `null` |
  | `barber_id` | query | não | `string` (uuid) \| `null` |
  | `kind` | query | não | [`TimeOffKind`](#timeoffkind) \| `null` |
  | `x-tenant-slug` (só em dev) | header | não | `string` \| `null` |

- **Respostas:**
  - `200` Successful Response → [`TimeOffOut`](#timeoffout)[]
  - `422` Validation Error → [`HTTPValidationError`](#httpvalidationerror)

### POST /time-off

**Add time off**

Permission depends on the kind. Overlap with another one of the barber → 409.

- **Acesso:** sessão (`Authorization: Bearer`)
- **Parâmetros:**

  | Nome | Onde | Obrigatório | Tipo |
  |---|---|---|---|
  | `x-tenant-slug` (só em dev) | header | não | `string` \| `null` |

- **Corpo:** [`TimeOffIn`](#timeoffin)
- **Respostas:**
  - `201` Successful Response → [`TimeOffResult`](#timeoffresult)
  - `422` Validation Error → [`HTTPValidationError`](#httpvalidationerror)

### PATCH /time-off/{time_off_id}

**Edit time off**

- **Acesso:** sessão (`Authorization: Bearer`)
- **Parâmetros:**

  | Nome | Onde | Obrigatório | Tipo |
  |---|---|---|---|
  | `time_off_id` | path | sim | `string` (uuid) |
  | `x-tenant-slug` (só em dev) | header | não | `string` \| `null` |

- **Corpo:** [`TimeOffUpdate`](#timeoffupdate)
- **Respostas:**
  - `200` Successful Response → [`TimeOffResult`](#timeoffresult)
  - `422` Validation Error → [`HTTPValidationError`](#httpvalidationerror)

### DELETE /time-off/{time_off_id}

**Remove time off**

A past block stays (it records why the slot was empty).

- **Acesso:** sessão (`Authorization: Bearer`)
- **Parâmetros:**

  | Nome | Onde | Obrigatório | Tipo |
  |---|---|---|---|
  | `time_off_id` | path | sim | `string` (uuid) |
  | `x-tenant-slug` (só em dev) | header | não | `string` \| `null` |

- **Respostas:**
  - `204` Successful Response
  - `422` Validation Error → [`HTTPValidationError`](#httpvalidationerror)

### GET /working-time

**Effective working time**

Schedule ∩ unit hours − time off, per day, in UTC. Up to 31 days.

- **Acesso:** permissão `appointment:read`
- **Parâmetros:**

  | Nome | Onde | Obrigatório | Tipo |
  |---|---|---|---|
  | `unit_id` | query | sim | `string` (uuid) |
  | `from` | query | sim | `string` (date) |
  | `to` | query | sim | `string` (date) |
  | `x-tenant-slug` (só em dev) | header | não | `string` \| `null` |

- **Respostas:**
  - `200` Successful Response → [`WorkingTimeOut`](#workingtimeout)
  - `422` Validation Error → [`HTTPValidationError`](#httpvalidationerror)

## Schemas

#### AffectedAppointment

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `id` | `string` (uuid) | sim |  |
| `starts_at` | `string` (date-time) | sim |  |
| `client_name` | `string` | sim |  |

#### BarberScheduleOut

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `barber_id` | `string` (uuid) | sim |  |
| `unit_id` | `string` (uuid) | sim |  |
| `configured` | `boolean` | sim | False: no schedule saved, the unit's hours apply (T2) |
| `days` | [`WorkDay`](#workday)[] | sim |  |
| `weekly_minutes` | `integer` | sim | Effective minutes a week (schedule ∩ unit hours) |
| `warnings` | `string`[] | não |  |

#### BarberWorkingTime

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `barber_id` | `string` (uuid) | sim |  |
| `days` | [`WorkingDay`](#workingday)[] | sim |  |

#### HTTPValidationError

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `detail` | [`ValidationError`](#validationerror)[] | não |  |

#### ShiftOverrideIn

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `intervals` | [`WorkInterval`](#workinterval)[] | sim |  |
| `reason` | `string` \| `null` | não |  |

#### ShiftOverrideOut

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `barber_id` | `string` (uuid) | sim |  |
| `date` | `string` (date) | sim |  |
| `intervals` | [`WorkInterval`](#workinterval)[] | sim |  |
| `reason` | `string` \| `null` | sim |  |
| `warnings` | `string`[] | não |  |

#### TimeOffIn

Whole days: `starts_on`/`ends_on`. Block: `starts_at`/`ends_at` (with offset).

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `barber_id` | `string` (uuid) | sim |  |
| `kind` | [`TimeOffKind`](#timeoffkind) | sim |  |
| `starts_on` | `string` (date) \| `null` | não |  |
| `ends_on` | `string` (date) \| `null` | não |  |
| `starts_at` | `string` (date-time) \| `null` | não |  |
| `ends_at` | `string` (date-time) \| `null` | não |  |
| `reason` | `string` \| `null` | não | Staff only; the AI just says the barber is not working |

#### TimeOffKind

Whole days off (`day_off`, `vacation`, `sick_leave`) or a `block` within one day.

Valores: `day_off`, `vacation`, `sick_leave`, `block`

#### TimeOffOut

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `id` | `string` (uuid) | sim |  |
| `barber_id` | `string` (uuid) | sim |  |
| `kind` | [`TimeOffKind`](#timeoffkind) | sim |  |
| `all_day` | `boolean` | sim |  |
| `starts_at` | `string` (date-time) | sim |  |
| `ends_at` | `string` (date-time) | sim |  |
| `starts_on` | `string` (date) | sim | First local day |
| `ends_on` | `string` (date) | sim | Last local day (inclusive) |
| `reason` | `string` \| `null` | sim |  |
| `created_by_user_id` | `string` (uuid) \| `null` | sim |  |
| `created_at` | `string` (date-time) | sim |  |

#### TimeOffRef

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `id` | `string` (uuid) | sim |  |
| `kind` | [`TimeOffKind`](#timeoffkind) | sim |  |
| `starts_at` | `string` (date-time) | sim |  |
| `ends_at` | `string` (date-time) | sim |  |

#### TimeOffResult

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `time_off` | [`TimeOffOut`](#timeoffout) | sim |  |
| `affected_appointments` | [`AffectedAppointment`](#affectedappointment)[] | não | Active appointments in the period (filled by S03) |

#### TimeOffUpdate

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `starts_on` | `string` (date) \| `null` | não |  |
| `ends_on` | `string` (date) \| `null` | não |  |
| `starts_at` | `string` (date-time) \| `null` | não |  |
| `ends_at` | `string` (date-time) \| `null` | não |  |
| `reason` | `string` \| `null` | não | Staff only; the AI just says the barber is not working |

#### UtcInterval

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `starts_at` | `string` (date-time) | sim |  |
| `ends_at` | `string` (date-time) | sim |  |

#### ValidationError

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `loc` | `string` \| `integer`[] | sim |  |
| `msg` | `string` | sim |  |
| `type` | `string` | sim |  |
| `input` | `any` | não |  |
| `ctx` | `object` | não |  |

#### WeeklyScheduleIn

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `days` | [`WorkDay`](#workday)[] | sim |  |

#### WorkDay

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `weekday` | `integer` | sim | ≥ 1.0; ISO: 1 = Monday … 7 = Sunday |
| `intervals` | [`WorkInterval`](#workinterval)[] | não |  |

#### WorkInterval

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `starts_at` | `string` | sim |  |
| `ends_at` | `string` | sim |  |

#### WorkingDay

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `date` | `string` (date) | sim |  |
| `intervals` | [`UtcInterval`](#utcinterval)[] | sim |  |
| `source` | `weekly` \| `unit_default` \| `override` | sim |  |
| `time_off` | [`TimeOffRef`](#timeoffref)[] | sim |  |

#### WorkingTimeOut

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `timezone` | `string` | sim |  |
| `barbers` | [`BarberWorkingTime`](#barberworkingtime)[] | sim |  |
