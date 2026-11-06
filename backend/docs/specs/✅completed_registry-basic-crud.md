# Cadastros básicos: barbeiros, clientes e serviços (CRUD)

**Priority:** high
**Status:** completed
**Espelho no frontend:** `frontend/docs/specs/⏳active_frontend-registry-basic-crud.md`

## Overview

Primeiro bloco de domínio depois da fundação (identidade, schema por barbearia, control plane).
Até aqui uma barbearia só tem login, equipe e unidades: as telas de Cadastros e Clientes do painel
são mock. Esta spec cria o **cadastro, a edição, a listagem e a exclusão** dos três registros que
todo o resto do produto usa — **barbeiros** (a coluna da agenda), **serviços** (o que se agenda e se
cobra) e **clientes** (quem agenda, inclusive pelo WhatsApp). A agenda, a comanda e a IA do
WhatsApp vão ler esses três; por isso as regras de identidade de cada um (telefone do cliente, nome
do serviço, unidade do barbeiro) são fixadas aqui.

**Barbeiro não é usuário.** O cadastro de barbeiros (quem atende: coluna da agenda, comissão,
serviços) é separado do cadastro de usuários (quem acessa o painel: login, cargo, unidades, em
Equipe). Um não cria o outro. Um barbeiro *pode* estar ligado a um login — o barbeiro que consulta
a própria agenda, ou o dono que também corta —, mas esse vínculo é opcional e explícito.

Fica de fora, cada um com spec própria depois: jornada e disponibilidade do barbeiro (agenda),
combos, clubes e planos (catálogo, fase 2), preço por unidade, histórico do cliente e autenticação
do cliente final por telefone + OTP.

## Decisões de produto já tomadas

| Parâmetro | Valor |
|---|---|
| Escopo | CRUD de barbeiros, clientes e serviços, mais o vínculo barbeiro ↔ serviços habilitados |
| Ordem de implementação | serviços → clientes → barbeiros (o barbeiro usa a lista de serviços) |
| Módulos | `catalog` (novo: serviços e vínculo), `clients` (novo: clientes); barbeiros continuam no `identity` (DEC-007, ver Notes) |
| Permissões | as que já existem no mapa: `catalog:*`, `client:*`, `team:*` — nenhuma permissão nova |
| Barbeiro × usuário | **cadastros separados** (decisão do dono do produto, 2026-11-06): cadastrar barbeiro não cria login, e criar usuário (convite) não cria barbeiro. O vínculo entre os dois é opcional. |

### Decisões P1–P6 (propostas pela spec, aprovadas em 2026-11-06 — DEC-016)

| # | Parâmetro | Proposta | Por quê |
|---|---|---|---|
| P1 | O que "apagar" faz | `DELETE` apaga **de verdade** quando o registro não tem histórico; com histórico responde `409` e o caminho é **inativar** (`active=false`). Mesma regra para os três. | Hoje nada referencia esses registros, então apagar é seguro. Quando a agenda chegar, as FKs com `ON DELETE RESTRICT` fazem o banco recusar sozinho, e o histórico de atendimentos e comissões nunca aponta para o vazio. |
| P2 | Telefone do cliente | **Obrigatório** e único por barbearia, guardado em E.164 (`+5511987654321`) | O WhatsApp identifica o cliente pelo número; sem telefone a IA cria um cliente duplicado na primeira mensagem. |
| P3 | Cliente e unidade | Cliente é **da barbearia**, não da unidade: quem tem `client:*` com escopo `unit` vê todos os clientes | O mesmo cliente corta na unidade Centro e na Zona Sul; dividir por unidade duplicaria o cadastro. |
| P4 | Serviço e unidade | Serviço vale para **todas as unidades** (preço único). Só quem enxerga todas as unidades pode criar, editar ou apagar serviços. | Preço por unidade é uma complexidade que a maioria (barbearia de uma unidade) não precisa; entra depois como sobrescrita por unidade, sem quebrar este contrato. |
| P5 | Como o barbeiro ganha acesso | Duas formas, ambas explícitas: (a) convite de usuário com `barber_id` — o aceite liga o login novo ao barbeiro já cadastrado; (b) `user_id` no próprio cadastro do barbeiro — liga a um usuário que já existe (o dono que também corta). O convite **deixa de criar barbeiro** (`create_barber` sai do contrato), e convite com cargo `barber` passa a exigir `barber_id`. | Consequência direta dos cadastros separados: sem isso, cada convite de barbeiro criaria um segundo registro do mesmo profissional. E o cargo `barber` só funciona ligado a um barbeiro (o escopo `own` filtra pelo `barber_id`). |
| P6 | Dinheiro | Preço em **centavos inteiros** (`price_cents`) | Sem arredondamento de ponto flutuante no JSON; o frontend formata em reais. |

