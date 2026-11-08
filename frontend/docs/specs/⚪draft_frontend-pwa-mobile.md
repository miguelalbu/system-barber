# Painel no celular (PWA), "Meu dia" do barbeiro e navegação por permissão

**Priority:** medium
**Status:** draft
**Espelho no backend:** não se aplica

## Overview

O barbeiro não tem app nativo (PD-26): ele usa o **painel instalável** no celular. Esta spec deixa o
painel pronto para isso em quatro partes: (1) **PWA** — manifest, ícones e um service worker mínimo
que só guarda arquivos estáticos (nada de dado de cliente offline); (2) **layout de celular** do shell
— barra inferior no lugar da sidebar, topbar compacta, tabelas viram cartões; (3) a tela **"Meu dia"**
do barbeiro — agenda do dia, próximo cliente e minhas comissões; (4) **navegação filtrada por
permissão e por plano** — resolve o ISS-005 (hoje um barbeiro vê "Financeiro").

Sem backend próprio: consome as rotas de agenda (S03), comissões (S08), ficha do cliente (S13) e o
`/auth/me`.

Referência: o "Minha agenda" do app do profissional do Trinks e do AppBarber — lista do dia, cartão
do próximo cliente com serviço e observações, e "minha produção/comissão" da semana.

## Decisões de produto já tomadas

| Parâmetro | Valor |
|---|---|
| PD-26 | Painel responsivo instalável (PWA): agenda do dia, próximo cliente, minhas comissões. Sem app nativo. |
| PD-18 | Sem push para handoff — e esta spec não cria push de nenhum tipo; só aviso dentro do app aberto (Q-S18-2). Web Push fica para spec própria. |
| PD-41 | Contato do cliente (telefone, e-mail) para o barbeiro: configurável pela barbearia, **padrão oculto** — o barbeiro vê nome, histórico e indicadores (S13). |
| PD-12 | Barbeiro só comissionado: "minhas comissões" é o número que importa para ele. |
| Offline | **Sem offline de dado sensível**: o service worker não guarda resposta da API. Sem rede → tela "Sem conexão". |
| Dependências | Nenhuma nova: service worker escrito à mão (`public/sw.js`), manifest estático. |

## Business Rules

### PWA

- [ ] `public/manifest.webmanifest`: `name` "Navalha", `short_name` "Navalha" (Q-S18-1), `start_url`
      `/app`, `scope` `/`, `display` `standalone`, `theme_color`/`background_color` dos tokens,
      ícones 192, 512 e `maskable`; `apple-touch-icon` e metas do iOS no `index.html`.
- [ ] `public/sw.js` (~60 linhas): `/assets/*` (arquivos com hash do Vite) **cache-first**;
      navegação (`mode: navigate`) **network-first** com fallback para o `index.html` em cache; **toda
      chamada `/api/*` passa direto (network-only), nunca entra no cache**. Cache versionado pelo
      build; versões antigas apagadas no `activate`.
- [ ] Registrado só em produção (`import.meta.env.PROD`), depois do `load`.
- [ ] Versão nova → faixa "Nova versão disponível · Atualizar" (`skipWaiting` + reload só quando a
      pessoa clica — nunca recarrega no meio de um formulário).
- [ ] Sem rede: o shell mostra "Sem conexão — os dados aparecem quando a internet voltar"; TanStack
      Query pausa (`onlineManager`) e retoma sozinho.
- [ ] Logout limpa o cache de consultas em memória (já faz); como nada da API é cacheado no SW, não há
      dado de cliente no aparelho depois de sair.
- [ ] Convite "Instalar no celular": em Android, botão a partir do `beforeinstallprompt` em "Meu dia"
      e Minha conta; em iOS, instrução "Compartilhar → Adicionar à Tela de Início". Some quando já
      está em `display-mode: standalone`.

### Layout de celular (≤ 768 px)

- [ ] Sidebar vira **barra inferior** com até 4 itens permitidos + "Mais" (folha com o resto, a troca
      de unidade, Minha conta e Sair). Ordem por cargo: barbeiro → Meu dia, Agenda, Clientes, Mais;
      recepção → Agenda, Conversas, Clientes, Mais; dono/gerente → Dashboard, Agenda, Conversas, Mais.
- [ ] Topbar compacta: título e uma ação principal da tela; respeita `safe-area-inset-*`.
- [ ] Tabelas das listas (clientes, barbeiros, serviços) viram lista de cartões abaixo de 768 px —
      componente `shared/ui/ResponsiveTable` (colunas declaradas com `primary`/`secondary`).
- [ ] Formulários em painel viram tela cheia; alvos de toque ≥ 44 px; inputs com `inputmode` certo
      (telefone, número, e-mail) e fonte ≥ 16 px (evita o zoom do iOS).
- [ ] Agenda (S03) no celular: um barbeiro por vez com troca por deslize/chips — a spec da agenda
      implementa a visão; esta spec dá o breakpoint e o shell.

