<!-- Gerado por backend/tools/api_docs.py a partir do OpenAPI. Não edite à mão: rode `make docs-api`. -->

# Clientes

Clientes da barbearia, compartilhados entre as unidades e identificados pelo telefone em E.164.

Erros seguem o formato `{"detail": "<mensagem em português>"}`; validação de entrada responde `422` com a lista de problemas.

## Rotas

- [`GET /clients`](#get-clients) — Search clients, one page at a time
- [`POST /clients`](#post-clients) — Register a client
- [`GET /clients/{client_id}`](#get-clientsclient_id) — One client
- [`PATCH /clients/{client_id}`](#patch-clientsclient_id) — Update a client
- [`DELETE /clients/{client_id}`](#delete-clientsclient_id) — Delete a client without history

## Endpoints

### GET /clients

**Search clients, one page at a time**

A barber (`own`) sees only the clients they served — none until scheduling exists.

- **Acesso:** permissão `client:read`
- **Parâmetros:**

  | Nome | Onde | Obrigatório | Tipo |
  |---|---|---|---|
  | `q` | query | não | `string` \| `null` |
  | `active` | query | não | `boolean` \| `null` |
  | `limit` | query | não | `integer` |
  | `offset` | query | não | `integer` |
  | `x-tenant-slug` (só em dev) | header | não | `string` \| `null` |

- **Respostas:**
  - `200` Successful Response → [`ClientPage`](#clientpage)
  - `422` Validation Error → [`HTTPValidationError`](#httpvalidationerror)

### POST /clients

**Register a client**

The phone is normalized to E.164 and unique in the shop.

- **Acesso:** permissão `client:write`
- **Parâmetros:**

  | Nome | Onde | Obrigatório | Tipo |
  |---|---|---|---|
  | `x-tenant-slug` (só em dev) | header | não | `string` \| `null` |

- **Corpo:** [`ClientIn`](#clientin)
- **Respostas:**
  - `201` Successful Response → [`ClientOut`](#clientout)
  - `422` Validation Error → [`HTTPValidationError`](#httpvalidationerror)

### GET /clients/{client_id}

**One client**

- **Acesso:** permissão `client:read`
- **Parâmetros:**

  | Nome | Onde | Obrigatório | Tipo |
  |---|---|---|---|
  | `client_id` | path | sim | `string` (uuid) |
  | `x-tenant-slug` (só em dev) | header | não | `string` \| `null` |

- **Respostas:**
  - `200` Successful Response → [`ClientOut`](#clientout)
  - `422` Validation Error → [`HTTPValidationError`](#httpvalidationerror)

### PATCH /clients/{client_id}

**Update a client**

- **Acesso:** permissão `client:write`
- **Parâmetros:**

  | Nome | Onde | Obrigatório | Tipo |
  |---|---|---|---|
  | `client_id` | path | sim | `string` (uuid) |
  | `x-tenant-slug` (só em dev) | header | não | `string` \| `null` |

- **Corpo:** [`ClientUpdate`](#clientupdate)
- **Respostas:**
  - `200` Successful Response → [`ClientOut`](#clientout)
  - `422` Validation Error → [`HTTPValidationError`](#httpvalidationerror)

### DELETE /clients/{client_id}

**Delete a client without history**

409 when the client has history: inactivate instead (`active: false`).

- **Acesso:** permissão `client:write`
- **Parâmetros:**

  | Nome | Onde | Obrigatório | Tipo |
  |---|---|---|---|
  | `client_id` | path | sim | `string` (uuid) |
  | `x-tenant-slug` (só em dev) | header | não | `string` \| `null` |

- **Respostas:**
  - `204` Successful Response
  - `422` Validation Error → [`HTTPValidationError`](#httpvalidationerror)

## Schemas

#### ClientIn

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `name` | `string` | sim | mín. 2; máx. 120 |
| `phone` | `string` | sim | máx. 32; Any common format; stored and returned in E.164 |
| `email` | `string` (email) \| `null` | não |  |
| `birth_date` | `string` (date) \| `null` | não |  |
| `notes` | `string` \| `null` | não |  |
| `active` | `boolean` | não | padrão `True` |

#### ClientOut

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `id` | `string` (uuid) | sim |  |
| `name` | `string` | sim |  |
| `phone` | `string` | sim | E.164 |
| `email` | `string` \| `null` | sim |  |
| `birth_date` | `string` (date) \| `null` | sim |  |
| `notes` | `string` \| `null` | sim |  |
| `active` | `boolean` | sim |  |
| `created_at` | `string` (date-time) | sim |  |
| `updated_at` | `string` (date-time) | sim |  |

#### ClientPage

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `items` | [`ClientOut`](#clientout)[] | sim |  |
| `total` | `integer` | sim | Matches across every page |

#### ClientUpdate

Partial: a field left out does not change. `null` clears the optional fields.

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `name` | `string` \| `null` | não |  |
| `phone` | `string` \| `null` | não |  |
| `email` | `string` (email) \| `null` | não |  |
| `birth_date` | `string` (date) \| `null` | não |  |
| `notes` | `string` \| `null` | não |  |
| `active` | `boolean` \| `null` | não |  |

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