## Business Rules

### Comuns aos três

- [x] Todo dado vive no schema da barbearia (`TenantBase`, sem `tenant_id`). Um teste com **duas
      barbearias** prova que A não lista, não lê, não altera e não apaga registro de B (o id de B
      responde 404 em A).
- [x] `PATCH` é parcial: campo ausente não muda; campo enviado como `null` só é aceito onde a coluna
      é opcional.
- [x] Texto livre é aparado nas pontas (`strip`); nome vazio depois do `strip` é `422`.
- [x] `DELETE` segue a P1: `204` sem histórico; `409` com a mensagem "Este cadastro tem histórico;
      inative em vez de apagar" quando houver referência.
- [x] Listagens ordenadas por nome, sem diferença de maiúsculas (`ORDER BY lower(name)`; acento:
      ver Notes).

### Serviços (`catalog`)

- [x] Campos: `name` (2–80), `description` (opcional, até 500), `duration_minutes` (5–480, múltiplo
      de 5), `price_cents` (0–10.000.000), `active`.
- [x] Nome único por barbearia sem diferença de maiúsculas (`UNIQUE` sobre `lower(name)`): repetir é
      `409` "Já existe um serviço com esse nome".
- [x] Escrever exige `catalog:write` **e** enxergar todas as unidades (P4); gerente restrito a
      algumas unidades recebe `403` "Serviços valem para todas as unidades".
- [x] Ler exige `catalog:read` (os quatro cargos têm).
- [x] Serviço inativo continua na listagem com `?active=false`/sem filtro e some de `?active=true`;
      a agenda futura só oferece ativos.
- [x] Apagar um serviço remove os vínculos com barbeiros (`barber_services` em cascata) — vínculo
      não é histórico.

### Vínculo barbeiro ↔ serviços (`catalog`)

- [x] `PUT /barbers/{id}/services` **substitui** o conjunto de serviços habilitados do barbeiro
      (lista vazia = nenhum).
- [x] Exige `team:manage` no escopo do barbeiro (o gerente só mexe nos barbeiros das próprias
      unidades). Barbeiro fora do escopo ou inexistente → `404`.
- [x] Todo id da lista precisa existir na barbearia; id desconhecido → `400` "Serviço não
      encontrado". Serviço inativo pode ficar vinculado.
- [x] `ServiceOut` traz `barber_ids`, para a tela montar a coluna "Serviços habilitados" sem uma
      chamada por barbeiro.

### Clientes (`clients`)

- [x] Campos: `name` (2–120), `phone` (obrigatório, P2), `email` (opcional, formato válido),
      `birth_date` (opcional, não futura), `notes` (opcional, até 1000), `active`.
- [x] Telefone normalizado no servidor para E.164: tira tudo que não for dígito; 10 ou 11 dígitos
      = número brasileiro com DDD (prefixa `+55`); com `+` na frente, aceita 8–15 dígitos como
      internacional. Fora disso, `422` "Telefone inválido". A resposta devolve sempre o E.164.
