<!-- Gerado por backend/tools/api_docs.py a partir do OpenAPI. Não edite à mão: rode `make docs-api`. -->

# Equipe e convites

Membros, convites e o aceite de convite — inclusive o primeiro acesso do dono de uma barbearia recém-provisionada.

Erros seguem o formato `{"detail": "<mensagem em português>"}`; validação de entrada responde `422` com a lista de problemas.

## Rotas

- [`GET /team`](#get-team) — Shop members
- [`GET /team/invites`](#get-teaminvites) — Pending invites
- [`POST /team/invites`](#post-teaminvites) — Invite someone to the team
- [`POST /team/invites/accept`](#post-teaminvitesaccept) — Accept an invite and create the login
- [`POST /team/invites/lookup`](#post-teaminviteslookup) — Describe a valid invite without using it
- [`DELETE /team/{user_id}`](#delete-teamuser_id) — Deactivate a member's access

## Endpoints

### GET /team

**Shop members**

- **Acesso:** permissão `team:read`
- **Parâmetros:**

  | Nome | Onde | Obrigatório | Tipo |
  |---|---|---|---|
  | `x-tenant-slug` (só em dev) | header | não | `string` \| `null` |

- **Respostas:**
  - `200` Successful Response → [`MemberOut`](#memberout)[]
  - `422` Validation Error → [`HTTPValidationError`](#httpvalidationerror)

### GET /team/invites

**Pending invites**

- **Acesso:** permissão `team:read`
- **Parâmetros:**

  | Nome | Onde | Obrigatório | Tipo |
  |---|---|---|---|
  | `x-tenant-slug` (só em dev) | header | não | `string` \| `null` |

- **Respostas:**
  - `200` Successful Response → [`InviteOut`](#inviteout)[]
  - `422` Validation Error → [`HTTPValidationError`](#httpvalidationerror)

### POST /team/invites

**Invite someone to the team**

- **Acesso:** permissão `team:manage`
- **Parâmetros:**

  | Nome | Onde | Obrigatório | Tipo |
  |---|---|---|---|
  | `x-tenant-slug` (só em dev) | header | não | `string` \| `null` |

- **Corpo:** [`InviteIn`](#invitein)
- **Respostas:**
  - `201` Successful Response → [`InviteCreatedOut`](#invitecreatedout)
  - `422` Validation Error → [`HTTPValidationError`](#httpvalidationerror)

### POST /team/invites/accept

**Accept an invite and create the login**

Public route — the caller has no login yet. The tenant comes from the
domain, and the invite token has to belong to it. Also the owner's first
access after provisioning.

- **Acesso:** pública
- **Parâmetros:**

  | Nome | Onde | Obrigatório | Tipo |
  |---|---|---|---|
  | `x-tenant-slug` (só em dev) | header | não | `string` \| `null` |

- **Corpo:** [`AcceptInviteIn`](#acceptinvitein)
- **Respostas:**
  - `201` Successful Response → [`MemberOut`](#memberout)
  - `422` Validation Error → [`HTTPValidationError`](#httpvalidationerror)

### POST /team/invites/lookup

**Describe a valid invite without using it**

Public route, for the acceptance page to check the link before asking for
a password. The token goes in the body, never in a URL that ends up in logs.

- **Acesso:** pública
- **Parâmetros:**

  | Nome | Onde | Obrigatório | Tipo |
  |---|---|---|---|
  | `x-tenant-slug` (só em dev) | header | não | `string` \| `null` |

- **Corpo:** [`InviteLookupIn`](#invitelookupin)
- **Respostas:**
  - `200` Successful Response → [`InviteLookupOut`](#invitelookupout)
  - `422` Validation Error → [`HTTPValidationError`](#httpvalidationerror)

### DELETE /team/{user_id}

**Deactivate a member's access**

Deactivate rather than delete: the appointment and commission history has to
keep pointing at a real person.

- **Acesso:** permissão `team:manage`
- **Parâmetros:**

  | Nome | Onde | Obrigatório | Tipo |
  |---|---|---|---|
  | `user_id` | path | sim | `string` (uuid) |
  | `x-tenant-slug` (só em dev) | header | não | `string` \| `null` |

- **Respostas:**
  - `204` Successful Response
  - `422` Validation Error → [`HTTPValidationError`](#httpvalidationerror)

## Schemas

#### AcceptInviteIn

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `token` | `string` | sim |  |
| `password` | `string` | sim | mín. 8; máx. 128 |

#### HTTPValidationError

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `detail` | [`ValidationError`](#validationerror)[] | não |  |

#### InviteCreatedOut

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `invite` | [`InviteOut`](#inviteout) | sim |  |
| `link` | `string` | sim |  |

#### InviteIn

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `name` | `string` | sim | mín. 2; máx. 120 |
| `email` | `string` (email) | sim |  |
| `role` | [`Role`](#role) | sim |  |
| `unit_ids` | `string` (uuid)[] | não | Empty means access to every unit |
| `barber_id` | `string` (uuid) \| `null` | não | Registered barber this login is linked to on acceptance. Required for the `barber` role; an invite never creates a barber. |

#### InviteLookupIn

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `token` | `string` | sim |  |

#### InviteLookupOut

What the acceptance page shows before asking for a password.

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `name` | `string` | sim |  |
| `email` | `string` (email) | sim |  |
| `role` | [`Role`](#role) | sim |  |
| `expires_at` | `string` (date-time) | sim |  |

#### InviteOut

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `id` | `string` (uuid) | sim |  |
| `name` | `string` | sim |  |
| `email` | `string` (email) | sim |  |
| `role` | [`Role`](#role) | sim |  |
| `barber_id` | `string` (uuid) \| `null` | sim |  |
| `expires_at` | `string` (date-time) | sim |  |
| `accepted_at` | `string` (date-time) \| `null` | sim |  |
| `created_at` | `string` (date-time) | sim |  |

#### MemberOut

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `id` | `string` (uuid) | sim |  |
| `name` | `string` | sim |  |
| `email` | `string` (email) | sim |  |
| `role` | [`Role`](#role) | sim |  |
| `active` | `boolean` | sim |  |
| `last_login_at` | `string` (date-time) \| `null` | sim |  |
| `barber_id` | `string` (uuid) \| `null` | não |  |

#### Role

Valores: `owner`, `manager`, `receptionist`, `barber`

#### ValidationError

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `loc` | `string` \| `integer`[] | sim |  |
| `msg` | `string` | sim |  |
| `type` | `string` | sim |  |
| `input` | `any` | não |  |
| `ctx` | `object` | não |  |
