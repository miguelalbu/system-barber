<!-- Gerado por backend/tools/api_docs.py a partir do OpenAPI. Não edite à mão: rode `make docs-api`. -->

# Control plane (`/core/*`)

Criação e ciclo de vida das barbearias, chamado pelo Core da plataforma. Autenticação própria pelo header `X-Core-Key`; fora do `/docs` público — o contrato também é servido em `GET /core/openapi.json`, atrás da chave.

Erros seguem o formato `{"detail": "<mensagem em português>"}`; validação de entrada responde `422` com a lista de problemas.

## Rotas

- [`GET /core/openapi.json`](#get-coreopenapijson) — OpenAPI of the control plane
- [`GET /core/tenants`](#get-coretenants) — Every shop
- [`POST /core/tenants`](#post-coretenants) — Provision a shop (async: 202 + job)
- [`GET /core/tenants/{tenant_id}`](#get-coretenantstenant_id) — A shop, its job, and the first-access link once
- [`DELETE /core/tenants/{tenant_id}`](#delete-coretenantstenant_id) — Delete a suspended shop's data (scope tenant:destroy)
- [`POST /core/tenants/{tenant_id}/invite`](#post-coretenantstenant_idinvite) — Reissue the owner's first-access link
- [`POST /core/tenants/{tenant_id}/resume`](#post-coretenantstenant_idresume) — Resume
- [`POST /core/tenants/{tenant_id}/retry`](#post-coretenantstenant_idretry) — Resume a provisioning job that did not finish
- [`POST /core/tenants/{tenant_id}/suspend`](#post-coretenantstenant_idsuspend) — Suspend

## Endpoints

### GET /core/openapi.json

**OpenAPI of the control plane**

- **Acesso:** `X-Core-Key` com escopo `tenant:read`
- **Parâmetros:**

  | Nome | Onde | Obrigatório | Tipo |
  |---|---|---|---|
  | `x-core-key` | header | não | `string` \| `null` |

- **Respostas:**
  - `200` Successful Response
  - `422` Validation Error → [`HTTPValidationError`](#httpvalidationerror)

### GET /core/tenants

**Every shop**

- **Acesso:** `X-Core-Key` com escopo `tenant:read`
- **Parâmetros:**

  | Nome | Onde | Obrigatório | Tipo |
  |---|---|---|---|
  | `x-core-key` | header | não | `string` \| `null` |

- **Respostas:**
  - `200` Successful Response → [`CoreTenantOut`](#coretenantout)[]
  - `422` Validation Error → [`HTTPValidationError`](#httpvalidationerror)

### POST /core/tenants

**Provision a shop (async: 202 + job)**

Validates, records and answers **202** with the job; the work runs after
the response. The same slug (or `Idempotency-Key`) again answers **200**
with the existing job — never a second schema.

- **Acesso:** `X-Core-Key` com escopo `tenant:provision`
- **Parâmetros:**

  | Nome | Onde | Obrigatório | Tipo |
  |---|---|---|---|
  | `idempotency-key` | header | não | `string` \| `null` |
  | `x-core-key` | header | não | `string` \| `null` |

- **Corpo:** [`ProvisionIn`](#provisionin)
- **Respostas:**
  - `202` Successful Response → [`ProvisionAccepted`](#provisionaccepted)
  - `422` Validation Error → [`HTTPValidationError`](#httpvalidationerror)

### GET /core/tenants/{tenant_id}

**A shop, its job, and the first-access link once**

- **Acesso:** `X-Core-Key` com escopo `tenant:read`
- **Parâmetros:**

  | Nome | Onde | Obrigatório | Tipo |
  |---|---|---|---|
  | `tenant_id` | path | sim | `string` (uuid) |
  | `x-core-key` | header | não | `string` \| `null` |

- **Respostas:**
  - `200` Successful Response → [`CoreTenantDetail`](#coretenantdetail)
  - `422` Validation Error → [`HTTPValidationError`](#httpvalidationerror)

### DELETE /core/tenants/{tenant_id}

**Delete a suspended shop's data (scope tenant:destroy)**

- **Acesso:** `X-Core-Key` com escopo `tenant:destroy`
- **Parâmetros:**

  | Nome | Onde | Obrigatório | Tipo |
  |---|---|---|---|
  | `tenant_id` | path | sim | `string` (uuid) |
  | `x-core-key` | header | não | `string` \| `null` |

- **Corpo:** [`DestroyIn`](#destroyin)
- **Respostas:**
  - `204` Successful Response
  - `422` Validation Error → [`HTTPValidationError`](#httpvalidationerror)

### POST /core/tenants/{tenant_id}/invite

**Reissue the owner's first-access link**

- **Acesso:** `X-Core-Key` com escopo `tenant:provision`
- **Parâmetros:**

  | Nome | Onde | Obrigatório | Tipo |
  |---|---|---|---|
  | `tenant_id` | path | sim | `string` (uuid) |
  | `x-core-key` | header | não | `string` \| `null` |

- **Respostas:**
  - `200` Successful Response → [`InviteLinkOut`](#invitelinkout)
  - `422` Validation Error → [`HTTPValidationError`](#httpvalidationerror)

### POST /core/tenants/{tenant_id}/resume

**Resume**

- **Acesso:** `X-Core-Key` com escopo `tenant:provision`
- **Parâmetros:**

  | Nome | Onde | Obrigatório | Tipo |
  |---|---|---|---|
  | `tenant_id` | path | sim | `string` (uuid) |
  | `x-core-key` | header | não | `string` \| `null` |

- **Respostas:**
  - `200` Successful Response → [`CoreTenantOut`](#coretenantout)
  - `422` Validation Error → [`HTTPValidationError`](#httpvalidationerror)

### POST /core/tenants/{tenant_id}/retry

**Resume a provisioning job that did not finish**

- **Acesso:** `X-Core-Key` com escopo `tenant:provision`
- **Parâmetros:**

  | Nome | Onde | Obrigatório | Tipo |
  |---|---|---|---|
  | `tenant_id` | path | sim | `string` (uuid) |
  | `x-core-key` | header | não | `string` \| `null` |

- **Respostas:**
  - `202` Successful Response → [`ProvisionAccepted`](#provisionaccepted)
  - `422` Validation Error → [`HTTPValidationError`](#httpvalidationerror)

### POST /core/tenants/{tenant_id}/suspend

**Suspend**

- **Acesso:** `X-Core-Key` com escopo `tenant:provision`
- **Parâmetros:**

  | Nome | Onde | Obrigatório | Tipo |
  |---|---|---|---|
  | `tenant_id` | path | sim | `string` (uuid) |
  | `x-core-key` | header | não | `string` \| `null` |

- **Respostas:**
  - `200` Successful Response → [`CoreTenantOut`](#coretenantout)
  - `422` Validation Error → [`HTTPValidationError`](#httpvalidationerror)

## Schemas

#### CoreTenantDetail

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `id` | `string` (uuid) | sim |  |
| `slug` | `string` | sim |  |
| `schema_name` | `string` | sim |  |
| `name` | `string` | sim |  |
| `custom_domain` | `string` \| `null` | sim |  |
| `plan` | `string` | sim |  |
| `status` | [`TenantStatus`](#tenantstatus) | sim |  |
| `schema_version` | `string` \| `null` | sim |  |
| `external_tenant_id` | `string` \| `null` | sim |  |
| `created_at` | `string` (date-time) | sim |  |
| `job` | [`JobOut`](#jobout) \| `null` | não |  |
| `invite_link` | `string` \| `null` | não | Owner's first-access link. Delivered once, then erased. |

#### CoreTenantOut

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `id` | `string` (uuid) | sim |  |
| `slug` | `string` | sim |  |
| `schema_name` | `string` | sim |  |
| `name` | `string` | sim |  |
| `custom_domain` | `string` \| `null` | sim |  |
| `plan` | `string` | sim |  |
| `status` | [`TenantStatus`](#tenantstatus) | sim |  |
| `schema_version` | `string` \| `null` | sim |  |
| `external_tenant_id` | `string` \| `null` | sim |  |
| `created_at` | `string` (date-time) | sim |  |

#### DestroyIn

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `confirm` | `string` | sim | The shop's slug, typed again |
| `exported` | `boolean` | sim | A pg_dump of the schema was taken |

#### HTTPValidationError

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `detail` | [`ValidationError`](#validationerror)[] | não |  |

#### InviteLinkOut

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `invite_link` | `string` | sim |  |

#### JobOut

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `id` | `string` (uuid) | sim |  |
| `status` | [`JobStatus`](#jobstatus) | sim |  |
| `step` | [`JobStep`](#jobstep) | sim |  |
| `log` | `string` | sim |  |
| `error` | `string` \| `null` | sim |  |
| `created_at` | `string` (date-time) | sim |  |
| `finished_at` | `string` (date-time) \| `null` | sim |  |

#### JobStatus

Valores: `pending`, `running`, `succeeded`, `failed`

#### JobStep

Provisioning steps, in order. Each one is idempotent, so a retry resumes.

Valores: `schema`, `migrations`, `grants`, `bootstrap`, `activate`, `done`

#### OwnerIn

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `name` | `string` | sim | mín. 2; máx. 120 |
| `email` | `string` (email) | sim |  |

#### ProvisionAccepted

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `tenant_id` | `string` (uuid) | sim |  |
| `status` | [`TenantStatus`](#tenantstatus) | sim |  |
| `job_id` | `string` (uuid) | sim |  |

#### ProvisionIn

Unknown fields are dropped — on purpose for `password`: the owner's password
never travels in this contract (doc §6) and never reaches the audit log.

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `slug` | `string` | sim | Subdomain and schema of the shop: &lt;slug&gt;.&lt;base_domain&gt; |
| `name` | `string` | sim | mín. 2; máx. 120 |
| `owner` | [`OwnerIn`](#ownerin) | sim |  |
| `unit_name` | `string` \| `null` | não |  |
| `plan` | `string` | não | máx. 40; padrão `basic` |
| `custom_domain` | `string` \| `null` | não |  |
| `external_tenant_id` | `string` \| `null` | não | The Core's id for this customer |

#### TenantStatus

Operational lifecycle of a shop (DEC-013). Billing lives in the Core; only
`active` is served.

Valores: `provisioning`, `active`, `failed`, `suspended`, `archived`

#### ValidationError

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `loc` | `string` \| `integer`[] | sim |  |
| `msg` | `string` | sim |  |
| `type` | `string` | sim |  |
| `input` | `any` | não |  |
| `ctx` | `object` | não |  |
