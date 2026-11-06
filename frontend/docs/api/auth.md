<!-- Gerado por frontend/scripts/api-docs.ts a partir das chamadas em src/features/*/api e do contrato do backend. Não edite à mão: rode `npm run docs:api`. -->

# Feature `auth`

Chamadas à API feitas em `src/features/auth/api/auth.api.ts`. Campos, erros e regras de acesso de cada rota estão na referência do backend (links).

| Função | Rota | Corpo | Resposta | Resumo |
|---|---|---|---|---|
| `login()` | [`POST /auth/login`](../../../backend/docs/api/auth.md#post-authlogin) | `LoginIn` | `200` `TokensOut` | Staff login |
| `fetchMe()` | [`GET /auth/me`](../../../backend/docs/api/auth.md#get-authme) | — | `200` `MeOut` | Current user, shop and permissions |
| `logout()` | [`POST /auth/logout`](../../../backend/docs/api/auth.md#post-authlogout) | `RefreshIn` | `204` — | Revoke the refresh token |
| `lookupInvite()` | [`POST /team/invites/lookup`](../../../backend/docs/api/team.md#post-teaminviteslookup) | `InviteLookupIn` | `200` `InviteLookupOut` | Describe a valid invite without using it |
| `acceptInvite()` | [`POST /team/invites/accept`](../../../backend/docs/api/team.md#post-teaminvitesaccept) | `AcceptInviteIn` | `201` `MemberOut` | Accept an invite and create the login |
