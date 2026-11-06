<!-- Gerado por backend/tools/api_docs.py a partir do OpenAPI. Não edite à mão: rode `make docs-api`. -->

# Catálogo

Serviços da barbearia (um preço para todas as unidades, em centavos) e os serviços que cada barbeiro faz.

Erros seguem o formato `{"detail": "<mensagem em português>"}`; validação de entrada responde `422` com a lista de problemas.

## Rotas

- [`PUT /barbers/{barber_id}/services`](#put-barbersbarber_idservices) — Set the services a barber performs
- [`GET /services`](#get-services) — Services of the shop
- [`POST /services`](#post-services) — Create a service
- [`GET /services/{service_id}`](#get-servicesservice_id) — One service
- [`PATCH /services/{service_id}`](#patch-servicesservice_id) — Update a service
- [`DELETE /services/{service_id}`](#delete-servicesservice_id) — Delete a service without history

## Endpoints

### PUT /barbers/{barber_id}/services

**Set the services a barber performs**

Replaces the whole set (empty list = none). Returns the services now enabled.

- **Acesso:** permissão `team:manage`
- **Parâmetros:**

  | Nome | Onde | Obrigatório | Tipo |
  |---|---|---|---|
  | `barber_id` | path | sim | `string` (uuid) |
  | `x-tenant-slug` (só em dev) | header | não | `string` \| `null` |

- **Corpo:** [`BarberServicesIn`](#barberservicesin)
- **Respostas:**
  - `200` Successful Response → [`ServiceOut`](#serviceout)[]
  - `422` Validation Error → [`HTTPValidationError`](#httpvalidationerror)

### GET /services

**Services of the shop**

- **Acesso:** permissão `catalog:read`
- **Parâmetros:**

  | Nome | Onde | Obrigatório | Tipo |
  |---|---|---|---|
  | `active` | query | não | `boolean` \| `null` |
  | `x-tenant-slug` (só em dev) | header | não | `string` \| `null` |

- **Respostas:**
  - `200` Successful Response → [`ServiceOut`](#serviceout)[]
  - `422` Validation Error → [`HTTPValidationError`](#httpvalidationerror)

### POST /services

**Create a service**

Requires access to every unit: a service is priced for all of them.

- **Acesso:** permissão `catalog:write`
- **Parâmetros:**

  | Nome | Onde | Obrigatório | Tipo |
  |---|---|---|---|
  | `x-tenant-slug` (só em dev) | header | não | `string` \| `null` |

- **Corpo:** [`ServiceIn`](#servicein)
- **Respostas:**
  - `201` Successful Response → [`ServiceOut`](#serviceout)
  - `422` Validation Error → [`HTTPValidationError`](#httpvalidationerror)

### GET /services/{service_id}

**One service**

- **Acesso:** permissão `catalog:read`
- **Parâmetros:**

  | Nome | Onde | Obrigatório | Tipo |
  |---|---|---|---|
  | `service_id` | path | sim | `string` (uuid) |
  | `x-tenant-slug` (só em dev) | header | não | `string` \| `null` |

- **Respostas:**
  - `200` Successful Response → [`ServiceOut`](#serviceout)
  - `422` Validation Error → [`HTTPValidationError`](#httpvalidationerror)

### PATCH /services/{service_id}

**Update a service**

- **Acesso:** permissão `catalog:write`
- **Parâmetros:**

  | Nome | Onde | Obrigatório | Tipo |
  |---|---|---|---|
  | `service_id` | path | sim | `string` (uuid) |
  | `x-tenant-slug` (só em dev) | header | não | `string` \| `null` |

- **Corpo:** [`ServiceUpdate`](#serviceupdate)
- **Respostas:**
  - `200` Successful Response → [`ServiceOut`](#serviceout)
  - `422` Validation Error → [`HTTPValidationError`](#httpvalidationerror)

### DELETE /services/{service_id}

**Delete a service without history**

409 when it has history: inactivate instead (`active: false`).

- **Acesso:** permissão `catalog:write`
- **Parâmetros:**

  | Nome | Onde | Obrigatório | Tipo |
  |---|---|---|---|
  | `service_id` | path | sim | `string` (uuid) |
  | `x-tenant-slug` (só em dev) | header | não | `string` \| `null` |

- **Respostas:**
  - `204` Successful Response
  - `422` Validation Error → [`HTTPValidationError`](#httpvalidationerror)

## Schemas

#### BarberServicesIn

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `service_ids` | `string` (uuid)[] | sim | The full set of services the barber performs; replaces the current one |

#### HTTPValidationError

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `detail` | [`ValidationError`](#validationerror)[] | não |  |

#### ServiceIn

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `name` | `string` | sim | mín. 2; máx. 80 |
| `description` | `string` \| `null` | não |  |
| `duration_minutes` | `integer` | sim | ≥ 5.0; Minutes, in steps of 5 |
| `price_cents` | `integer` | sim | ≥ 0.0; Price in cents (BRL) |
| `active` | `boolean` | não | padrão `True` |

#### ServiceOut

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `id` | `string` (uuid) | sim |  |
| `name` | `string` | sim |  |
| `description` | `string` \| `null` | sim |  |
| `duration_minutes` | `integer` | sim |  |
| `price_cents` | `integer` | sim |  |
| `active` | `boolean` | sim |  |
| `barber_ids` | `string` (uuid)[] | sim | Barbers who perform this service |
| `created_at` | `string` (date-time) | sim |  |
| `updated_at` | `string` (date-time) | sim |  |

#### ServiceUpdate

Partial: a field left out does not change. `description: null` clears it.

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `name` | `string` \| `null` | não |  |
| `description` | `string` \| `null` | não |  |
| `duration_minutes` | `integer` \| `null` | não |  |
| `price_cents` | `integer` \| `null` | não |  |
| `active` | `boolean` \| `null` | não |  |

#### ValidationError

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `loc` | `string` \| `integer`[] | sim |  |
| `msg` | `string` | sim |  |
| `type` | `string` | sim |  |
| `input` | `any` | não |  |
| `ctx` | `object` | não |  |
