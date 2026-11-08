<!-- Gerado por frontend/scripts/api-docs.ts a partir das chamadas em src/features/*/api e do contrato do backend. Não edite à mão: rode `npm run docs:api`. -->

# Feature `registry`

Chamadas à API feitas em `src/features/registry/api/registry.api.ts`, `src/features/registry/api/units.api.ts`. Campos, erros e regras de acesso de cada rota estão na referência do backend (links).

| Função | Rota | Corpo | Resposta | Resumo |
|---|---|---|---|---|
| `listBarbers()` | [`GET /barbers`](../../../backend/docs/api/barbers.md#get-barbers) | — | `200` `BarberOut`[] | Barbers in the caller's units |
| `createBarber()` | [`POST /barbers`](../../../backend/docs/api/barbers.md#post-barbers) | `BarberIn` | `201` `BarberOut` | Register a barber |
| `updateBarber()` | [`PATCH /barbers/{barber_id}`](../../../backend/docs/api/barbers.md#patch-barbersbarber_id) | `BarberUpdate` | `200` `BarberOut` | Update a barber |
| `deleteBarber()` | [`DELETE /barbers/{barber_id}`](../../../backend/docs/api/barbers.md#delete-barbersbarber_id) | — | `204` — | Delete a barber without history |
| `setBarberServices()` | [`PUT /barbers/{barber_id}/services`](../../../backend/docs/api/catalog.md#put-barbersbarber_idservices) | `BarberServicesIn` | `200` `ServiceOut`[] | Set the services a barber performs |
| `listServices()` | [`GET /services`](../../../backend/docs/api/catalog.md#get-services) | — | `200` `ServiceOut`[] | Services of the shop |
| `createService()` | [`POST /services`](../../../backend/docs/api/catalog.md#post-services) | `ServiceIn` | `201` `ServiceOut` | Create a service |
| `updateService()` | [`PATCH /services/{service_id}`](../../../backend/docs/api/catalog.md#patch-servicesservice_id) | `ServiceUpdate` | `200` `ServiceOut` | Update a service |
| `deleteService()` | [`DELETE /services/{service_id}`](../../../backend/docs/api/catalog.md#delete-servicesservice_id) | — | `204` — | Delete a service without history |
| `listUnits()` | [`GET /tenant/units`](../../../backend/docs/api/shop.md#get-tenantunits) | — | `200` `UnitOut`[] | Visible units |
| `listMembers()` | [`GET /team`](../../../backend/docs/api/team.md#get-team) | — | `200` `MemberOut`[] | Shop members |
| `listUnitRecords()` | [`GET /tenant/units`](../../../backend/docs/api/shop.md#get-tenantunits) | — | `200` `UnitOut`[] | Visible units |
| `createUnit()` | [`POST /tenant/units`](../../../backend/docs/api/shop.md#post-tenantunits) | `UnitIn` | `201` `UnitOut` | New unit |
| `updateUnit()` | [`PATCH /tenant/units/{unit_id}`](../../../backend/docs/api/shop.md#patch-tenantunitsunit_id) | `UnitUpdate` | `200` `UnitOut` | Update a unit |
| `deleteUnit()` | [`DELETE /tenant/units/{unit_id}`](../../../backend/docs/api/shop.md#delete-tenantunitsunit_id) | — | `204` — | Delete a unit without history |
| `getUnitHours()` | [`GET /tenant/units/{unit_id}/hours`](../../../backend/docs/api/shop.md#get-tenantunitsunit_idhours) | — | `200` `WeeklyHoursOut` | Weekly hours |
| `setUnitHours()` | [`PUT /tenant/units/{unit_id}/hours`](../../../backend/docs/api/shop.md#put-tenantunitsunit_idhours) | `WeeklyHoursIn` | `200` `WeeklyHoursOut` | Replace the week |
| `listUnitExceptions()` | [`GET /tenant/unit-exceptions`](../../../backend/docs/api/shop.md#get-tenantunit-exceptions) | — | `200` `UnitExceptionOut`[] | Holidays and closures |
| `createUnitExceptions()` | [`POST /tenant/unit-exceptions`](../../../backend/docs/api/shop.md#post-tenantunit-exceptions) | `UnitExceptionIn` | `201` `UnitExceptionOut`[] | Close or open specially on dates |
| `updateUnitException()` | [`PATCH /tenant/unit-exceptions/{exception_id}`](../../../backend/docs/api/shop.md#patch-tenantunit-exceptionsexception_id) | `UnitExceptionUpdate` | `200` `UnitExceptionOut` | Edit an exception |
| `deleteUnitException()` | [`DELETE /tenant/unit-exceptions/{exception_id}`](../../../backend/docs/api/shop.md#delete-tenantunit-exceptionsexception_id) | — | `204` — | Delete an exception |
| `listHolidays()` | [`GET /tenant/holidays`](../../../backend/docs/api/shop.md#get-tenantholidays) | — | `200` `HolidayOut`[] | Suggested national holidays |
