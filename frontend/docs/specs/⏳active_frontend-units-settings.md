# Unidades, horários e configurações da barbearia no painel

**Priority:** high
**Status:** active
**Espelho no backend:** `backend/docs/specs/⏳active_identity-units-hours.md`

## Overview

O cadastro "Unidades" em `/app/cadastros` hoje mostra "Em breve", e não existe tela de
configurações. Esta spec liga as duas coisas à API: a página **Unidades** (lista, formulário,
expediente semanal e feriados/datas especiais) e a nova feature **`settings`** em
`/app/configuracoes`, com as seções "Barbearia" (nome, contato, texto de apresentação) e
"Agendamento" (políticas). As próximas specs (WhatsApp S10, IA S11, automações S12) acrescentam
seções a essa mesma tela. Regras e contrato completos estão no espelho do backend.

## Decisões de produto já tomadas

| Parâmetro | Valor |
|---|---|
| Onde fica | Unidades: `/app/cadastros/unidades` (feature `registry`, item que já existe). Configurações: `/app/configuracoes` (feature nova `settings`, ROADMAP §3) |
| Padrão de tela | O mesmo dos cadastros (DEC-010 do frontend): lista + painel de formulário abaixo, TanStack Query, `DeleteRecordDialog` para "apagar → 409 → inativar" |
| Grade de 15 min | Não é configurável (PD-04); a tela não oferece esse campo |
| "Não confirmado" | Prazo em horas configurável, nunca cancela sozinho (PD-07) — o texto de ajuda diz isso |
| Limite do plano | `402` vira aviso de upgrade (PD-22, S15) |
| PD-33 | Horário de funcionamento e feriados: dono em todas as unidades; gerente nas unidades dele (`unit:configure`). Criar/editar/apagar unidade e as Configurações continuam só do dono (`tenant:configure`) |
| PD-41 | Contato do cliente para o barbeiro: configurável, **padrão oculto** (chave na seção Barbearia). |

## Business Rules

### Unidades (`/app/cadastros/unidades`)

- [x] Tabela: nome, endereço, telefone formatado, fuso (só aparece se alguma unidade não for
      `America/Sao_Paulo`), "Agendamento online" (sim/não), status. Os quatro estados de lista.
- [x] Formulário: nome, endereço, telefone (máscara de `shared/text/phone`), fuso (select com os
      fusos do Brasil + "Outro" com campo livre IANA), "Aceita agendamento pela IA e pelo link",
      ativa. Editável só com `tenant:configure`; o gerente vê o formulário só leitura, mas edita as
      seções de horário e feriados das unidades dele (`unit:configure`, PD-33).
- [x] Botão "Nova unidade" e "Apagar" só com `tenant:configure`.
- [x] Ao mudar o fuso de unidade existente, confirmação: "Os horários locais dos agendamentos
      futuros desta unidade vão mudar."
- [x] `402` ao criar ou reativar: aviso no topo do formulário com a mensagem do backend e o botão
      "Falar com o suporte" (link de contato; sem self-service, PD-23).
- [x] `409` de última unidade ativa, de barbeiros ativos e de usuários vinculados aparece no
      formulário com a mensagem do `detail`.
- [x] Unidade aberta mostra duas seções abaixo do formulário: **Horário de funcionamento** e
      **Feriados e datas especiais**.

### Horário de funcionamento

- [x] Editor semanal: uma linha por dia (segunda a domingo), interruptor "Aberto" e até 3
      intervalos `HH:MM–HH:MM` (seletor de 5 em 5 min); "+ intervalo" e "Copiar para todos os
      dias".
- [x] Validação local espelha a do backend: início antes do fim, sem sobreposição, sem intervalos
      encostados (mensagem: "Junte os intervalos que se encostam"); salva a semana inteira de uma
      vez (`PUT`).
- [x] `warning` do backend (semana toda fechada) aparece como aviso amarelo, sem bloquear.
- [x] Texto fixo abaixo do editor: "Mudar o horário não altera agendamentos já marcados; os que
      ficarem fora aparecem destacados na agenda."
- [x] Sem `unit:configure` na unidade aberta: editor só leitura, sem "Salvar".

### Feriados e datas especiais

- [x] Lista das exceções futuras da unidade (data ou período, "Fechado" ou "Aberto 08:00–14:00",
      motivo), com editar e apagar (confirmação).