- [x] Telefone único por barbearia: repetir é `409` "Já existe um cliente com esse telefone".
- [x] Lista **paginada** (`limit` 1–100, padrão 50; `offset`), com busca `q` por nome (contém, sem
      diferença de maiúsculas) ou telefone (contém, só dígitos), resposta `{items, total}`.
- [x] Escopo de leitura: `all` e `unit` veem todos (P3). `own` (barbeiro) vê só clientes que ele já
      atendeu — **até a agenda existir, a lista do barbeiro é vazia** (comportamento documentado,
      completado pela spec da agenda).
- [x] Escrever exige `client:write` (dono, gerente, recepção; barbeiro não tem).

### Barbeiros (`identity`)

- [x] Campos: `name` (2–120), `initials` (1–4, opcional na entrada: derivado do nome com a mesma
      regra do aceite de convite), `unit_id` (obrigatório, unidade existente), `default_commission`
      (0–100, duas casas), `active`. A resposta inclui `user_id` e `email` (do login vinculado, ou
      `null`).
- [x] Criar barbeiro nunca cria login, e criar usuário nunca cria barbeiro (cadastros separados).
- [x] Ler exige `team:read`; escrever, `team:manage`. Com escopo de unidade, a lista mostra só
      barbeiros das unidades do usuário, e criar/editar/mover só para essas unidades (destino fora →
      `403`).
- [x] Vínculo pelo cadastro (P5b): `user_id` em `POST`/`PATCH /barbers` liga a um usuário ativo da
      barbearia que ainda não está ligado a outro barbeiro (`409` se estiver; `400` se não existir
      ou estiver inativo). `user_id: null` desfaz o vínculo — recusado (`409`) se o usuário tiver o
      cargo `barber`, que sem barbeiro ficaria sem escopo.
- [x] Barbeiro **vinculado a um login** não pode ser apagado: `409` "Este barbeiro tem acesso ao
      painel; desfaça o vínculo ou desative o acesso em Equipe antes". Inativar é permitido.

### Convites (mudança no `identity`, P5a)

- [x] `POST /team/invites` ganha `barber_id` (opcional): o aceite **liga** o login novo a esse
      barbeiro. Barbeiro inexistente ou fora do escopo de quem convida → `400`; já ligado a um
      login (ou a outro convite pendente) → `409`.
- [x] Convite com `role = barber` sem `barber_id` → `422` "Escolha o barbeiro cadastrado".
- [x] `create_barber` sai do `InviteIn`, e o aceite **não cria mais barbeiro** em nenhum caso.
      A coluna `invites.create_barber` deixa de ser lida e é removida numa migration posterior
      (contract), para o build anterior continuar funcionando durante o deploy.
- [x] O convite de primeiro acesso do dono (provisionamento) não muda: dono sem barbeiro; se ele
      também atende, o vínculo é feito depois pelo cadastro do barbeiro (P5b).

## Data Contract

