# Endurecer a autenticação

**Priority:** high
**Status:** draft
**Espelho no frontend:** `frontend/docs/specs/⚪draft_frontend-auth-hardening.md`

## Overview

A autenticação da equipe funciona (login, refresh rotativo, logout, convites — `✅completed_identity-core`),
mas tem cinco buracos registrados: **sem recuperação de senha** (ISS-008), **sem rate limit** no login
e nos tokens de convite (ISS-007, impacto alto), **reuso de refresh** que só falha em vez de derrubar a
sessão roubada (ISS-003), **tokens em `localStorage`** (frontend ISS-001) e nenhuma forma de **trocar
a senha** ou **encerrar sessões** (celular perdido, ex-funcionário que ainda tem a aba aberta). Esta
spec fecha os cinco no `identity`, com auditoria dos eventos de autenticação.

## Decisões de produto já tomadas

| Parâmetro | Valor |
|---|---|
| DEC-005 | Access JWT 15 min + refresh opaco rotativo 30 dias, guardado só como SHA-256. Continua; ganha família e detecção de reuso. |
| DEC-002/DEC-011 | Tenant pelo host; e-mail único por barbearia; token recusado em outro host. O cookie é **host-only**, então cada subdomínio/domínio próprio tem o seu. |
| Identity-core | E-mail inexistente e senha errada têm a mesma resposta e o mesmo tempo. Vale também para "esqueci a senha". |
| Recuperação de senha | E-mail quando configurado **e** link gerado pelo dono/gerente na tela Equipe (Q-S17-1). |
| "Manter conectado" | Caixa no login: marcada = sessão de 30 dias; desmarcada = cookie de sessão do navegador, máx. 12 h (Q-S17-2). |
| Fora | 2FA agora; app autenticador opcional numa spec própria (Q-S17-3), login da conta de plataforma (ISS-005), verificação de e-mail no convite (ISS-004), login social. |

### Propostas desta spec

| # | Parâmetro | Proposta |
|---|---|---|
| H1 | Onde fica o refresh | Cookie `HttpOnly; Secure; SameSite=Strict; Path=<AUTH_COOKIE_PATH>`, sem `Domain` (host-only). Access token só no corpo, guardado em memória pelo frontend. |
| H2 | Mesma origem | Em produção a API é servida **no mesmo host do painel** sob `/api` (proxy reverso, junto do ISS-009). Sem isso o cookie vira de terceiros num domínio próprio. `AUTH_COOKIE_PATH` padrão `/api/auth`. |
| H3 | CSRF | `SameSite=Strict` + header obrigatório `X-Navalha-Client: web` em `/auth/refresh` e `/auth/logout` (header customizado força preflight) + checagem de `Origin` contra as origens permitidas do CORS. |
| H4 | Rate limit | Redis (já provisionado), janela deslizante, chaves particionadas pelo schema da barbearia. Sem bloqueio de conta (seria DoS fácil): só espera. |
| H5 | Revogação imediata | O JWT ganha `sid` (a família/sessão). Sessão encerrada entra num conjunto no Redis com TTL de 15 min, consultado a cada request — o access token de uma sessão derrubada para de valer na hora, não em 15 min. |

## Business Rules

### Sessões (família de refresh) e detecção de reuso — ISS-003

- [ ] Cada login cria uma **sessão** (`family_id`); toda rotação gera o próximo token da mesma família
      e grava `replaced_by_id` no anterior.
- [ ] Refresh com token **já rotacionado**: se a rotação aconteceu há mais de 30 s → **reuso**:
      revoga a família inteira (`revoked_reason = reuse_detected`), grava `auth_events`, `401`
      "Sessão encerrada por segurança. Entre de novo.". Dentro de 30 s (duas abas renovando juntas)
      → `409` "Sessão renovada em outra aba" **sem** revogar (o frontend tenta de novo com o cookie
      novo).
- [ ] Sessão expira por inatividade (refresh não usado em 30 dias) e tem idade máxima de 90 dias
      (novo login obrigatório).
- [ ] **"Manter conectado"** (Q-S17-2): `LoginIn.remember_me` (padrão `false`). Marcado → regra
      acima, cookie com `Max-Age` de 30 dias. Desmarcado → cookie **sem** `Max-Age` (some ao fechar
      o navegador) e a sessão tem idade máxima de **12 h** desde o login (`family_expires_at`),
      checada em toda rotação: passou → `401` "Sessão expirada. Entre de novo.". A rotação mantém o
      modo da família.
