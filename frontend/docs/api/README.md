<!-- Gerado por frontend/scripts/api-docs.ts a partir das chamadas em src/features/*/api e do contrato do backend. Não edite à mão: rode `npm run docs:api`. -->

# API consumida pelo frontend

Quais endpoints do backend cada feature chama, casados com o contrato congelado (`backend/tests/test_contracts/snapshots/openapi.json`). A referência completa — campos, erros, permissões — está em [`backend/docs/api/`](../../../backend/docs/api/README.md).

| Feature | Chamadas |
|---|---|
| [`auth`](auth.md) | 5 |
| [`customers`](customers.md) | 4 |
| [`registry`](registry.md) | 11 |
| [`shared`](shared.md) | 1 |

## Ainda sobre dados de demonstração

Features com `api/*.mock.ts` (sem módulo no backend ainda): `conversations`, `dashboard`, `scheduling`.

Todas as chamadas passam por `src/shared/api/http.ts` (base `/api`, `X-Tenant-Slug` em dev, bearer e renovação de token).