```text
# Serviços — módulo catalog, tag "catalog"
GET    /services?active=true|false             → 200 ServiceOut[]
POST   /services          ServiceIn            → 201 ServiceOut | 403 | 409 | 422
GET    /services/{id}                          → 200 ServiceOut | 404
PATCH  /services/{id}     ServiceUpdate        → 200 ServiceOut | 403 | 404 | 409 | 422
DELETE /services/{id}                          → 204 | 403 | 404 | 409
PUT    /barbers/{id}/services  {service_ids}   → 200 ServiceOut[] (os habilitados) | 400 | 403 | 404

ServiceIn     {name, description?, duration_minutes, price_cents, active? = true}
ServiceUpdate {name?, description?, duration_minutes?, price_cents?, active?}
ServiceOut    {id, name, description, duration_minutes, price_cents, active, barber_ids[],
               created_at, updated_at}

# Clientes — módulo clients, tag "clients"
GET    /clients?q=&active=&limit=50&offset=0   → 200 {items: ClientOut[], total}
POST   /clients           ClientIn             → 201 ClientOut | 409 | 422
GET    /clients/{id}                           → 200 ClientOut | 404
PATCH  /clients/{id}      ClientUpdate         → 200 ClientOut | 404 | 409 | 422
DELETE /clients/{id}                           → 204 | 404 | 409

ClientIn      {name, phone, email?, birth_date?, notes?, active? = true}
ClientUpdate  {name?, phone?, email?, birth_date?, notes?, active?}
ClientOut     {id, name, phone (E.164), email, birth_date, notes, active, created_at, updated_at}

# Barbeiros — módulo identity, tag "barbers"
GET    /barbers?unit_id=&active=               → 200 BarberOut[]
POST   /barbers           BarberIn             → 201 BarberOut | 403 | 422
GET    /barbers/{id}                           → 200 BarberOut | 404
PATCH  /barbers/{id}      BarberUpdate         → 200 BarberOut | 403 | 404 | 422
DELETE /barbers/{id}                           → 204 | 404 | 409

BarberIn      {name, unit_id, initials?, default_commission? = 40, active? = true, user_id?}
BarberUpdate  {name?, unit_id?, initials?, default_commission?, active?, user_id?}
BarberOut     {id, name, initials, unit_id, default_commission, active, user_id, email,
               created_at, updated_at}

# Mudança em rota existente (quebra o contrato: create_barber sai)
POST   /team/invites      InviteIn − {create_barber} + {barber_id?}
                          → como hoje; 400/409/422 novos (ver regras)

Erros: sempre {"detail": "<mensagem em português>"}; 422 é a validação do FastAPI.
```

### Banco de dados

Uma migration de tenant, `t0002_registry` (expand only — tabelas novas, nada renomeado):

```text
services        id uuid pk · name varchar(80) · description varchar(500) null ·
                duration_minutes smallint check (5..480, % 5 = 0) ·
                price_cents integer check (>= 0) · active bool · created_at · updated_at
                UNIQUE INDEX uq_service_name ON lower(name)

barber_services id uuid pk · barber_id → barbers.id ON DELETE CASCADE ·
                service_id → services.id ON DELETE CASCADE
                UNIQUE (barber_id, service_id) · INDEX (service_id)

clients         id uuid pk · name varchar(120) · phone varchar(16) · email varchar(255) null ·
                birth_date date null · notes varchar(1000) null · active bool ·
                created_at · updated_at
                UNIQUE (phone)

invites         + barber_id uuid null → barbers.id ON DELETE SET NULL
                  (create_barber fica até a migration de contract seguinte)
```

`barbers` não muda. Nenhum `GRANT` novo: os default privileges do provisionamento já cobrem tabelas
novas (DEC-012). Futuras FKs da agenda para `barbers`, `services` e `clients` serão
`ON DELETE RESTRICT` — é isso que faz o `409` da P1 valer sem código extra.

## Permissões

Sem mudança no mapa (`docs/PERMISSIONS_MAP.md` continua igual). Como cada rota usa:

| Rota | Permissão | owner | manager | receptionist | barber |
|---|---|---|---|---|---|
| `GET /services` | `catalog:read` | todos | todos | todos | todos |
| escrita em `/services` | `catalog:write` + todas as unidades | sim | só se vê todas as unidades | — | — |
| `PUT /barbers/{id}/services` | `team:manage` | todos | barbeiros das suas unidades | — | — |
| `GET /clients` | `client:read` | todos | todos (P3) | todos (P3) | os que atendeu (vazio até a agenda) |
| escrita em `/clients` | `client:write` | sim | sim | sim | — |
| `GET /barbers` | `team:read` | todos | suas unidades | suas unidades | — |
| escrita em `/barbers` | `team:manage` | sim | suas unidades | — | — |

## Acceptance Criteria

- [x] Módulos `catalog` e `clients` com o layout completo (`router/ service/ repository/ model/`
      + `schemas.py` + `public.py`), registrados no `model_registry`, no `main.py` e no contrato de
      camadas do `pyproject.toml`; `test_module_layout` e `lint-imports` verdes.
