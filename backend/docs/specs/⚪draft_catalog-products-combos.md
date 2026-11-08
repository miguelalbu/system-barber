# Produtos, combos e formas de pagamento

**Priority:** high
**Status:** draft
**Espelho no frontend:** `frontend/docs/specs/⚪draft_frontend-products-combos.md`

## Overview

A comanda (S06) vende mais do que serviço: vende **produto** (pomada, shampoo, cerveja), vende
**combo** (Corte + Barba por um preço fechado) e recebe por **formas de pagamento** que custam taxa
(a maquininha cobra 1,99% no débito, 4,5% no crédito parcelado). Esta spec amplia o módulo
`catalog` com esses três cadastros. Eles são a matéria-prima da comanda, da regra de comissão
"desconta a taxa do cartão" (S08) e da conferência do caixa por forma de pagamento (S09).

Fica de fora: estoque (PD-11), preço por unidade (mesma regra de serviço, P4 da DEC-016), clubes e
pacotes (S07), gateway de pagamento (PD-10).

## Decisões de produto já tomadas

| Parâmetro | Valor |
|---|---|
| PD-09 | Combo = serviços **e** produtos juntos, preço fechado, vendido avulso. Menu Cadastros troca "Clubes e combos" + "Planos" por Clubes, Pacotes e Combos. |
| PD-10 | Sem gateway: forma de pagamento é só um **rótulo com taxa** para registrar o que foi recebido fora. Modelada para um provedor entrar depois. |
| PD-11 | Produto sem estoque: preço e comissão, sem quantidade em estoque. |
| PD-13 | Produto tem comissão (regra "comissão sobre produto", ligável em S08); a taxa da forma de pagamento alimenta a regra "desconta taxa do cartão". |
| DEC-016 P1, P4, P6 | Apagar só sem histórico (senão inativar); vale para todas as unidades; dinheiro em centavos. |

### Decisões técnicas desta spec

| # | Decisão | Por quê |
|---|---|---|
| T1 | Produto tem `commission_percent` **opcional**; `null` = usa o percentual padrão de produto configurado em S08. | Trinks e AppBarber trabalham assim: a maioria dos produtos segue o padrão, poucos têm comissão própria. |
| T2 | Combo guarda os componentes com quantidade; a comanda **rateia** o preço do combo entre os componentes proporcionalmente ao preço de tabela, sobra de arredondamento no componente mais caro. | Comissão, relatório por serviço e "desconta taxa" precisam de valor por item; rateio proporcional é o padrão do mercado e não depende de configuração. |
| T3 | Forma de pagamento tem `kind` fixo (enum) e nome livre. Taxa = `fee_percent` + `fee_fixed_cents`; crédito parcelado tem taxa por número de parcelas em tabela própria. | O caixa precisa saber o que é dinheiro (conta na gaveta); o nome livre deixa a barbearia ter "Crédito Stone" e "Crédito Cielo". |
| T4 | Quatro formas nascem com a barbearia (Dinheiro, Pix, Débito, Crédito), taxa zero, criadas pela migration nos schemas existentes e pelo provisionamento nos novos. | A comanda funciona no primeiro dia sem configuração. |
| T5 | `provider` (`manual` hoje) já existe na forma de pagamento. | Quando o gateway entrar, uma forma `provider = 'stone'` passa a gerar cobrança em vez de só registrar; nada muda na comanda. |
| T6 | Produto tem `category` em texto livre opcional (a tela sugere as já usadas), sem tabela de categorias. | Lista de produto de barbearia é curta; categoria serve para agrupar na comanda. Tabela entra se um relatório pedir. |

## Business Rules

### Produtos

- [ ] Campos: `name` (2–80), `description` (até 500, opcional), `category` (até 60, opcional),
      `price_cents` (0–10.000.000), `commission_percent` (0–100, duas casas, opcional — T1),
      `active`.
- [ ] Nome único sem diferença de maiúsculas (`lower(name)`): repetir é `409` "Já existe um
      produto com esse nome".
