# Agenda real e modal de agendamento

**Priority:** high
**Status:** draft
**Espelho no backend:** `backend/docs/specs/⚪draft_scheduling-appointments.md`

## Overview

A agenda (`/app/agenda`) e o modal de agendamento são hoje o protótipo com dados de
`scheduling.mock.ts` e um seletor "Demo" (dia cheio, vazio, conflito). Esta spec os liga à API: a
grade por barbeiro com os agendamentos reais, a escala e as ausências desenhadas na coluna, os
status do ciclo de vida (incluindo **não confirmado** em destaque, PD-07), as ações da recepção
(confirmar, check-in, concluir, falta, remarcar, cancelar), arrastar para remarcar e o modal de
novo agendamento com **horários livres de verdade**, vários serviços em sequência e "qualquer
barbeiro". O visual do protótipo (grade, blocos, faixa de conflito, legenda, selo IA) é mantido.
Regras e contrato completos estão no espelho do backend.

## Decisões de produto já tomadas

| Parâmetro | Valor |
|---|---|
| Grade | Linhas de 15 min; o modal oferece início em grade de 15 min (PD-04); o painel aceita "outro horário" de 5 em 5 min (T7 do backend) |
| Vários serviços | Lista ordenada de serviços, cada um com barbeiro ou "Qualquer barbeiro" (PD-05, PD-06) |
| "Qualquer barbeiro" | Quem escolhe é o backend (equilíbrio do mês) — a tela mostra o sugerido antes de salvar |
| Não confirmado | Destaque visual e contador no topo; nunca cancela sozinho (PD-07) |
| Falta | Ação explícita da recepção; fica no histórico do cliente (PD-07) |
| Sem lista de espera e sem recorrência | PD-08 |
| Encaixe | Painel pode marcar fora da escala com confirmação; sobrepor outro cliente do mesmo barbeiro, nunca |
| PD-31 | Agendamento feito pelo cliente (IA/link) chega "agendado" e confirma pelo lembrete; marcado já dentro do prazo do lembrete, chega confirmado. A tela só mostra o status que o backend devolve |
| PD-32 | Campo **"Para quem"** (`attendee_name`): o mesmo cliente pode ter horários simultâneos (pai que marca para os filhos) |

## Business Rules

### Grade

- [ ] Visões **Dia** (uma coluna por barbeiro ativo da unidade, como o protótipo) e **Semana** (um
      barbeiro, sete colunas). "Mês" sai do seletor nesta versão. O barbeiro (`own`) abre na visão
      Dia só com a própria coluna.
- [ ] A unidade vem do seletor da barra lateral. Com "Todas as unidades" selecionado, a agenda
      mostra um seletor de unidade próprio (a grade é sempre de uma unidade).
- [ ] Faixa de horas: do primeiro horário de abertura ao último fechamento do(s) dia(s) visível(is),
      arredondada para a hora (padrão 08:00–20:00 quando a unidade está fechada).
- [ ] Todos os horários exibidos no **fuso da unidade** (`AgendaOut.unit.timezone`), não no do
      navegador; linha do "agora" só no dia de hoje, atualizada a cada minuto.