### "Meu dia" (`/app/meu-dia`)

- [ ] Aparece para quem tem `barber_id` no `/auth/me` (barbeiro, ou dono/gerente que também atende).
      Para o cargo barbeiro é a **tela inicial** (`/app` → `/app/meu-dia`).
- [ ] Cabeçalho: dia (hoje por padrão; setas para ontem/amanhã; data na URL `?dia=`), unidade, resumo
      "6 atendimentos · 1 não confirmado · próximo às 14:30".
- [ ] **Próximo cliente** (cartão em destaque): horário, nome, serviço(s) e duração, status de
      confirmação (PD-07, "não confirmado" em destaque), observação do agendamento e da ficha,
      indicadores da S13 (última visita, "costuma cortar com você", faltas). Contato (telefone,
      botão de WhatsApp) só se a barbearia liberou para o barbeiro (PD-41, padrão oculto): a tela
      mostra o que a S13 devolve e nunca tenta revelar o que veio mascarado/omitido. Ações conforme as permissões do barbeiro na S03 (ex.: marcar atendido/falta).
- [ ] **Agenda do dia**: lista em ordem de horário com status, intervalos livres ("Livre 11:00–12:00")
      e bloqueios; tocar abre o detalhe do agendamento (S03).
- [ ] **Minhas comissões**: hoje, semana e mês corrente (valor e número de atendimentos), e o último
      fechamento (S08); link para o detalhe em Financeiro → Comissões quando a tela da S08 existir.
