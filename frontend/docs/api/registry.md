<!-- Gerado por frontend/scripts/api-docs.ts a partir das chamadas em src/features/*/api e do contrato do backend. Não edite à mão: rode `npm run docs:api`. -->

# Feature `registry`

Chamadas à API feitas em `src/features/registry/api/registry.api.ts`. Campos, erros e regras de acesso de cada rota estão na referência do backend (links).

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
