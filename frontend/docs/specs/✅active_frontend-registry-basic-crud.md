# Cadastros básicos no painel: barbeiros, serviços e clientes

**Priority:** high
**Status:** active
**Espelho no backend:** `backend/docs/specs/✅completed_registry-basic-crud.md`

## Overview

As telas de Cadastros (`/app/cadastros`) e Clientes (`/app/clientes`) são hoje um mock do protótipo
e um placeholder. Esta spec as liga à API real para **listar, cadastrar, editar, inativar e apagar**
barbeiros, serviços e clientes. É a **primeira feature com dado de servidor além da sessão**, então
ela instala o TanStack Query (DEC-005) e define o padrão que as próximas telas copiam: `*.api.ts` +
`*.queries.ts`, formulário com validação local espelhando a do backend, estados de carregando,
vazio e erro, e ações escondidas por permissão.

Regras de negócio, contrato e as propostas P1–P6 (o que "apagar" faz, telefone obrigatório etc.)
estão no espelho do backend; aqui fica só o que é de tela.

## Decisões de produto já tomadas

| Parâmetro | Valor |
|---|---|
| Onde fica cada cadastro | Barbeiros e Serviços: páginas próprias, `/app/cadastros/barbeiros` e `/app/cadastros/servicos`, abertas pelo dropdown "Cadastros" da sidebar (feature `registry`; antes eram abas — mudado em 2026-11-06). Clientes: `/app/clientes` (feature `customers`). |
| Abas fora do escopo | Unidades, Clubes e combos, Planos continuam como estão (aviso "em breve"). |
| Formulário | Painel abaixo da tabela, como no protótipo (não modal), para criar e editar. |
| Apagar | Sempre com confirmação. `409` do backend vira a mensagem dele + botão "Inativar". |
| Jornada / horas por semana | Saem da tabela e do formulário de barbeiro (vão para a spec da agenda). |
| Barbeiro × usuário | **Cadastros separados** (decisão do dono do produto, 2026-11-06). Barbeiros ficam em Cadastros; usuários com acesso ao painel, em Equipe (tela fora desta spec). O formulário do barbeiro não pede e-mail nem senha. |
| Acesso do barbeiro | Coluna e campo "Acesso ao painel": mostra o e-mail do usuário ligado ou "Sem acesso". No formulário, um seletor opcional liga o barbeiro a um usuário existente (o dono que também corta). |

### Aprovado junto com a spec (2026-11-06)

- **Dependência nova:** `@tanstack/react-query@5` (DEC-005 já previa; a aprovação fica registrada
  numa DEC nova). Sem devtools.

## Business Rules

### Comuns

- [x] Toda lista tem os quatro estados: carregando (esqueleto da tabela), vazio (texto + botão de
      criar, se o usuário puder), erro (mensagem do `ApiError` + "Tentar de novo") e com dados.
- [x] Depois de criar, editar, inativar ou apagar, a lista é invalidada e recarregada (sem
      atualização otimista nesta primeira versão).
- [x] Botão de salvar fica desabilitado enquanto a requisição corre; erro do backend (`400`, `403`,
      `409`) aparece no formulário com a mensagem do `detail`; `422` vira "Confira os campos".
- [x] Validação local espelha a do backend (tamanhos, faixas, obrigatórios) e mostra o erro no
      campo; o backend valida de novo.
- [x] Ações escondidas por permissão de `GET /auth/me` (`useAuth().can`): sem a permissão de
      escrita, a tela fica só leitura (sem "Novo", "Editar", "Apagar").
- [x] Fechar o formulário com alteração não salva pede confirmação.

### Serviços (aba "Serviços")

- [x] Tabela: nome, duração (`45 min`, `1 h 30 min`), preço (`R$ 45,00`), barbeiros habilitados
      (quantidade), status.
- [x] Formulário: nome, descrição, duração (seleção de 5 em 5 min, até 8 h), preço (campo em reais
      convertido para centavos), ativo.
- [x] Escrever só aparece com `catalog:write` **e** acesso a todas as unidades (o `403` do backend
      para gerente restrito vira o aviso "Serviços valem para todas as unidades").

### Barbeiros (aba "Barbeiros")

- [x] Tabela: barbeiro (iniciais, nome), unidade, serviços habilitados (nomes, a partir do
      `barber_ids` de cada serviço), comissão, acesso ao painel (e-mail ou "Sem acesso"), status.
- [x] Filtros: busca por nome (no cliente — a lista é pequena), unidade e status; filtros na URL.
- [x] Formulário: nome, iniciais (preenchidas a partir do nome, editáveis), unidade (de
      `GET /tenant/units`), comissão padrão (%), ativo e os **serviços habilitados** (chips
      liga/desliga, salvos com `PUT /barbers/{id}/services` depois do `POST`/`PATCH`) e "Acesso ao
      painel" (opcional: usuários ativos de `GET /team` ainda sem barbeiro; enviado como `user_id`).
- [x] Barbeiro com login não mostra "Apagar" (o backend recusaria); mostra "Inativar".
- [x] Ver com `team:read`; escrever com `team:manage`.

### Clientes (`/app/clientes`)

- [x] Tabela paginada (50 por página): nome, telefone formatado (`(11) 98765-4321`), e-mail,
      aniversário (`dd/mm`), status. Total de registros no topo.
