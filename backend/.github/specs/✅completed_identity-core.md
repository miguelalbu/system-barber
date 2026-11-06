# Núcleo de identidade e tenancy

**Priority:** high
**Status:** completed (spec retroativa, escrita em 2026-11-05 a partir do código e dos testes)
**Espelho no frontend:** `frontend/.github/specs/✅completed_frontend-auth-session.md`

## Overview

Tudo o que existe antes de qualquer funcionalidade de barbearia: quais barbearias existem, como uma
request descobre de qual barbearia é, quem da equipe pode entrar, o que cada cargo pode fazer, e
como um novo membro da equipe ganha login. É a base da qual todo módulo de domínio depende
(`app.modules.identity.public`). Decisões de fundo: DEC-001 a DEC-005.

## Decisões de produto já tomadas

| Parâmetro | Valor |
|---|---|
| Isolamento | banco compartilhado + RLS (DEC-001) |
| Identificação da barbearia | pelo domínio; `X-Tenant-Slug` só em dev (DEC-002) |
| E-mail de login | único **por barbearia** |
| Cargos | `owner`, `manager`, `receptionist`, `barber` |
| Sessão | access JWT 15 min + refresh opaco rotativo 30 dias (DEC-005) |
| Senha da equipe | mínimo 8 caracteres; argon2id |
| Novo membro | só por convite (7 dias); nunca senha criada pelo dono |
| Remoção de membro | desativação, nunca exclusão (histórico de agenda e comissão) |
| Auto-cadastro de barbearia | ligado por padrão (`ALLOW_SELF_SIGNUP`) |

## Business Rules

### Tenancy

- [x] Toda tabela de barbearia tem `tenant_id` e policy RLS; sem tenant fixado, nenhuma linha
      aparece.
- [x] O tenant vem do `Host` (`<slug>.<BASE_DOMAIN>` ou `custom_domain`); em dev, `X-Tenant-Slug`
      tem prioridade.
- [x] Domínio sem barbearia → 404 `Barbearia não encontrada para '<host>'`.
- [x] Barbearia `suspended` ou `canceled` → 403 `Assinatura inativa`.
- [x] Slug: 3–63 caracteres, minúsculas, números e hífen, sem hífen nas pontas; reservados:
      `www, app, api, admin, painel, static, assets`. Slug repetido → 409.
- [x] Domínio próprio é único entre barbearias (409).

### Autenticação

- [x] E-mail inexistente e senha errada têm a mesma resposta (401 `E-mail ou senha inválidos`) —
      não revela quais e-mails existem.
- [x] Usuário desativado → 403 `Acesso desativado`.
- [x] O refresh é rotativo: o token usado é revogado ao gerar o novo; reutilizá-lo → 401.
- [x] Logout revoga o refresh; token desconhecido ou já revogado não é erro (204).
- [x] Token de uma barbearia apresentado em outra → 403 `Token de outra barbearia`.
- [x] Permissões não vão no token; `/auth/me` devolve o mapa do cargo.

### Equipe

- [x] Convite não pode ser para `owner` (transferência de propriedade é outro fluxo).
- [x] E-mail já cadastrado na barbearia → 409.
- [x] Quem administra só algumas unidades só concede acesso a essas unidades, e precisa informar
      ao menos uma (403).
- [x] Unidade inexistente no convite → 400.
- [x] Convite aceito, expirado ou inválido → 400; o token do convite só casa com a barbearia do
      domínio.
- [x] Convite de `barber` (ou com `create_barber`) cria também a coluna de agenda (`barbers`), na
      primeira unidade do convite ou na unidade mais antiga.
- [x] Ninguém desativa a si mesmo (400) nem o dono (403).
- [x] Lista vazia de unidades (`user_units`) significa acesso a todas.

### Admin da plataforma

- [x] Criado só pelo seed; idempotente (rodar de novo não altera a conta sem
      `--update-password`); senha mínima de 12 caracteres; e-mail normalizado.

## Data Contract

```text
POST   /auth/register-shop     público           RegisterShop → 201 RegistrationOut
POST   /auth/login             tenant do domínio LoginIn → TokensOut
POST   /auth/refresh           tenant do domínio RefreshIn → TokensOut
POST   /auth/logout            tenant do domínio RefreshIn → 204
GET    /auth/me                autenticado       → MeOut {user, tenant, barber_id, units, all_units, permissions}

GET    /tenant                 autenticado       → TenantOut
PATCH  /tenant                 tenant:configure  TenantUpdate → TenantOut
GET    /tenant/units           autenticado       → UnitOut[]

GET    /team                   team:read         → MemberOut[]
POST   /team/invites           team:manage       InviteIn → 201 InviteCreatedOut {invite, link}
GET    /team/invites           team:read         → InviteOut[] (pendentes, mais novos primeiro)
POST   /team/invites/accept    público           AcceptInviteIn → 201 MemberOut
DELETE /team/{user_id}         team:manage       → 204

Erros: {"detail": "<mensagem em português>"}; validação Pydantic → 422.
```

O contrato completo e congelado está em `tests/test_contracts/snapshots/openapi.json`.

### Banco de dados

Migration `0001_identity_core`. Control plane (sem RLS): `tenants`, `platform_admins`. Com RLS:
`units`, `users`, `user_units`, `barbers`, `refresh_tokens`, `invites`.

## Permissões

Ver `docs/PERMISSIONS_MAP.md`. Neste módulo: `team:read`, `team:manage`, `tenant:configure`.

## Acceptance Criteria

- [x] Testes de isolamento (`tests/test_identity/test_isolation.py`, 5 testes).
- [x] Testes de autenticação, convite e RBAC (`tests/test_identity/test_auth.py`, 9 testes).
- [x] Testes do seed (`tests/test_identity/test_seed.py`, 7 testes).
- [x] Contrato congelado em `tests/test_contracts/`.

## Dependencies

- PostgreSQL 16 com o role `navalha_app` (`infra/postgres/init/01-app-role.sql`).

## Notes

- Pendências conhecidas em `memory/issues.md`: ISS-003 (reuso de refresh), ISS-004 (convite sem
  e-mail), ISS-005 (login da plataforma), ISS-007 (rate limit), ISS-008 (recuperação de senha).
