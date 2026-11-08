# Sessão segura, recuperação de senha e sessões ativas

**Priority:** high
**Status:** draft
**Espelho no backend:** `backend/docs/specs/⚪draft_identity-auth-hardening.md`

## Overview

Fecha o ISS-001 do frontend: o refresh token sai do `localStorage` e passa a viver num **cookie
httpOnly** que o JavaScript não lê; o access token fica **só em memória**. Junto vêm as telas que o
backend passa a oferecer: **esqueci a senha** e **redefinir senha**, **trocar senha**, **sessões
ativas** (sair de uma ou de todas as outras) e, na Equipe, gerar link de redefinição e encerrar as
sessões de um membro. Muda também a mensagem do login sobre senha esquecida (hoje: "peça um novo
convite ao dono").

## Decisões de produto já tomadas

| Parâmetro | Valor |
|---|---|
| Sessão | Refresh em cookie httpOnly (backend H1); access em memória; renovação silenciosa na subida. Substitui a DEC-002. |
| Mesma origem | O painel chama a API em `/api` no mesmo host (já é assim em dev pelo proxy do Vite; em produção pelo proxy reverso — backend H2). |
| Recuperação | E-mail quando configurado + link gerado pela equipe (Q-S17-1). |
| "Manter conectado" | Caixa no login: marcada = 30 dias; desmarcada = até fechar o navegador, máx. 12 h (Q-S17-2). |
| Fora | 2FA agora; app autenticador opcional em spec própria (Q-S17-3). |

## Business Rules

### Tokens

- [ ] `shared/session/tokens.ts` guarda só o access token, numa variável de módulo; nada de
      `localStorage`. Na primeira subida depois do deploy, as chaves antigas
      (`navalha.access_token`, `navalha.refresh_token`) são **apagadas**.
- [ ] Subida do app: `POST /auth/refresh` (cookie) → access token → `/auth/me`. Sem cookie válido →
      anônimo, sem piscar o login (o `AuthProvider` continua em `loading` até a resposta).
- [ ] `shared/api/http.ts` manda `credentials: 'same-origin'` e o header `X-Navalha-Client: web` em
      `/auth/refresh` e `/auth/logout`; a renovação continua única e compartilhada (DEC-002).
- [ ] `409` "Sessão renovada em outra aba" no refresh → espera 300 ms e tenta uma vez de novo (o
      cookie já é o novo). Outras abas não precisam trocar mensagem: o cookie é o mesmo.
- [ ] `401` no refresh → sessão encerrada; se o motivo for reuso ("Sessão encerrada por
      segurança"), o login mostra essa mensagem num aviso.
- [ ] Logout chama `/auth/logout` (o servidor apaga o cookie) e limpa a memória e o cache de consultas.
- [ ] Durante a transição o backend ainda manda `refresh_token` no corpo: o frontend **ignora**.
- [ ] Login ganha a caixa **"Manter conectado"** (desmarcada por padrão; ajuda: "Desmarque em
      computador compartilhado") → `remember_me` no `POST /auth/login` (Q-S17-2). `401` "Sessão
      expirada" no refresh leva ao login sem aviso de segurança.

### Esqueci / redefinir senha

- [ ] Link "Esqueci minha senha" no login → `/esqueci-senha`: e-mail (e barbearia em localhost) →
      sempre a mesma resposta: "Se esse e-mail tiver acesso, enviamos um link. Não recebeu? Peça ao
      responsável pela barbearia um link de redefinição." `429` mostra a mensagem com o tempo.
- [ ] `/redefinir-senha/:token`: valida o link antes (`lookup`); link morto → mensagem e botão para
      pedir outro; válido → mostra o e-mail, pede senha nova + confirmação com as regras visíveis
      (8–128, diferente do e-mail) → sucesso leva ao login com "Senha alterada. Entre com a nova
      senha." Mesma estrutura de tela do aceite de convite (`/convite/:token`).

### Minha conta (`/app/minha-conta`)

- [ ] Acesso pelo nome/avatar no rodapé da sidebar (e no menu do celular, S18).
- [ ] **Trocar senha**: atual, nova, confirmação; sucesso avisa "As outras sessões foram encerradas".
- [ ] **Sessões ativas**: lista (dispositivo, último uso relativo, IP mascarado, selo "Esta sessão");
      "Encerrar" em cada uma (menos a atual) e "Sair de todas as outras" com confirmação.

### Equipe

- [ ] Na tela de Equipe (quando existir; até lá, a ação fica disponível no cadastro do barbeiro com
      login), para quem tem `team:manage`: "Gerar link de redefinição de senha" (mostra o link com
      "Copiar" e "Enviar pelo WhatsApp" — `https://wa.me/?text=`) e "Encerrar sessões".
      Nunca para si mesmo nem para o dono.

## Telas e fluxos

| Rota | Tela | Fluxos |
|---|---|---|
| `/esqueci-senha` | `features/auth/pages/ForgotPasswordScreen.tsx` | `pages/forgot/` |
| `/redefinir-senha/:token` | `features/auth/pages/ResetPasswordScreen.tsx` | `pages/reset/` |
| `/app/minha-conta` | `features/auth/pages/AccountScreen.tsx` | `pages/account/password/`, `pages/account/sessions/` |

## Data Contract

```text
POST /auth/login     {email, password, remember_me} → {access_token, token_type, expires_in, session_id}  + cookie
POST /auth/refresh   (cookie, X-Navalha-Client) → idem | 401 | 409 | 429
POST /auth/logout    (cookie, X-Navalha-Client) → 204
POST /auth/password/forgot {email} → 202
POST /auth/password/reset/lookup {token} → {email, expires_at}
POST /auth/password/reset {token, new_password} → 204
POST /auth/password/change {current_password, new_password} → 204
GET  /auth/sessions · DELETE /auth/sessions/{id} · POST /auth/sessions/revoke-others
POST /team/{user_id}/password-reset → {link, expires_at} · DELETE /team/{user_id}/sessions
```

```text
shared/session/tokens.ts            access em memória; limpeza das chaves antigas
shared/api/http.ts                  credentials, header, 409 do refresh, Retry-After no ApiError
features/auth/model/password.rules.ts   regras de senha espelhando o backend (menos a lista de comuns)
features/auth/model/session.rules.ts    rótulo "último uso", ordenação (atual primeiro)
features/auth/api/auth.api.ts       + chamadas acima · auth.queries.ts (['sessions'])
```

## Estado

| Estado | Onde |
|---|---|
| Access token | memória (`shared/session/tokens.ts`) |
| Refresh token | cookie httpOnly — o frontend nunca lê |
| Sessões ativas | TanStack Query `['sessions']` |
| Formulários | estado local |

## Permissões

| Ação | Permissão |
|---|---|
| Minha conta (senha, sessões) | qualquer usuário autenticado |
| gerar link de redefinição, encerrar sessões de membro | `team:manage` |

## Acceptance Criteria

- [ ] Nenhuma ocorrência de token em `localStorage`/`sessionStorage` (teste que inspeciona o storage
      depois do login e do refresh).
- [ ] Testes em `tests/`: regras de senha, rótulos de sessão, renovação única com `409` (http com
      `fetch` simulado), limpeza das chaves antigas.
- [ ] Conferido no navegador: recarregar mantém a sessão; duas abas renovando juntas não deslogam;
      sair de todas as outras derruba a outra aba na próxima chamada; esqueci/redefinir com link
      válido e morto.
- [ ] DEC nova no `memory/decisions.md` substituindo a DEC-002; ISS-001 fechada.
- [ ] Testes em `tests/` cobrindo as regras puras da feature
- [ ] Tela conferida no navegador (estados vazio, carregando, erro)
- [ ] `make check-frontend` verde

## Dependencies

- Backend `⚪draft_identity-auth-hardening.md` (cookie, rotas novas, transição).
- Deploy: o build do frontend com cookie e o backend com a transição saem juntos; o backend aceita o
  build anterior por uma versão.

## Notes

- PWA (S18): no iOS o app instalado tem cookies próprios, separados do Safari — o barbeiro entra uma
  vez no app instalado; com "Manter conectado" (Q-S17-2) a sessão dura 30 dias.
- Perguntas de produto no espelho do backend (Q-S17-1 a Q-S17-3).
  > Resolvido em 2026-11-06: Q-S17-1 = e-mail e link gerado pelo dono/gerente; Q-S17-2 = caixa
  > "Manter conectado" (30 dias, ou até fechar o navegador com máx. 12 h); Q-S17-3 = sem 2FA agora
  > (ROADMAP §7).
- ISS-006 (senha colada com espaço): o formulário de senha nova avisa "sua senha começa ou termina com
  espaço" — vale a pena reaproveitar o aviso no login.