- [x] `catalog` e `clients` importam o `identity` só pelo `public.py`; `identity` não importa
      nenhum dos dois (o vínculo barbeiro ↔ serviço mora no `catalog` por isso).
- [x] Migration `t0002_registry` aplicada no `tenant_template` e em toda barbearia (`make migrate`);
      `alembic check` limpo nos dois conjuntos.
- [x] `tests/test_catalog/`, `tests/test_clients/` e `tests/test_identity/test_barbers.py`: um teste
      por regra acima, o teste de **cruzamento entre duas barbearias** em cada um, e os escopos
      (gerente de uma unidade, recepção, barbeiro).
- [x] Testes de vínculo: convite com `barber_id` liga e não duplica (o `/auth/me` do login novo
      traz o `barber_id` do cadastro existente); convite `barber` sem `barber_id` é recusado;
      nenhum aceite cria barbeiro; `user_id` no cadastro liga o dono que também corta. Os testes
      atuais que contam com `create_barber` são reescritos.
- [x] Snapshots (`openapi.json`, `routes.json`, `db_schema.json`) regenerados com o diff lido: só as
      rotas, tabelas e o campo `barber_id` desta spec.
- [x] `tools/api_docs.py` com os grupos novos (`catalog.md`, `clients.md`, `barbers.md`) e
      `make docs-api` rodado.
- [x] `make check` verde (backend e frontend).
- [x] Memória atualizada: `progress.md` (catálogo e clientes `stable` para o escopo desta spec),
      `issues.md`, `decisions.md` (DEC nova para P1–P6 depois de confirmadas).

## Dependencies

- `✅completed_identity-schema-per-tenant.md` — schema por barbearia, `TenantBase`, migrations de
  tenant.
- `✅completed_identity-core.md` — RBAC com escopo, convites.
- Espelho: `frontend/docs/specs/⏳active_frontend-registry-basic-crud.md` (telas de Cadastros e
  Clientes saindo do mock).

## Notes

- **Onde mora o barbeiro.** DEC-007 manda reavaliar quando a agenda chegar. Com os cadastros
  separados, o aceite de convite não cria mais barbeiro, mas ainda **liga** um a outro e o token
  carrega o `barber_id`; mover `Barber` para um módulo próprio agora criaria ciclo (o módulo novo
  dependeria do `identity` para autenticar, e o `identity` dele para o vínculo). As rotas `/barbers` ficam no `identity`, e o que é
  catálogo (serviços habilitados) fica no `catalog`, que aponta para `barbers.id` por FK em string,
  sem importar o model. A reavaliação continua valendo para a spec da agenda.
- **Jornada / horas por semana** aparecem no protótipo da tela de barbeiros, mas são
  disponibilidade: entram na spec da agenda, não aqui.
- **LGPD.** Apagar cliente sem histórico é exclusão real. Quando houver histórico, a exclusão vira
  anonimização (nome e telefone trocados, histórico mantido) — spec própria, junto com a agenda.
- **Cliente vindo do WhatsApp.** O módulo de conversas vai criar cliente pelo telefone; a regra de
  unicidade em E.164 desta spec é o que evita duplicata. O serviço de criação fica exposto no
  `clients/public.py` para isso.
- > Resolvido em 2026-11-06: implementado como especificado. Notas de implementação: o vínculo
  > barbeiro ↔ login feito pelo `PATCH /barbers` entra no token na próxima renovação (o `bid` vai no
  > JWT; até 15 min — ISS-018); `invites.create_barber` aguarda a migration de contract (ISS-019).
  > Testes: `tests/test_identity/test_barbers.py`, `tests/test_catalog/`, `tests/test_clients/`.
- **Busca com acento.** `lower(name)` não iguala "José" e "Jose". Se a busca incomodar, a extensão
  `unaccent` entra numa migration própria (precisa de DDL no `public` do migrator).
