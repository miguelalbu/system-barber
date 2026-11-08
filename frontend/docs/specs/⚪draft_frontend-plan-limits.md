# Plano, uso e bloqueios no painel

**Priority:** high
**Status:** draft
**Espelho no backend:** `backend/docs/specs/⚪draft_provisioning-plan-entitlements.md`

## Overview

O painel passa a saber o **plano** da barbearia (vem no `/auth/me`) e a usá-lo em três lugares: (1) a
página **Plano** para o dono, com recursos incluídos, **uso × limite** (barbeiros ativos, unidades,
números de WhatsApp e mensagens de campanha do mês) e o **saldo, o consumo (em créditos e em US$) e
o extrato dos créditos de IA** (PD-40, PD-43, PD-44);
(2) a **navegação e as ações** — recurso fora do
plano aparece travado com convite para mudar de plano, em vez de dar erro; (3) o tratamento global do
`402` que o backend devolve quando alguém chega lá mesmo assim. O painel nunca mostra preço nem
cobra (PD-21).

## Decisões de produto já tomadas

| Parâmetro | Valor |
|---|---|
| PD-21 | Cobrança mora no Core; o painel não mostra preço nem forma de pagamento. |
| PD-22 | Limites e recursos vêm do plano; nomes e valores não estão no código. |
| PD-39 | Downgrade acima do limite: nada é desativado; só fica bloqueado criar/reativar até voltar ao limite. |
| PD-40 | IA por **créditos** comprados no Core; créditos acabaram → conversas novas vão para "aguardando humano". O painel mostra saldo e extrato, nunca vende. |
| PD-43 | Crédito **proporcional ao custo real** de cada chamada ao modelo e de cada transcrição (`credits_per_usd`); o plano inclui créditos por mês que **não acumulam**; comprados **não vencem**. O backend guarda e devolve **milicréditos** (`*_millicredits`, 1 crédito = 1000). |
| PD-44 | O dono vê o consumo **em créditos e o custo estimado em US$** (`cost_usd_micros`). |
| PD-42 | Números de WhatsApp: um geral e, opcionalmente, um por unidade, limitados por `whatsapp_numbers`. |
| Travado × escondido | Travado para o dono, escondido para os demais (Q-S15-5, resolvida). |

## Business Rules

- [ ] `useAuth()` ganha `hasFeature(feature)` e `limitOf(limit)` a partir de `me.plan`.
- [ ] `FeatureGate` (`features/plan/ui/`): com o recurso, mostra o conteúdo; sem, mostra
      `PlanUpgradeNotice` ("Este recurso não está no seu plano") — com o botão "Mudar de plano" só para
      quem tem `subscription:manage`; os demais leem "Fale com o responsável pela barbearia".
- [ ] Item de navegação com `feature` (S18 define o campo): sem o recurso, o dono vê o item com
      cadeado e a tela de upgrade; os outros cargos não veem o item.
- [ ] `shared/api/http.ts` traduz `402` em `PlanError` (subclasse de `ApiError`) com `code`, `feature`,
      `limit`, `max`, `used`. Formulários mostram a mensagem do backend; um `PlanError` de limite
      também mostra "N de N barbeiros ativos" e o link para a página Plano.
- [ ] Botões que criam registro limitado ("Novo barbeiro", "Nova unidade", reativar) ficam
      desabilitados com dica quando o uso já é igual ao limite (`GET /tenant/plan` para o dono;
      para os outros, o `402` do backend basta).
- [ ] **Página Plano** (`/app/configuracoes/plano`, só `subscription:manage`): nome do plano, lista de
      recursos com ✓/cadeado e descrição curta, barras de uso (cor de alerta a partir de 80%,
      perigo em 100%; "Ilimitado" quando `null`) para barbeiros, unidades, números de WhatsApp e
      mensagens de campanha, mês de referência da cota de campanha, botão "Mudar de plano"
      (`upgrade_url`; sem URL, o botão some).
- [ ] **Aviso de excesso** (depois de downgrade): faixa no topo do painel para o dono quando algum
      `usage > limit` — "Você tem 6 barbeiros ativos e seu plano permite 4. Inative 2 para voltar a
      cadastrar." — dispensável por sessão, volta no próximo login.
