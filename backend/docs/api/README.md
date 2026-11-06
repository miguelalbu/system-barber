<!-- Gerado por backend/tools/api_docs.py a partir do OpenAPI. Não edite à mão: rode `make docs-api`. -->

# Referência da API

Gerada do OpenAPI do código (`app.openapi()` e o contrato do control plane). Para o *porquê* de cada regra, veja as specs em [`../specs/`](../specs/); para o contrato congelado, `tests/test_contracts/snapshots/`.

| Documento | Conteúdo |
|---|---|
| [Autenticação](auth.md) | Login da equipe, renovação rotativa do token, logout e o perfil da sessão. |
| [Barbearia](shop.md) | Dados e configuração da barbearia da sessão e as unidades visíveis ao usuário. |
| [Equipe e convites](team.md) | Membros, convites e o aceite de convite — inclusive o primeiro acesso do dono de uma barbearia recém-provisionada. |
| [Barbeiros](barbers.md) | Cadastro dos profissionais que atendem (coluna da agenda, comissão). |
| [Catálogo](catalog.md) | Serviços da barbearia (um preço para todas as unidades, em centavos) e os serviços que cada barbeiro faz. |
| [Clientes](clients.md) | Clientes da barbearia, compartilhados entre as unidades e identificados pelo telefone em E. |
| [Infraestrutura](infra.md) | Sondas de saúde. |
| [Control plane (`/core/*`)](control-plane.md) | Criação e ciclo de vida das barbearias, chamado pelo Core da plataforma. |

## Convenções

- **Barbearia:** vem do domínio (`<slug>.<BASE_DOMAIN>` ou domínio próprio). Em desenvolvimento, o header `X-Tenant-Slug` substitui o subdomínio.
- **Sessão:** `Authorization: Bearer <access_token>` (15 min); renovação por `POST /auth/refresh`. O token só vale no domínio da barbearia que o emitiu.
- **Acesso:** cada rota diz a permissão exigida (mapa em [`../PERMISSIONS_MAP.md`](../PERMISSIONS_MAP.md)) ou o escopo da `X-Core-Key`.
- **Erros:** `{"detail": "..."}` em português; `422` para validação; `503` quando a barbearia está em preparação ou manutenção.
