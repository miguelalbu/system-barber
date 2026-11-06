<!-- Gerado por backend/tools/api_docs.py a partir do OpenAPI. Não edite à mão: rode `make docs-api`. -->

# Barbeiros

Cadastro dos profissionais que atendem (coluna da agenda, comissão). Separado do cadastro de usuários com acesso ao painel: um não cria o outro, e o vínculo é opcional.

Erros seguem o formato `{"detail": "<mensagem em português>"}`; validação de entrada responde `422` com a lista de problemas.

## Rotas

- [`GET /barbers`](#get-barbers) — Barbers in the caller's units
- [`POST /barbers`](#post-barbers) — Register a barber
- [`GET /barbers/{barber_id}`](#get-barbersbarber_id) — One barber
- [`PATCH /barbers/{barber_id}`](#patch-barbersbarber_id) — Update a barber
- [`DELETE /barbers/{barber_id}`](#delete-barbersbarber_id) — Delete a barber without history

## Endpoints

### GET /barbers

**Barbers in the caller's units**

- **Acesso:** permissão `team:read`
- **Parâmetros:**

  | Nome | Onde | Obrigatório | Tipo |
  |---|---|---|---|
  | `unit_id` | query | não | `string` (uuid) \| `null` |
  | `active` | query | não | `boolean` \| `null` |
  | `x-tenant-slug` (só em dev) | header | não | `string` \| `null` |

- **Respostas:**
  - `200` Successful Response → [`BarberOut`](#barberout)[]
  - `422` Validation Error → [`HTTPValidationError`](#httpvalidationerror)

### POST /barbers

**Register a barber**

Does not create a login. `user_id` links an existing one (an owner who also cuts).

- **Acesso:** permissão `team:manage`
- **Parâmetros:**

  | Nome | Onde | Obrigatório | Tipo |
  |---|---|---|---|
  | `x-tenant-slug` (só em dev) | header | não | `string` \| `null` |

- **Corpo:** [`BarberIn`](#barberin)
- **Respostas:**
  - `201` Successful Response → [`BarberOut`](#barberout)
  - `422` Validation Error → [`HTTPValidationError`](#httpvalidationerror)

### GET /barbers/{barber_id}

**One barber**

- **Acesso:** permissão `team:read`
- **Parâmetros:**

  | Nome | Onde | Obrigatório | Tipo |
  |---|---|---|---|
  | `barber_id` | path | sim | `string` (uuid) |
  | `x-tenant-slug` (só em dev) | header | não | `string` \| `null` |

- **Respostas:**
  - `200` Successful Response → [`BarberOut`](#barberout)
  - `422` Validation Error → [`HTTPValidationError`](#httpvalidationerror)

### PATCH /barbers/{barber_id}

**Update a barber**

Partial update. `user_id: null` unlinks the login — refused for a `barber` login.

- **Acesso:** permissão `team:manage`
- **Parâmetros:**

  | Nome | Onde | Obrigatório | Tipo |
  |---|---|---|---|
  | `barber_id` | path | sim | `string` (uuid) |
  | `x-tenant-slug` (só em dev) | header | não | `string` \| `null` |

- **Corpo:** [`BarberUpdate`](#barberupdate)
- **Respostas:**
  - `200` Successful Response → [`BarberOut`](#barberout)
  - `422` Validation Error → [`HTTPValidationError`](#httpvalidationerror)

### DELETE /barbers/{barber_id}

**Delete a barber without history**

409 when the barber has a login or history: inactivate instead (`active: false`).

- **Acesso:** permissão `team:manage`
- **Parâmetros:**

  | Nome | Onde | Obrigatório | Tipo |
  |---|---|---|---|
  | `barber_id` | path | sim | `string` (uuid) |
  | `x-tenant-slug` (só em dev) | header | não | `string` \| `null` |

- **Respostas:**
  - `204` Successful Response
  - `422` Validation Error → [`HTTPValidationError`](#httpvalidationerror)

## Schemas

#### BarberIn

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `name` | `string` | sim | mín. 2; máx. 120 |
| `unit_id` | `string` (uuid) | sim |  |
| `initials` | `string` \| `null` | não | Derived from the name if omitted |
| `default_commission` | `number` | não | ≥ 0.0; padrão `40` |
| `active` | `boolean` | não | padrão `True` |
| `user_id` | `string` (uuid) \| `null` | não | Existing login to link (e.g. an owner who also cuts) |

#### BarberOut

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `id` | `string` (uuid) | sim |  |
| `name` | `string` | sim |  |
| `initials` | `string` | sim |  |
| `unit_id` | `string` (uuid) | sim |  |
| `default_commission` | `number` | sim |  |
| `active` | `boolean` | sim |  |
| `user_id` | `string` (uuid) \| `null` | sim |  |
| `email` | `string` (email) \| `null` | sim | Email of the linked login, if any |
| `created_at` | `string` (date-time) | sim |  |
| `updated_at` | `string` (date-time) | sim |  |

#### BarberUpdate

Partial: a field left out does not change. `user_id: null` unlinks the login.

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `name` | `string` \| `null` | não |  |
| `unit_id` | `string` (uuid) \| `null` | não |  |
| `initials` | `string` \| `null` | não |  |
| `default_commission` | `number` \| `null` | não |  |
| `active` | `boolean` \| `null` | não |  |
| `user_id` | `string` (uuid) \| `null` | não |  |

#### HTTPValidationError

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `detail` | [`ValidationError`](#validationerror)[] | não |  |

#### ValidationError

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `loc` | `string` \| `integer`[] | sim |  |
| `msg` | `string` | sim |  |
| `type` | `string` | sim |  |
| `input` | `any` | não |  |
| `ctx` | `object` | não |  |
