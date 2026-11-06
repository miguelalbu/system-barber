<!-- Gerado por backend/tools/api_docs.py a partir do OpenAPI. Não edite à mão: rode `make docs-api`. -->

# Autenticação

Login da equipe, renovação rotativa do token, logout e o perfil da sessão. A barbearia vem do domínio de acesso (em dev, do header `X-Tenant-Slug`).

Erros seguem o formato `{"detail": "<mensagem em português>"}`; validação de entrada responde `422` com a lista de problemas.

## Rotas

- [`POST /auth/login`](#post-authlogin) — Staff login
- [`POST /auth/logout`](#post-authlogout) — Revoke the refresh token
- [`GET /auth/me`](#get-authme) — Current user, shop and permissions
- [`POST /auth/refresh`](#post-authrefresh) — Renew the access token

## Endpoints

### POST /auth/login

**Staff login**

- **Acesso:** pública
- **Parâmetros:**

  | Nome | Onde | Obrigatório | Tipo |
  |---|---|---|---|
  | `x-tenant-slug` (só em dev) | header | não | `string` \| `null` |

- **Corpo:** [`LoginIn`](#loginin)
- **Respostas:**
  - `200` Successful Response → [`TokensOut`](#tokensout)
  - `422` Validation Error → [`HTTPValidationError`](#httpvalidationerror)

### POST /auth/logout

**Revoke the refresh token**

- **Acesso:** pública
- **Parâmetros:**

  | Nome | Onde | Obrigatório | Tipo |
  |---|---|---|---|
  | `x-tenant-slug` (só em dev) | header | não | `string` \| `null` |

- **Corpo:** [`RefreshIn`](#refreshin)
- **Respostas:**
  - `204` Successful Response
  - `422` Validation Error → [`HTTPValidationError`](#httpvalidationerror)

### GET /auth/me

**Current user, shop and permissions**

- **Acesso:** sessão (`Authorization: Bearer`)
- **Parâmetros:**

  | Nome | Onde | Obrigatório | Tipo |
  |---|---|---|---|
  | `x-tenant-slug` (só em dev) | header | não | `string` \| `null` |

- **Respostas:**
  - `200` Successful Response → [`MeOut`](#meout)
  - `422` Validation Error → [`HTTPValidationError`](#httpvalidationerror)

### POST /auth/refresh

**Renew the access token**

- **Acesso:** pública
- **Parâmetros:**

  | Nome | Onde | Obrigatório | Tipo |
  |---|---|---|---|
  | `x-tenant-slug` (só em dev) | header | não | `string` \| `null` |

- **Corpo:** [`RefreshIn`](#refreshin)
- **Respostas:**
  - `200` Successful Response → [`TokensOut`](#tokensout)
  - `422` Validation Error → [`HTTPValidationError`](#httpvalidationerror)

## Schemas

#### HTTPValidationError

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `detail` | [`ValidationError`](#validationerror)[] | não |  |

#### LoginIn

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `email` | `string` (email) | sim |  |
| `password` | `string` | sim |  |

#### MeOut

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `user` | [`UserOut`](#userout) | sim |  |
| `tenant` | [`TenantOut`](#tenantout) | sim |  |
| `barber_id` | `string` (uuid) \| `null` | sim |  |
| `units` | [`UnitOut`](#unitout)[] | sim |  |
| `all_units` | `boolean` | sim |  |
| `permissions` | objeto de `string` | sim |  |

#### RefreshIn

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `refresh_token` | `string` | sim |  |

#### Role

Valores: `owner`, `manager`, `receptionist`, `barber`

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

#### TokensOut

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `access_token` | `string` | sim |  |
| `refresh_token` | `string` | sim |  |
| `token_type` | `string` | não | padrão `bearer` |
| `expires_in` | `integer` | sim | Access token lifetime, in seconds |

#### UnitOut

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `id` | `string` (uuid) | sim |  |
| `name` | `string` | sim |  |
| `timezone` | `string` | sim |  |
| `active` | `boolean` | sim |  |

#### UserOut

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `id` | `string` (uuid) | sim |  |
| `name` | `string` | sim |  |
| `email` | `string` (email) | sim |  |
| `role` | [`Role`](#role) | sim |  |
| `active` | `boolean` | sim |  |
| `last_login_at` | `string` (date-time) \| `null` | sim |  |

#### ValidationError

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `loc` | `string` \| `integer`[] | sim |  |
| `msg` | `string` | sim |  |
| `type` | `string` | sim |  |
| `input` | `any` | não |  |
| `ctx` | `object` | não |  |