- [x] Busca por nome ou telefone com espera de 300 ms; `q` e a página ficam na URL.
- [x] Formulário: nome, telefone (máscara brasileira; aceita `+` para internacional), e-mail, data
      de nascimento, observações, ativo. O telefone que volta do backend (E.164) é o que se mostra.
- [x] Telefone repetido (`409`) mostra a mensagem no campo de telefone.
- [x] Ver com `client:read`; escrever com `client:write`. Para o barbeiro a lista vem vazia até a
      agenda existir: o estado vazio dele diz "Seus clientes aparecem aqui depois do primeiro
      atendimento".

## Telas e fluxos

| Rota | Tela | Fluxos |
|---|---|---|
| `/app/cadastros?aba=barbeiros` | `features/registry/pages/RegistryScreen.tsx` | `pages/barbers/` (lista, formulário) |
| `/app/cadastros?aba=servicos` | `features/registry/pages/RegistryScreen.tsx` | `pages/services/` (lista, formulário) |
| `/app/clientes` | `features/customers/pages/CustomersScreen.tsx` | `pages/list/`, `pages/form/` |

A aba ativa vai para a URL (`?aba=`), para sobreviver a refresh e poder ser linkada.

## Data Contract

Contrato completo no espelho do backend. Endpoints consumidos:

```text
GET/POST /services · GET/PATCH/DELETE /services/{id}
PUT      /barbers/{id}/services
GET/POST /barbers  · GET/PATCH/DELETE /barbers/{id}
GET/POST /clients  · GET/PATCH/DELETE /clients/{id}   (GET com q, active, limit, offset)
GET      /tenant/units                                (já existe)
GET      /team                                        (já existe; seletor "Acesso ao painel")
```

Arquivos:

```text
features/registry/model/registry.types.ts   Barber, Service (+ BarberInput, ServiceInput)
features/registry/model/*.rules.ts          validação dos formulários, duração/preço
features/registry/api/registry.api.ts       chamadas HTTP puras
features/registry/api/registry.queries.ts   hooks do TanStack Query
features/customers/model/customers.types.ts Client (+ ClientInput, ClientPage)
features/customers/model/*.rules.ts         validação, máscara de telefone
features/customers/api/customers.api.ts     · customers.queries.ts
shared/text/money.ts · duration.ts · phone.ts   formatação pura (usada por mais de uma feature)
shared/ui/ConfirmDialog.tsx                  confirmação de apagar (registry e customers)
```

Tipos espelham o `openapi.json` congelado do backend; nenhum campo inventado.

## Estado

| Estado | Onde |
|---|---|
| Listas e registro aberto | TanStack Query (`QueryClientProvider` em `main.tsx`; chaves `['services']`, `['barbers', filtros]`, `['clients', q, página]`) |
| Aba, filtros, busca, página | URL (search params) |
| Formulário aberto e valores | estado local da tela |
| Permissões | `useAuth().can(...)` (já existe) |

## Permissões

| Ação | Permissão em `/auth/me` |
|---|---|
| ver aba Serviços | `catalog:read` |
| criar/editar/apagar serviço | `catalog:write` (e todas as unidades) |
| ver aba Barbeiros | `team:read` |
| criar/editar/apagar barbeiro, serviços habilitados | `team:manage` |
| ver Clientes | `client:read` |
| criar/editar/apagar cliente | `client:write` |

## Acceptance Criteria

- [x] TanStack Query instalado com aprovação registrada (DEC nova) e o padrão `*.queries.ts`
      documentado no `rules.md` / skill `new-feature.md`.
- [x] `registry.mock.ts` apagado (as abas fora do escopo não dependem dele); ISS-002 atualizada.
- [x] Testes em `tests/`: formatação de dinheiro, duração e telefone; validação dos três
      formulários; derivação de iniciais; montagem da coluna "serviços habilitados".
- [x] `make docs-api` regenerado: `docs/api/` mostra as chamadas novas, todas dentro do contrato.
- [ ] Tela conferida no navegador com a barbearia `demo`, como dono e como recepção: criar, editar,
      inativar, apagar, `409` de telefone repetido, estados vazio, carregando e erro.
- [x] `make check-frontend` verde.
- [x] `README.md` (estado das telas) e `memory/progress.md` atualizados.

## Dependencies

- Backend: `backend/docs/specs/✅completed_registry-basic-crud.md` implementado e com o
  `openapi.json` congelado (as telas começam depois das rotas existirem).
- `✅completed_frontend-auth-session.md` — `useAuth().can`, `ApiError`, renovação de token.

## Notes

- > 2026-11-06: implementado; falta só conferir no navegador (ISS-010 — o ambiente Docker caiu
  > durante a verificação). Além do previsto: `request()` ganhou `query` (o caminho continua literal
  > para o gerador de `docs/api/`), `shared/ui/DeleteRecordDialog` concentra o fluxo "apagar → 409 →
  > inativar" das três telas, e o `signOut` limpa o cache de consultas.
- O tipo `Barber` de `features/scheduling` (mock da agenda) continua separado: a agenda passa a usar
  o barbeiro real na spec dela, importando pelo `index.ts` do `registry`.
- Atualização otimista, edição em linha e exportação de clientes (CSV) ficam para depois.
- A tela de Equipe (usuários e convites) ainda não existe no painel. Quando existir, o convite com
  cargo `barber` escolhe o barbeiro já cadastrado (`barber_id`), como o backend passa a exigir.
