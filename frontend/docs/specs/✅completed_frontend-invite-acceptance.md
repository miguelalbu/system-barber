# Primeiro acesso e aceite de convite

**Priority:** high
**Status:** completed
**Espelho no backend:** `backend/docs/specs/✅completed_identity-schema-per-tenant.md`

## Overview

Com o schema por barbearia, toda barbearia nasce pelo control plane do backend e o dono recebe um
**convite de primeiro acesso** — a senha dele nunca passa pelo contrato de provisionamento. O link
(`https://<slug>.<domínio>/convite/<token>`) precisava de uma tela: ela é a porta de entrada de toda
barbearia nova e também a de qualquer convite de equipe.

## Decisões de produto já tomadas

| Parâmetro | Valor |
|---|---|
| Rota | `/convite/:token` (pública) |
| Ordem | valida o link **antes** de pedir a senha (doc §6, fechamento) |
| Depois do aceite | entra direto no painel (`/app/agenda`) |
| Barbearia em localhost | a tela pede o slug primeiro, como o login |

## Business Rules

- [x] Ao abrir, a tela consulta `POST /team/invites/lookup` (não gasta o convite) e mostra nome,
      cargo e e-mail do convidado.
- [x] Link inválido, expirado ou já usado (400) → mensagem única pedindo um novo link; nenhum campo
      de senha aparece.
- [x] Em localhost sem slug guardado, a tela pede a barbearia antes; barbearia não encontrada (404)
      volta para esse passo.
- [x] Senha: mínimo 8, máximo 128, sem espaço nas pontas (evita o "senha certa, 401" da ISS-006),
      digitada duas vezes. O backend valida de novo.
- [x] Aceite (`POST /team/invites/accept`) e, em seguida, login com o mesmo e-mail e senha.
- [x] Erro do backend (ex.: 503 barbearia em manutenção) aparece com a mensagem dele.

## Telas e fluxos

| Rota | Tela | Fluxos |
|---|---|---|
| `/convite/:token` | `features/auth/pages/AcceptInviteScreen.tsx` | `pages/accept-invite/AcceptInviteForm.tsx` (barbearia → verificando → senha / link morto) |

## Data Contract

```text
POST /team/invites/lookup  {token}            → {name, email, role, expires_at} | 400
POST /team/invites/accept  {token, password}  → 201 MemberOut | 400 | 409
```

Tipos em `features/auth/model/auth.types.ts` (`InviteLookup`, `TenantStatus`); cliente em
`features/auth/api/auth.api.ts`; regras puras em `features/auth/model/invite.rules.ts`.

## Estado

Local ao formulário (passo, convite descrito, senhas, erro). Sessão pelo `AuthProvider` existente.

## Permissões

Nenhuma — rota pública; o token é a credencial.

## Acceptance Criteria

- [x] `tests/invite-rules.test.ts` (5 testes).
- [x] `make check-frontend` verde (lint, typecheck, 15 testes, build).
- [x] Endpoints exercitados contra o backend local com a barbearia `demo` (lookup 200, aceite 201,
      login 200 pelo proxy do Vite).
- [ ] Tela conferida num navegador — **não feito nesta sessão** (sem automação de browser aqui).

## Notes

- `AuthTenant.status` passou a `provisioning | active | failed | suspended | archived` (o backend
  só serve `active`, então o painel só vê esse valor na prática).
- O host do link em dev (`demo.navalha.local`) não resolve: use `localhost:5173/convite/<token>`
  (backend ISS-015).