- [ ] Desativar um usuário (`DELETE /team/{id}`, existente) passa a revogar todas as sessões dele.

### Cookie e corpo — frontend ISS-001

- [ ] `POST /auth/login` e `/auth/refresh` gravam o cookie `navalha_rt` (em `ENVIRONMENT=dev`:
      `navalha_rt_<slug>`, sem `Secure`, porque em localhost várias barbearias dividem o host) e
      devolvem `{access_token, token_type, expires_in, session_id}`.
- [ ] **Transição (expand/contract)**: por uma versão, o corpo ainda traz `refresh_token` e
      `/auth/refresh` ainda aceita `{refresh_token}` no corpo quando não há cookie — para o build
      anterior do frontend. Depois, uma mudança de contrato remove os dois (ISS a abrir).
- [ ] `/auth/logout` revoga a sessão do cookie e apaga o cookie (`Max-Age=0`); sem cookie, `204`.
- [ ] Sem `X-Navalha-Client` ou com `Origin` não permitida → `403` "Requisição recusada".

### Recuperação de senha — ISS-008

- [ ] `POST /auth/password/forgot {email}` responde **sempre `202`**, no mesmo tempo, exista ou não o
      e-mail. Se existir e o usuário estiver ativo: cria `password_resets` (token opaco, SHA-256,
      validade 60 min, uso único), invalida os pedidos anteriores e envia o e-mail com
      `https://<host da barbearia>/redefinir-senha/<token>`.
- [ ] `POST /auth/password/reset/lookup {token}` descreve o pedido sem gastá-lo (`{email,
      expires_at}`) para a tela recusar link morto antes de pedir a senha; inválido → `400`
      "Link inválido, expirado ou já utilizado" (mesma mensagem para os três casos).
- [ ] `POST /auth/password/reset {token, new_password}` — reivindicação atômica (`UPDATE … WHERE
      used_at IS NULL AND expires_at > now()`), troca o hash, **revoga todas as sessões** do usuário
      e grava o evento. Não faz login automático (a pessoa entra com a senha nova).
- [ ] **Link gerado pela equipe** (funciona sem e-mail configurado): `POST /team/{user_id}/password-reset`
      cria o mesmo pedido e devolve o link para o dono/gerente repassar (como o convite, ISS-004).
      Ninguém gera link para si mesmo nem para o dono (dono usa "esqueci a senha" ou o suporte).
- [ ] E-mail: `app/core/email.py` com `EMAIL_BACKEND = console | smtp` (console em dev: o link vai
      para o log). Sem backend de e-mail configurado, `forgot` registra o pedido e não envia — a tela
      de login orienta a pedir o link ao dono (Q-S17-1).

### Troca de senha e sessões ativas

- [ ] `POST /auth/password/change {current_password, new_password}` — senha atual errada → `400`
      "Senha atual incorreta" (conta no rate limit); troca o hash e revoga **as outras** sessões (a
      atual continua).
- [ ] Política de senha (convite, reset, troca): 8–128 caracteres, diferente do e-mail, fora de uma
      lista embutida das 1.000 senhas mais comuns (`422` "Escolha uma senha menos comum").
- [ ] `GET /auth/sessions` lista as sessões ativas do próprio usuário: criada em, último uso,
      dispositivo (rótulo derivado do User-Agent: "Chrome no Windows", "Safari no iPhone"), IP
      mascarado (`189.40.x.x`), `current`.
- [ ] `DELETE /auth/sessions/{id}` encerra uma; `POST /auth/sessions/revoke-others` encerra todas
      menos a atual. Sessão de outro usuário → `404`.
- [ ] `DELETE /team/{user_id}/sessions` (`team:manage`, no escopo) encerra todas as sessões de um
      membro sem desativá-lo (celular do barbeiro perdido).

### Rate limit — ISS-007

| Rota | Chave | Limite |
|---|---|---|
| `/auth/login` | `schema + e-mail (hash)` — só falhas | 5 em 15 min |
| `/auth/login` | `IP` (global, todas as barbearias) | 30 em 15 min |
| `/auth/password/forgot` | `schema + e-mail` / `IP` | 3 por hora / 10 por hora |
| `/auth/password/reset*`, `/team/invites/accept`, `/team/invites/lookup` | `IP` | 20 em 15 min |
| `/auth/password/change` | `usuário` — só falhas | 5 em 15 min |
| `/auth/refresh` | `IP` | 120 em 15 min |

