# Unidades, expediente, feriados e configurações da barbearia

**Priority:** high
**Status:** active
**Espelho no frontend:** `frontend/docs/specs/⏳active_frontend-units-settings.md`

## Overview

A agenda (S02, S03) precisa saber **quando a unidade está aberta** para oferecer horário, e a IA e o
link (S11, S04) precisam das **políticas** da barbearia (antecedência mínima, até quando o cliente
pode cancelar…). Hoje a unidade existe só como linha mínima (`units`: nome, fuso, endereço,
telefone, ativa), criada no provisionamento e listada em `GET /tenant/units`; não há tela, nem
expediente, nem feriado, nem configuração. Esta spec entrega:

1. **CRUD de unidades** respeitando o limite de unidades do plano (S15).
2. **Expediente semanal** por unidade (até 3 intervalos por dia).
3. **Exceções de calendário** por unidade: dia fechado (feriado, reforma) ou horário especial
   (véspera de Natal 08:00–14:00), criadas para uma ou várias unidades de uma vez — como os "closed
   periods" do Fresha e os feriados do Trinks.
4. **Configurações da barbearia** (`shop_settings`): contato público e políticas de agendamento.
5. Funções no `identity/public.py` que a agenda usa para montar o calendário efetivo de uma unidade.

O nome da barbearia e o domínio próprio continuam no control plane (`PATCH /tenant`, já existe).

## Decisões de produto já tomadas

| Parâmetro | Valor |
|---|---|
| Fuso | Cada unidade tem `timezone` (padrão `America/Sao_Paulo`); horário de expediente e "dia" são calculados nele (ROADMAP §2) |
| Grade | Horários oferecidos em grade de 15 min (PD-04) — não é configuração; o expediente pode ter qualquer minuto múltiplo de 5 |
| "Não confirmado" | Prazo **X horas antes** configurável; nunca cancela sozinho (PD-07) — o prazo mora aqui, a regra em S03 |
| Cliente | Pertence à barbearia, não à unidade (PD-03) — nada aqui é por cliente |
| Apagar | Só sem histórico; com histórico, inativar (DEC-016 P1) |
| Limite de unidades | Vem do plano (PD-22, S15); a regra de bloqueio está aqui |
| Primeiros passos | O assistente de onboarding (PD-23, S16) usa estas rotas; não há rota especial para ele |
| PD-33 | **Expediente e feriados** da unidade: dono em todas; gerente nas unidades dele (permissão nova `unit:configure`). Criar/apagar unidade e políticas da barbearia continuam só do dono |
| PD-41 | **Contato do cliente para o barbeiro**: configurável, **padrão oculto** (barbeiro vê nome e histórico). O campo `barber_sees_client_contact` mora em `shop_settings`; a S13 aplica. |

### Decisões técnicas desta spec

| # | Decisão |
|---|---|
| T1 | Rotas sob `/tenant/units` (já existe o `GET`; o `UnitOut` só **ganha** campos, sem quebrar o contrato). |
| T2 | Dia da semana ISO: 1 = segunda … 7 = domingo (`date.isoweekday()`). |
| T3 | Intervalo não cruza a meia-noite (`opens_at < closes_at`, ambos no mesmo dia). Barbearia que fecha depois da meia-noite fica fora por ora. |
| T4 | Configurações são **da barbearia** (uma linha), não por unidade (Q-S01-4, resolvida). |
| T5 | A normalização de telefone (hoje em `clients/phone.py`) desce para `app/core/phone.py` (sem regra de negócio, só formato E.164); `clients.public` continua reexportando. Assim `identity` valida o telefone da unidade sem importar `clients`. |
| T6 | Unidade nova nasce com expediente padrão seg–sáb 09:00–19:00 (editável), para a agenda nunca nascer vazia; a migration aplica o mesmo padrão às unidades que já existem. |

## Business Rules

### Unidades

- [x] Campos: `name` (2–120, único sem diferença de maiúsculas), `timezone` (IANA válido para
      `zoneinfo`; inválido → `422` "Fuso horário inválido"), `address` (opcional, até 300),
      `phone` (opcional, normalizado para E.164), `online_booking` (padrão `true`: a unidade aparece
      para a IA e no link), `active`.
