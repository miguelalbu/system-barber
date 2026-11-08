# Ficha do cliente no painel

**Priority:** high
**Status:** draft
**Espelho no backend:** `backend/docs/specs/⚪draft_clients-profile.md`

## Overview

Hoje `/app/clientes` é uma lista paginada com formulário. Esta spec acrescenta a **ficha do cliente**
(`/app/clientes/:id`): indicadores no topo, linha do tempo de atendimentos e compras, tags,
preferências de comunicação e as ações de LGPD (exportar, anonimizar) e de **mescla de duplicados**.
A lista ganha colunas de relacionamento (última visita, visitas), filtro por tag e ordenação. Regras,
contrato e eventos estão no espelho do backend; aqui fica só o que é de tela.

Referência de mercado: o topo da ficha do Trinks/AppBarber (cartões "Última visita", "Frequência",
"Ticket médio") e a linha do tempo da Fresha, com a falta destacada em vermelho.

## Decisões de produto já tomadas

| Parâmetro | Valor |
|---|---|
| PD-03 | Cliente é da barbearia: a ficha é a mesma em qualquer unidade. |
| PD-07 | Faltas aparecem no histórico e no contador "Faltas". |
| PD-20 | A ficha mostra e permite mudar o opt-out de lembretes e de marketing. |
| PD-30 | Marketing só para quem tem ao menos um atendimento ou disse "sim" explícito (importados e contatos sem atendimento); utilidade (lembrete, confirmação) para todo cliente com agendamento. |
| PD-41 | O barbeiro vê o contato do cliente só se a barbearia ligar a configuração; **padrão oculto** (vê nome, histórico e indicadores). |
| Onde | Ficha em página própria `/app/clientes/:id` (não modal): é linkável a partir da agenda, da comanda e da Central de conversas. |
| Formulário | O formulário atual (`ClientForm`) continua, aberto pelo botão "Editar" da ficha. |

## Business Rules

- [ ] Clicar numa linha da lista abre a ficha; a busca e a página da lista sobrevivem ao "Voltar"
      (estão na URL).