- [ ] Estourou → `429` "Muitas tentativas. Tente de novo em N minutos." com `Retry-After`. Login com
      sucesso zera o contador de falhas do e-mail.
- [ ] Chave Redis com prefixo e TTL: `identity:rl:<regra>:<schema>:<sujeito>` (rules.md: estado de
      processo particionado pelo tenant). O IP vem do socket, ou de `X-Forwarded-For` só quando o
      salto anterior está em `TRUSTED_PROXIES`.
- [ ] Redis fora do ar: o limite **deixa passar** e registra erro no log (falhar fechado tiraria o
      login do ar junto com o Redis); a resposta continua genérica e com tempo constante.
- [ ] O limitador do `/core/*` (ISS-012) migra para o mesmo `RedisRateLimiter`.

### Auditoria

- [ ] `auth_events` grava: `login_succeeded`, `login_failed`, `login_throttled`, `refresh_reuse_detected`,
      `session_revoked`, `sessions_revoked_all`, `password_changed`, `password_reset_requested`,
      `password_reset_completed`, `reset_link_issued` — com usuário (quando conhecido), IP, User-Agent
      e detalhes **sem segredo nem senha**. Retenção de 180 dias (tarefa do worker, S00).
- [ ] Senha trocada ou redefinida → e-mail de aviso ao usuário (se houver backend de e-mail).

## Data Contract

```text
POST   /auth/login         LoginIn                → 200 TokenOut + Set-Cookie | 401 | 403 | 429
POST   /auth/refresh       (cookie; corpo opcional na transição) + X-Navalha-Client
                                                   → 200 TokenOut + Set-Cookie | 401 | 403 | 409 | 429
POST   /auth/logout        (cookie) + X-Navalha-Client → 204 + cookie apagado
POST   /auth/password/forgot        {email}       → 202 | 429
POST   /auth/password/reset/lookup  {token}       → 200 {email, expires_at} | 400 | 429
POST   /auth/password/reset         {token, new_password} → 204 | 400 | 422 | 429
POST   /auth/password/change        {current_password, new_password} → 204 | 400 | 422 | 429
GET    /auth/sessions                              → 200 SessionOut[]
DELETE /auth/sessions/{id}                         → 204 | 404
POST   /auth/sessions/revoke-others                → 204
POST   /team/{user_id}/password-reset   team:manage → 201 {link, expires_at} | 403 | 404
DELETE /team/{user_id}/sessions         team:manage → 204 | 403 | 404

LoginIn     {email, password, remember_me? = false}     (ganha remember_me)
TokenOut    {access_token, token_type: "bearer", expires_in, session_id,
             refresh_token (só durante a transição; deprecated no OpenAPI)}
SessionOut  {id, created_at, last_used_at, device, ip_masked, current}
JWT         + sid (family_id)
Erros: {"detail"}; 429 com Retry-After.
```

### Banco de dados

Migration de tenant (próxima `tNNNN_auth_hardening`, expand):

```text
refresh_tokens  + family_id uuid not null (backfill: id do próprio token) · + replaced_by_id uuid null ·
                + revoked_reason varchar(20) null (rotated, logout, reuse_detected, user_revoked,
                  password_changed, deactivated, expired) · + last_used_at timestamptz null ·
                + user_agent varchar(255) null · + ip varchar(64) null · + family_created_at timestamptz ·
                + remember_me bool not null default true (backfill: sessões atuais seguem 30 dias) ·
                + family_expires_at timestamptz (created + 90 dias, ou + 12 h sem remember_me)
                INDEX (family_id)
password_resets id uuid pk · user_id → users.id ON DELETE CASCADE · token_hash char(64) UNIQUE ·
                expires_at · used_at null · created_by uuid null (link gerado pela equipe) · created_at
                INDEX (user_id)
auth_events     id uuid pk · user_id uuid null (sem FK: e-mail desconhecido também é evento) ·
                event varchar(30) · ip varchar(64) null · user_agent varchar(255) null ·
                details jsonb · created_at · INDEX (created_at) · INDEX (user_id, created_at)
users           + password_changed_at timestamptz null
```

Variáveis de ambiente novas: `AUTH_COOKIE_PATH`, `EMAIL_BACKEND`, `SMTP_HOST`, `SMTP_PORT`,
`SMTP_USER`, `SMTP_PASSWORD`, `EMAIL_FROM`, `TRUSTED_PROXIES`. Sem dependência nova (`smtplib` e
`redis` já disponíveis).