- [ ] Sem estoque (PD-11): nenhum campo de quantidade; vender nunca falha por falta de produto.
- [ ] Escrever exige `catalog:write` **e** todas as unidades (`403` "Produtos valem para todas as
      unidades"); ler exige `catalog:read`.
- [ ] Apagar com histórico (item de comanda ou componente de combo) → `409`, o caminho é inativar.
      Produto inativo não entra em combo novo nem em comanda nova; combos existentes que o usam
      continuam vendáveis com o snapshot da comanda.

### Combos

- [ ] Campos: `name` (2–80, único sem diferença de maiúsculas), `description` (até 500),
      `price_cents` (0–10.000.000), `active` e `items` (1–10 componentes).
- [ ] Componente: `kind` (`service` | `product`), `service_id` ou `product_id` (exatamente um, de
      acordo com o `kind`), `quantity` (1–10). Serviço repetido no mesmo combo vira uma linha só
      com `quantity` (`422` se vier duplicado).
- [ ] Combo precisa de pelo menos **um serviço ou dois itens** no total (combo de um produto só é
      produto com desconto): `422` "Um combo junta pelo menos dois itens".
- [ ] Componente inativo ou inexistente na criação/edição → `400` "Serviço não encontrado" /
      "Produto não encontrado" (inativo conta como não encontrado na criação).
- [ ] A resposta traz `list_price_cents` (soma do preço de tabela dos componentes × quantidade) e
      `savings_cents` (`list_price_cents − price_cents`, pode ser negativo; a tela avisa).
- [ ] `PUT` dos componentes substitui o conjunto inteiro (mesmo padrão de `barber_services`).
- [ ] Rateio do preço (T2) exposto como função pura no `public.py` (`allocate_combo_price`), para
      a comanda e os testes usarem a mesma conta.
- [ ] Mesmas regras de permissão, apagar e inativar dos produtos. Apagar um serviço ou produto que
      é componente de combo → `409` (o componente é referência com `RESTRICT`).
- [ ] **Combo agendável** (Q-S05-1): combo ativo **só de serviços** tem `bookable = true` (calculado,
      não é campo editável) e aparece para a IA e o link público com o preço fechado e
      `duration_minutes` (soma dos serviços × quantidade, na ordem dos componentes). Combo com
      produto só existe na comanda. `list_bookable_combos` no `public.py` devolve os agendáveis.

### Formas de pagamento

- [ ] Campos: `name` (2–60, único sem diferença de maiúsculas), `kind`
      (`cash` | `pix` | `debit_card` | `credit_card` | `bank_transfer` | `other`), `fee_percent`
      (0–100, duas casas), `fee_fixed_cents` (0–100.000), `max_installments` (1–24; só
      `credit_card` pode ser > 1), `active`, `sort_order` (ordem na comanda).
- [ ] Taxa por parcela (`installment_fees`): lista de `{installments 2..max_installments,
      fee_percent}`; parcela sem linha usa o `fee_percent` da forma. Linha acima de
      `max_installments` → `422`.
- [ ] Cálculo da taxa de um pagamento (função pura `payment_fee_cents` no `public.py`):
      `round_half_up(amount × percent / 100) + fee_fixed_cents`, nunca maior que o valor pago.
- [ ] A taxa é sempre **absorvida pela barbearia** (Q-S05-2): não existe acréscimo ao cliente no
      parcelado; o cliente paga o preço da tabela. A taxa só reduz o líquido (S08, S09).
- [ ] Só pode existir **uma** forma ativa com `kind = cash` (`409` "Já existe uma forma de
      pagamento em dinheiro"): o caixa (S09) conta a gaveta por ela.
- [ ] As quatro formas padrão (T4) podem ser renomeadas, ter taxa alterada e ser inativadas; não há
      forma "do sistema" intocável. Ficar sem nenhuma forma ativa é permitido (a comanda avisa).
- [ ] Mudar a taxa **não** recalcula pagamentos já registrados: a comanda guarda o snapshot.
- [ ] Apagar com pagamento registrado → `409`; inativar some da comanda nova.
- [ ] Escrever exige `catalog:write` + todas as unidades; ler, `catalog:read`.
- [ ] `provider` é só leitura nesta spec (sempre `manual`, T5).

## Data Contract

```text
# Produtos — módulo catalog, tag "catalog"
GET    /products?active=&category=&q=          → 200 ProductOut[]
POST   /products            ProductIn          → 201 ProductOut | 403 | 409 | 422
GET    /products/{id}                          → 200 ProductOut | 404
PATCH  /products/{id}       ProductUpdate      → 200 ProductOut | 403 | 404 | 409 | 422
DELETE /products/{id}                          → 204 | 403 | 404 | 409
GET    /products/categories                    → 200 string[]   (categorias em uso, para sugerir)

ProductIn     {name, description?, category?, price_cents, commission_percent?, active? = true}
ProductUpdate {name?, description?, category?, price_cents?, commission_percent?, active?}
ProductOut    {id, name, description, category, price_cents, commission_percent, active,
               created_at, updated_at}

# Combos
GET    /combos?active=                         → 200 ComboOut[]
POST   /combos              ComboIn            → 201 ComboOut | 400 | 403 | 409 | 422
GET    /combos/{id}                            → 200 ComboOut | 404
PATCH  /combos/{id}         ComboUpdate        → 200 ComboOut | 400 | 403 | 404 | 409 | 422
DELETE /combos/{id}                            → 204 | 403 | 404 | 409

ComboItemIn   {kind: service|product, service_id?, product_id?, quantity = 1}
ComboIn       {name, description?, price_cents, active? = true, items: ComboItemIn[1..10]}
ComboUpdate   {name?, description?, price_cents?, active?, items?}   (items substitui tudo)
ComboOut      {id, name, description, price_cents, active, list_price_cents, savings_cents,
               duration_minutes (soma dos serviços), bookable (só serviços e ativo), items: [{id, kind, service_id, product_id,
               name, quantity, unit_list_price_cents, active}], created_at, updated_at}

# Formas de pagamento
GET    /payment-methods?active=                → 200 PaymentMethodOut[]  (ordem sort_order, nome)
POST   /payment-methods     PaymentMethodIn    → 201 PaymentMethodOut | 403 | 409 | 422
GET    /payment-methods/{id}                   → 200 PaymentMethodOut | 404
PATCH  /payment-methods/{id} PaymentMethodUpdate → 200 | 403 | 404 | 409 | 422
DELETE /payment-methods/{id}                   → 204 | 403 | 404 | 409

PaymentMethodIn  {name, kind, fee_percent = 0, fee_fixed_cents = 0, max_installments = 1,
                  installment_fees?: [{installments, fee_percent}], sort_order = 0, active = true}
PaymentMethodOut {id, name, kind, provider, fee_percent, fee_fixed_cents, max_installments,
                  installment_fees[], sort_order, active, created_at, updated_at}

Erros novos: 400 "Serviço não encontrado" · "Produto não encontrado"
             403 "Produtos valem para todas as unidades" (mesma frase para combos e formas)
             409 "Já existe um produto|combo|forma de pagamento com esse nome"
             409 "Já existe uma forma de pagamento em dinheiro"
             409 "Este cadastro tem histórico; inative em vez de apagar"
             422 "Um combo junta pelo menos dois itens"
```

### Banco de dados

Migration de tenant `tNNNN_catalog_sales_items` (próxima revisão livre; expand only):

```text
products        id uuid pk · name varchar(80) · description varchar(500) null ·
                category varchar(60) null · price_cents integer check (>= 0) ·
                commission_percent numeric(5,2) null check (0..100) · active bool ·
                created_at · updated_at
                UNIQUE INDEX uq_product_name ON lower(name) · INDEX ix_product_category (category)

combos          id uuid pk · name varchar(80) · description varchar(500) null ·
                price_cents integer check (>= 0) · active bool · created_at · updated_at
                UNIQUE INDEX uq_combo_name ON lower(name)

combo_items     id uuid pk · combo_id → combos.id ON DELETE CASCADE ·
                kind combo_item_kind ('service','product') ·
                service_id → services.id ON DELETE RESTRICT null ·
                product_id → products.id ON DELETE RESTRICT null ·
                quantity smallint check (1..10)
                CHECK ck_combo_item_ref ((kind='service') = (service_id IS NOT NULL)
                                         AND (kind='product') = (product_id IS NOT NULL))
                UNIQUE (combo_id, service_id) · UNIQUE (combo_id, product_id)

payment_methods id uuid pk · name varchar(60) · kind payment_method_kind
                ('cash','pix','debit_card','credit_card','bank_transfer','other') ·
                provider varchar(30) default 'manual' · fee_percent numeric(5,2) check (0..100) ·
                fee_fixed_cents integer check (0..100000) ·
                max_installments smallint check (1..24) · sort_order smallint default 0 ·
                active bool · created_at · updated_at
                UNIQUE INDEX uq_payment_method_name ON lower(name)
                UNIQUE INDEX uq_payment_method_cash ON (kind) WHERE kind='cash' AND active
                CHECK ck_installments_credit (max_installments = 1 OR kind = 'credit_card')

payment_method_installment_fees
                id uuid pk · payment_method_id → payment_methods.id ON DELETE CASCADE ·
                installments smallint check (2..24) · fee_percent numeric(5,2) check (0..100)
                UNIQUE (payment_method_id, installments)
```

Dados: a migration insere as quatro formas padrão (T4) em cada schema; `bootstrap_tenant` não
precisa mudar porque o `tenant_template` já sai migrado com elas. Itens de comanda (S06) apontam
para `products`, `combos` e `payment_methods` com `ON DELETE RESTRICT`, o que faz valer o `409`.

## Permissões

Nenhuma permissão nova.

| Rota | Permissão | owner | manager | receptionist | barber |
|---|---|---|---|---|---|
| `GET` produtos, combos, formas | `catalog:read` | todos | todos | todos | todos |
| escrita em produtos, combos, formas | `catalog:write` + todas as unidades | sim | só se vê todas as unidades | — | — |

## Acceptance Criteria

- [ ] Tabelas, migration e seed das formas padrão; `alembic check` limpo.
- [ ] `catalog/public.py` exporta: `get_product`, `get_combo` (com componentes, `bookable` e
      `duration_minutes`), `list_bookable_combos`, `get_payment_method`, `allocate_combo_price`,
      `payment_fee_cents`.
- [ ] Testes de `allocate_combo_price` (rateio proporcional, arredondamento, componente de preço
      zero, combo mais caro que a soma) e de `payment_fee_cents` (percentual, fixo, por parcela,
      teto no valor pago).
- [ ] Testes em `tests/test_catalog/` para cada regra acima, cruzamento entre duas barbearias e os
      escopos (gerente de uma unidade recebe `403` na escrita; barbeiro lê).
- [ ] Snapshots (`openapi.json`, `routes.json`, `db_schema.json`) regenerados com o diff lido.
- [ ] `tools/api_docs.py` com os grupos novos e `make docs-api`.
- [ ] `make check` verde; memória do backend atualizada.

## Dependencies

- `✅completed_registry-basic-crud.md` — `services`, regras P1/P4/P6, padrão de rotas do `catalog`.
- Oferece para **S06** (`sales`): `get_product`, `get_combo`, `get_payment_method`,
  `allocate_combo_price`, `payment_fee_cents`.
- Oferece para **S08** (`commissions`): `products.commission_percent` (via snapshot no item da
  comanda) e as taxas (via snapshot no pagamento).
- Oferece para **S03/S04/S11** (Q-S05-1 = combos só de serviços agendáveis): `get_combo` com
  `duration_minutes` e a ordem dos serviços, e `list_bookable_combos`.
- Oferece para **S09** (`finance`): `list_payment_methods` (conferência do caixa por forma).

## Notes

- **Combo na agenda.** Esta spec não muda a agenda. Com Q-S05-1 = 2, S03 aceita `combo_id` no
  agendamento (os serviços do combo viram itens em sequência) e a comanda aberta a partir dele
  agrupa os itens no combo. Combo com produto só existe na comanda.
- **Prazo de recebimento** (D+1, D+30 da maquininha) e conciliação ficam fora; entram com
  previsão de fluxo de caixa ou com o gateway.
- **Acréscimo ao cliente** no parcelado: não (Q-S05-2); o modelo só tem taxa absorvida. Entra com o
  gateway, se pedirem.

### Perguntas em aberto

✅ **Q-S05-1 — O cliente pode agendar um combo (IA e link público)?**
1. Não: combo só existe na comanda; a recepção aplica o preço fechado no fechamento.
2. Sim, combos só de serviços aparecem para agendar (com a duração somada); combos com produto só
   na comanda.
3. Sim, todos; o produto do combo entra na comanda quando ela abre.

Recomendação: **2**. É como Trinks e AppBarber mostram "Corte + Barba" no agendamento online; o
cliente vê o preço fechado já no WhatsApp, e produto não tem o que agendar.

> Resolvido em 2026-11-06: 2 — IA e link agendam só combos de serviços; combo com produto só na
> comanda (ROADMAP §7).

✅ **Q-S05-2 — A taxa do cartão pode ser repassada ao cliente (acréscimo no parcelado)?**
1. Não: a barbearia sempre absorve a taxa; o cliente paga o preço da tabela.
2. Sim, por forma de pagamento: "Crédito 3x" pode ter acréscimo de X% somado ao total da comanda.

Recomendação: **1** agora. O acréscimo mexe no total da comanda, na base de comissão e no que o
cliente vê no WhatsApp; entra junto com o gateway, se pedirem.

> Resolvido em 2026-11-06: 1 — a barbearia absorve a taxa do cartão, sem acréscimo no parcelado
> (ROADMAP §7; mesma linha da gorjeta, PD-38).
