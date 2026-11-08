# Comanda no painel

**Priority:** high
**Status:** draft
**Espelho no backend:** `backend/docs/specs/⚪draft_sales-tickets.md`

## Overview

Feature nova `sales`: a recepção abre a comanda **a partir do agendamento** (botão no modal da
agenda) ou **avulsa** ("Nova comanda"), ajusta itens, barbeiros, descontos e gorjeta, aplica clube
ou pacote do cliente e **fecha** registrando uma ou várias formas de pagamento, com troco. Comanda
fechada é só leitura; corrigir é estornar (e "Abrir cópia"). Regras, cálculos e contrato estão no
espelho do backend — **os totais vêm sempre do servidor**; o painel só calcula o que ainda não foi
enviado (o que falta pagar e o troco, no diálogo de fechamento).

## Decisões de produto já tomadas

| Parâmetro | Valor |
|---|---|
| PD-05 | Comanda do agendamento traz um item por serviço, cada um com o seu barbeiro. |
| PD-10 | Sem gateway: "pagar" é registrar a forma e o valor recebidos fora (maquininha, Pix, dinheiro). |
| PD-09 / PD-11 | Vende serviço, produto e combo; produto sem estoque. Clube e pacote são aplicados por item (S07). |
| PD-38 | Gorjeta por barbeiro, fora da receita, repassada integral; a barbearia absorve a taxa do cartão sobre ela. |
| Fechada | Imutável; estorno com motivo; "Abrir cópia" a partir da estornada. |

## Business Rules

### Lista (`/app/comandas`)

- [ ] Abas na URL: **Abertas** (padrão), **Fechadas**, **Estornadas**. Filtros: unidade (a da
      sessão por padrão), período, cliente, barbeiro.
- [ ] Linha: número, cliente (ou "Cliente não identificado"), barbeiros (iniciais), total, hora
      de abertura ou fechamento. Aberta há mais de um dia ganha o selo "Desde DD/MM".
- [ ] "Nova comanda" (com `ticket:write`) abre a avulsa na unidade selecionada e navega para ela.

### Abrir pela agenda

- [ ] O modal de agendamento (feature `scheduling`) mostra "Abrir comanda" quando o agendamento não
      foi cancelado nem marcado como falta, ou "Ver comanda #N" quando já tem uma. O botão vem do
      `index.ts` de `sales` (`OpenTicketButton`).
- [ ] `409` "já tem a comanda #N" navega para a comanda existente.

### Comanda aberta (`/app/comandas/:id`)

- [ ] Cabeçalho: número, unidade, cliente (trocar/escolher com a busca de clientes da feature
      `customers`), agendamento de origem, observações.
- [ ] Itens: nome, barbeiro (seletor só com barbeiros da unidade que fazem o serviço), quantidade
      (produto), preço, desconto, líquido. Combo aparece como grupo com os componentes recuados;
      remover o grupo remove os componentes.
- [ ] Adicionar item: uma busca única por serviço, produto ou combo ativo; serviço sem barbeiro
      fica destacado "Escolha o barbeiro".
- [ ] Desconto de item e da comanda: valor ou %, com motivo obrigatório (diálogo).
- [ ] Benefício: com cliente identificado, cada item elegível mostra "Usar clube" / "Usar pacote"
      (componente `BenefitPicker` do `index.ts` de `memberships`, S07); item com benefício mostra
      o selo e "Remover benefício". Sem a feature de clubes no plano, nada aparece.
- [ ] Itens de mensalidade e de venda de pacote aparecem com selo e só saem pelo "Remover" deles
      (rota do `memberships`).
- [ ] Gorjeta (PD-38): "Adicionar gorjeta" por barbeiro que está na comanda; aparece separada
      dos totais da receita ("vai integral para o barbeiro"), somando só ao "a pagar".
- [ ] Totais do servidor: subtotal, descontos, total, gorjeta, a pagar.
- [ ] Toda alteração usa a resposta (`TicketOut`) para atualizar o cache — sem refetch extra.

### Fechar

- [ ] Diálogo de pagamento: botões das formas ativas (ordem do cadastro); cada clique adiciona uma
      linha com o **valor que falta**; o valor é editável; crédito com seletor de parcelas (até o
      máximo da forma); dinheiro com "Valor recebido" e o troco calculado.
- [ ] Rodapé: a pagar, pago, falta / troco. "Fechar comanda" só habilita com falta = 0. Total zero
      (tudo coberto por benefício) fecha sem pagamento.
- [ ] Campo opcional "Código da maquininha" (NSU) por linha de cartão.
- [ ] `409` do caixa ("Abra o caixa da unidade antes de receber"): mensagem com botão "Abrir caixa"
      (link para `/app/financeiro/caixa`) quando o usuário tem `cash:operate`.