- [ ] Atualiza a cada 60 s com a tela visível e ao voltar para o app (`refetchOnWindowFocus`).
- [ ] **Aviso dentro do app** (Q-S18-2): quando a atualização traz agendamento novo, cancelado ou
      remarcado do dia que não estava na leitura anterior, aparece um aviso no topo ("Cliente
      desmarcou o horário das 15:00", "Novo agendamento às 16:30") que some sozinho e destaca o item
      na lista. Só com o app aberto; sem push, sem som.
- [ ] Estados: dia sem agendamento ("Agenda livre hoje"), folga ("Você está de folga hoje" — S02),
      erro por bloco (comissões fora do ar não esconde a agenda).

### Navegação por permissão e plano (ISS-005)

- [ ] Cada item de `NAV` declara `permission` (uma ou várias, "qualquer uma") e opcionalmente
      `feature` (plano, S15) e `requiresBarber`. A sidebar e a barra inferior mostram só o que
      `useAuth().can` e `hasFeature` permitem (recurso fora do plano: regra da Q-S15-5).
- [ ] Mapa: Dashboard `appointment:read` (escopo ≠ `own`); Meu dia `requiresBarber`; Agenda
      `appointment:read`; Conversas `conversation:read` + `whatsapp`; Clientes `client:read`;
      Cadastros qualquer permissão de leitura de cadastro (`team:read`, `catalog:read`); Relatórios
      (S14); Financeiro `finance:read` ou `commission:read`; Configurações `tenant:configure`;
      Tokens só em `import.meta.env.DEV`.
- [ ] `RequirePermission` (guarda por rota em `features/auth/ui/`): URL digitada sem permissão mostra
      "Você não tem acesso a esta área" com link para a tela inicial — não redireciona em silêncio.
- [ ] **Tela inicial por cargo** (`/app`): barbeiro → Meu dia; quem não vê dashboard → Agenda; dono
      com primeiros passos pendentes → `/app/primeiros-passos` (S16); demais → Dashboard.
- [ ] Badge de Conversas deixa de ser fixo (ISS-004): vem da contagem da fila de handoff (S10) ou
      some.

## Telas e fluxos

| Rota | Tela | Fluxos |
|---|---|---|
| `/app/meu-dia` | `features/scheduling/pages/MyDayScreen.tsx` | `pages/my-day/next-client/`, `pages/my-day/day-list/`, `pages/my-day/commissions/` |
| `/app` (índice) | redirecionamento por cargo (`app/router.tsx`) | — |
| (shell) | `app/_shell/Sidebar.tsx`, `app/_shell/BottomNav.tsx`, `app/_shell/MoreSheet.tsx`, `app/_shell/UpdateBanner.tsx`, `app/_shell/OfflineBanner.tsx` | — |

"Meu dia" fica na feature `scheduling` (é uma visão da agenda); as comissões entram pelo `index.ts` da
feature `finance` (S08).

## Data Contract

Nenhuma rota nova. Consome (assinaturas assumidas das specs vizinhas):

```text
GET /auth/me                                        barber_id, permissions, plan (S15)
GET /agenda?unit_id=&from=&to=&barber_ids=          S03 (escopo own já filtra para o barbeiro)
GET /working-time?unit_id=&from=&to=                S02: intervalos de trabalho e folgas do dia
GET /commissions/summary?date_from=&date_to=&barber_id=   S08 (chamado 3×: hoje, semana, mês)
GET /commissions/payouts?barber_id=&status=closed&limit=1 S08 (último fechamento)
GET /clients/{id}/profile                           S13 (indicadores do próximo cliente)
GET /conversations/counts                           S10 (badge: waiting_human)
```

```text
app/_shell/nav.ts                         NAV com permission/feature/requiresBarber
app/_shell/nav.rules.ts                   visibleNav(me), homePathFor(me), itens da barra inferior
features/scheduling/model/myDay.rules.ts  próximo cliente, intervalos livres, resumo do dia
shared/ui/ResponsiveTable.tsx             tabela ↔ cartões
public/manifest.webmanifest · public/sw.js · public/icons/*
src/shared/pwa/registerServiceWorker.ts   registro + evento de versão nova
```

## Estado

| Estado | Onde |
|---|---|
| Dia selecionado em "Meu dia" | URL (`?dia=`) |
| Agenda, disponibilidade, comissões, ficha | TanStack Query (chaves das features donas) |
| Versão nova / offline | estado do shell (evento do SW, `onlineManager`) |
| Convite de instalar dispensado | `localStorage` (não é dado sensível) |

## Permissões

| Ação | Permissão em `/auth/me` |
|---|---|
| ver "Meu dia" | `barber_id` presente + `appointment:read` |
| comissões em "Meu dia" | `commission:read` (barbeiro: `own`) |
| cada item de navegação | tabela da regra "Mapa" acima |

## Acceptance Criteria

- [ ] Lighthouse PWA "instalável" ok; instalado e aberto em Android (Chrome) e iOS (Safari).
- [ ] Com DevTools offline: o shell abre, "Sem conexão" aparece, e **nenhuma** resposta `/api/*`
      está no Cache Storage (teste manual documentado + teste do `sw.js` com fetch simulado).
- [ ] Testes em `tests/`: `visibleNav` para os quatro cargos e para dono-barbeiro; `homePathFor`;
      itens da barra inferior; próximo cliente (agora entre dois horários, último do dia, dia
      vazio); intervalos livres com bloqueio no meio.
- [ ] Barbeiro não vê Financeiro, Cadastros de equipe nem Configurações (ISS-005 fechado); ISS-004
      atualizado.
- [ ] Painel conferido em 375 px (iPhone SE) e 768 px: sem rolagem horizontal da página.
- [ ] Testes em `tests/` cobrindo as regras puras da feature
- [ ] Tela conferida no navegador (estados vazio, carregando, erro)
- [ ] `make check-frontend` verde

## Dependencies

- **S03** (agenda: lista do dia por barbeiro, detalhe, ações do barbeiro), **S02** (jornada/folga),
  **S08** (resumo de comissões do barbeiro), **S13** (ficha), **S10** (contagem da fila).
- **S15** (`hasFeature`, regra de item travado), **S16** (tela inicial do dono com primeiros passos).
- **S17** (cookie de refresh): sem ele, o app instalado guardaria token em `localStorage` — esta spec
  pode sair antes, mas o fechamento do ISS-001 é da S17.

## Notes

- Ícones: gerados a partir da marca da sidebar (`sidebar-brand-mark`); ISS-008 (referências de design
  fora do repositório) — se a marca final mudar, só os PNGs mudam.
- Tela cheia no iOS: `apple-mobile-web-app-status-bar-style` `black-translucent` + safe areas, senão a
  barra inferior fica sob o indicador de início.

### Perguntas em aberto

- ✅ **Q-S18-1 — Nome e ícone do app instalado.**
  (a) "Navalha" para todas as barbearias; (b) nome e logo da barbearia (manifest gerado por barbearia
  — exige rota no backend e upload de logo); (c) "Navalha" agora, (b) quando houver logo da barbearia.
  **Recomendação: (c)** — o barbeiro instala uma vez; o valor de marca própria aparece mais no link
  público (S04) do que no ícone do celular dele.
  > Resolvido em 2026-11-06: (c) — o app instalado se chama "Navalha" agora; nome e logo da
  > barbearia quando houver logo (ROADMAP §7).
- ✅ **Q-S18-2 — Notificação push para o barbeiro (novo agendamento, cancelamento)?**
  (a) não; (b) sim, Web Push opcional por barbeiro (funciona no Android e no iOS 16.4+ instalado);
  (c) só aviso dentro do app quando aberto.
  **Recomendação: (c) agora e (b) numa spec própria** — push exige chave VAPID, assinatura por
  aparelho e backend; o PD-18 já descartou push para handoff, mas para o barbeiro "cliente desmarcou
  às 15h" é o valor mais citado no mercado.
  > Resolvido em 2026-11-06: (c) agora — sem push, só aviso dentro do app aberto; Web Push numa
  > spec própria (ROADMAP §7).