- [ ] Cabeçalho da coluna: iniciais, nome e resumo do dia ("09:00–19:00", "Turno especial
      13:00–20:00", "Folga", "Horário da unidade").
- [ ] Fora da escala, ausências e bloqueios: faixa hachurada com o motivo no `title`; unidade
      fechada (feriado): camada sobre a grade inteira com o motivo.
- [ ] Bloco por **item**: agendamento com dois serviços em barbeiros diferentes aparece nas duas
      colunas, com "1/2" e "2/2" e destaque dos dois ao passar o mouse.
- [ ] Bloco com `attendee_name` mostra "para <nome>" abaixo do cliente (PD-32).
- [ ] Classes de status: `is-agendado`, `is-confirmado`, `is-nao-confirmado` (borda e ícone de
      alerta), `is-chegou`, `is-concluido`, `is-falta`, `is-cancelado`. Cancelados ficam ocultos
      por padrão (filtro Status). Legenda atualizada.
- [ ] `flags` do backend viram ícone de aviso no bloco com o texto ("Fora da escala do barbeiro",
      "Barbeiro inativo", "Unidade fechada neste dia", "Sem baixa").
- [ ] Selo IA nos agendamentos com `origin = assistant` e selo "Link" em `booking_link`
      (interruptor "Selo IA" mantido, salvo no `localStorage`).
- [ ] Faixa **Atenção** no topo quando há não confirmados hoje/amanhã ou agendamentos sem baixa:
      "3 não confirmados · 2 sem baixa"; clicar filtra a grade.
- [ ] Estado vazio do protótipo com texto real ("A unidade Centro está aberta das 08:00 às 20:00
      com 4 barbeiros escalados") e o botão "Editar escala" levando a `/app/agenda/escala` (S02).
- [ ] Polling a cada 30 s e ao voltar o foco para a aba (T9 do backend).

### Detalhe do agendamento

- [ ] Clicar num bloco abre o modal em modo detalhe: cliente (nome, telefone formatado, link para a
      ficha), serviços com barbeiro e horário, total, origem, histórico de status (confirmado às…,
      chegou às…), motivo do "não confirmado" ("Sem resposta ao lembrete" / "Lembrete não
      entregue"), observação e "para quem".
- [ ] Botões conforme a tabela de transições do backend (`appointment.rules.ts` replica a tabela e
      as janelas de tempo, para só mostrar o que o backend aceitaria): Confirmar, Chegou (check-in),
      Concluir, Falta, Desfazer falta, Remarcar, Cancelar (pede motivo opcional, confirmação).
- [ ] Origem `assistant` mostra "Abrir conversa" (`/app/conversas?conversa=<origin_ref>`, S10);
      "Abrir comanda" aparece quando S06 existir.
- [ ] Ações escondidas por permissão: sem `appointment:cancel` não há "Cancelar"; sem
      `appointment:update`, só leitura.

### Novo agendamento e remarcação (modal)

- [ ] Abre por "Novo agendamento" (vazio) ou pelo clique num horário vazio (barbeiro, data e hora já
      preenchidos). Remarcar abre o mesmo modal com os dados atuais e `exclude_appointment_id`.
- [ ] Cliente: busca por nome ou telefone (`GET /clients?q`, 300 ms); "Cadastrar novo" abre nome +
      telefone inline e cria com `POST /clients` antes de agendar (só com `client:write`).
- [ ] Serviços: lista ordenada (adicionar, remover, mover), até 5; por serviço, o seletor de
      barbeiro mostra "Qualquer barbeiro" + os habilitados (`barber_ids` do serviço).
- [ ] O seletor de serviço lista também os **combos agendáveis** (`GET /combos`, `bookable = true`,
      Q-S05-1): escolher um combo preenche os serviços dele na ordem (cada um com seu barbeiro), mostra
      o preço fechado no resumo e envia `combo_id`. Mexer na lista de serviços desfaz o combo (aviso).
- [ ] Horários: ao mudar data, serviços ou barbeiros, consulta `POST /availability` e mostra os
      inícios livres em botões (manhã / tarde / noite); escolher um preenche os barbeiros sugeridos
      para "Qualquer barbeiro" ("Qualquer barbeiro → Igor"). Sem horário livre: "Nenhum horário
      livre neste dia" + "Próximo dia com horário" (`POST /availability/days`).
- [ ] "Outro horário" (campo de 5 em 5 min) e "Encaixe fora da escala" (`allow_outside_hours`), com o
      aviso "Diego não está escalado nesse horário".
- [ ] Resumo no rodapé: duração total, término, preço total (`R$ 85,00`); "Cliente já confirmou";
      observações; "Para quem" (opcional, até 120 — PD-32; ajuda: "Use quando o horário é para
      outra pessoa, como um filho"). O `409` "Este cliente já tem um agendamento nesse horário"
      sugere preencher "Para quem".
- [ ] Cada abertura do modal gera um `Idempotency-Key`; salvar duas vezes não duplica.
- [ ] `409` de horário ocupado: a faixa de conflito do protótipo com "Ver próximo horário livre"
      (primeiro slot depois do pedido), "Trocar barbeiro" (foca o seletor) e "Descartar"; a lista
      de horários é recarregada.
- [ ] Fechar com alteração não salva pede confirmação; `Esc` fecha.

### Arrastar para remarcar

- [ ] Bloco de agendamento de **um serviço** em `agendado/confirmado/não confirmado` pode ser
      arrastado para outro horário (encaixa em 15 min) e/ou outra coluna; ao soltar, confirmação
      "Remarcar Bruno para 10:30 com Igor?" → `POST /appointments/{id}/reschedule`. `409` devolve o
      bloco ao lugar com a mensagem. Agendamento com vários serviços usa "Remarcar" no detalhe.
- [ ] Só com `appointment:update`; o barbeiro arrasta só no tempo, sem trocar de coluna.

## Telas e fluxos

| Rota | Tela | Fluxos |
|---|---|---|
| `/app/agenda?data=AAAA-MM-DD&visao=dia\|semana&barbeiro=&status=` | `features/scheduling/pages/AgendaScreen.tsx` | `pages/agenda/` (grade, colunas, blocos, faixa de atenção, arrastar, menu do horário vazio) |
| modal (qualquer tela) | `features/scheduling/ui/AppointmentModal.tsx` | `ui/appointment-modal/` (detalhe, formulário, horários, conflito) |

O `AppointmentModalProvider` continua no shell; `openAppointment` passa a receber
`{ mode: 'new', prefill?: { unitId, barberId, startsAt, clientId, serviceIds } }` ou
`{ mode: 'view', id }` — a Central de conversas (S10) usa o `prefill` com o cliente da conversa.

## Data Contract

Contrato completo no espelho do backend. Endpoints consumidos:

```text
GET  /agenda?unit_id&from&to&barber_ids&status
GET  /appointments/{id}
POST /appointments                 (Idempotency-Key)
PATCH /appointments/{id}
POST /appointments/{id}/reschedule | confirm | check-in | complete | no-show | revert-no-show | cancel
POST /availability · POST /availability/days
GET  /clients?q · POST /clients    (já existem)
GET  /services?active=true         (já existe; barber_ids de cada serviço)
```

Arquivos:

```text
features/scheduling/model/scheduling.types.ts  substituído: Appointment, AppointmentItem, Agenda,
                                                AppointmentStatus (valores do backend), Slot…
features/scheduling/model/appointment.rules.ts transições e janelas (botões visíveis), rótulos e
                                                classes de status, total e término
features/scheduling/model/agendaTime.ts        UTC ↔ hora local da unidade com Intl (sem dependência
                                                nova), geometria dos blocos, faixa de horas
features/scheduling/api/scheduling.api.ts · scheduling.queries.ts
features/scheduling/api/scheduling.mock.ts     apagado (e o seletor "Demo")
features/auth/model/unitSelection.tsx          passa a expor unitId (null = todas)
```

## Estado

| Estado | Onde |
|---|---|
| Agenda do período, agendamento aberto, horários livres | TanStack Query: `['agenda', unitId, from, to]` (refetch 30 s), `['appointment', id]`, `['availability', consulta]` (staleTime 0) |
| Data, visão, barbeiro, filtro de status | URL |
| Unidade | `useUnitSelection()` (`unitId`) |
| Modal aberto e modo | context `appointmentModal.tsx` (já existe) |
| Formulário do modal, arrasto em curso | estado local / `useReducer` |
| "Selo IA" | `localStorage` |

Toda mutação invalida `['agenda']` e `['appointment', id]`; criar cliente invalida `['clients']`.

## Permissões

| Ação | Permissão em `/auth/me` |
|---|---|
| ver a agenda | `appointment:read` (barbeiro: só a própria coluna) |
| novo agendamento | `appointment:create` |
| confirmar, check-in, concluir, falta, remarcar, arrastar, editar | `appointment:update` |
| cancelar | `appointment:cancel` |
| cadastrar cliente no modal | `client:write` |

## Acceptance Criteria

- [ ] `scheduling.mock.ts` e o seletor "Demo" removidos; ISS-002 atualizada.
- [ ] Testes em `tests/`: conversão UTC ↔ hora local (inclusive fuso com horário de verão),
      geometria dos blocos, faixa de horas, botões por status e horário (tabela de transições),
      total/término de vários serviços, agrupamento dos horários livres em manhã/tarde/noite,
      encaixe do arrasto em 15 min.
- [ ] `make docs-api` regenerado; nenhuma chamada fora do contrato.
- [ ] Tela conferida no navegador como dono, recepção e barbeiro: criar com dois serviços e
      barbeiros diferentes, "qualquer barbeiro", `409` simulado em duas abas, remarcar arrastando,
      ciclo confirmar → chegou → concluir, falta e desfazer, cancelar, não confirmado em destaque,
      feriado e folga na grade, estados vazio, carregando e erro.
- [ ] `make check-frontend` verde; `README.md` e `memory/progress.md` atualizados.

## Dependencies

- Backend `⚪draft_scheduling-appointments.md` implementado, com `openapi.json` congelado.
- `⏳active_frontend-barber-schedule.md` — abas Escala/Ausências e o formulário de bloqueio.
- `⏳active_frontend-units-settings.md` — `shared/text/time.ts`.
- `✅active_frontend-registry-basic-crud.md` — clientes e serviços reais.
- S10 (`conversations`) e S06 (`sales`) — links "Abrir conversa" e "Abrir comanda".

## Notes

- Visão "Mês" (contagem por dia) pode voltar com os relatórios (S14).
- Atualização em tempo real (SSE) substitui o polling quando o backend tiver o canal (S00, Notes).
- O layout de celular da agenda (uma coluna, deslizar entre barbeiros) é da S18; aqui a grade só
  precisa não quebrar em tela estreita.
- Perguntas de produto: Q-S03-1 a Q-S03-6 no espelho do backend.
  > Resolvido em 2026-11-06: Q-S03-1 = cliente agenda "agendado" e confirma pelo lembrete (PD-31);
  > Q-S03-2 = fechar a comanda conclui, "Concluir" na agenda continua; Q-S03-3 = sem duração/preço
  > por barbeiro; Q-S03-4 = limite de agendamentos futuros na IA/link configurável, padrão 3 (campo
  > em Configurações → Agendamento, S01); Q-S03-5 = "Para quem" (PD-32); Q-S03-6 = sem intervalo
  > entre atendimentos (PD-31, PD-32 | ROADMAP §7).
