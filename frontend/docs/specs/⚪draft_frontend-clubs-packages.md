# Clubes e pacotes no painel

**Priority:** high
**Status:** draft
**Espelho no backend:** `backend/docs/specs/⚪draft_memberships-clubs-packages.md`

## Overview

Duas frentes. **Cadastro** (feature `registry`): as páginas Clubes e Pacotes saem do "em breve" em
`/app/cadastros/clubes` e `/app/cadastros/pacotes`. **Operação** (feature nova `memberships`):
`/app/assinaturas` com os assinantes, as **cobranças** a receber e os pacotes vendidos, e os
componentes que a comanda e a ficha do cliente usam — aplicar benefício num item, aderir ao clube,
vender pacote, cobrar mensalidade em aberto, cartão de benefícios do cliente. Regras e contrato no
espelho do backend; elegibilidade é sempre decidida pelo servidor.

## Decisões de produto já tomadas

| Parâmetro | Valor |
|---|---|
| PD-09 | Clube (ilimitado, N por ciclo e/ou desconto) e Pacote (N serviços, validade). |
| PD-10 | Sem gateway: a cobrança do ciclo é paga numa comanda; a tela leva até ela. |
| PD-22 | Clubes é recurso do plano: sem ele, a tela mostra o aviso de upgrade (`402`). |
| PD-35 | O modo de comissão de assinante é escolhido pela barbearia ao ligar a regra (tela de regras de comissão, S08); esta feature não define padrão. |
| PD-36 | Mensalidade vencida: tolerância configurável (padrão 5 dias), depois bloqueia o uso; nunca cancela sozinho. |
| PD-37 | A IA não vende: explica, registra o interesse e passa para a fila de humano; **a equipe fecha** a adesão ou o pacote aqui ou na comanda. Não há adesão "da IA". |
| Um clube por cliente | Trocar de clube = cancelar e aderir (T2 do backend). |

## Business Rules

### Cadastro de clubes (`/app/cadastros/clubes`)

