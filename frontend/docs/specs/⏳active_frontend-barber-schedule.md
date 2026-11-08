# Escala dos barbeiros, folgas e bloqueios no painel

**Priority:** high
**Status:** active
**Espelho no backend:** `backend/docs/specs/⏳active_scheduling-barber-schedule.md`

## Overview

A agenda só oferece horário quando sabe quem trabalha quando. Esta spec cria, na feature
`scheduling`, as telas para a gerência montar a **escala semanal** de cada barbeiro (com o almoço
como pausa), lançar **turnos especiais** de um dia, **folgas, férias e atestados**, e para a
recepção e o próprio barbeiro (na coluna dele, Q-S02-3) **bloquearem um horário** direto na agenda. É o que o
protótipo chama de "Editar escala do dia" no estado vazio da agenda. Regras e contrato completos
estão no espelho do backend.

## Decisões de produto já tomadas

| Parâmetro | Valor |
|---|---|
| Onde fica | Dentro da agenda: abas **Agenda · Escala · Ausências** no topo de `/app/agenda` (feature `scheduling`, ROADMAP §3) |
| Jornada | Intervalos por dia; a tela mostra como "expediente + pausa" (T1 do backend) |
| Barbeiro sem escala | Segue o horário da unidade e aparece com a etiqueta "Horário da unidade" (T2) |
| Ausência sobre agendamentos | Permitida; a tela lista os afetados depois de salvar (T5, Q-S01-3) |
| Bloqueio | Criado a partir da própria agenda (clicar num horário vazio → "Bloquear horário"); o barbeiro bloqueia só a própria coluna, folgas e férias só a gerência (Q-S02-3) |
| PD-34 | Barbeiro em **uma unidade por vez**: a escala é da unidade do cadastro; para cobrir outra loja, muda-se a unidade do barbeiro. Escala por dia/unidade fica para depois |

## Business Rules

### Escala (`/app/agenda/escala`)

- [x] Grade: uma linha por barbeiro ativo da unidade selecionada, colunas segunda a domingo, cada
      célula com o resumo do dia (`09:00–19:00 · pausa 12:00–13:00`, "Folga" ou vazio em cinza
      quando a unidade fecha), e a coluna "Horas/semana" (`weekly_minutes` → `44 h`).
- [x] Barbeiro sem escala salva aparece com a etiqueta "Horário da unidade" e a escala da unidade em
      cinza.
- [x] Clicar na linha abre o **editor da semana** (painel abaixo da grade, como nos cadastros): por
      dia, interruptor "Trabalha", início, fim e até duas pausas (convertidas para intervalos ao
      salvar); "Copiar segunda para dias úteis"; validação local espelhando o backend; `warnings`
      ("fica fora do horário da unidade") como aviso amarelo depois de salvar.
- [x] Desligar todos os dias mostra o erro do backend antes de enviar: "Para afastar o barbeiro,
      registre uma ausência ou inative o cadastro".
- [x] No mesmo painel, a lista **Dias especiais** (turnos especiais futuros) com "Adicionar dia
      especial" (data, horários, motivo) e remover (volta à escala semanal).
- [x] Editar só com `team:manage`; os demais veem a grade só leitura. O barbeiro (`own`) vê só a
      própria linha.

### Ausências (`/app/agenda/ausencias`)

- [x] Lista de ausências de dias inteiros da unidade, de hoje em diante (filtro "Mostrar passadas"),
      com barbeiro, tipo (Folga, Férias, Atestado), período (`12/11 a 26/11 · 15 dias`) e motivo.
- [x] Formulário: barbeiro, tipo, de/até, motivo. Depois de salvar, se `affected_appointments` não
      vier vazio: aviso "N agendamentos de Diego nesse período continuam marcados" com links que
      abrem cada um na agenda.
- [x] `409` de sobreposição aparece no campo de período.
- [x] Criar/editar/apagar com `team:manage`; sem ela, só leitura.

### Bloqueio de horário (na agenda)

- [ ] Clicar num horário vazio da coluna de um barbeiro abre um menu: "Novo agendamento" e
      "Bloquear horário" (este só com `appointment:create` no alcance do barbeiro).
- [ ] O formulário de bloqueio já vem com barbeiro, dia e início do clique; duração em passos de
      15 min (padrão 1 h); motivo opcional. Salvar mostra os afetados como acima.
- [ ] Bloqueios, folgas e horário fora da escala aparecem na agenda como faixas hachuradas na coluna
      do barbeiro (renderização na spec da agenda, S03); clicar num bloqueio permite editar ou
      remover (bloqueio passado não tem "remover").

## Telas e fluxos

| Rota | Tela | Fluxos |
|---|---|---|
| `/app/agenda/escala` | `features/scheduling/pages/ScheduleScreen.tsx` | `pages/schedule/` (grade, editor da semana, dias especiais) |
| `/app/agenda/ausencias` | `features/scheduling/pages/TimeOffScreen.tsx` | `pages/time-off/` (lista, formulário) |
| `/app/agenda` | `AgendaScreen.tsx` (S03) | `pages/agenda/BlockForm.tsx` |

