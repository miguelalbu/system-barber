<!-- Gerado por frontend/scripts/api-docs.ts a partir das chamadas em src/features/*/api e do contrato do backend. Não edite à mão: rode `npm run docs:api`. -->

# Transporte compartilhado (`shared/api`)

Chamadas à API feitas em `src/shared/api/http.ts`. Campos, erros e regras de acesso de cada rota estão na referência do backend (links).

| Função | Rota | Corpo | Resposta | Resumo |
|---|---|---|---|---|
| `runRefresh()` | [`POST /auth/refresh`](../../../backend/docs/api/auth.md#post-authrefresh) | `RefreshIn` | `200` `TokensOut` | Renew the access token |