- [ ] Cartões de indicador: Última visita ("há 12 dias", data no título), Frequência ("a cada 21
      dias"; "—" com menos de 2 visitas), Gasto total, Ticket médio, Faltas, Barbeiro preferido,
      Cliente desde. Selo **"Atrasado"** quando `days_since_last_visit > 1,5 × avg_interval_days`
      (regra pura, testada).
- [ ] Linha do tempo paginada por cursor ("Carregar mais"): data local, unidade, barbeiro(s), itens,
      valor; falta em vermelho, cancelamento em cinza, comanda estornada riscada. Agendamento e
      comanda viram link quando as telas deles existirem (S03, S06).
- [ ] Tags: chips coloridos na ficha; combobox para adicionar (cria tag nova digitando, com
      `client:write`); filtro por tag na lista (vários = "tem todas"), na URL (`?tag=`).
- [ ] Comunicação: "Aceita mensagens no WhatsApp" (opt-in, com a origem: "mandou mensagem em 03/11",
      "pelo link", "pela equipe", "importado", "respondeu VOLTAR"), **"Autorizou receber promoções"**
      (o "sim" explícito da PD-30, `marketing_consent`, com a origem: "pelo link", "pelo WhatsApp",
      "pela equipe" — marcar grava origem equipe), "Não quer promoções" (opt-out de marketing) e "Não
      quer nenhuma mensagem" (opt-out total), e o resultado em linguagem simples a partir de
      `utility_allowed`/`marketing_allowed` ("Recebe lembretes · Não recebe promoções"). Quando o
      marketing está bloqueado só por falta de consentimento (sem atendimento e sem "sim"), o texto
      diz "Promoções só depois do primeiro atendimento ou com autorização". Cliente anonimizado: tudo
      desligado e travado.
- [ ] Lista: colunas novas "Última visita" e "Visitas"; ordenação por nome, última visita, gasto
      (gasto só para quem tem `finance:read`, ver Permissões) e visitas; filtro "Sem visita há mais
      de N dias" (`last_visit_before`).
- [ ] **Exportar dados (LGPD)**: baixa o JSON (`cliente-<nome>-<data>.json`) gerado pelo backend.
- [ ] **Anonimizar**: diálogo que explica o efeito ("o histórico financeiro fica, os dados pessoais
      somem e não voltam") e pede para digitar o telefone do cliente. `409` mostra a mensagem do
      backend (ex.: "Cancele os agendamentos futuros antes").
- [ ] **Duplicados** (`/app/clientes/duplicados`): lista de pares sugeridos com o motivo; "Não são a
      mesma pessoa" descarta; "Mesclar" abre a comparação lado a lado, o usuário escolhe qual
      cadastro **fica** e confirma. Depois da mescla, vai para a ficha do que ficou.
- [ ] Da ficha, "Mesclar com…" busca outro cliente (mesmo componente de busca da lista) e cai no
      mesmo fluxo de comparação.
- [ ] Cliente anonimizado: faixa "Cliente anonimizado em dd/mm/aaaa"; sem editar, mesclar ou exportar.
- [ ] Barbeiro (`client:read` = `own`): telefone/e-mail como o backend devolve — **mascarados** por
      padrão (`(11) 9••••-4321`), completos só com `barber_sees_client_contact` ligado (PD-41); a tela
      não oferece copiar/ligar/WhatsApp para contato mascarado. Sem ações de escrita.

## Telas e fluxos

| Rota | Tela | Fluxos |
|---|---|---|
| `/app/clientes` | `features/customers/pages/CustomersScreen.tsx` (existe) | `pages/list/` (colunas, filtro de tag, ordenação) |
| `/app/clientes/:id` | `features/customers/pages/ClientProfileScreen.tsx` | `pages/profile/` (cabeçalho, indicadores, linha do tempo, tags, comunicação), `pages/privacy/` (exportar, anonimizar) |
| `/app/clientes/duplicados` | `features/customers/pages/ClientDuplicatesScreen.tsx` | `pages/merge/` (pares, comparação, confirmação) |

Rotas registradas em `app/router.tsx`; título da topbar "Clientes · <nome>" pelo mesmo mecanismo do
`AppLayout` usado nos Cadastros.

## Data Contract

Contrato completo no espelho do backend. Consumidos:

```text
GET    /clients?q=&tag_id=&sort=&order=&last_visit_before=&limit=&offset=
GET    /clients/{id}/profile        GET /clients/{id}/history?limit=&before=
PUT    /clients/{id}/tags           PATCH /clients/{id}/communication
GET    /clients/{id}/export         POST  /clients/{id}/anonymize {confirm}
GET    /clients/duplicates          POST  /clients/duplicates/dismiss {a_id, b_id}
POST   /clients/{id}/merge {source_id}
GET/POST /client-tags · PATCH/DELETE /client-tags/{id}
```

Arquivos:

```text
features/customers/model/customers.types.ts   + ClientProfile, ClientStats, Visit, ClientTag, Communication
features/customers/model/profile.rules.ts      atraso, "a cada N dias", rótulos de status da visita
features/customers/api/customers.api.ts        + chamadas acima (caminho literal, variáveis em query)
features/customers/api/customers.queries.ts    + useClientProfile, useClientHistory (infinite), useClientTags…
shared/text/relativeDays.ts                    "hoje", "ontem", "há 12 dias" (puro; usado também em S18)
```

## Estado

| Estado | Onde |
|---|---|
| Ficha, histórico, tags, duplicados | TanStack Query: `['client', id, 'profile']`, `['client', id, 'history']` (infinite), `['client-tags']`, `['client-duplicates']` |
| Filtros e ordenação da lista | URL (`q`, `pagina`, `tag`, `ordem`, `sem-visita-dias`) |
| Diálogos (anonimizar, mesclar, editar) | estado local |

Mutação de tags/comunicação invalida o perfil; mescla e anonimização invalidam `['clients']`, o
perfil e os duplicados.

## Permissões

| Ação | Permissão em `/auth/me` |
|---|---|
| ver ficha, histórico | `client:read` |
| editar, tags, comunicação, ver duplicados | `client:write` |
| exportar, anonimizar, mesclar | `client:manage` (nova, no backend) |
| coluna/ordenação "Gasto total" e cartões de dinheiro | `finance:read` (recepção e barbeiro veem visitas e faltas, não valores) |

> Sem `finance:read` o backend já devolve os valores como `null`; a tela esconde os cartões e a
> coluna em vez de mostrar "—".

## Acceptance Criteria

- [ ] Ficha com os quatro estados (carregando, vazio — "Nenhum atendimento ainda", erro, com dados).
- [ ] Testes em `tests/`: regra de atraso, formatação "a cada N dias"/"há N dias", rótulos e cores
      de status da visita, montagem do nome do arquivo de exportação, validação do `confirm`.
- [ ] Fluxos de mesclar e anonimizar conferidos no navegador, inclusive o `409`.
- [ ] `make docs-api` regenerado com as chamadas novas dentro do contrato.
- [ ] Testes em `tests/` cobrindo as regras puras da feature
- [ ] Tela conferida no navegador (estados vazio, carregando, erro)
- [ ] `make check-frontend` verde

## Dependencies

- Backend `⚪draft_clients-profile.md` implementado e congelado no `openapi.json`.
- `✅active_frontend-registry-basic-crud.md` — lista e formulário de clientes que esta spec estende.
- S03/S06 frontend: links "ver agendamento"/"ver comanda" e o botão "Agendar" da ficha (abre o modal
  de agendamento com o cliente preenchido — `scheduling` exporta pelo `index.ts`).

## Notes

- ✅ **Q-S13-1** (consentimento), **Q-S13-2** (contato para o barbeiro) e **Q-S13-3** (quem mescla)
  estão no backend.
  > Resolvido em 2026-11-06: Q-S13-1 — marketing com ao menos um atendimento ou "sim" explícito,
  > utilidade para quem tem agendamento; "SAIR" pergunta "Só promoções" / "Tudo" (PD-30, Q-S12-2);
  > Q-S13-2 — configurável, padrão oculto; o interruptor "Barbeiro vê telefone e e-mail do cliente"
  > fica em Configurações da barbearia (`shop_settings`, espelho da S01), não nesta tela (PD-41);
  > Q-S13-3 — só dono e gerente mesclam (`client:manage`) (ROADMAP §7).
- Indicadores chegam por evento: logo depois de fechar uma comanda, a ficha pode levar alguns
  segundos para refletir. A tela mostra "Atualizado há instantes" sem forçar recarga.