- [ ] Depois de fechar: a comanda vira leitura, com os pagamentos e o troco em destaque.

### Estornar

- [ ] Aberta: "Descartar comanda" (com `ticket:write`), motivo obrigatório.
- [ ] Fechada: "Estornar" só com `finance:write`; o diálogo avisa que o caixa de hoje registrará a
      devolução e que comissões e uso de clube/pacote serão revertidos. Depois: "Abrir cópia".

## Telas e fluxos

| Rota | Tela | Fluxos |
|---|---|---|
| `/app/comandas` | `features/sales/pages/TicketsScreen.tsx` | `pages/list/` |
| `/app/comandas/:id` | `features/sales/pages/TicketScreen.tsx` | `pages/detail/` (itens, descontos, gorjeta), `pages/close/` (pagamento), `pages/void/` |
| modal da agenda | `features/scheduling` | usa `OpenTicketButton` de `sales` |

Sidebar: entrada "Comandas" (ícone novo `comanda`) depois de "Agenda", com `permission:
'ticket:read'` (filtro de navegação por permissão: S18/ISS-005).

## Data Contract

```text
GET  /tickets (status, unit_id, date_from, date_to, client_id, barber_id, appointment_id,
               limit, offset)
POST /tickets · GET/PATCH /tickets/{id}
POST /tickets/{id}/items · PATCH/DELETE /tickets/{id}/items/{item_id}
PUT  /tickets/{id}/tips · POST /tickets/{id}/close · POST /tickets/{id}/void
GET  /products · /combos · /services · /payment-methods · /barbers   (via registry)
GET  /clients?q=                                                      (via customers)
```

```text
features/sales/model/sales.types.ts       Ticket, TicketItem, TicketPayment, TicketSummary,
                                          Discount, TicketStatus (espelham o openapi.json)
features/sales/model/paymentSplit.rules.ts falta, troco, linha nova com o restante, validação
features/sales/model/ticketItems.rules.ts  agrupamento de combo, barbeiros elegíveis por serviço,
                                          "item precisa de barbeiro"
features/sales/api/sales.api.ts · sales.queries.ts   ['tickets', filtros] ['ticket', id]
features/sales/ui/OpenTicketButton.tsx    exportado para a agenda
features/sales/index.ts                   TicketsScreen, TicketScreen, OpenTicketButton
```

## Estado

| Estado | Onde |
|---|---|
| Comanda e listas | TanStack Query; mutação grava o `TicketOut` em `['ticket', id]` e invalida `['tickets']` |
| Aba e filtros | URL |
| Linhas de pagamento em edição | estado local do diálogo (`useReducer`) |
| Unidade padrão | `useUnitSelection()` da feature `auth` |

## Permissões

| Ação | Permissão em `/auth/me` |
|---|---|
| ver Comandas | `ticket:read` (barbeiro vê só as dele — o backend filtra) |
| abrir, editar, fechar, descartar | `ticket:write` |
| estornar fechada | `finance:write` |
| atalho "Abrir caixa" | `cash:operate` (permissão nova do S09) |

## Acceptance Criteria

- [ ] Feature `sales` com `index.ts` + `api/ model/ pages/ ui/`; rotas no `router.tsx`.
- [ ] Testes em `tests/`: divisão de pagamento (falta, troco, só dinheiro tem troco, parcelas),
      agrupamento de combo, barbeiros elegíveis.
- [ ] `make docs-api` com as chamadas novas dentro do contrato.
- [ ] Tela conferida no navegador: comanda da agenda com dois barbeiros, avulsa com produto,
      combo, desconto, pagamento em três formas com troco, estorno e cópia, `409` do caixa.
- [ ] `make check-frontend` verde; `README.md` e `memory/progress.md` atualizados.

## Dependencies

- Backend `⚪draft_sales-tickets.md` implementado e congelado.
- `⚪draft_frontend-products-combos.md` (produtos, combos, formas de pagamento no `registry`).
- S03 frontend (`frontend-agenda`): modal real de agendamento, onde entra o `OpenTicketButton`.
- S07 frontend: `BenefitPicker` (até lá, a comanda funciona sem benefícios).

## Notes

- Comanda no celular (barbeiro) é só leitura e entra no layout de S18.
- Recibo para imprimir/enviar no WhatsApp: fora (ver Notes do backend).
- Perguntas de produto: Q-S06-1 a Q-S06-4 no espelho do backend.
  > Resolvido em 2026-11-06: Q-S06-1 — gorjeta por barbeiro, repassada integral, taxa absorvida
  > pela barbearia (PD-38); Q-S06-2 — desconto livre com motivo; Q-S06-3 — sem "fiado"; Q-S06-4 —
  > só `finance:write` estorna fechada (ROADMAP §7). A tela acima já segue essas respostas.
