<!-- Gerado por frontend/scripts/api-docs.ts a partir das chamadas em src/features/*/api e do contrato do backend. Não edite à mão: rode `npm run docs:api`. -->

# Feature `scheduling`

Chamadas à API feitas em `src/features/scheduling/api/schedule.api.ts`. Campos, erros e regras de acesso de cada rota estão na referência do backend (links).

| Função | Rota | Corpo | Resposta | Resumo |
|---|---|---|---|---|
| `listSchedules()` | [`GET /schedules`](../../../backend/docs/api/scheduling.md#get-schedules) | — | `200` `BarberScheduleOut`[] | Schedule grid |
| `setSchedule()` | [`PUT /barbers/{barber_id}/schedule`](../../../backend/docs/api/scheduling.md#put-barbersbarber_idschedule) | `WeeklyScheduleIn` | `200` `BarberScheduleOut` | Replace the week |
| `listShiftOverrides()` | [`GET /barbers/{barber_id}/shift-overrides`](../../../backend/docs/api/scheduling.md#get-barbersbarber_idshift-overrides) | — | `200` `ShiftOverrideOut`[] | Special shifts |
| `setShiftOverride()` | [`PUT /barbers/{barber_id}/shift-overrides/{on_date}`](../../../backend/docs/api/scheduling.md#put-barbersbarber_idshift-overrideson_date) | `ShiftOverrideIn` | `200` `ShiftOverrideOut` | Special shift on a day |
| `deleteShiftOverride()` | [`DELETE /barbers/{barber_id}/shift-overrides/{on_date}`](../../../backend/docs/api/scheduling.md#delete-barbersbarber_idshift-overrideson_date) | — | `204` — | Back to the weekly schedule |
| `listTimeOff()` | [`GET /time-off`](../../../backend/docs/api/scheduling.md#get-time-off) | — | `200` `TimeOffOut`[] | Time off and blocks in a period |
| `createTimeOff()` | [`POST /time-off`](../../../backend/docs/api/scheduling.md#post-time-off) | `TimeOffIn` | `201` `TimeOffResult` | Add time off |
| `updateTimeOff()` | [`PATCH /time-off/{time_off_id}`](../../../backend/docs/api/scheduling.md#patch-time-offtime_off_id) | `TimeOffUpdate` | `200` `TimeOffResult` | Edit time off |
| `deleteTimeOff()` | [`DELETE /time-off/{time_off_id}`](../../../backend/docs/api/scheduling.md#delete-time-offtime_off_id) | — | `204` — | Remove time off |
| `listBarberRefs()` | [`GET /barbers`](../../../backend/docs/api/barbers.md#get-barbers) | — | `200` `BarberOut`[] | Barbers in the caller's units |
