# Página pública de agendamento (S04)

**Priority:** high
**Status:** draft
**Espelho no backend:** `backend/docs/specs/⚪draft_booking-public-link.md`

## Overview

A página que o cliente final abre pelo link da bio do Instagram: `https://<slug>.<BASE_DOMAIN>/agendar`
(ou o domínio próprio da barbearia). **Celular primeiro**, sem login de painel e fora do shell
`/app`. O cliente escolhe unidade, serviço(s), barbeiro ou "qualquer um", dia e horário, confirma o
telefone com o código que chega no WhatsApp e pronto; volta depois em **"Meus agendamentos"** para
remarcar ou cancelar. Feature nova `booking`. Inclui também, no painel, a tela
`/app/configuracoes/agendamento-online` para o dono ligar a página, ocultar serviços/barbeiros e
copiar o link. Regras e contrato no espelho do backend.

## Decisões de produto já tomadas

| Parâmetro | Valor |
|---|---|
| PD-01 | Sem app do cliente: é uma página web, rápida no celular. |
| PD-02 | Identificação por telefone + código no WhatsApp, sem senha. |
| PD-04/05/06 | Horários de 15 em 15 min; vários serviços em sequência (barbeiro por serviço, se o cliente quiser); "qualquer um" deixa o sistema escolher o barbeiro livre. |
| PD-30 | Quem agenda recebe lembrete e confirmação (utilidade); promoções só com "sim" explícito — a caixa "aceito receber promoções" nasce **desmarcada**. |
| PD-31 | O agendamento nasce "agendado" e confirma pelo lembrete; marcado já dentro do prazo do lembrete, nasce confirmado. |
| PD-32 | Campo "Para quem é o horário?" (`attendee_name`); o mesmo cliente pode marcar horários simultâneos. |
| PD-42 | "Falar no WhatsApp" usa o número da unidade escolhida e, sem ele, o geral. |
| DEC-002 | A barbearia vem do endereço. No subdomínio de uma barbearia, `/` leva a `/agendar`; a landing do Navalha só existe no domínio raiz. |
| Backend T5 | Escolher horário não pede código; o código só aparece para confirmar ou ver "meus agendamentos". |

## Business Rules

### Fluxo de agendamento

- [ ] Passos com barra de progresso e "voltar" que preserva as escolhas: **Unidade** (pulado com uma
      só) → **Serviços** (múltipla escolha, com duração e preço quando `show_prices`; total somado;
      combos agendáveis de `GET /booking/combos` no topo, com o preço fechado — escolher um combo
      marca os serviços dele e envia `combo_id`, Q-S05-1) →
      **Barbeiro** ("Qualquer um" primeiro quando permitido; com mais de um serviço, opção "Escolher
      por serviço") → **Dia** (faixa de dias com e sem vaga, `availability/days`, até
      `max_advance_days`) → **Horário** (agrupado em Manhã/Tarde/Noite; com barbeiro escolhido, só os
      dele; com "qualquer um", o horário e "com quem estiver livre") → **Seus dados** → **Pronto**.
- [ ] Escolhas na URL (`?unidade=&servicos=&barbeiro=&dia=`) para sobreviver a refresh e permitir
      link direto (o barbeiro pode divulgar `…/agendar?barbeiro=<id>`). Parâmetro inválido é ignorado
      sem erro.
- [ ] Sem horário no dia: "Sem horários neste dia" + próximo dia com vaga em um toque.
- [ ] **Seus dados**: telefone (máscara brasileira; `+` para internacional) → "Enviar código no
      WhatsApp" (captcha invisível) → campo de 6 dígitos (`inputmode="numeric"`,
      `autocomplete="one-time-code"`, colar funciona) com "Reenviar em 60 s" e "Trocar número".
      Cliente novo: pede o nome. Texto fixo "Você vai receber a confirmação e o lembrete do horário
      pelo WhatsApp" (utilidade, PD-30) e caixa **desmarcada** "Aceito receber promoções da barbearia
      no WhatsApp" (`accept_marketing` no `POST /booking/appointments`). "Para quem é o horário?"
      (`attendee_name`, até 120) opcional, com dica "Deixe em branco se for para você" (PD-32).
      Observação opcional (300).
- [ ] Já identificado (cookie válido, `GET /booking/me`): o passo mostra "Agendando como <nome> ·
      <telefone> · Não é você?" e vai direto para confirmar.
- [ ] Confirmar mostra o resumo (serviços, barbeiro, unidade com endereço, dia, hora, total). `409`
      de horário ocupado volta ao passo Horário com "Esse horário acabou de ser ocupado" e as
      alternativas devolvidas pelo backend; `409`/`422` de limite (máximo de futuros, padrão 3) ou de
      bloqueio por faltas (quando a barbearia ligou) mostra a mensagem do backend e o botão "Falar no
      WhatsApp" (`whatsapp_url` da unidade, senão o geral).