- [ ] Criar unidade ativa, ou reativar uma, chama `assert_within_limit(session, tenant,
      PlanLimit.MAX_UNITS)` (S15) na mesma transação: atingido → `402` com o corpo padrão da
      S15 (`detail` "Seu plano permite até N unidades…", `code: plan_limit_reached`, `limit`, `max`,
      `used`). Unidade inativa não conta.
- [x] Inativar a **última** unidade ativa → `409` "A barbearia precisa de pelo menos uma unidade
      ativa".
- [x] Inativar unidade com barbeiros ativos → `409` "Mova ou inative os barbeiros desta unidade
      antes". (Agendamentos futuros são do S03, que os destaca na agenda — ver Q-S01-3.)
- [x] `DELETE` só sem histórico (P1): barbeiros (`RESTRICT`, já existe) e agendamentos (S03,
      `RESTRICT`) fazem o banco recusar → `409` "Esta unidade tem histórico; inative em vez de
      apagar".
- [x] `DELETE` também é recusado (`409` "Há usuários com acesso a esta unidade; ajuste em Equipe
      antes") se houver `user_units` apontando para ela: hoje o `CASCADE` apagaria o vínculo e o
      usuário restrito a essa unidade passaria a ver **todas** (lista vazia = todas).
- [x] Mudar `timezone` não move nada em UTC; a resposta é normal, e o frontend avisa que os
      horários locais dos agendamentos futuros mudam.
- [x] Escopo: listar/ler usa `ctx.unit_filter` como o `GET /tenant/units` atual; unidade fora do
      alcance → `404`.
- [x] Criar, editar os dados (`PATCH`: nome, fuso, endereço, telefone, `online_booking`, `active`) e
      apagar unidade exigem `tenant:configure` (só o dono). Expediente e exceções usam
      `unit:configure` (PD-33, abaixo).

### Expediente semanal

- [x] `PUT /tenant/units/{id}/hours` **substitui** a semana inteira: lista de 7 dias, cada um com
      0–3 intervalos; dia sem intervalo = fechado. Exige `unit:configure` (PD-33): dono em qualquer
      unidade, gerente só nas unidades dele (fora do alcance → `404`).
- [x] Cada intervalo: `opens_at < closes_at`, minutos múltiplos de 5; intervalos do mesmo dia não se
      sobrepõem nem se encostam (encostados → `422` "Junte os intervalos que se encostam").
- [x] A semana toda fechada é permitida (unidade temporariamente parada), mas a resposta traz
      `warning: "Unidade sem nenhum horário de funcionamento"`.
- [x] Mudar o expediente não mexe em agendamento existente; o que ficar fora aparece destacado na
      agenda (S03, `flags`).

### Exceções de calendário (feriados, dias fechados, horário especial)

- [x] Campos: `unit_id`, `starts_on`, `ends_on` (inclusivo, `ends_on >= starts_on`, no máximo 366
      dias), `kind` (`closed` | `special_hours`), `opens_at`/`closes_at` (obrigatórios só em
      `special_hours`, um intervalo, mesma regra do expediente), `reason` (opcional, até 120 — a IA
      usa para explicar: "Estaremos fechados no feriado de Finados").
- [x] Criar, editar e apagar exceção exige `unit:configure` com a unidade no alcance (PD-33).
- [x] `POST` recebe `unit_ids` (uma ou várias, todas no alcance do usuário em `unit:configure`) e
      cria uma exceção por unidade na mesma transação; qualquer unidade inválida ou fora do alcance →
      `400` e nada é criado.
- [x] Duas exceções da mesma unidade não se sobrepõem em datas → `409` "Já existe uma exceção nesse
      período nesta unidade".
- [x] Não se cria nem se edita exceção que termina antes de hoje (no fuso da unidade) → `422`
      "Data no passado". Apagar exceção passada é permitido.
- [x] Exceção vence o expediente semanal no(s) dia(s) dela: `closed` = fechado o dia todo;
      `special_hours` = só aquele intervalo.
- [x] Exceção `closed` (ou `special_hours` menor) num dia que já tem agendamentos é **permitida**
      (Q-S01-3): a tela conta antes de salvar quantos agendamentos serão afetados lendo a agenda da
      S03 (`GET /appointments` do período — o `identity` não importa o `scheduling`, DEC-006), e a
      agenda destaca os afetados (`flags`). O aviso automático aos clientes entra com a S12.
- [x] **Feriados nacionais sugeridos** (Q-S01-2): `GET /tenant/holidays?year=` devolve a lista fixa
      do backend (nacionais, com os móveis calculados — Carnaval, Sexta-feira Santa, Corpus Christi)
      com `already_closed` por unidade; o dono/gerente marca quais fecha e a tela cria as exceções
      `closed` pelo `POST` normal. Nada fecha sozinho.

### Configurações da barbearia (`shop_settings`)

- [x] Uma linha só por barbearia, criada pela migration (barbearias existentes) e pelo
      `bootstrap_tenant` (novas), com os padrões abaixo. `GET` nunca devolve `404`.
- [x] Contato público: `contact_phone` (E.164, opcional), `instagram` (até 60, sem `@`),
      `about` (até 1000: texto da página pública e contexto da IA).
- [x] Políticas (padrões confirmados em Q-S01-5):
  - `min_advance_minutes` (0–2880, múltiplo de 15; padrão 60) — antecedência mínima para o
    **cliente** agendar pela IA ou link. A equipe no painel não tem esse limite.
  - `max_advance_days` (1–180; padrão 30) — até quantos dias à frente o cliente vê horário.
  - `confirmation_deadline_hours` (1–48; padrão 3) — sem confirmação até X h antes, o agendamento
    vira "não confirmado" (PD-07).
  - `client_change_min_hours` (0–72; padrão 2) — até quantas horas antes o **cliente** cancela ou
    remarca sozinho; depois disso a IA passa para a recepção (handoff, PD-18).
  - `late_tolerance_minutes` (0–60; padrão 10) — tolerância de atraso: a IA informa o cliente, e a
    falta (no-show) só pode ser marcada depois de `início + tolerância` (S03).
  - `max_future_appointments_per_client` (1–20; padrão 3) — quantos agendamentos futuros o mesmo
    cliente pode ter marcados pela IA ou pelo link (Q-S03-4); a equipe no painel não tem limite. A
    regra é aplicada pela S03.
- [x] Privacidade (PD-41): `barber_sees_client_contact` (padrão `false`) — com ele desligado, o
      barbeiro (escopo `own`) vê nome, histórico e indicadores do cliente, mas telefone e e-mail
      mascarados. A regra é aplicada pela S13 (ficha do cliente) e pela S18 ("Meu dia").
- [x] `PATCH` parcial; `updated_by_user_id` registra quem mudou.

## Data Contract

```text
# Unidades — tag "shop"
GET    /tenant/units?active=true|false          → 200 UnitOut[]     (já existe; ganha campos)
POST   /tenant/units          UnitIn            → 201 UnitOut | 402 | 403 | 409 | 422
GET    /tenant/units/{id}                       → 200 UnitOut | 404
PATCH  /tenant/units/{id}     UnitUpdate        → 200 UnitOut | 402 | 403 | 404 | 409 | 422
DELETE /tenant/units/{id}                       → 204 | 403 | 404 | 409

UnitIn      {name, timezone? = "America/Sao_Paulo", address?, phone?, online_booking? = true,
             active? = true}
UnitUpdate  {name?, timezone?, address?, phone?, online_booking?, active?}
UnitOut     {id, name, timezone, address, phone, online_booking, active, created_at, updated_at}

# Expediente
GET    /tenant/units/{id}/hours                 → 200 WeeklyHoursOut | 404
PUT    /tenant/units/{id}/hours  WeeklyHoursIn  → 200 WeeklyHoursOut | 403 | 404 | 422

WeeklyHoursIn   {days: [{weekday: 1..7, intervals: [{opens_at: "HH:MM", closes_at: "HH:MM"}]}]}
                (exatamente 7 dias, sem repetir weekday)
WeeklyHoursOut  {unit_id, days: [...mesmo formato], warning: str | null}

# Exceções de calendário
GET    /tenant/unit-exceptions?unit_id=&from=&to=     → 200 UnitExceptionOut[]
       (from/to datas; padrão: hoje até +365 dias; ordenado por starts_on)
POST   /tenant/unit-exceptions   UnitExceptionIn      → 201 UnitExceptionOut[] | 400 | 403 | 409 | 422
PATCH  /tenant/unit-exceptions/{id} UnitExceptionUpdate → 200 UnitExceptionOut | 403 | 404 | 409 | 422
DELETE /tenant/unit-exceptions/{id}                   → 204 | 403 | 404

# Feriados nacionais sugeridos (Q-S01-2)
GET    /tenant/holidays?year=                         → 200 HolidayOut[]
HolidayOut          {date, name, already_closed_unit_ids: uuid[]}

UnitExceptionIn     {unit_ids: uuid[1..], starts_on, ends_on, kind, opens_at?, closes_at?, reason?}
UnitExceptionUpdate {starts_on?, ends_on?, kind?, opens_at?, closes_at?, reason?}
UnitExceptionOut    {id, unit_id, starts_on, ends_on, kind, opens_at, closes_at, reason,
                     created_at, updated_at}

# Configurações
GET    /tenant/settings                          → 200 ShopSettingsOut
PATCH  /tenant/settings   ShopSettingsUpdate     → 200 ShopSettingsOut | 403 | 422

ShopSettingsOut    {contact_phone, instagram, about, min_advance_minutes, max_advance_days,
                    confirmation_deadline_hours, client_change_min_hours,
                    late_tolerance_minutes, max_future_appointments_per_client,
                    barber_sees_client_contact, updated_at}
ShopSettingsUpdate {todos os campos acima, opcionais}

Erros: {"detail": "<mensagem em português>"}; 402 traz a mensagem de upgrade do plano.
```

### Funções públicas (`identity/public.py`) usadas por S02, S03, S04, S11

```text
get_unit(session, unit_id) -> UnitInfo | None           # id, name, timezone, online_booking, active
list_units(session, *, active_only, online_only) -> list[UnitInfo]
get_unit_calendar(session, unit_id, start: date, end: date) -> UnitCalendar
    UnitCalendar {unit_id, timezone: ZoneInfo,
                  days: dict[date, list[tuple[time, time]]],   # intervalos abertos já com exceções
                  closed_reason: dict[date, str | None]}      # dia fechado por exceção
get_shop_settings(session) -> ShopSettings              # dataclass imutável com as políticas
list_servable_tenants() -> list[ServableTenant]         # S00
```

### Banco de dados

Migration de tenant `t000N_units_hours` (expand):

```text
units               + address  → varchar(300) (hoje text; só encurta se nenhum valor passar — ver Notes)
                    + online_booking bool not null default true
                    + UNIQUE INDEX uq_unit_name ON lower(name)
unit_business_hours id uuid pk · unit_id → units.id ON DELETE CASCADE · weekday smallint
                    check (1..7) · opens_at time · closes_at time · check (opens_at < closes_at)
                    INDEX (unit_id, weekday)
unit_exceptions     id uuid pk · unit_id → units.id ON DELETE CASCADE · starts_on date ·
                    ends_on date · kind enum unit_exception_kind(closed, special_hours) ·
                    opens_at time null · closes_at time null · reason varchar(120) null ·
                    created_by_user_id uuid null → users.id ON DELETE SET NULL · created_at · updated_at
                    check (ends_on >= starts_on) ·
                    check ((kind = 'closed' AND opens_at IS NULL AND closes_at IS NULL) OR
                           (kind = 'special_hours' AND opens_at < closes_at))
                    EXCLUDE USING gist (unit_id WITH =, daterange(starts_on, ends_on, '[]') WITH &&)
                      name ex_unit_exception_overlap   (precisa de btree_gist — ver S03)
shop_settings       id smallint pk check (id = 1) · contact_phone varchar(16) null ·
                    instagram varchar(60) null · about varchar(1000) null ·
                    min_advance_minutes smallint default 60 · max_advance_days smallint default 30 ·
                    confirmation_deadline_hours smallint default 3 ·
                    client_change_min_hours smallint default 2 · late_tolerance_minutes smallint default 10 ·
                    max_future_appointments_per_client smallint default 3 ·
                    barber_sees_client_contact bool not null default false ·
                    updated_by_user_id uuid null → users.id ON DELETE SET NULL · updated_at
                    (checks com as faixas das regras)
```

Dados na migration: `shop_settings` (id 1) e o expediente padrão seg–sáb 09:00–19:00 para cada
unidade existente (T6). Sem `GRANT` novo.

## Permissões

**Permissão nova `unit:configure`** (PD-33): owner `all`, manager `unit`; receptionist e barber não
têm. Justificativa: em rede com gerente por loja, é ele quem fecha a loja num feriado municipal ou
muda o horário dela; dar `tenant:configure` ao gerente liberaria também renomear a barbearia, mudar
as políticas e criar/apagar unidades. Entra no mapa de `app/modules/identity/permissions.py`
(DEC-004), em `docs/PERMISSIONS_MAP.md` e no snapshot de permissões; usuários existentes ganham pelo
cargo, sem migration de dado.

| Rota | Permissão | owner | manager | receptionist | barber |
|---|---|---|---|---|---|
| `GET /tenant/units`, `/hours`, `/unit-exceptions`, `/holidays` | autenticado + unidade no alcance | todas | suas unidades | suas unidades | sua unidade |
| `POST`/`PATCH`/`DELETE /tenant/units` | `tenant:configure` | sim | — | — | — |
| `PUT /hours`, escrita em `/unit-exceptions` | `unit:configure` | todas | suas unidades | — | — |
| `GET /tenant/settings` | autenticado | sim | sim | sim | sim |
| `PATCH /tenant/settings` | `tenant:configure` | sim | — | — | — |

## Acceptance Criteria

- [x] Rotas novas no `identity/router/tenant.py` (ou `units.py` + `settings.py`), services um por
      ação, repositórios `units`, `unit_hours`, `unit_exceptions`, `shop_settings`.
- [x] `app/core/phone.py` com a normalização; `clients` passa a usá-la; testes de cliente
      continuam verdes.
- [x] `get_unit_calendar` testado: semana normal, dia sem expediente, exceção `closed` de vários
      dias, `special_hours`, intervalo atravessando a virada do horário de verão de outro fuso
      (unidade com `timezone` diferente de São Paulo).
- [ ] `tests/test_identity/test_units.py`, `test_unit_hours.py`, `test_unit_exceptions.py`,
      `test_shop_settings.py`: uma prova por regra, inclusive `402` do limite de plano (com limite
      simulado), última unidade ativa, unidade com `user_units` e o teste de **cruzamento entre duas
      barbearias** (unidade, expediente, exceção e configurações de A invisíveis e intocáveis em B).
- [x] `unit:configure` no mapa de permissões: gerente edita expediente e exceções das unidades dele
      (`200`) e recebe `404` nas outras; gerente não cria/edita/apaga unidade nem muda
      `/tenant/settings` (`403`); recepção e barbeiro recebem `403` na escrita. Snapshot de
      permissões e `docs/PERMISSIONS_MAP.md` atualizados.
- [x] Feriados sugeridos: lista do ano com os móveis corretos (teste com 2026 e 2027) e
      `already_closed_unit_ids` refletindo as exceções existentes.
- [x] `bootstrap_tenant` cria `shop_settings` e o expediente padrão da primeira unidade; provisionar
      duas vezes não duplica (idempotente).
- [x] Snapshots (`openapi`, `routes`, `db_schema`) regenerados com o diff lido; `make docs-api`.
- [x] `make check` verde; `progress.md`, `issues.md`, DEC nova (T1–T6 e respostas das perguntas).

## Dependencies

- S15 (`provisioning-plan-entitlements`) — **assumido**: `identity.public.assert_within_limit(session,
  tenant, PlanLimit.MAX_UNITS)` e a exceção `PaymentRequired` (402) — a S15 põe o plano
  efetivo no `identity`, que está abaixo do `provisioning`, então não há import para cima. Até S15
  existir, sem limite.
- S03 cria a extensão `btree_gist` (migration de controle); se S01 for implementada antes, a
  migration de controle entra aqui.
- Consumidores: S02, S03 (`get_unit_calendar`, `get_shop_settings`), S04 e S11 (políticas e
  `online_booking`), S16 (onboarding: unidade e horários).

## Notes

### Implementação (2026-11-06)

- **Pendente da S15:** o `402` de limite de unidades (regra e teste com limite simulado). O ponto de
  chamada está marcado em `create_unit.py` e `update_unit.py`; até a S15, sem limite (como previsto em
  Dependencies). Por isso a spec continua `⏳active`.
- **Pendente da S00:** `list_servable_tenants()` entra com o worker.
- `units.address` ficou `text` no banco, com o limite de 300 só no schema (Notes acima) — evita
  `ALTER` com risco em barbearias que já têm dado.
- A extensão `btree_gist` entrou aqui (`c0002_btree_gist`); a exclusion constraint funciona com o
  `search_path` da migration restrito ao schema da barbearia e com o role de runtime (sem `USAGE`
  no `public`) — provado pelos testes de sobreposição.
- `app/core/exceptions.py` ganhou `UnprocessableEntity` (422) para regras que precisam de dado
  guardado ("Data no passado", período da exceção editada).
- Funções públicas: `get_unit`, `list_units`, `get_unit_calendar`, `get_shop_settings` em
  `identity.public` (dataclasses `UnitInfo`, `UnitCalendar`, `ShopPolicies`).
- Testes: `test_units.py` (6), `test_unit_hours.py` (4), `test_unit_exceptions.py` (6),
  `test_shop_settings.py` (3), incluindo o cruzamento entre duas barbearias.
- A limpeza da suíte (`tests/conftest.py`) passou a apagar um schema por transação: com mais objetos
  por barbearia, apagar todos de uma vez estourava `max_locks_per_transaction`.

- `units.address` hoje é `text` sem limite; a migration só aplica `varchar(300)` depois de conferir
  que nenhuma linha passa disso (se passar, fica `text` e a validação é só no schema).
- Endereço estruturado (CEP, cidade, link do mapa) e logo/foto da barbearia ficam para S04 (página
  pública), que define onde guardar arquivo.
- Feriado móvel e lista de feriados nacionais: Q-S01-2 (resolvida — sugestão, o dono marca).
  Feriados estaduais e municipais continuam manuais.

### Perguntas em aberto

- ✅ **Q-S01-1 — Quem edita horários e feriados da unidade?**
  (a) Só o dono (`tenant:configure`, como está no contrato acima). (b) Dono e gerente, este só nas
  unidades dele — exige permissão nova `unit:configure` (owner `all`, manager `unit`), porque dar
  `tenant:configure` ao gerente liberaria renomear a barbearia. (c) Dono, gerente e recepção.
  **Recomendação: (b)** — em rede com gerente por loja, é ele quem fecha a loja num feriado
  municipal; criar e apagar unidade continua só do dono.
  > Resolvido em 2026-11-06: (b) — permissão nova `unit:configure` (dono `all`, gerente `unit`) para
  > expediente, horários especiais e feriados/fechamentos; criar, editar e apagar unidade e as
  > políticas continuam `tenant:configure` (PD-33).
- ✅ **Q-S01-2 — Feriados nacionais.** (a) Só manual. (b) O sistema sugere os feriados nacionais do
  ano (lista fixa no backend) e o dono marca quais fecha. (c) Fecha automaticamente em todo
  feriado nacional. **Recomendação: (b)** — muita barbearia abre em feriado; fechar sozinho geraria
  agenda bloqueada sem querer.
  > Resolvido em 2026-11-06: (b) — o sistema sugere os feriados nacionais do ano e o dono marca
  > quais fecha (ROADMAP §7).
- ✅ **Q-S01-3 — Fechamento criado num dia que já tem agendamentos.** (a) Bloquear até a recepção
  remarcar tudo. (b) Permitir; a agenda destaca os afetados e a recepção avisa os clientes.
  (c) Permitir e a IA avisa os clientes oferecendo remarcar (depende de S12). **Recomendação: (b)
  agora e (c) quando S12 existir** — a tela mostra antes de salvar quantos agendamentos serão
  afetados.
  > Resolvido em 2026-11-06: (b) agora — permitido, com os agendamentos destacados na agenda; aviso
  > automático aos clientes quando a S12 existir (ROADMAP §7).
- ✅ **Q-S01-4 — Políticas por barbearia ou por unidade?** (a) Uma configuração para a barbearia toda.
  (b) Por unidade, com o padrão da barbearia. **Recomendação: (a)** — a maioria tem uma unidade;
  sobrescrita por unidade entra depois sem quebrar este contrato.
  > Resolvido em 2026-11-06: (a) — políticas valem para a barbearia inteira (ROADMAP §7).
- ✅ **Q-S01-5 — Valores padrão das políticas.** Antecedência mínima 60 min, horizonte 30 dias,
  "não confirmado" 3 h antes, cliente muda sozinho até 2 h antes, tolerância de atraso 10 min.
  (a) Aceitar. (b) Ajustar algum valor. **Recomendação: (a)** — são os padrões mais comuns nos
  apps de agendamento de barbearia (AppBarber, Trinks).
  > Resolvido em 2026-11-06: (a) — 60 min, 30 dias, 3 h, 2 h e 10 min (ROADMAP §7). Junto, o limite
  > de agendamentos futuros por cliente na IA/link, padrão 3 (Q-S03-4), entra em `shop_settings`.
