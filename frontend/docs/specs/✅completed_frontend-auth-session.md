# Sessão e login do painel

**Priority:** high
**Status:** completed (spec retroativa, escrita em 2026-11-05 a partir do código)
**Espelho no backend:** `backend/docs/specs/✅completed_identity-core.md`

## Overview

A única parte do painel ligada à API de verdade: entrar, manter a sessão viva, saber quem é o
usuário, em qual barbearia e unidades, com quais permissões, e sair. Tudo sob `/app` exige sessão.

## Decisões de produto já tomadas

| Parâmetro | Valor |
|---|---|
| Rota de login | `/entrar`; destino padrão `/app/agenda` |
| Barbearia | do subdomínio em produção; campo "Barbearia" só em localhost |
| Armazenamento | `localStorage` (DEC-002, ISS-001) |
| Esqueci a senha | não existe; texto orienta a pedir novo convite ao dono |

## Business Rules

- [x] Na subida, um token guardado é só uma pista: `/auth/me` decide se a sessão vale; token
      revogado/expirado cai para anônimo sem "fingir" sessão.
- [x] Enquanto `/auth/me` está em voo, a guarda mostra "Carregando…" (não pisca o login).
- [x] Visitante anônimo em `/app/*` vai para `/entrar` e, após o login, volta ao destino original.
- [x] Usuário já autenticado em `/entrar` é mandado direto ao painel.
- [x] O slug da barbearia é gravado **antes** do login, porque o cliente HTTP o lê para montar o
      `X-Tenant-Slug`.
- [x] Login OK mas `/auth/me` falhando: limpa os tokens (sem sessão pela metade) e mostra o erro.
- [x] Um 401 em chamada autenticada dispara **uma** renovação compartilhada entre chamadas
      simultâneas e refaz a chamada uma vez; renovação falhando limpa a sessão.
- [x] Logout revoga o refresh no servidor em "melhor esforço": falha de rede não prende o usuário.
- [x] Mensagens: rede fora → "Não foi possível falar com o servidor…"; 404 → "Barbearia não
      encontrada…"; 401/403 → a mensagem do backend.
- [x] A sidebar mostra a barbearia, as unidades reais (com "Todas as unidades" para quem vê
      várias), o nome e o cargo (`ROLE_LABELS`).

## Telas e fluxos

| Rota | Tela | Fluxos |
|---|---|---|
| `/entrar` | `features/auth/pages/LoginScreen.tsx` | `pages/login/LoginForm.tsx` |
| `/app/*` | guarda `features/auth/ui/RequireAuth.tsx` | — |

## Data Contract

```text
POST /auth/login    {email, password}  → {access_token, refresh_token, token_type, expires_in}
POST /auth/refresh  {refresh_token}    → idem
POST /auth/logout   {refresh_token}    → 204
GET  /auth/me                          → Me {user, tenant, barber_id, units, all_units, permissions}
```

Tipos em `features/auth/model/auth.types.ts`; cliente em `features/auth/api/auth.api.ts`; transporte
em `shared/api/http.ts`.

## Estado

- Sessão: `AuthProvider` (context da feature `auth`), status `loading | authenticated | anonymous`.
- Unidade selecionada: `UnitSelectionProvider` (context da feature `auth`, montado pelo shell).

## Permissões

`useAuth().can(permission)` devolve o escopo ou `null` — ainda não usado por nenhuma tela (ISS-005).

## Acceptance Criteria

- [x] Login, renovação e logout funcionando contra o backend local (verificado em 2026-11-05).
- [x] `tests/tenant.test.ts` (leitura do slug pelo hostname) e `tests/unit-selection.test.ts`.

## Notes

- Ver ISS-001 (tokens no localStorage), ISS-005 (navegação não respeita permissões) e ISS-006
  (senha colada com espaço).