- [x] Formulário: período (de/até; "até" começa igual a "de"), tipo (Fechado / Horário especial),
      horário (só no especial), motivo, e **"Aplicar também em"** com as outras unidades em que o
      usuário tem `unit:configure` (marcadas por padrão quando há mais de uma) — vira `unit_ids` no
      `POST`. Sem `unit:configure`: lista só leitura, sem formulário.
- [x] **Feriados nacionais** (Q-S01-2): botão "Sugerir feriados de <ano>" abre a lista de
      `GET /tenant/holidays?year=` com caixas de seleção (as já fechadas aparecem marcadas e
      desabilitadas); confirmar cria as exceções `closed` marcadas pelo `POST` normal (motivo = nome
      do feriado). Nada é marcado por padrão.
- [ ] Antes de salvar um fechamento, a tela consulta `GET /appointments` (S03) no período e, se
      houver agendamentos ativos, mostra "N agendamentos nesse período continuarão marcados e serão
      destacados na agenda" (Q-S01-3). Até S03 existir, o aviso não aparece.
- [x] `409` de sobreposição aparece no campo de período.

### Configurações (`/app/configuracoes`)

- [x] Navegação lateral da tela com seções; nesta spec: **Barbearia** e **Agendamento**. Cada
      seção salva sozinha (botão "Salvar" por seção, desabilitado sem alteração).
