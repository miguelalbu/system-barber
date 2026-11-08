# Comissões no painel: regras, fechamento e "minhas comissões"

**Priority:** high
**Status:** draft
**Espelho no backend:** `backend/docs/specs/⚪draft_commissions-rules-closing.md`

## Overview

Três telas na feature `finance`: **Regras de comissão** (as quatro regras de PD-13 e as exceções
por serviço/barbeiro), **Comissões** (quanto cada barbeiro tem a receber, de onde veio cada
centavo, fechar o período e marcar como pago) e **Minhas comissões** (o barbeiro, no celular, vê
os próprios lançamentos e acertos — PD-26). Regras de cálculo e contrato no espelho do backend; o
painel nunca calcula comissão, só mostra o livro-razão.

Esta spec também transforma `/app/financeiro` (hoje placeholder) num **índice** com as páginas do
financeiro visíveis por permissão — Caixa, Despesas e Resultado chegam com S09.

## Decisões de produto já tomadas

| Parâmetro | Valor |
|---|---|
| PD-12 | Barbeiro só comissionado. |
| PD-13 | Quatro regras ligáveis e ajustáveis; prioridade barbeiro × serviço > serviço > % padrão do barbeiro. |
| PD-14 | Sem vales/adiantamentos no fechamento. |
| PD-26 | "Minhas comissões" no painel responsivo do barbeiro. |
| PD-35 | Comissão de assinante: a barbearia escolhe o modo ao ligar a regra (rateio, fixo por atendimento, % da tabela ou sem comissão). Sem padrão: nada vem pré-selecionado. |
| PD-38 | Gorjeta repassada integral, sem desconto da taxa do cartão (a barbearia absorve). |
| Transparência | O barbeiro vê base, percentual e regra de cada lançamento. |

## Business Rules

### Índice do financeiro (`/app/financeiro`)

- [ ] Lista de páginas, como em Cadastros: Caixa (`cash:operate`), Despesas (`finance:read`),
      Resultado do mês (`finance:read`), Comissões (`commission:read` com escopo `all`/`unit`),
      Regras de comissão (`finance:read`). Página sem permissão não aparece; página ainda não
      implementada mostra "Em breve".
- [ ] Sidebar: "Financeiro" aparece se o usuário tem qualquer uma dessas; "Minhas comissões"
      aparece se `commission:read` tem escopo `own` (lido de `me.permissions`).

### Regras de comissão (`/app/financeiro/comissoes/regras`)