- [ ] Tabela: nome, preço/mês, benefícios em texto ("Corte ilimitado · Barba 2x · 10% em
      produtos"), assinantes, "Vende online", status.
- [ ] Formulário em seções: dados (nome, descrição, preço, termos para o cliente, vende online,
      ativo); **benefícios** (linhas: "Inclui [serviço] [ilimitado | N por mês]" ou "Desconto de
      [%] em [serviço | produto | todos os serviços | todos os produtos]"); **regras de uso**
      (máx. por dia, por semana, intervalo mínimo em dias, dias da semana em chips seg–dom,
      unidades e barbeiros permitidos — vazio = todos).
- [ ] Prévia em texto do clube como a IA vai descrevê-lo (função pura, a mesma do cartão de
      benefícios).
- [ ] Mudar preço com assinantes pergunta o alcance (Q-S07-2): "Só para novos assinantes"
      (pré-selecionado) ou "Para todos a partir de [data]" — com o aviso de que os assinantes
      recebem a mensagem antes do próximo ciclo (`price_applies_to`, `price_effective_from`).

### Cadastro de pacotes (`/app/cadastros/pacotes`)

- [ ] Tabela: nome, itens ("4× Corte · 2× Barba"), preço, preço de tabela, validade, status.
- [ ] Formulário: nome, descrição, itens (serviço + quantidade), preço, validade em dias (atalhos
      30/60/90/180), vende online, ativo; mostra o valor por uso calculado.

### Assinaturas (`/app/assinaturas`)

- [ ] Abas na URL: **Assinantes**, **Cobranças**, **Pacotes**.
- [ ] Assinantes: cliente, clube, status (Ativo, Pendente, Em atraso, Bloqueado, Cancelamento em
      DD/MM, Cancelado), próximo vencimento. Filtros: status, clube, busca. "Nova adesão"
      (`client:write`). Sem selo nem filtro de origem "IA": a IA não cria adesão (PD-37); o
      interesse do cliente chega pela fila "aguardando humano" da Central de conversas (motivo
      "venda de clube/pacote", S10), e a equipe usa "Nova adesão" / "Vender pacote".
- [ ] Detalhe da adesão (`/app/assinaturas/:id`): dados, uso do ciclo atual por serviço
      ("Corte: 3 usados · ilimitado"), histórico de ciclos com comanda de pagamento, ações:
      Cobrar, Isentar (`finance:write`, com motivo), Cancelar (fim do ciclo ou agora, motivo),
      Desfazer cancelamento.
- [ ] Cobranças: ciclos pendentes, vencidas primeiro; soma no topo; "Cobrar" escolhe "Comanda
      aberta do cliente" (se existir) ou "Nova comanda" e navega para `/app/comandas/:id`.
- [ ] Pacotes: pacotes vendidos com saldo e validade; ações Prorrogar e Cancelar
      (`finance:write`).
- [ ] Configurações (diálogo, `finance:write`): tolerância de atraso em dias (padrão 5; depois
      dela o uso é sempre bloqueado, PD-36), "Bloquear já no atraso, sem tolerância" (desligado por
      padrão) e dias para cancelar adesão pendente não paga (padrão 7).

### Componentes exportados (usados por `sales` e `customers`)

- [ ] `BenefitPicker` (no item da comanda): pede `GET /clients/{id}/eligibility` ao abrir; mostra
      as opções ("Clube — incluso, restam 2", "Pacote Corte 4× — vence 12/12") e, quando o clube
      não se aplica, o motivo do servidor ("Fora dos dias do clube"). Aplicar/remover chama as rotas
      de benefício e devolve o controle para a comanda recarregar.
- [ ] `JoinClubDialog` e `SellPackageDialog` (recebem `clientId` e, da comanda, `ticketId`): criam
      a adesão/venda já com o item na comanda.
- [ ] `PendingChargeBanner` (comanda com cliente): "Mensalidade de novembro em aberto — R$ 99,00"
      com "Adicionar à comanda".
- [ ] `ClientBenefitsCard` (ficha do cliente, S13): clube, status, saldo e pacotes.
- [ ] `memberships` **não** importa `sales` (a comanda importa `memberships`); a navegação para a
      comanda usa o caminho literal.

## Telas e fluxos

| Rota | Tela | Fluxos |
|---|---|---|
| `/app/cadastros/clubes` | `registry` · `RegistryPageScreen` | `pages/clubs/` |
| `/app/cadastros/pacotes` | `registry` · `RegistryPageScreen` | `pages/packages/` |
| `/app/assinaturas` | `features/memberships/pages/MembershipsScreen.tsx` | `pages/members/`, `pages/charges/`, `pages/client-packages/`, `pages/settings/` |
| `/app/assinaturas/:id` | `MembershipScreen.tsx` | `pages/detail/` |

Sidebar: "Assinaturas" com `permission: 'client:read'`, escondida sem o recurso `memberships` no plano
(quando S15 expuser os recursos em `/auth/me`; até lá, a tela trata o `402`).

## Data Contract

```text
GET/POST /clubs · GET/PATCH/DELETE /clubs/{id}
GET/POST /packages · GET/PATCH/DELETE /packages/{id}
GET/POST /client-memberships · GET /client-memberships/{id} · POST .../cancel · .../undo-cancel
GET /membership-cycles · POST /membership-cycles/{id}/charge · /waive
DELETE /tickets/{ticket_id}/membership-charges/{cycle_id}
GET/POST /client-packages · GET /client-packages/{id} · POST .../extend · .../cancel
DELETE /tickets/{ticket_id}/package-sales/{client_package_id}
GET /clients/{id}/benefits · GET /clients/{id}/eligibility
POST/DELETE /tickets/{ticket_id}/items/{item_id}/benefit
GET/PUT /membership-settings
```

```text
features/registry/model/clubs.types.ts        Club, ClubBenefit, Package (+ inputs)
features/registry/model/clubs.rules.ts        validação, valor por uso, texto dos benefícios
features/memberships/model/memberships.types.ts  Membership, Cycle, ClientPackage, BenefitOption,
                                              Eligibility, ClientBenefits, MembershipStatus
features/memberships/model/memberships.rules.ts  rótulo/cor de status, "vence primeiro",
                                              descrição do uso do ciclo
features/memberships/api/memberships.api.ts · memberships.queries.ts
features/memberships/ui/                      BenefitPicker, JoinClubDialog, SellPackageDialog,
                                              PendingChargeBanner, ClientBenefitsCard
```

O texto dos benefícios ("Corte ilimitado · 10% em produtos") é uma função pura em
`registry/model/clubs.rules.ts`, exportada pelo `index.ts` do `registry` e usada pelo cartão.

## Estado

| Estado | Onde |
|---|---|
| Cadastros, adesões, ciclos, pacotes, benefícios | TanStack Query (`['clubs']`, `['packages']`, `['memberships', filtros]`, `['membership', id]`, `['membership-cycles', filtros]`, `['client-benefits', clientId]`, `['eligibility', ...]`); aplicar benefício invalida `['ticket', id]` e `['client-benefits', clientId]` |
| Aba, filtros | URL |
| Formulários, benefícios em edição | estado local |

## Permissões

| Ação | Permissão em `/auth/me` |
|---|---|
| ver cadastros de clube/pacote | `catalog:read` |
| editar cadastros | `catalog:write` + todas as unidades |
| ver Assinaturas, benefícios do cliente | `client:read` |
| aderir, cancelar adesão, vender pacote | `client:write` |
| ver/cobrar cobranças, aplicar benefício | `ticket:read` / `ticket:write` |
| isentar, prorrogar/cancelar pacote, configurações | `finance:write` |

## Acceptance Criteria

- [ ] `REGISTRY_PAGES`: `clubes` e `pacotes` com `ready: true`.
- [ ] Feature `memberships` com `index.ts` + `api/ model/ pages/ ui/`; rotas no `router.tsx`.
- [ ] Testes em `tests/`: texto dos benefícios, valor por uso do pacote, rótulos de status, pacote
      que vence primeiro, validação do formulário de clube (included × discount).
- [ ] `402` mostra o aviso de upgrade em vez do erro genérico.
- [ ] `make docs-api` dentro do contrato.
- [ ] Tela conferida no navegador: criar clube com regras, aderir na comanda e usar no mesmo
      atendimento, cobrar mensalidade em atraso, vender e consumir pacote, cancelar adesão.
- [ ] `make check-frontend` verde; `README.md` e `memory/progress.md` atualizados.

## Dependencies

- Backend `⚪draft_memberships-clubs-packages.md` implementado e congelado.
- `⚪draft_frontend-tickets.md` — a comanda usa `BenefitPicker`, os diálogos e o banner.
- `⚪draft_frontend-products-combos.md` — seletores de serviço e produto.
- S13 frontend (ficha do cliente) usa `ClientBenefitsCard`.

## Notes

- Perguntas de produto: Q-S07-1 a Q-S07-4 no espelho do backend.
  > Resolvido em 2026-11-06: Q-S07-1 — tolerância de 5 dias e depois bloqueia, nunca cancela
  > (PD-36); Q-S07-2 — o dono escolhe o alcance do reajuste, "só novos" pré-selecionado
  > (ROADMAP §7); Q-S07-3 — a IA não vende, faz handoff e a equipe fecha (PD-37); Q-S07-4 —
  > pacote vencido perde o saldo, prorrogação manual (ROADMAP §7).
- Página pública do clube (link de adesão) ficou fora: dependia de Q-S07-3 = 2, e a PD-37 tirou a
  venda pelos canais do cliente.
