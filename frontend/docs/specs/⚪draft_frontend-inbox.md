# Central de conversas e conexão do WhatsApp no painel (S10)

**Priority:** high
**Status:** draft
**Espelho no backend:** `backend/docs/specs/⚪draft_messaging-whatsapp-inbox.md`

## Overview

`/app/conversas` é hoje o mock do protótipo (`features/conversations`, `conversations.mock.ts`).
Esta spec liga a Central à API real: lista de conversas com filas (**Aguardando humano** primeiro),
thread com mensagens de texto, áudio (com transcrição), imagem, botões e status de entrega,
composer que respeita quem conduz a conversa (IA, fila, eu) e a janela de 24 h, e a ficha resumida
do cliente ao lado. Cria também a primeira tela da feature nova **`settings`**:
`/app/configuracoes/whatsapp`, onde o dono conecta o número pelo Embedded Signup da Meta em
coexistência com o app do celular e acompanha os modelos de mensagem.

Regras de canal, janela, modos da conversa, opt-out e contrato estão no espelho do backend; aqui
fica só o que é de tela.

## Decisões de produto já tomadas

| Parâmetro | Valor |
|---|---|
| PD-15 | Coexistência: o que a equipe responde pelo celular aparece na thread, marcado "pelo celular". |
| PD-18 | Fila "Aguardando humano" com o resumo da IA no topo da conversa; a IA só volta com "Devolver para a IA". Sem push nem som de notificação no navegador nesta versão — o aviso é o contador na barra lateral. |
| PD-19 | No painel a equipe vê quem escreveu (cliente, IA, equipe, celular, automação); para o cliente tudo sai como a barbearia. |
| PD-28 | No início a barbearia paga a Meta com o cartão dela (Navalha Tech Provider): a tela de conexão avisa isso e o painel só estima custo. |
| PD-37 | A IA não fecha venda de clube/pacote: a conversa chega à fila com motivo "Venda de clube/pacote" para a equipe fechar. |
| PD-40 | Créditos de IA acabaram → conversas novas chegam à fila com motivo "Sem créditos de IA". |
| PD-42 | Um número geral e, opcionalmente, um por unidade, com quantidade limitada pelo plano (`whatsapp_numbers`). |
| Atualização | Polling (decisão T5 do backend): lista a cada 15 s, conversa aberta a cada 5 s, contador da barra lateral a cada 30 s; pausa com a aba oculta. |
| Onde fica a conexão | `/app/configuracoes/whatsapp`, feature nova `settings` (o roadmap junta ali WhatsApp, IA, automações e políticas). |

## Business Rules

### Lista

- [ ] Abas na URL (`?fila=`): **Aguardando** (`waiting_human`, com contador), **Minhas**
      (assumidas por mim), **IA** (`ai`), **Todas** (abertas) e **Resolvidas**. A aba padrão é
      Aguardando quando ela tem itens, senão Todas.
- [ ] Item: nome do contato (ou telefone formatado), hora relativa da última mensagem, prévia,
      etiqueta do modo (`IA conduzindo`, `Aguardando humano`, `Com <nome>`, `Resolvida`), contador de
      não lidas e o motivo do handoff quando houver, com rótulo por `handoff_reason`: "Pediu
      atendente" (`client_asked`), "Reclamação" (`complaint`), "Venda de clube/pacote" (`sale`),
      "Sem créditos de IA" (`no_ai_credits`), "Avaliação baixa" (`low_review`)…
- [ ] Na aba Aguardando, conversas com motivo `no_ai_credits` são agrupadas sob um aviso "Os
      créditos de IA acabaram — novas conversas chegam aqui" (para o dono, com link para
      `/app/configuracoes/plano`).
- [ ] Busca por nome ou telefone (`q`, espera de 300 ms, na URL); filtro de unidade só aparece para
      quem vê mais de uma unidade. Conversa do número geral sem unidade definida aparece como "Geral"
      e entra no filtro de qualquer unidade para quem a vê (PD-42).
- [ ] Rolagem infinita pelo `next_cursor`; os quatro estados (carregando, vazio por aba, erro, dados).
- [ ] O contador da barra lateral (hoje fixo `'4'`) vem de `GET /conversations/counts`
      (`waiting_human`); some quando é zero.