- [ ] Quatro blocos, um por regra, cada um com liga/desliga e os campos dele:
      1. Exceção por serviço (a tabela de exceções abaixo fica cinza quando desligada);
      2. Descontar a taxa do cartão;
      3. Comissão sobre produto + % padrão de produto;
      4. Atendimento de assinante (PD-35): quatro opções em rádio, **nenhuma pré-selecionada**
         na primeira configuração — "Sem comissão" (regra desligada), "Rateio da mensalidade",
         "Valor fixo por atendimento" (+ valor fixo padrão, obrigatório) e "% sobre o preço de
         tabela". Escolher uma das três últimas liga a regra com o modo; salvar com a regra ligada
         e sem modo é bloqueado no formulário (e o `422` do backend vira mensagem no campo). Cada
         modo com uma frase de exemplo ("Mensalidade R$ 100, dois cortes com o João e um com o
         Pedro…"). Com clubes cadastrados e a regra nunca configurada, o bloco mostra "Escolha
         como pagar o atendimento de assinante — hoje ele não gera comissão".
- [ ] Mais: "Desconto reduz a base da comissão" e "Sugerir fechamento" (semanal, quinzenal, mensal).
- [ ] Tabela de exceções: linha por serviço; colunas "% para todos", "Fixo assinante" e, expandindo
      a linha, uma linha por barbeiro com o % dele. Vazio = herda. A célula mostra em cinza o valor
      herdado ("40% — padrão do barbeiro").
- [ ] Salvar envia o conjunto inteiro (`PUT`) e avisa "Vale para as próximas comandas; o que já foi
      lançado não muda".
- [ ] Editar exige `finance:write` e todas as unidades; senão, leitura.

### Comissões (`/app/financeiro/comissoes`)

- [ ] Período na URL (padrão: o sugerido pela configuração, ex. mês corrente) e unidade.
- [ ] Resumo por barbeiro: em aberto, em fechamento, pago; quebra em serviços, produtos,
      assinantes, gorjetas (integrais, PD-38), ajustes, estornos. Total geral no topo.
- [ ] Clicar no barbeiro abre os lançamentos (paginados): data, comanda (link), cliente, item,
      regra em texto ("Exceção do serviço"), base, % ou fixo, valor; estorno em vermelho com link
      para o original; ajuste manual com o motivo.
- [ ] "Novo ajuste" (com `finance:write`, Q-S08-2): barbeiro, data, valor positivo ou negativo e
      motivo obrigatório; texto de apoio "Ajuste não é vale nem adiantamento".
- [ ] "Fechar até [data]" (com `finance:write`): escolhe barbeiros (todos com saldo por padrão),
      mostra a prévia dos totais e confirma; o resultado lista os fechamentos criados.
- [ ] Aba "Fechamentos": lista com status; abrir um mostra os lançamentos; "Marcar como pago"
      (data e observação) e "Desfazer" (só não pago). Fechamento negativo aparece em destaque.
- [ ] Imprimir/exportar o fechamento (PDF/CSV) fica fora; o detalhe tem layout limpo para imprimir
      pelo navegador.

### Minhas comissões (`/app/minhas-comissoes`)

- [ ] Layout de celular primeiro: total a receber em aberto (grande), período, lista de lançamentos
      agrupada por dia, e a lista de acertos (fechados/pagos).
- [ ] Atendimento de assinante no modo rateio aparece como "Assinante — calculado no fim do ciclo"
      enquanto o ciclo não fecha (sem valor), para o barbeiro não achar que faltou.
- [ ] Sem filtros de barbeiro: o backend devolve só os dele.

## Telas e fluxos

| Rota | Tela | Fluxos |
|---|---|---|
| `/app/financeiro` | `features/finance/pages/FinanceScreen.tsx` (índice) | — |
| `/app/financeiro/comissoes` | `CommissionsScreen.tsx` | `pages/commissions/summary/`, `entries/`, `payouts/`, `close/` |
| `/app/financeiro/comissoes/regras` | `CommissionRulesScreen.tsx` | `pages/commission-rules/` |
| `/app/minhas-comissoes` | `MyCommissionsScreen.tsx` | `pages/my-commissions/` |

## Data Contract

```text
GET/PUT /commission-settings · GET/PUT /commission-rates
GET/POST /commissions/entries · GET /commissions/summary
GET/POST /commissions/payouts · GET/DELETE /commissions/payouts/{id} · POST .../{id}/pay
GET /services · /barbers   (tabela de exceções, via registry)
```

```text
features/finance/model/commissions.types.ts   CommissionSettings, CommissionRate, CommissionEntry,
                                              BarberSummary, Payout, SubscriberMode, CommissionRule
features/finance/model/commissionRules.rules.ts  valor herdado por célula, montagem do PUT,
                                              texto de cada regra/modo
features/finance/model/finance.constants.ts   páginas do índice (chave, rótulo, permissão)
features/finance/api/commissions.api.ts · commissions.queries.ts
```

## Estado

| Estado | Onde |
|---|---|
| Configurações, exceções, resumo, lançamentos, fechamentos | TanStack Query (`['commission-settings']`, `['commission-rates']`, `['commissions', 'summary', filtros]`, `['commissions', 'entries', filtros]`, `['payouts', filtros]`) |
| Período, unidade, barbeiro aberto, aba | URL |
| Formulário das regras e tabela de exceções em edição | estado local (`useReducer`), com aviso ao sair sem salvar |

## Permissões

| Ação | Permissão em `/auth/me` |
|---|---|
| ver Comissões | `commission:read` com escopo `all` ou `unit` |
| ver Minhas comissões | `commission:read` com escopo `own` |
| ver Regras | `finance:read` |
| editar Regras | `finance:write` + todas as unidades |
| fechar, pagar, desfazer, novo ajuste | `finance:write` |

## Acceptance Criteria

- [ ] `FinanceScreen` vira índice; rotas novas no `router.tsx`; sidebar com as duas entradas.
- [ ] Testes em `tests/`: valor herdado nas três camadas, montagem do `PUT` de exceções (vazio
      não vai), texto dos modos, regra 4 sem modo pré-selecionado e bloqueio de "ligada sem modo",
      agrupamento por dia.
- [ ] `make docs-api` dentro do contrato.
- [ ] Tela conferida no navegador como dono (regras, fechar, pagar) e como barbeiro no tamanho de
      celular (minhas comissões).
- [ ] `make check-frontend` verde; `README.md` e `memory/progress.md` atualizados.

## Dependencies

- Backend `⚪draft_commissions-rules-closing.md` implementado e congelado.
- `⚪draft_frontend-tickets.md` — link para a comanda de cada lançamento.
- S18 — layout de celular/PWA e filtro de navegação por permissão (esta tela funciona sem ele,
  mas fica melhor com ele).

## Notes

- Perguntas de produto (modo do assinante, ajuste manual, comissão de venda de clube): Q-S08-1 a
  Q-S08-3 no espelho do backend.
  > Resolvido em 2026-11-06: Q-S08-1 — a barbearia escolhe o modo ao ligar a regra, sem padrão
  > (PD-35); Q-S08-2 — "sim": ajuste manual com motivo, só `finance:write` (a tela ganhou "Novo
  > ajuste"); Q-S08-3 — sem comissão sobre venda de clube/pacote (ROADMAP §7).
