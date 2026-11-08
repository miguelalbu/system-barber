<!-- Gerado por frontend/scripts/api-docs.ts a partir das chamadas em src/features/*/api e do contrato do backend. Não edite à mão: rode `npm run docs:api`. -->

# Feature `settings`

Chamadas à API feitas em `src/features/settings/api/settings.api.ts`. Campos, erros e regras de acesso de cada rota estão na referência do backend (links).

| Função | Rota | Corpo | Resposta | Resumo |
|---|---|---|---|---|
| `getShopSettings()` | [`GET /tenant/settings`](../../../backend/docs/api/shop.md#get-tenantsettings) | — | `200` `ShopSettingsOut` | Shop settings |
| `updateShopSettings()` | [`PATCH /tenant/settings`](../../../backend/docs/api/shop.md#patch-tenantsettings) | `ShopSettingsUpdate` | `200` `ShopSettingsOut` | Update shop settings |
| `renameShop()` | [`PATCH /tenant`](../../../backend/docs/api/shop.md#patch-tenant) | `TenantUpdate` | `200` `TenantOut` | Update shop details |