As três telas compartilham o cabeçalho com as abas (`ui/SchedulingTabs.tsx`). A página de barbeiros
em Cadastros ganha o link "Escala" por linha (`/app/agenda/escala?barbeiro=<id>`).

## Data Contract

Contrato completo no espelho do backend. Endpoints consumidos:

```text
GET      /schedules?unit_id=
GET/PUT  /barbers/{id}/schedule
GET      /barbers/{id}/shift-overrides?from&to
PUT/DELETE /barbers/{id}/shift-overrides/{date}
GET/POST /time-off   · PATCH/DELETE /time-off/{id}
GET      /barbers?unit_id=&active=true       (já existe)
```

Arquivos:

```text
features/scheduling/model/schedule.types.ts   BarberSchedule, DaySchedule, ShiftOverride, TimeOff
features/scheduling/model/schedule.rules.ts   "expediente + pausas" ↔ intervalos, validação,
                                              resumo do dia, horas por semana, período em dias
features/scheduling/api/schedule.api.ts · schedule.queries.ts
shared/text/time.ts                           (criado na S01 frontend) "HH:MM" ↔ minutos
```

## Estado

| Estado | Onde |
|---|---|
| Escalas, dias especiais, ausências | TanStack Query: `['schedules', unitId]`, `['shift-overrides', barberId]`, `['time-off', unitId, filtros]` |
| Barbeiro aberto, "mostrar passadas" | URL (`?barbeiro=`, `?passadas=1`) |
| Editor da semana | `useReducer` local |
| Unidade | seletor da barra lateral (`useUnitSelection().unitId`, ver S03 frontend) |

Salvar escala, dia especial, ausência ou bloqueio invalida também `['agenda', unitId]`.

## Permissões

| Ação | Permissão em `/auth/me` |
|---|---|
| ver Escala e Ausências | `appointment:read` |
| editar escala, dias especiais, folgas/férias/atestados | `team:manage` |
| bloquear horário | `appointment:create` (barbeiro só na própria coluna, Q-S02-3) |

## Acceptance Criteria

- [x] Abas Agenda · Escala · Ausências funcionando com a unidade do seletor.
- [x] Testes em `tests/`: conversão expediente + pausas ↔ intervalos (ida e volta), validação do
      editor, resumo do dia, horas por semana, duração do período de ausência. *(A montagem do
      bloqueio a partir do clique vai com a S03.)*
- [x] `make docs-api` regenerado; nenhuma chamada fora do contrato.
- [ ] Tela conferida no navegador como dono, gerente de uma unidade, recepção e barbeiro: editar
      escala, dia especial, férias sobre agendamento existente (lista de afetados), bloqueio pela
      agenda, estados vazio, carregando e erro.
- [x] `make check-frontend` verde; `README.md` e `memory/progress.md` atualizados.

## Dependencies

- Backend `⏳active_scheduling-barber-schedule.md` implementado, com `openapi.json` congelado.
- `⏳active_frontend-units-settings.md` — `shared/text/time.ts` e o horário da unidade.
- `⚪draft_frontend-agenda.md` — a agenda que mostra as faixas e hospeda o bloqueio; o `unitId` no
  seletor de unidade.

## Notes

### Implementação (2026-11-07)

- **Ficam para a S03 (agenda real):** o bloqueio de horário pelo clique na agenda e as faixas
  hachuradas de bloqueio, folga e fora da escala. As rotas de bloqueio já existem no backend.
- **Falta:** conferir no navegador (ISS-010). Por isso a spec continua `⏳active`.
- O seletor de unidade da barra lateral passou a expor `unitId` (`null` = todas as unidades); as
  telas de Escala e Ausências filtram por ele.
- Nomes dos barbeiros vêm de `GET /barbers` (`team:read`); o barbeiro, que não tem essa permissão,
  vê o próprio nome a partir do `/auth/me`.
- Cadastros → Barbeiros ganhou o link "Escala" por linha (`/app/agenda/escala?barbeiro=<id>`).
- Testes: `tests/schedule-rules.test.ts` (11) e `unitOptionsFor` em `unit-selection.test.ts`.

- Arrastar para pintar a escala (estilo planilha) fica para depois; o editor por formulário cobre o
  caso.
- Perguntas de produto: Q-S02-1 a Q-S02-3 no espelho do backend.
  > Resolvido em 2026-11-06: Q-S02-1 = uma unidade por vez (PD-34); Q-S02-2 = turno especial só
  > dentro do horário da unidade; Q-S02-3 = o barbeiro bloqueia horários pontuais da própria
  > agenda, folgas só a gerência (PD-34 | ROADMAP §7).
