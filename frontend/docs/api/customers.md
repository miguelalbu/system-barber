<!-- Gerado por frontend/scripts/api-docs.ts a partir das chamadas em src/features/*/api e do contrato do backend. Não edite à mão: rode `npm run docs:api`. -->

# Feature `customers`

Chamadas à API feitas em `src/features/customers/api/customers.api.ts`. Campos, erros e regras de acesso de cada rota estão na referência do backend (links).

| Função | Rota | Corpo | Resposta | Resumo |
|---|---|---|---|---|
| `listClients()` | [`GET /clients`](../../../backend/docs/api/clients.md#get-clients) | — | `200` `ClientPage` | Search clients, one page at a time |
| `createClient()` | [`POST /clients`](../../../backend/docs/api/clients.md#post-clients) | `ClientIn` | `201` `ClientOut` | Register a client |
| `updateClient()` | [`PATCH /clients/{client_id}`](../../../backend/docs/api/clients.md#patch-clientsclient_id) | `ClientUpdate` | `200` `ClientOut` | Update a client |
| `deleteClient()` | [`DELETE /clients/{client_id}`](../../../backend/docs/api/clients.md#delete-clientsclient_id) | — | `204` — | Delete a client without history |