### Conversa

- [ ] Cabeçalho: contato, telefone, número da barbearia que recebeu (quando há mais de um: telefone
      + "Geral" ou o nome da unidade), modo e
      ações conforme o estado e a permissão: **Assumir conversa**, **Devolver para a IA**,
      **Resolver**, **Ver ficha**.
- [ ] Em `waiting_human`, uma faixa no topo mostra o motivo e o **resumo da IA**
      (`handoff_summary`) com a hora do pedido.
- [ ] Mensagens agrupadas por dia; bolha por autor (cliente à esquerda; IA, equipe, celular e
      automação à direita com rótulo distinto); notas de sistema centralizadas ("Camila assumiu",
      "Agendamento criado pela IA · 17/08 10:30 · Diego").
- [ ] Status da saída: relógio (`queued`), um tique (`sent`), dois (`delivered`), dois destacados
      (`read`), e falha em vermelho com a mensagem do backend e "Tentar de novo" (reenvia o mesmo
      conteúdo como mensagem nova).
- [ ] Áudio: player nativo + transcrição abaixo (quando a IA transcreveu). Imagem: miniatura que
      abre em tamanho real. Documento: nome + baixar. A mídia vem da rota autenticada e vira
      `blob:` URL (o `<img src>` não manda o bearer); mídia expirada (410) mostra "Mídia não está mais
      disponível".
- [ ] Botões e listas enviados aparecem como na conversa do cliente (texto + opções); a resposta do
      cliente a um botão mostra o texto do botão.
- [ ] Mensagem com `author = phone_app` leva o rótulo "pelo celular". Conversa em `human` por resposta
      no celular (`human_via_phone_at`) mostra "Respondida pelo celular — a IA volta se ninguém
      responder em 12 h" com a hora prevista (Q-S10-4); assumir no painel tira o aviso.
- [ ] Mensagens importadas do histórico do app (Q-S10-3) aparecem antes de uma nota "Histórico
      importado do WhatsApp Business", sem status de entrega.
- [ ] Abrir a conversa chama `POST /conversations/{id}/read` uma vez e zera o contador dela.
- [ ] Mensagens antigas carregam ao rolar para cima (`before=`), sem pular a posição de leitura.

### Composer

- [ ] Modo `ai`: travado com "A IA está respondendo. Assuma a conversa para digitar." + botão
      **Assumir**. Modo `waiting_human`: idem, com "Aguardando alguém da equipe". Modo `human` com
      outro responsável: "Com <nome>" + **Assumir**. Sem `conversation:reply`: não aparece.
- [ ] Modo `human` comigo e janela aberta: texto (Enter envia, Shift+Enter quebra linha, até 4096),
      anexo de imagem/documento (16 MB) e respostas rápidas. A mensagem aparece na hora como
      `queued` (atualização otimista: é o único ponto da feature com ela) e é substituída pela
      resposta do servidor.
- [ ] Janela fechada (`window_expires_at` no passado): o campo de texto dá lugar a "Fora da janela
      de 24 h — envie um modelo aprovado" + seletor de modelos `approved` com os campos das variáveis
      preenchidos com o que se sabe (nome do cliente). Faltando 1 h para fechar, um aviso discreto.
- [ ] Cliente com opt-out, conforme `opt_out_scope` (Q-S12-2): `marketing` → "Este cliente pediu
      para não receber promoções (lembretes continuam)"; `all` → "Este cliente pediu para não receber
      mensagens da barbearia". Responder dentro da janela continua permitido (é conversa iniciada por
      ele). A pergunta automática do SAIR (botões "Só promoções" / "Tudo") e a resposta do cliente
      aparecem na thread como mensagens de sistema/botão.
- [ ] Erros do backend (`409` janela/assumir, `402` plano) aparecem acima do composer com a
      mensagem do `detail`.

### Ficha ao lado

- [ ] Mostra o cliente ligado: nome, telefone, unidade, barbeiro habitual, clube/pacote, ticket
      médio, faltas e os últimos atendimentos — a partir do que a S13 expõe (componente exportado
      pelo `index.ts` de `customers`). Até a S13 existir, mostra nome, telefone e **Ver ficha**.