- [ ] **Pronto**: resumo (com "Para: <nome>" quando houver `attendee_name`), "Adicionar à agenda"
      (`.ics`), "Ver meus agendamentos", "Agendar outro" e o texto conforme o `status` (PD-31):
      `scheduled` → "Agendado! Vamos te mandar um lembrete no WhatsApp para confirmar";
      `confirmed` → "Confirmado! Te esperamos".
- [ ] Erros do código: 400 mostra tentativas restantes; 410 volta a "Enviar código"; 429 mostra o
      tempo de espera; 503 "Não conseguimos enviar o código agora".

### Meus agendamentos (`/agendar/meus-agendamentos`)

- [ ] Sem sessão: pede telefone + código (mesmo componente do fluxo).
- [ ] Próximos (com status "Agendado" / "Confirmado", "para quem" quando houver, e Remarcar e Cancelar
      quando `can_reschedule`/`can_cancel`) e últimos atendimentos
      (com "Agendar de novo", que abre o fluxo com os mesmos serviços e barbeiro).
- [ ] Remarcar reaproveita os passos Dia e Horário com os mesmos serviços; Cancelar pede confirmação
      e motivo opcional. Fora da política: mensagem do backend + "Falar no WhatsApp".
- [ ] "Sair" chama `POST /booking/logout`.

### Página, marca e compartilhamento

- [ ] Cabeçalho com logo e nome da barbearia, texto de boas-vindas e, no rodapé, unidades com
      endereço (link para mapa), telefone e "Falar no WhatsApp" (número da unidade, senão o geral —
      PD-42). Discreto "Agendamento por Navalha". Barbearia sem WhatsApp conectado continua com a
      página e o código (Q-S04-1); só o botão "Falar no WhatsApp" some.
- [ ] Unidade com "agendamento online" desligado (S01) não aparece. Página indisponível (404 do backend): "Agendamento online indisponível. Fale com a barbearia"
      com o WhatsApp, se houver.
- [ ] `<title>` e `meta description` atualizados com o nome da barbearia (o cartão de prévia para
      robôs é do backend, `GET /booking/share`).
- [ ] Acessível: navegação por teclado, foco visível, botões de horário com rótulo completo
      ("Quarta, 18 de setembro, 15:30"), contraste dos tokens; funciona a partir de 360 px.

### Configuração no painel (`/app/configuracoes/agendamento-online`)

- [ ] Com `tenant:configure`: liga/desliga, **logo** (envio com prévia, até 1 MB), texto de
      boas-vindas, ocultar serviços e barbeiros, "qualquer um", mostrar preços e bloqueio após N faltas
      (Q-S04-2: desligado por padrão; ligado, N de 1 a 10 nos últimos 90 dias). Antecedência,
      horizonte, limite de agendamentos futuros e janela de mudança do cliente ficam em
      Configurações da barbearia (S01) — esta tela só mostra um resumo com link para lá.
- [ ] Link público em destaque com **Copiar** e **Abrir**, e sugestão de texto para a bio do
      Instagram. Sem o recurso no plano (`402`): caminho de upgrade.

## Telas e fluxos

| Rota | Tela | Fluxos |
|---|---|---|
| `/agendar` (host de barbearia; `/` redireciona para cá) | `features/booking/pages/BookingScreen.tsx` | `pages/steps/unit/`, `services/`, `barber/`, `day/`, `time/`, `identify/`, `done/` |
| `/agendar/meus-agendamentos` | `features/booking/pages/MyAppointmentsScreen.tsx` | `pages/my-appointments/list/`, `reschedule/`, `cancel/` |
| `/app/configuracoes/agendamento-online` | `features/settings/pages/BookingSettingsScreen.tsx` | `pages/booking/` |

O `router.tsx` decide `/` pelo host: domínio raiz → landing; host de barbearia
(`tenantComesFromHostname()`) → `/agendar`. Em localhost, `/agendar` usa o slug guardado (como o
login) e, sem ele, pede a barbearia.

## Data Contract

Contrato completo no espelho do backend. Endpoints consumidos:

```text
GET  /booking/shop · /booking/services · /booking/barbers
GET  /booking/availability/days · /booking/availability
POST /booking/otp/request · /booking/otp/verify · /booking/logout · /booking/appointments
GET  /booking/me · /booking/me/appointments · /booking/me/appointments/{id}/calendar.ics
POST /booking/me/appointments/{id}/reschedule · /booking/me/appointments/{id}/cancel
GET/PUT /booking/settings · PUT/DELETE /booking/settings/logo · GET /booking/logo
```

