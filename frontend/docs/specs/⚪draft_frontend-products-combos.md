# Cadastros de produtos, combos e formas de pagamento

**Priority:** high
**Status:** draft
**Espelho no backend:** `backend/docs/specs/⚪draft_catalog-products-combos.md`

## Overview

Três páginas novas em Cadastros (`/app/cadastros/*`, feature `registry`), no mesmo padrão de
Barbeiros e Serviços: **Produtos**, **Combos** e **Formas de pagamento**. A lista de cadastros
(`registry.constants.ts`) troca "Clubes e combos" + "Planos" pelo menu de PD-09. Regras, contrato e
erros estão no espelho do backend; aqui fica o que é de tela.

## Decisões de produto já tomadas

| Parâmetro | Valor |
|---|---|
| PD-09 | Cadastros: Unidades, Barbeiros, Serviços, **Produtos**, **Combos**, **Clubes**, **Pacotes**, **Formas de pagamento**. Clubes e Pacotes ficam "em breve" até S07. |
| PD-11 | Produto sem estoque: nenhuma coluna ou campo de quantidade. |
| Padrão de tela | O de `✅active_frontend-registry-basic-crud.md`: lista + formulário em painel abaixo, apagar com confirmação e `409` → "Inativar", quatro estados da lista. |

## Business Rules

### Lista de cadastros

- [x] `REGISTRY_PAGES` na ordem acima; `clubes` e `pacotes` com `ready: false`; chave `planos`
      some (link antigo `/app/cadastros/planos` volta para a lista). *(Feito em 2026-11-06 junto com o
      dropdown "Cadastros" da sidebar; as páginas ainda mostram "em breve".)*
- [x] Produtos, Combos e Formas de pagamento com `permission: 'catalog:read'`.

### Produtos (`/app/cadastros/produtos`)

- [ ] Tabela: nome, categoria, preço, comissão ("10%" ou "Padrão" quando `null`), status.
- [ ] Filtros na URL: busca por nome, categoria, status.
- [ ] Formulário: nome, categoria (texto com sugestões de `GET /products/categories`), descrição,
      preço (reais → centavos), comissão própria (opcional; vazio = "usa o padrão de produto",
      com link para Regras de comissão quando o usuário tem `finance:read`), ativo.

### Combos (`/app/cadastros/combos`)

- [ ] Tabela: nome, itens ("Corte + Barba + Pomada"), preço, preço de tabela riscado, economia,
      duração (soma dos serviços), status.
- [ ] Formulário: nome, descrição, itens (seletor de serviço ou produto ativo + quantidade, até 10,
      remover), preço do combo. Mostra em tempo real o preço de tabela e a economia; economia
      negativa mostra aviso "O combo está mais caro que os itens separados" (não bloqueia).
- [ ] Validação local: pelo menos dois itens no total ou um serviço; sem item repetido (somar
      quantidade em vez de repetir linha).
- [ ] Item inativo num combo existente aparece com o selo "Inativo".
- [ ] Combo com `bookable = true` (só serviços) mostra o selo "Aparece no agendamento" na tabela e
      no formulário (Q-S05-1); ao incluir um produto, o formulário avisa "Combos com produto só
      aparecem na comanda".

### Formas de pagamento (`/app/cadastros/formas-de-pagamento`)

- [ ] Tabela na ordem de exibição: nome, tipo ("Dinheiro", "Pix", "Débito", "Crédito",
      "Transferência", "Outro"), taxa ("1,99% + R$ 0,30"), parcelas ("até 12x"), status.
      Botões subir/descer alteram `sort_order` (sem arrastar).
- [ ] Formulário: nome, tipo, taxa %, taxa fixa (R$), e só para crédito: máximo de parcelas e a
      tabela "taxa por parcela" (2x…Nx, vazio = usa a taxa base).