- [ ] "Trocar cliente" (com `conversation:reply`): busca de clientes e `PUT /conversations/{id}/client`.

### Conexão do WhatsApp (`/app/configuracoes/whatsapp`)

- [ ] Só com `tenant:configure`. Sem o recurso no plano (`402`): tela de upgrade em vez do botão.
- [ ] Sem número: explicação curta ("Seu WhatsApp continua no celular; as conversas passam a
      aparecer também no painel"), requisitos (app WhatsApp Business atualizado, acesso ao Facebook
      da empresa) e **Conectar WhatsApp**: carrega o SDK JS da Meta com o `GET /whatsapp/signup-config`,
      abre o Embedded Signup em modo coexistência e envia `code`, `waba_id` e `phone_number_id` ao
      backend. Cancelado pelo usuário: volta ao estado inicial sem erro. Aviso fixo (PD-28): "As
      mensagens que a barbearia inicia (lembretes, campanhas) são cobradas pela Meta no cartão que
      você cadastrar na conta do WhatsApp; o Navalha só mostra uma estimativa."
- [ ] Com números (PD-42): **lista de números**, cada um com telefone, nome verificado, status
      (Conectado / Desconectado / Erro com a mensagem), qualidade, destino — "Geral (toda a
      barbearia)" ou a unidade (seletor, quando a barbearia tem mais de uma; unidades que já têm número
      e a opção "Geral" quando já existe um ficam desabilitadas) — e **Desconectar** (confirmação: "As
      conversas continuam no painel; novas mensagens deixam de chegar").
- [ ] Uso do limite: "N de M números" (`whatsapp_numbers`, do plano — S15). **Conectar outro número**
      (escolhendo a unidade) só aparece com vaga; no limite, o botão vira o aviso de upgrade do plano, e
      um `402 plan_limit_reached` vindo do backend mostra o mesmo aviso. `409` (unidade já tem número,
      já há número geral) mostra o `detail`.
- [ ] Lista de **modelos de mensagem** com nome legível, categoria, status (Em análise / Aprovado /
      Rejeitado com o motivo) e "Atualizar status". Criar modelo de campanha fica na S12.

## Telas e fluxos

| Rota | Tela | Fluxos |
|---|---|---|
| `/app/conversas?fila=&q=&c=<id>` | `features/conversations/pages/InboxScreen.tsx` | `pages/list/`, `pages/thread/`, `pages/composer/`, `pages/client-panel/` |
| `/app/configuracoes` | `features/settings/pages/SettingsScreen.tsx` (lista de seções, como Cadastros) | — |
| `/app/configuracoes/whatsapp` | `features/settings/pages/WhatsappSettingsScreen.tsx` | `pages/whatsapp/` (conexão, número, modelos) |

A conversa aberta vai para a URL (`?c=`), para o link "abrir conversa" de outras telas (ficha do
cliente, alerta de avaliação baixa) e para o celular (lista e conversa viram telas separadas abaixo
de 768 px).

## Data Contract

Contrato completo no espelho do backend. Endpoints consumidos:

```text
GET  /conversations · /conversations/counts · /conversations/{id}
GET  /conversations/{id}/messages · /conversations/{id}/messages/{mid}/media
POST /conversations/{id}/messages · /assume · /return-to-ai · /resolve · /read · /uploads
PUT  /conversations/{id}/client
GET  /whatsapp/signup-config · /whatsapp/numbers · /whatsapp/templates
POST /whatsapp/numbers · /whatsapp/templates/sync
PATCH/DELETE /whatsapp/numbers/{id}
GET  /clients?q=   (trocar cliente) · GET /tenant/units
GET  uso do plano (S15, `frontend-plan-limits`) para `whatsapp_numbers` (used/max)
```

Arquivos:

```text
features/conversations/model/conversations.types.ts   Conversation, Message, Queue… (substitui os tipos do mock)
features/conversations/model/inbox.rules.ts           modo → estado do composer, janela, agrupamento por dia, rótulos
features/conversations/api/conversations.api.ts       · conversations.queries.ts
features/conversations/api/conversations.mock.ts      apagado
features/settings/model/whatsapp.types.ts · api/whatsapp.api.ts · whatsapp.queries.ts
features/settings/model/metaSdk.ts                    carrega o SDK da Meta e embrulha o Embedded Signup em Promise
```

## Estado

| Estado | Onde |
|---|---|
| Lista, contadores, conversa, mensagens, números, modelos | TanStack Query (`['conversations', fila, q, unidade]`, `['conversation', id]`, `['messages', id]` infinita, `['conversation-counts']`, `['whatsapp-numbers']`, `['whatsapp-templates']`) com `refetchInterval` |
| Fila, busca, unidade, conversa aberta | URL |
| Texto do composer | local, com rascunho por conversa em `sessionStorage` (não perde ao trocar de conversa) |
| Mensagem sendo enviada | cache do TanStack Query (otimista) |

## Permissões

| Ação | Permissão em `/auth/me` |
|---|---|
| ver Conversas na navegação e a Central | `conversation:read` |
| assumir, responder, devolver, resolver, trocar cliente | `conversation:reply` |
| ver Configurações → WhatsApp, conectar, desconectar | `tenant:configure` |

O barbeiro (`conversation:read` com `own`) vê a Central só leitura, sem composer nem ações.

## Acceptance Criteria

- [ ] Mock apagado; ISS do mock da Central fechada; tipos espelham o `openapi.json` congelado.
- [ ] Feature `settings` criada com `index.ts` + `api/ model/ pages/ ui/`, rota e item "Configurações"
      na barra lateral (visível com `tenant:configure`).
- [ ] O SDK da Meta é o único script externo; a origem dele entra na política de CSP e no README.
- [ ] Testes em `tests/`: estado do composer por modo/janela/permissão; agrupamento por dia;
      rótulos de autor e status; rótulos de `handoff_reason` (inclui `sale` e `no_ai_credits`);
      aviso de opt-out por `opt_out_scope`; cálculo de "janela fecha em" e de "IA volta em" (12 h do
      celular); destinos disponíveis no seletor de unidade do número (um geral, um por unidade);
      máscara/formatação de telefone internacional na lista.
- [ ] Tela conferida no navegador com a barbearia `demo`: fila, assumir, responder, devolver,
      janela fechada com modelo, áudio com transcrição, imagem, falha de envio, celular (< 768 px).
- [ ] `make docs-api` regenerado; `README.md` e `memory/progress.md` atualizados.
- [ ] Testes em `tests/` cobrindo as regras puras da feature
- [ ] Tela conferida no navegador (estados vazio, carregando, erro)
- [ ] `make check-frontend` verde

## Dependencies

- Backend: `⚪draft_messaging-whatsapp-inbox.md` implementado e congelado no `openapi.json`.
- `customers` (S13, `⚪draft_frontend-client-profile.md`): componente de ficha resumida exportado
  pelo `index.ts`; sem ele, a ficha mostra o mínimo.
- `⚪draft_frontend-assistant-settings.md` (S11) e `⚪draft_frontend-automations.md` (S12) usam a
  mesma feature `settings`.
- App da Meta com Embedded Signup (`config_id`) configurado pela plataforma.

## Notes

- ✅ Perguntas em aberto que mudam a tela estão no backend: **Q-S10-2** (número por unidade muda o
  seletor de unidade e a lista de números) e **Q-S10-4** (o que a etiqueta "pelo celular" faz com o
  modo).
  > Resolvido em 2026-11-06: Q-S10-2 — um número geral e, opcionalmente, um por unidade, limitado
  > por `whatsapp_numbers`; a tela vira lista de números com destino e uso do limite (PD-42).
  > Q-S10-4 — resposta pelo celular pausa a IA até 12 h sem mensagem da equipe e depois a conversa
  > se resolve sozinha; a thread mostra o aviso com a hora prevista (ROADMAP §7). Q-S10-1 — a
  > barbearia paga a Meta no início; a tela de conexão avisa (PD-28). Q-S10-3 — histórico do app
  > importado e ligado só a clientes existentes (ROADMAP §7).
- Respostas rápidas: nesta versão, lista fixa por barbearia guardada no navegador; cadastro de
  respostas rápidas no servidor fica para depois.
- SSE/WebSocket, notificação do navegador e som ficam para depois (PD-18 não pede push).
