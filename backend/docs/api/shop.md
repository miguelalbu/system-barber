<!-- Gerado por backend/tools/api_docs.py a partir do OpenAPI. Não edite à mão: rode `make docs-api`. -->

# Barbearia

Dados e configuração da barbearia da sessão e as unidades visíveis ao usuário.

Erros seguem o formato `{"detail": "<mensagem em português>"}`; validação de entrada responde `422` com a lista de problemas.

## Rotas

- [`GET /tenant`](#get-tenant) — Current shop
- [`PATCH /tenant`](#patch-tenant) — Update shop details
- [`GET /tenant/holidays`](#get-tenantholidays) — Suggested national holidays
- [`GET /tenant/settings`](#get-tenantsettings) — Shop settings
- [`PATCH /tenant/settings`](#patch-tenantsettings) — Update shop settings
- [`GET /tenant/unit-exceptions`](#get-tenantunit-exceptions) — Holidays and closures
- [`POST /tenant/unit-exceptions`](#post-tenantunit-exceptions) — Close or open specially on dates
- [`PATCH /tenant/unit-exceptions/{exception_id}`](#patch-tenantunit-exceptionsexception_id) — Edit an exception
- [`DELETE /tenant/unit-exceptions/{exception_id}`](#delete-tenantunit-exceptionsexception_id) — Delete an exception
- [`GET /tenant/units`](#get-tenantunits) — Visible units
- [`POST /tenant/units`](#post-tenantunits) — New unit
- [`GET /tenant/units/{unit_id}`](#get-tenantunitsunit_id) — One unit
- [`PATCH /tenant/units/{unit_id}`](#patch-tenantunitsunit_id) — Update a unit
- [`DELETE /tenant/units/{unit_id}`](#delete-tenantunitsunit_id) — Delete a unit without history
- [`GET /tenant/units/{unit_id}/hours`](#get-tenantunitsunit_idhours) — Weekly hours
- [`PUT /tenant/units/{unit_id}/hours`](#put-tenantunitsunit_idhours) — Replace the week

## Endpoints

### GET /tenant

**Current shop**

- **Acesso:** sessão (`Authorization: Bearer`)
- **Parâmetros:**

  | Nome | Onde | Obrigatório | Tipo |
  |---|---|---|---|
  | `x-tenant-slug` (só em dev) | header | não | `string` \| `null` |

- **Respostas:**
  - `200` Successful Response → [`TenantOut`](#tenantout)
  - `422` Validation Error → [`HTTPValidationError`](#httpvalidationerror)

### PATCH /tenant

**Update shop details**

- **Acesso:** permissão `tenant:configure`
- **Parâmetros:**

  | Nome | Onde | Obrigatório | Tipo |
  |---|---|---|---|
  | `x-tenant-slug` (só em dev) | header | não | `string` \| `null` |

- **Corpo:** [`TenantUpdate`](#tenantupdate)
- **Respostas:**
  - `200` Successful Response → [`TenantOut`](#tenantout)
  - `422` Validation Error → [`HTTPValidationError`](#httpvalidationerror)

### GET /tenant/holidays

**Suggested national holidays**

Nothing closes by itself: the panel creates the closures the user picks.

- **Acesso:** sessão (`Authorization: Bearer`)
- **Parâmetros:**

  | Nome | Onde | Obrigatório | Tipo |
  |---|---|---|---|
  | `year` | query | sim | `integer` |
  | `x-tenant-slug` (só em dev) | header | não | `string` \| `null` |

- **Respostas:**
  - `200` Successful Response → [`HolidayOut`](#holidayout)[]
  - `422` Validation Error → [`HTTPValidationError`](#httpvalidationerror)

### GET /tenant/settings

**Shop settings**

- **Acesso:** sessão (`Authorization: Bearer`)
- **Parâmetros:**

  | Nome | Onde | Obrigatório | Tipo |
  |---|---|---|---|
  | `x-tenant-slug` (só em dev) | header | não | `string` \| `null` |

- **Respostas:**
  - `200` Successful Response → [`ShopSettingsOut`](#shopsettingsout)
  - `422` Validation Error → [`HTTPValidationError`](#httpvalidationerror)

### PATCH /tenant/settings

**Update shop settings**

Partial. Policies apply to the client channels (AI, booking link), not to the staff.

- **Acesso:** permissão `tenant:configure`
- **Parâmetros:**

  | Nome | Onde | Obrigatório | Tipo |
  |---|---|---|---|
  | `x-tenant-slug` (só em dev) | header | não | `string` \| `null` |

- **Corpo:** [`ShopSettingsUpdate`](#shopsettingsupdate)
- **Respostas:**
  - `200` Successful Response → [`ShopSettingsOut`](#shopsettingsout)
  - `422` Validation Error → [`HTTPValidationError`](#httpvalidationerror)

### GET /tenant/unit-exceptions

**Holidays and closures**

Touching the period; default from today to 365 days ahead.

- **Acesso:** sessão (`Authorization: Bearer`)
- **Parâmetros:**

  | Nome | Onde | Obrigatório | Tipo |
  |---|---|---|---|
  | `unit_id` | query | não | `string` (uuid) \| `null` |
  | `from` | query | não | `string` (date) \| `null` |
  | `to` | query | não | `string` (date) \| `null` |
  | `x-tenant-slug` (só em dev) | header | não | `string` \| `null` |

- **Respostas:**
  - `200` Successful Response → [`UnitExceptionOut`](#unitexceptionout)[]
  - `422` Validation Error → [`HTTPValidationError`](#httpvalidationerror)

### POST /tenant/unit-exceptions

**Close or open specially on dates**

One per unit in `unit_ids`, all or nothing. Overlap in a unit → 409.

- **Acesso:** permissão `unit:configure`
- **Parâmetros:**

  | Nome | Onde | Obrigatório | Tipo |
  |---|---|---|---|
  | `x-tenant-slug` (só em dev) | header | não | `string` \| `null` |

- **Corpo:** [`UnitExceptionIn`](#unitexceptionin)
- **Respostas:**
  - `201` Successful Response → [`UnitExceptionOut`](#unitexceptionout)[]
  - `422` Validation Error → [`HTTPValidationError`](#httpvalidationerror)

### PATCH /tenant/unit-exceptions/{exception_id}

**Edit an exception**

- **Acesso:** permissão `unit:configure`
- **Parâmetros:**

  | Nome | Onde | Obrigatório | Tipo |
  |---|---|---|---|
  | `exception_id` | path | sim | `string` (uuid) |
  | `x-tenant-slug` (só em dev) | header | não | `string` \| `null` |

- **Corpo:** [`UnitExceptionUpdate`](#unitexceptionupdate)
- **Respostas:**
  - `200` Successful Response → [`UnitExceptionOut`](#unitexceptionout)
  - `422` Validation Error → [`HTTPValidationError`](#httpvalidationerror)

### DELETE /tenant/unit-exceptions/{exception_id}

**Delete an exception**

- **Acesso:** permissão `unit:configure`
- **Parâmetros:**

  | Nome | Onde | Obrigatório | Tipo |
  |---|---|---|---|
  | `exception_id` | path | sim | `string` (uuid) |
  | `x-tenant-slug` (só em dev) | header | não | `string` \| `null` |

- **Respostas:**
  - `204` Successful Response
  - `422` Validation Error → [`HTTPValidationError`](#httpvalidationerror)

### GET /tenant/units

**Visible units**

- **Acesso:** sessão (`Authorization: Bearer`)
- **Parâmetros:**

  | Nome | Onde | Obrigatório | Tipo |
  |---|---|---|---|
  | `active` | query | não | `boolean` \| `null` |
  | `x-tenant-slug` (só em dev) | header | não | `string` \| `null` |

- **Respostas:**
  - `200` Successful Response → [`UnitOut`](#unitout)[]
  - `422` Validation Error → [`HTTPValidationError`](#httpvalidationerror)

### POST /tenant/units

**New unit**

Born open Monday to Saturday, 09:00–19:00 (editable).

- **Acesso:** permissão `tenant:configure`
- **Parâmetros:**

  | Nome | Onde | Obrigatório | Tipo |
  |---|---|---|---|
  | `x-tenant-slug` (só em dev) | header | não | `string` \| `null` |

- **Corpo:** [`UnitIn`](#unitin)
- **Respostas:**
  - `201` Successful Response → [`UnitOut`](#unitout)
  - `422` Validation Error → [`HTTPValidationError`](#httpvalidationerror)

### GET /tenant/units/{unit_id}

**One unit**

- **Acesso:** sessão (`Authorization: Bearer`)
- **Parâmetros:**

  | Nome | Onde | Obrigatório | Tipo |
  |---|---|---|---|
  | `unit_id` | path | sim | `string` (uuid) |
  | `x-tenant-slug` (só em dev) | header | não | `string` \| `null` |

- **Respostas:**
  - `200` Successful Response → [`UnitOut`](#unitout)
  - `422` Validation Error → [`HTTPValidationError`](#httpvalidationerror)

### PATCH /tenant/units/{unit_id}

**Update a unit**

409 when deactivating the last active unit or one with active barbers.

- **Acesso:** permissão `tenant:configure`
- **Parâmetros:**

  | Nome | Onde | Obrigatório | Tipo |
  |---|---|---|---|
  | `unit_id` | path | sim | `string` (uuid) |
  | `x-tenant-slug` (só em dev) | header | não | `string` \| `null` |

- **Corpo:** [`UnitUpdate`](#unitupdate)
- **Respostas:**
  - `200` Successful Response → [`UnitOut`](#unitout)
  - `422` Validation Error → [`HTTPValidationError`](#httpvalidationerror)

### DELETE /tenant/units/{unit_id}

**Delete a unit without history**

409 with history, users linked to it, or when it is the last active unit.

- **Acesso:** permissão `tenant:configure`
- **Parâmetros:**

  | Nome | Onde | Obrigatório | Tipo |
  |---|---|---|---|
  | `unit_id` | path | sim | `string` (uuid) |
  | `x-tenant-slug` (só em dev) | header | não | `string` \| `null` |

- **Respostas:**
  - `204` Successful Response
  - `422` Validation Error → [`HTTPValidationError`](#httpvalidationerror)

### GET /tenant/units/{unit_id}/hours

**Weekly hours**

- **Acesso:** sessão (`Authorization: Bearer`)
- **Parâmetros:**

  | Nome | Onde | Obrigatório | Tipo |
  |---|---|---|---|
  | `unit_id` | path | sim | `string` (uuid) |
  | `x-tenant-slug` (só em dev) | header | não | `string` \| `null` |

- **Respostas:**
  - `200` Successful Response → [`WeeklyHoursOut`](#weeklyhoursout)
  - `422` Validation Error → [`HTTPValidationError`](#httpvalidationerror)

### PUT /tenant/units/{unit_id}/hours

**Replace the week**

All 7 days, 0–3 intervals each; a day without intervals is closed.

- **Acesso:** permissão `unit:configure`
- **Parâmetros:**

  | Nome | Onde | Obrigatório | Tipo |
  |---|---|---|---|
  | `unit_id` | path | sim | `string` (uuid) |
  | `x-tenant-slug` (só em dev) | header | não | `string` \| `null` |

- **Corpo:** [`WeeklyHoursIn`](#weeklyhoursin)
- **Respostas:**
  - `200` Successful Response → [`WeeklyHoursOut`](#weeklyhoursout)
  - `422` Validation Error → [`HTTPValidationError`](#httpvalidationerror)

## Schemas

#### DayHours

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `weekday` | `integer` | sim | ≥ 1.0; ISO: 1 = Monday … 7 = Sunday |
| `intervals` | [`Interval`](#interval)[] | não |  |

#### HTTPValidationError

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `detail` | [`ValidationError`](#validationerror)[] | não |  |

#### HolidayOut

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `date` | `string` (date) | sim |  |
| `name` | `string` | sim |  |
| `already_closed_unit_ids` | `string` (uuid)[] | sim | Visible units already closed on this date |

#### Interval

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `opens_at` | `string` | sim |  |
| `closes_at` | `string` | sim |  |

#### ShopSettingsOut

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `contact_phone` | `string` \| `null` | sim |  |
| `instagram` | `string` \| `null` | sim |  |
| `about` | `string` \| `null` | sim |  |
| `min_advance_minutes` | `integer` | sim | Client channels only; the staff has no limit |
| `max_advance_days` | `integer` | sim |  |
| `confirmation_deadline_hours` | `integer` | sim |  |
| `client_change_min_hours` | `integer` | sim |  |
| `late_tolerance_minutes` | `integer` | sim |  |
| `max_future_appointments_per_client` | `integer` | sim |  |
| `barber_sees_client_contact` | `boolean` | sim |  |
| `updated_at` | `string` (date-time) | sim |  |

#### ShopSettingsUpdate

Partial. `null` clears the contact fields; for a policy it means no change.

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `contact_phone` | `string` \| `null` | não | Any common format; stored and returned in E.164 |
| `instagram` | `string` \| `null` | não |  |
| `about` | `string` \| `null` | não |  |
| `min_advance_minutes` | `integer` \| `null` | não |  |
| `max_advance_days` | `integer` \| `null` | não |  |
| `confirmation_deadline_hours` | `integer` \| `null` | não |  |
| `client_change_min_hours` | `integer` \| `null` | não |  |
| `late_tolerance_minutes` | `integer` \| `null` | não |  |
| `max_future_appointments_per_client` | `integer` \| `null` | não |  |
| `barber_sees_client_contact` | `boolean` \| `null` | não |  |

#### TenantOut

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `id` | `string` (uuid) | sim |  |
| `slug` | `string` | sim |  |
| `name` | `string` | sim |  |
| `custom_domain` | `string` \| `null` | sim |  |
| `plan` | `string` | sim |  |
| `status` | [`TenantStatus`](#tenantstatus) | sim |  |
| `created_at` | `string` (date-time) | sim |  |

#### TenantStatus

Operational lifecycle of a shop (DEC-013). Billing lives in the Core; only
`active` is served.

Valores: `provisioning`, `active`, `failed`, `suspended`, `archived`

#### TenantUpdate

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `name` | `string` \| `null` | não |  |
| `custom_domain` | `string` \| `null` | não |  |

#### UnitExceptionIn

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `unit_ids` | `string` (uuid)[] | sim | One exception per unit |
| `starts_on` | `string` (date) | sim |  |
| `ends_on` | `string` (date) | sim |  |
| `kind` | [`UnitExceptionKind`](#unitexceptionkind) | sim |  |
| `opens_at` | `string` \| `null` | não | Only for special_hours |
| `closes_at` | `string` \| `null` | não | Only for special_hours |
| `reason` | `string` \| `null` | não | Shown to clients by the AI, e.g. 'feriado de Finados' |

#### UnitExceptionKind

What a calendar exception does to a unit's day (spec S01).

Valores: `closed`, `special_hours`

#### UnitExceptionOut

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `id` | `string` (uuid) | sim |  |
| `unit_id` | `string` (uuid) | sim |  |
| `starts_on` | `string` (date) | sim |  |
| `ends_on` | `string` (date) | sim |  |
| `kind` | [`UnitExceptionKind`](#unitexceptionkind) | sim |  |
| `opens_at` | `string` \| `null` | sim |  |
| `closes_at` | `string` \| `null` | sim |  |
| `reason` | `string` \| `null` | sim |  |
| `created_at` | `string` (date-time) | sim |  |
| `updated_at` | `string` (date-time) | sim |  |

#### UnitExceptionUpdate

Partial; the merged result is checked with the same rules as a new one.

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `starts_on` | `string` (date) \| `null` | não |  |
| `ends_on` | `string` (date) \| `null` | não |  |
| `kind` | [`UnitExceptionKind`](#unitexceptionkind) \| `null` | não |  |
| `opens_at` | `string` \| `null` | não |  |
| `closes_at` | `string` \| `null` | não |  |
| `reason` | `string` \| `null` | não | Shown to clients by the AI, e.g. 'feriado de Finados' |

#### UnitIn

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `name` | `string` | sim | mín. 2; máx. 120 |
| `timezone` | `string` | não | mín. 1; máx. 64; padrão `America/Sao_Paulo`; IANA timezone, e.g. America/Sao_Paulo |
| `address` | `string` \| `null` | não |  |
| `phone` | `string` \| `null` | não | Any common format; stored and returned in E.164 |
| `online_booking` | `boolean` | não | padrão `True` |
| `active` | `boolean` | não | padrão `True` |

#### UnitOut

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `id` | `string` (uuid) | sim |  |
| `name` | `string` | sim |  |
| `timezone` | `string` | sim |  |
| `address` | `string` \| `null` | sim |  |
| `phone` | `string` \| `null` | sim | E.164 |
| `online_booking` | `boolean` | sim | Offered to the AI and the public booking link |
| `active` | `boolean` | sim |  |
| `created_at` | `string` (date-time) | sim |  |
| `updated_at` | `string` (date-time) | sim |  |

#### UnitUpdate

Partial. `null` clears address and phone; for the other fields it means no change.

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `name` | `string` \| `null` | não |  |
| `timezone` | `string` \| `null` | não |  |
| `address` | `string` \| `null` | não |  |
| `phone` | `string` \| `null` | não | Any common format; stored and returned in E.164 |
| `online_booking` | `boolean` \| `null` | não |  |
| `active` | `boolean` \| `null` | não |  |

#### ValidationError

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `loc` | `string` \| `integer`[] | sim |  |
| `msg` | `string` | sim |  |
| `type` | `string` | sim |  |
| `input` | `any` | não |  |
| `ctx` | `object` | não |  |

#### WeeklyHoursIn

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `days` | [`DayHours`](#dayhours)[] | sim |  |

#### WeeklyHoursOut

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `unit_id` | `string` (uuid) | sim |  |
| `days` | [`DayHours`](#dayhours)[] | sim |  |
| `warning` | `string` \| `null` | não |  |