- [ ] Simulador no formulário: "Num pagamento de R$ 100,00 em 3x, a taxa é R$ 4,79" — mesma conta
      do backend (função pura testada). Ajuda fixa: "A taxa é da barbearia; o cliente paga o preço
      da tabela" (Q-S05-2) — sem campo de acréscimo.
- [ ] `409` de "forma em dinheiro" aparece no campo tipo.
- [ ] Sem nenhuma forma ativa, a lista mostra o aviso "Sem forma de pagamento ativa a comanda não
      fecha".

### Comuns

- [ ] Escrever só com `catalog:write` **e** todas as unidades (mesma regra de Serviços); sem isso,
      só leitura.

## Telas e fluxos

| Rota | Tela | Fluxos |
|---|---|---|
| `/app/cadastros/produtos` | `RegistryPageScreen` | `pages/products/` (lista, formulário) |
| `/app/cadastros/combos` | `RegistryPageScreen` | `pages/combos/` (lista, formulário, seletor de itens) |
| `/app/cadastros/formas-de-pagamento` | `RegistryPageScreen` | `pages/payment-methods/` (lista, formulário, simulador) |

## Data Contract

```text
GET /products · /products/categories · POST /products · GET/PATCH/DELETE /products/{id}
GET /combos · POST /combos · GET/PATCH/DELETE /combos/{id}
GET /payment-methods · POST /payment-methods · GET/PATCH/DELETE /payment-methods/{id}
GET /services (seletor de itens do combo — já existe)
```

```text
features/registry/model/catalog.types.ts       Product, Combo, ComboItem, PaymentMethod (+ inputs),
                                               PaymentMethodKind
features/registry/model/combo.rules.ts         preço de tabela, economia, validação dos itens
features/registry/model/paymentFee.rules.ts    taxa de um pagamento (espelha payment_fee_cents)
features/registry/model/*.rules.ts             validação dos formulários de produto e forma
features/registry/api/registry.api.ts          + chamadas novas
features/registry/api/registry.queries.ts      + ['products', filtros] ['combos'] ['payment-methods']
shared/text/percent.ts                         "1,99%" ↔ número (usado também por comissões)
```

`PaymentMethod`, `Product` e `Combo` são exportados pelo `index.ts` do `registry` (a comanda, S06,
usa os tipos e as queries).

## Estado

| Estado | Onde |
|---|---|
| Listas | TanStack Query (chaves acima); mutações invalidam a lista e `['combos']` quando um produto muda |
| Filtros | URL |
| Formulário, itens do combo em edição | estado local |

## Permissões

| Ação | Permissão em `/auth/me` |
|---|---|
| ver as três páginas | `catalog:read` |
| criar, editar, inativar, apagar, reordenar | `catalog:write` (e todas as unidades) |

## Acceptance Criteria

- [ ] `REGISTRY_PAGES` atualizado; links antigos redirecionam.
- [ ] Testes em `tests/`: economia do combo, validação de itens, `paymentFee` (percentual, fixo,
      parcela, teto), conversão de percentual, validações dos formulários.
- [ ] `make docs-api`: chamadas novas dentro do contrato.
- [ ] Tela conferida no navegador (vazio, carregando, erro, `409` de apagar → inativar).
- [ ] `make check-frontend` verde; `README.md` e `memory/progress.md` atualizados.

## Dependencies

- Backend: `⚪draft_catalog-products-combos.md` implementado e congelado no `openapi.json`.
- `✅active_frontend-registry-basic-crud.md` — padrão das páginas e `DeleteRecordDialog`.

## Notes

- Combo agendável (Q-S05-1): a agenda (S03), a IA e o link oferecem combos só de serviços; nesta
  tela muda só o selo "Aparece no agendamento".
- Perguntas de produto: ver Q-S05-1 e Q-S05-2 no espelho do backend.
  > Resolvido em 2026-11-06: Q-S05-1 = IA e link agendam só combos de serviços; Q-S05-2 = a
  > barbearia absorve a taxa do cartão, sem acréscimo no parcelado (ROADMAP §7).