## Permissões

| Rota | Permissão | owner | manager | receptionist | barber |
|---|---|---|---|---|---|
| `/auth/password/*`, `/auth/login`, `/auth/refresh`, `/auth/logout` | pública (com rate limit) | — | — | — | — |
| `/auth/sessions*`, `/auth/password/change` | autenticado (o próprio usuário) | sim | sim | sim | sim |
| `POST /team/{id}/password-reset`, `DELETE /team/{id}/sessions` | `team:manage` (no escopo; nunca o dono) | all | unit | — | — |

Nenhuma permissão nova.

## Acceptance Criteria

- [ ] `tests/test_identity/test_auth_hardening.py`: reuso fora da janela derruba a família e o access
      token dela (via `sid`) na mesma hora; reuso dentro da janela → `409` sem revogar; cookie com os
      atributos certos (dev e produção); refresh sem header/Origin → `403`; transição com corpo.
- [ ] Recuperação: `202` igual para e-mail existente e inexistente (tempo comparável); token de uso
      único concorrente (um sucesso); reset revoga todas as sessões; link gerado pela equipe com as
      restrições (si mesmo, dono, fora do escopo).
- [ ] Rate limit: cada linha da tabela, `Retry-After`, sucesso zera, Redis fora → passa e loga,
      chaves de duas barbearias não se misturam.
- [ ] Sessões: lista só as próprias, encerra uma, encerra as outras; desativar membro revoga.
- [ ] Testes em `tests/test_identity/` cobrindo as regras acima; cruzamento entre duas barbearias.
- [ ] Snapshots de contrato revisados (`UPDATE_CONTRACT_SNAPSHOTS=1` só se a mudança for intencional)
- [ ] ISS-003, ISS-007, ISS-008 fechadas; ISS-012 fechada pela migração do limitador.

## Dependencies

- Redis (já no compose). **S00** para a limpeza de `auth_events` e `password_resets` vencidos (até
  lá, limpeza preguiçosa no login).
- Infra (ISS-009): proxy reverso servindo painel e API no mesmo host — pré-requisito do cookie em
  produção.
- Espelho no frontend: troca do armazenamento de tokens (precisa ir junto na mesma versão da
  transição).

## Notes

- O `sid` no Redis é o único estado consultado por request além do registry; custo de um `SISMEMBER`.
  Redis fora do ar → aceita o token (mesma lógica do rate limit) e loga.
- O e-mail transacional criado aqui é o que resolve o ISS-004 (convite por e-mail) numa spec seguinte.

### Perguntas em aberto

- ✅ **Q-S17-1 — Como a equipe recupera a senha?**
  (a) só e-mail automático (exige provedor de e-mail em produção); (b) só link gerado pelo
  dono/gerente na tela Equipe; (c) os dois — e-mail quando configurado, link da equipe sempre.
  **Recomendação: (c)** — barbeiro raramente lê e-mail; o dono manda o link no WhatsApp (como já faz
  com o convite), e o e-mail cobre o próprio dono.
  > Resolvido em 2026-11-06: (c) — e-mail quando configurado e link gerado pelo dono/gerente
  > (ROADMAP §7).
- ✅ **Q-S17-2 — Quanto tempo a sessão dura em computador compartilhado (recepção)?**
  (a) 30 dias para todos, como hoje; (b) caixa "Manter conectado" no login: marcada = 30 dias,
  desmarcada = cookie de sessão do navegador (some ao fechar) com máximo de 12 h; (c) por cargo
  (recepção 12 h, demais 30 dias).
  **Recomendação: (b)** — padrão conhecido, resolve o PC da recepção sem atrapalhar o celular do
  barbeiro.
  > Resolvido em 2026-11-06: (b) — caixa "Manter conectado": 30 dias, ou até fechar o navegador com
  > máximo de 12 h (ROADMAP §7).
- ✅ **Q-S17-3 — Verificação em duas etapas para o dono?**
  (a) não agora; (b) TOTP (app autenticador) opcional para quem quiser; (c) obrigatório para o dono.
  **Recomendação: (a) agora, (b) numa spec própria** — com cookie, rate limit e reuso detectado, o
  risco principal cai; 2FA obrigatório gera chamado de suporte em barbearia pequena.
  > Resolvido em 2026-11-06: (a) agora — sem 2FA; app autenticador opcional numa spec própria
  > (ROADMAP §7).