- [ ] **Formatação** (regra pura em `plan.rules.ts`, reaproveitada pela S11 e pela S14): milicréditos
      → crédito com até 1 casa decimal em pt-BR ("312,4 créditos"; "312 créditos" quando inteiro;
      saldo arredondado para baixo, consumo ao mais próximo; consumo acima de 0 e abaixo de 0,1 →
      "< 0,1 crédito"). `cost_usd_micros` → dólar ("US$ 3,27"; abaixo de US$ 0,01, 4 casas:
      "US$ 0,0042"), sempre com o rótulo "custo estimado".
- [ ] **Créditos de IA** (só com `ai_assistant` no plano): bloco na página Plano com o saldo
      ("312,4 créditos"), separado em inclusos no plano (só se `monthly_included > 0`; "não acumulam:
      vencem no fim do mês") e comprados ("não vencem", salvo `next_expiry`), o próximo vencimento
      ("40 vencem em 30/11"), o **consumo do mês em créditos e em US$** ("86,2 créditos · custo
      estimado US$ 0,86"), separado por tipo (conversas, transcrição de áudio), e a regra em uma linha
      a partir da política ("Cada resposta da IA e cada áudio transcrito gastam créditos proporcionais
      ao custo: US$ 1 de custo = N créditos"). Botão "Comprar créditos" leva ao `upgrade_url` (sem
      URL, some). Link "Ver extrato" abre `pages/credits/` com a lista paginada (data, tipo — Compra,
      Crédito do plano, Ajuste, Uso da IA (agrupado por dia, com custo em US$ e nº de chamadas),
      Vencimento —, quantidade com sinal e saldo depois), filtro por tipo.
- [ ] Faixa de créditos para o dono: alerta quando `ai_credits.low` ("Seus créditos de IA estão
      acabando: restam 18,5") e perigo quando `ai_credits.empty` ("Seus créditos de IA acabaram. Novas
      conversas vão para Aguardando humano até você comprar mais."), com o botão "Comprar créditos".
      A de saldo baixo é dispensável por sessão; a de saldo zerado não.
- [ ] Rótulos dos recursos e limites em português num só lugar (`plan.constants.ts`), testados contra o
      enum (todo recurso tem rótulo).

## Telas e fluxos

| Rota | Tela | Fluxos |
|---|---|---|
| `/app/configuracoes/plano` | `features/plan/pages/PlanScreen.tsx` | `pages/usage/` (barras), `pages/features/` (lista), `pages/credits/` (saldo e extrato dos créditos de IA) |
| (global) | `features/plan/ui/PlanUpgradeNotice.tsx`, `FeatureGate.tsx`, `PlanBanner.tsx` | montados pelo shell e pelas features |

Feature nova `plan` (pequena e transversal; não fica em `settings` para as outras features poderem
importar o `FeatureGate` sem depender da tela de configurações). O menu de Configurações (S01) linka
para a página Plano.

## Data Contract

```text
GET /auth/me        → Me + plan {code, name, features: PlanFeature[], limits: Record<PlanLimit, number|null>}
GET /tenant/plan    → {code, name, features[], limits{}, usage{}, period,
                       ai_credits {balance_millicredits, included_millicredits, purchased_millicredits,
                                   held_millicredits, low, empty,
                                   next_expiry {amount_millicredits, expires_at}|null,
                                   month, consumed_millicredits, consumed_cost_usd_micros,
                                   consumed_by_kind [{call_kind: llm|transcription, millicredits,
                                                      cost_usd_micros, calls}]},
                       upgrade_url|null}
GET /tenant/ai-credits?cursor=&kind= → ai_credits + {policy {credits_per_usd, monthly_included,
                       included_rollover, purchased_expiry_days, low_balance_threshold},
                       entries [{date|created_at, kind: purchase|included_grant|adjustment|consume|expire,
                       amount_millicredits, balance_after_millicredits, note|null,
                       call_kind|null, cost_usd_micros|null, calls|null}], next_cursor|null}
                       (`consume` vem agrupado por dia e tipo; `hold`/`release` não aparecem)
402                 → {detail, code: 'feature_not_in_plan'|'plan_limit_reached', feature?, limit?, max?, used?}
```

```text
features/auth/model/auth.types.ts      + Plan, PlanFeature, PlanLimit (espelham o openapi)
features/plan/model/plan.constants.ts  rótulos e descrições
features/plan/model/plan.rules.ts      nível de alerta do uso, excesso, texto do limite, faixa de
                                       créditos (baixo/zerado), frase da regra de consumo,
                                       formatCredits (milicréditos) e formatUsdMicros (exportados
                                       pelo index.ts para S11 e S14)
features/plan/api/plan.api.ts          · plan.queries.ts (['tenant-plan'], ['ai-credits', kind])
shared/api/http.ts                     + PlanError (sem tipo de negócio: carrega só os campos do corpo)
```

## Estado

| Estado | Onde |
|---|---|
| Plano efetivo | `me.plan` no `AuthProvider` (já carregado na subida) |
| Uso e limites | TanStack Query `['tenant-plan']`, só para o dono; invalidado depois de criar/inativar barbeiro, unidade ou número |
| Créditos de IA | `ai_credits` dentro de `['tenant-plan']` (faixa) e `['ai-credits', kind]` (extrato, paginado), só para o dono |
| Faixa dispensada | `sessionStorage` |

## Permissões

| Ação | Permissão / plano |
|---|---|
| ver página Plano, faixas de excesso e de créditos, extrato de créditos | `subscription:manage` |
| ver item/ação de recurso pago | `hasFeature(...)` + a permissão do próprio recurso |

## Acceptance Criteria

- [ ] Testes em `tests/`: nível de alerta (79/80/100/ilimitado), detecção de excesso, montagem do
      texto do `402` de limite, todo `PlanFeature`/`PlanLimit` com rótulo, faixa de créditos
      (normal/baixo/zerado), frase da regra montada da política (`credits_per_usd`), rótulo de todo
      `kind` do extrato, `formatCredits` (inteiro, 1 casa, arredondamento do saldo para baixo,
      "< 0,1") e `formatUsdMicros` (2 casas, 4 casas abaixo de US$ 0,01, zero).
- [ ] Conferido no navegador com um plano sem IA, com limite de barbeiros atingido (dono e recepção)
      e com créditos de IA baixos e zerados.
- [ ] Testes em `tests/` cobrindo as regras puras da feature
- [ ] Tela conferida no navegador (estados vazio, carregando, erro)
- [ ] `make check-frontend` verde

## Dependencies

- Backend `⚪draft_provisioning-plan-entitlements.md` (campo `plan` no `/auth/me`, `GET /tenant/plan`,
  corpo do `402`, `GET /tenant/ai-credits`).
- `⚪draft_frontend-pwa-mobile.md` (S18): campo `feature` nos itens de navegação.
- Usado por: registry (barbeiros/unidades), S07, S10–S12, S14 (`FeatureGate`, `PlanError`).

## Notes

### Perguntas em aberto

- ✅ **Q-S15-5 — Recurso fora do plano: esconder ou mostrar travado?**
  (a) esconder para todos; (b) mostrar travado para todos; (c) travado para o dono (quem decide o
  upgrade), escondido para equipe.
  **Recomendação: (c)** — vitrine para quem compra, menu limpo para quem só opera.
  > Resolvido em 2026-11-06: (c) — travado para o dono, escondido para a equipe (ROADMAP §7).
- ✅ **Q-S15-6** (backend) — unidade de consumo, créditos inclusos no plano e validade. A tela
  continua sem fixar valores: mostra o que a `policy` devolve (inclusos só aparecem se
  `monthly_included > 0`, vencimento só se houver `next_expiry`).
  > Resolvido em 2026-11-06: 1(c) proporcional ao custo (credits_per_usd, milicréditos, reserva e acerto), 2(b), 3(a) (PD-43); custo em US$ visível ao dono (PD-44).
- Q-S15-1 e Q-S15-3 (backend), que mudam esta tela:
  > Resolvido em 2026-11-06: downgrade não desativa nada, só bloqueia criar/reativar (PD-39); não há mais cota mensal de IA, e sim saldo de créditos com faixa de baixo/zerado (PD-40 | ROADMAP §7).
