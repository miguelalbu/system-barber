<!-- Gerado por backend/tools/api_docs.py a partir do OpenAPI. Não edite à mão: rode `make docs-api`. -->

# Barbearia

Dados e configuração da barbearia da sessão e as unidades visíveis ao usuário.

Erros seguem o formato `{"detail": "<mensagem em português>"}`; validação de entrada responde `422` com a lista de problemas.

## Rotas

- [`GET /tenant`](#get-tenant) — Current shop
- [`PATCH /tenant`](#patch-tenant) — Update shop details
- [`GET /tenant/units`](#get-tenantunits) — Visible units

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

### GET /tenant/units

**Visible units**

- **Acesso:** sessão (`Authorization: Bearer`)
- **Parâmetros:**

  | Nome | Onde | Obrigatório | Tipo |
  |---|---|---|---|
  | `x-tenant-slug` (só em dev) | header | não | `string` \| `null` |

- **Respostas:**
  - `200` Successful Response → [`UnitOut`](#unitout)[]
  - `422` Validation Error → [`HTTPValidationError`](#httpvalidationerror)

## Schemas

#### HTTPValidationError

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `detail` | [`ValidationError`](#validationerror)[] | não |  |

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

#### UnitOut

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `id` | `string` (uuid) | sim |  |
| `name` | `string` | sim |  |
| `timezone` | `string` | sim |  |
| `active` | `boolean` | sim |  |

#### ValidationError

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `loc` | `string` \| `integer`[] | sim |  |
| `msg` | `string` | sim |  |
| `type` | `string` | sim |  |
| `input` | `any` | não |  |
| `ctx` | `object` | não |  |
