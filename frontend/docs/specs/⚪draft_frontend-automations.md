# Automações, campanhas e avaliações no painel (S12)

**Priority:** high
**Status:** draft
**Espelho no backend:** `backend/docs/specs/⚪draft_automations-messages-campaigns.md`

## Overview

Três telas para o que a barbearia manda no WhatsApp sem ninguém digitar: **Automações**
(`/app/configuracoes/automacoes`, na feature `settings`) — liga, ajusta e edita o texto do aviso de
agendamento, do lembrete com confirmação, da reativação, do aniversário e da avaliação, com o
histórico de envios e o custo estimado; **Campanhas** (`/app/marketing/campanhas`) — monta o público
por filtros, vê a prévia com custo e agenda o envio; e **Avaliações** (`/app/marketing/avaliacoes`) —
notas por barbeiro e os alertas de nota baixa para tratar. As duas últimas inauguram a feature
`marketing` prevista no roadmap. Regras e contrato no espelho do backend.

## Decisões de produto já tomadas

| Parâmetro | Valor |
|---|---|
| PD-07 | Lembrete com Confirmar/Remarcar/Cancelar e prazo de "não confirmado" configurável; a tela deixa claro que **nunca cancela sozinho**. |
| PD-20 | Reativação (padrão 40 dias), aniversário, avaliação (link do Google para todos que responderam, nota baixa → alerta — PD-27), campanhas com modelo aprovado; opt-out respeitado. |
| PD-27 | O **link do Google vai para toda nota**; nota baixa continua gerando alerta. A tela não oferece "só nota alta recebe o link". |
| PD-30 | Marketing só para quem tem ao menos um atendimento ou disse "sim" explícito; utilidade para todo cliente com agendamento. A prévia e os envios mostram o motivo "Sem consentimento". |
| PD-18 | Alerta de nota baixa aparece no painel (contador), sem push. |

## Business Rules

### Automações (`/app/configuracoes/automacoes`)

- [ ] Um cartão por automação, nesta ordem: Aviso de agendamento, Lembrete e confirmação,
      Avaliação, Reativação, Aniversário. Cada cartão: liga/desliga, resumo em uma frase
      ("Lembra 24 h antes; sem resposta até 3 h antes, marca como não confirmado"), status do
      modelo (Aprovado / Em análise / Rejeitado com motivo) e números dos últimos 30 dias (enviados,
      pulados, respostas).
- [ ] Abrir o cartão mostra os campos do `config` com os limites do backend (lembrete 2–72 h, maior
      que o prazo de confirmação; inatividade 15–365 dias; atraso da avaliação 30–1440 min; nota que
      gera alerta, 1–4) e a validação local espelhada. O cartão de Avaliação diz "Todo cliente que
      responder recebe o link do Google da unidade; nota até N gera alerta" (PD-27) — sem campo de
      "nota alta". O **prazo de "não confirmado"**
      é da barbearia (S01, `confirmation_deadline_hours`): o cartão do lembrete mostra o valor e um
      link para Configurações da barbearia, sem editá-lo aqui.
- [ ] Editor do texto da mensagem: corpo com variáveis inseridas por botões (`{{nome_cliente}}`,
      `{{barbeiro}}`…), prévia em bolha de WhatsApp com dados de exemplo, botões fixos quando a
      automação os exige (lembrete, avaliação). Salvar o texto avisa: "O novo texto vai para análise da
      Meta; até ser aprovado, o texto atual continua sendo usado".
- [ ] Automação ligada com modelo ainda não aprovado mostra "Aguardando aprovação do modelo — nada é
      enviado ainda".
- [ ] Seção **Regras gerais**: horário de silêncio (início/fim, mínimo 8 h fora), limites de
      marketing por cliente (7 e 30 dias) e **link de avaliação do Google por unidade**.