- [x] Barbearia: nome (`PATCH /tenant`), telefone de contato, Instagram (aceita colar com `@` ou URL
      e envia só o usuário), "Sobre a barbearia" (contador até 1000; ajuda: "Aparece na página de
      agendamento e a IA usa para responder clientes"), e a chave "Barbeiro vê telefone e e-mail
      do cliente" (`barber_sees_client_contact`, desligada por padrão; ajuda: "Desligado, o barbeiro
      vê nome e histórico, mas o contato aparece mascarado") — PD-41.
- [x] Agendamento: antecedência mínima (select: sem mínimo, 15 min, 30 min, 1 h, 2 h, 4 h, 12 h,
      24 h, 48 h), agendar até (dias), prazo de confirmação (horas), cliente pode cancelar/remarcar
      até (horas antes), tolerância de atraso (min), máximo de agendamentos futuros por cliente na
      IA e no link (padrão 3; ajuda: "A recepção no painel não tem esse limite"). Cada campo com uma frase de ajuda em linguagem
      de dono de barbearia (ex.: "Se o cliente não confirmar até 3 h antes, o horário fica marcado
      como 'não confirmado' para a recepção decidir. Nada é cancelado sozinho.").
- [x] A entrada "Configurações" no menu aparece só para quem tem `tenant:configure` (navegação por
      permissão, S18). Acesso direto à URL sem a permissão volta para a agenda.

## Telas e fluxos

| Rota | Tela | Fluxos |
|---|---|---|
| `/app/cadastros/unidades` | `features/registry/pages/RegistryPageScreen.tsx` (item `unidades` passa a `ready: true`) | `pages/units/` (lista, formulário, `WeeklyHoursEditor`, `UnitExceptions`) |
| `/app/configuracoes` | `features/settings/pages/SettingsScreen.tsx` | `pages/shop/`, `pages/booking-policies/` |
| `/app/configuracoes?secao=agendamento` | idem | seção na URL |

`app/router.tsx` ganha a rota; `app/_shell/Sidebar.tsx` ganha "Configurações" (ícone engrenagem).

## Data Contract

Contrato completo no espelho do backend. Endpoints consumidos:

```text
GET/POST /tenant/units · GET/PATCH/DELETE /tenant/units/{id}
GET/PUT  /tenant/units/{id}/hours
GET/POST /tenant/unit-exceptions · PATCH/DELETE /tenant/unit-exceptions/{id}
GET      /tenant/holidays?year=        (feriados nacionais sugeridos)
GET/PATCH /tenant/settings
GET/PATCH /tenant                       (já existe: nome da barbearia)
GET      /appointments?unit_id&from&to  (S03; só para o aviso de fechamento)
```

Arquivos:

```text
features/registry/model/unit.types.ts       Unit, UnitInput, WeeklyHours, UnitException
features/registry/model/unit.rules.ts       validação do formulário e do editor semanal
features/registry/api/units.api.ts · units.queries.ts
features/settings/                          index.ts · api/settings.api.ts · settings.queries.ts ·
                                            model/settings.types.ts · settings.rules.ts · pages/
shared/text/time.ts                         "HH:MM" ↔ minutos, faixas (usado também pela agenda)
```

## Estado

| Estado | Onde |
|---|---|
| Unidades, horário, exceções, configurações | TanStack Query: `['units']`, `['units', id, 'hours']`, `['unit-exceptions', unitId]`, `['shop-settings']` |
| Unidade aberta, seção das configurações | URL (`?unidade=<id>`, `?secao=`) |
| Editor semanal e formulários | estado local (`useReducer` no editor semanal) |

Salvar unidade invalida também `['auth','me']` (o seletor de unidade da barra lateral usa as
unidades do `/auth/me`).

## Permissões

| Ação | Permissão em `/auth/me` |
|---|---|
| ver Unidades, horário e feriados | autenticado (lista já vem filtrada pelo backend) |
| criar/editar/apagar unidade | `tenant:configure` |
| editar horário e feriados da unidade | `unit:configure` com a unidade no escopo (dono: todas; gerente: as dele — PD-33) |
| ver Configurações | `tenant:configure` (S18) |
| salvar Configurações | `tenant:configure` |

## Acceptance Criteria

- [x] Item "Unidades" de `REGISTRY_PAGES` com `ready: true` e `permission: null`.
- [x] Feature `settings` criada com o layout padrão e registrada no ESLint de fronteiras.
- [x] Testes em `tests/`: validação do editor semanal (sobreposição, encostados, fim antes do
      início), "copiar para todos os dias", conversão `HH:MM` ↔ minutos, normalização do Instagram,
      montagem de `unit_ids` no "Aplicar também em" (só unidades com `unit:configure`), seleção de
      feriados sugeridos.
- [x] `make docs-api` regenerado; nenhuma chamada fora do contrato.
- [ ] Tela conferida no navegador como dono, como gerente (edita horário e feriados só das unidades
      dele, formulário da unidade só leitura) e como recepção (só leitura): criar unidade, `402`
      simulado, editar horário, criar feriado para duas unidades, `409` de sobreposição, estados
      vazio, carregando e erro.
- [x] `make check-frontend` verde; `README.md` e `memory/progress.md` atualizados.

## Dependencies

- Backend `⏳active_identity-units-hours.md` implementado, com `openapi.json` congelado.
- S03 (`GET /appointments`) só para o aviso de fechamento; a tela funciona sem ele.
- S15 (frontend `frontend-plan-limits`) pode trocar o aviso de `402` por um componente comum de
  upgrade; aqui ele é simples.

## Notes

### Implementação (2026-11-06)

- **Falta:** conferir no navegador (ISS-010) e o aviso de agendamentos afetados por um fechamento,
  que depende do `GET /appointments` da S03. Por isso a spec continua `⏳active`.
- `402`: mostra a mensagem do backend e "Fale com o suporte do Navalha para mudar de plano." — sem
  link, porque ainda não há canal de contato definido; a S15 troca por um componente comum.
- O `/auth/me` não está no TanStack Query: o contexto de autenticação ganhou `reloadMe()`, chamado
  depois de salvar unidade e de renomear a barbearia (seletor de unidade e nome na barra lateral).
- Horários com `<input type="time" step=300>` (5 em 5 min) em vez de um select de 288 opções por
  campo.
- "Sugerir feriados" oferece o ano corrente e o seguinte.
- Testes: `tests/unit-rules.test.ts` (10) e `tests/settings-rules.test.ts` (5).

- O seletor de unidade da barra lateral (`auth/model/unitSelection.tsx`) passa a expor também o
  `unitId` na spec da agenda (S03), não aqui.
- O assistente de primeiros passos (S16) reaproveita `WeeklyHoursEditor`; por isso ele fica em
  `features/registry/ui/` e é exportado pelo `index.ts`.
- Perguntas de produto desta tela estão no espelho do backend (Q-S01-1 a Q-S01-5).
  > Resolvido em 2026-11-06: Q-S01-1 = `unit:configure` para horário e feriados, dono `all`, gerente
  > `unit` (PD-33); Q-S01-2 = feriados nacionais sugeridos, o dono marca; Q-S01-3 = fechamento
  > permitido com aviso e destaque na agenda; Q-S01-4 = políticas da barbearia inteira; Q-S01-5 =
  > padrões aceitos (60 min, 30 dias, 3 h, 2 h, 10 min) (PD-33 | ROADMAP §7).