As chamadas públicas usam o `shared/api/http.ts` com uma opção nova `auth: false` (sem bearer, sem
renovação de token) e o header `X-Requested-With: navalha` em toda mutação; o cookie de sessão vai
sozinho (mesma origem).

Arquivos:

```text
features/booking/model/booking.types.ts       Shop, PublicService, PublicBarber, Slot, PublicAppointment, BookingDraft
features/booking/model/booking.rules.ts       passos válidos, total e duração, agrupamento por período,
                                              serialização dos itens (PD-05), estado de URL ↔ rascunho
features/booking/api/booking.api.ts · booking.queries.ts
features/settings/api/bookingSettings.api.ts · bookingSettings.queries.ts
shared/ui/OtpInput.tsx                        campo de código (genérico, sem tipo de negócio)
```

O componente de captcha carrega o script do Turnstile só no passo de identificação.

## Estado

| Estado | Onde |
|---|---|
| Barbearia, serviços, barbeiros, dias, horários, meus agendamentos, sessão (`/booking/me`) | TanStack Query (`['booking-shop']`, `['booking-slots', unidade, itens, dia]`…) |
| Escolhas do fluxo (unidade, serviços, barbeiro, dia, horário) | URL |
| Telefone, código, nome, observação | local |
| Sessão | cookie HttpOnly (o frontend só sabe dela por `GET /booking/me`) |

## Permissões

A página pública não usa `/auth/me`. No painel:

| Ação | Permissão em `/auth/me` |
|---|---|
| ver e editar "Configurações → Agendamento online" | `tenant:configure` |

## Acceptance Criteria

- [ ] Feature `booking` criada (`index.ts` + `api/ model/ pages/ ui/`), fora do `RequireAuth`; o
      shell do painel não é carregado na página pública (divisão de código por rota).
- [ ] `http.ts` com `auth: false` sem mudar o comportamento do painel (teste).
- [ ] Testes em `tests/`: validação de passos e URL ↔ rascunho; total e duração com vários
      serviços; agrupamento de horários por período no fuso da unidade; serialização de `items`;
      máscara de telefone; decisão de `/` por host; texto do Pronto por `status`; caixa de promoções
      desmarcada por padrão; escolha do `whatsapp_url` (unidade → geral → nenhum).
- [ ] Tela conferida no navegador em 360 px e em desktop: fluxo completo com cliente novo e
      existente, "qualquer um", vários serviços com barbeiros diferentes, horário ocupado (409),
      código errado/expirado/reenvio, meus agendamentos com remarcar e cancelar fora da política,
      página indisponível.
- [ ] Peso da página pública medido (meta: < 150 kB de JS comprimido na primeira carga).
- [ ] `make docs-api` regenerado; `README.md` e `memory/progress.md` atualizados.
- [ ] Testes em `tests/` cobrindo as regras puras da feature
- [ ] Tela conferida no navegador (estados vazio, carregando, erro)
- [ ] `make check-frontend` verde

## Dependencies

- Backend: `⚪draft_booking-public-link.md` implementado e congelado no `openapi.json`.
- `⚪draft_frontend-inbox.md` (S10): feature `settings`.
- S03 (`frontend-agenda`): o agendamento aparece na agenda com a origem "link".
- Turnstile (chave pública em `VITE_TURNSTILE_SITE_KEY`, nova variável em `.env.example` e
  `docs/ENVIRONMENT_VARIABLES.md`).

## Notes

- ✅ Perguntas que mudam esta tela estão no backend: **Q-S04-1** (página sem WhatsApp conectado),
  **Q-S04-2** (bloqueio por faltas); e na S03: **Q-S03-4** (limite de futuros) e **Q-S03-5** ("para
  quem é o horário").
  > Resolvido em 2026-11-06: Q-S04-1 — sem WhatsApp conectado, o código sai de um número da
  > plataforma Navalha (ROADMAP §7). Q-S04-2 — bloqueio por faltas configurável, desligado por padrão
  > (ROADMAP §7). Q-S03-4 — limite de futuros configurável, padrão 3 (ROADMAP §7). Q-S03-5 — campo
  > "para quem" (`attendee_name`), com horários simultâneos (PD-32). Consentimento: caixa de
  > promoções desmarcada, lembrete por utilidade (PD-30).
- QR code do link para imprimir no balcão: útil, mas exige dependência nova; fica para depois.
- Tema da página com a cor da barbearia (marca própria) fica para depois; nesta versão usa os tokens
  do Navalha com o logo da barbearia.