- [ ] Aba **Envios**: tabela paginada (data, automação, cliente, status, motivo de pulado, resposta,
      custo estimado) com filtros por automação, status e período na URL. Motivos traduzidos
      ("Cliente pediu para não receber promoções", "Cliente pediu para não receber nada", "Sem
      consentimento para promoções" — importado ou contato sem atendimento, PD-30 —, "Limite de
      frequência", "Sem WhatsApp conectado").
- [ ] Cartão de **custo do mês** por automação e total, com o rótulo "estimativa — a cobrança é feita
      pela Meta".
- [ ] Sem WhatsApp conectado: faixa com link para `/app/configuracoes/whatsapp`. Sem o recurso no
      plano (`402`): cartões em modo leitura com o caminho de upgrade.

### Campanhas (`/app/marketing/campanhas`)

- [ ] Lista: nome, status (Rascunho, Agendada, Enviando, Enviada, Cancelada), data de envio,
      destinatários e, para enviadas, entregues/lidas/respostas/agendamentos.
- [ ] Criar/editar em três passos na mesma tela: **Mensagem** (escolhe um modelo de campanha
      aprovado; atalho "Criar modelo" abre o editor de modelo da S10 com categoria marketing e o
      rodapé de SAIR já incluído), **Público** (filtros do `AudienceFilter` com rótulos em português)
      e **Envio** (agora ou data/hora fora do silêncio).
- [ ] A prévia do público atualiza ao mudar filtros (espera de 500 ms): elegíveis, excluídos por
      motivo, 10 nomes de amostra e custo estimado em reais. Elegíveis = 0 desabilita "Agendar".
- [ ] Agendar pede confirmação com o resumo ("312 clientes, cerca de R$ 98,00, sábado 10:00").
      `409` mostra a mensagem do backend.
- [ ] Campanha enviando atualiza o progresso a cada 10 s e oferece **Cancelar envio**; enviada mostra
      os números e a lista de destinatários com status.

### Avaliações (`/app/marketing/avaliacoes`)

- [ ] Topo: média do período, total e distribuição por nota; tabela por barbeiro (média, quantidade).
- [ ] Lista de avaliações com filtros (nota máxima, alerta aberto, unidade, barbeiro, período) na
      URL; cada item mostra nota, comentário, cliente, barbeiro, data e "Abrir conversa"
      (`/app/conversas?c=`).
- [ ] Alerta aberto destacado com **Marcar como tratado** (nota opcional). O item "Marketing" da
      barra lateral mostra o contador de alertas abertos.
- [ ] Barbeiro (`client:read` com `own`) vê só as dele, sem ação de tratar.

## Telas e fluxos

| Rota | Tela | Fluxos |
|---|---|---|
| `/app/configuracoes/automacoes?aba=automacoes\|envios` | `features/settings/pages/AutomationsSettingsScreen.tsx` | `pages/automations/cards/`, `pages/automations/message-editor/`, `pages/automations/dispatches/` |
| `/app/marketing` | redireciona para `campanhas` (ou `avaliacoes` sem `tenant:configure`) | — |
| `/app/marketing/campanhas` e `/app/marketing/campanhas/:id` | `features/marketing/pages/CampaignsScreen.tsx` | `pages/campaigns/list/`, `pages/campaigns/editor/`, `pages/campaigns/detail/` |
| `/app/marketing/avaliacoes` | `features/marketing/pages/ReviewsScreen.tsx` | `pages/reviews/summary/`, `pages/reviews/list/` |

## Data Contract

Contrato completo no espelho do backend. Endpoints consumidos:

```text
GET  /automations · /automations/settings · /automations/dispatches · /automations/costs
PUT  /automations/{kind} · /automations/{kind}/message · /automations/settings
GET  /campaigns · /campaigns/{id} · /campaigns/{id}/recipients
POST /campaigns · /campaigns/audience-preview · /campaigns/{id}/schedule · /campaigns/{id}/cancel
PATCH/DELETE /campaigns/{id}
GET  /reviews · /reviews/summary · POST /reviews/{id}/handle
GET  /whatsapp/templates?purpose=campaign · POST /whatsapp/templates     (S10)
GET  /tenant/units · /barbers · /services                                (filtros)
```

Arquivos:

```text
features/settings/model/automations.types.ts · automations.rules.ts (limites, resumo em frase, motivos)
features/settings/api/automations.api.ts · automations.queries.ts
features/marketing/model/campaigns.types.ts · campaigns.rules.ts (filtros ↔ rótulos, validação de horário)
features/marketing/model/reviews.types.ts
features/marketing/api/marketing.api.ts · marketing.queries.ts
features/settings/ui/TemplateEditor.tsx   exportado pelo index.ts de settings (usado em campanhas)
```

## Estado

| Estado | Onde |
|---|---|
| Automações, envios, custos, campanhas, prévia, avaliações | TanStack Query (`['automations']`, `['dispatches', filtros]`, `['campaigns']`, `['campaign', id]` com `refetchInterval` enquanto `sending`, `['audience-preview', filtro]`, `['reviews', filtros]`) |
| Abas, filtros, passo do editor de campanha | URL |
| Formulários e rascunho do texto | local |

## Permissões

| Ação | Permissão em `/auth/me` |
|---|---|
| Automações (ver e editar), Campanhas | `tenant:configure` |
| ver Avaliações | `client:read` |
| marcar alerta como tratado | `client:write` |
| item "Marketing" na barra lateral | `client:read` ou `tenant:configure` |

## Acceptance Criteria

- [ ] Feature `marketing` criada (`index.ts` + `api/ model/ pages/ ui/`), rotas e item na barra
      lateral com contador de alertas.
- [ ] Testes em `tests/`: validação de cada `config` (inclusive antecedência > prazo da S01 e nota de
      alerta 1–4); frase-resumo de cada automação; tradução de motivos de pulado; filtros ↔ rótulos e
      serialização do `AudienceFilter`; validação de horário de envio contra o silêncio.
- [ ] Tela conferida no navegador: ligar lembrete, editar texto (modelo em análise), envios com
      filtros, campanha do rascunho ao envio e cancelamento, avaliações com alerta tratado, barbeiro
      vendo só as dele, plano sem o recurso.
- [ ] `make docs-api` regenerado; `README.md` e `memory/progress.md` atualizados.
- [ ] Testes em `tests/` cobrindo as regras puras da feature
- [ ] Tela conferida no navegador (estados vazio, carregando, erro)
- [ ] `make check-frontend` verde

## Dependencies

- Backend: `⚪draft_automations-messages-campaigns.md` implementado e congelado no `openapi.json`.
- `⚪draft_frontend-inbox.md` (S10): feature `settings`, modelos de mensagem, `?c=` da Central.
- S03 (`frontend-agenda`): o destaque de "não confirmado" na agenda é de lá.

## Notes

- ✅ Perguntas que mudam estas telas estão no backend: **Q-S12-1/Q-S12-2** (motivos de exclusão e o
  que o opt-out mostra), **Q-S12-3** (alerta na fila de conversas), **Q-S12-4** (gerente em
  Campanhas) e **Q-S12-5** (texto do cartão de Avaliação conforme a decisão sobre o link do Google).
  > Resolvido em 2026-11-06: Q-S12-1 — marketing só com ao menos um atendimento ou "sim" explícito,
  > utilidade para todo cliente com agendamento (PD-30); Q-S12-2 — "SAIR" pergunta "Só promoções" /
  > "Tudo", e os motivos de pulado distinguem os dois (ROADMAP §7); Q-S12-3 — contador de alertas +
  > conversa em "aguardando humano" (ROADMAP §7); Q-S12-4 — Campanhas só para o dono
  > (`tenant:configure`) (ROADMAP §7); Q-S12-5 — link do Google para toda nota, alerta na nota baixa
  > (PD-27).
