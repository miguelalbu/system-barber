# Progress

Estado atual do backend. Atualizado ao fim de cada tarefa concluída.
Estados: `stable` · `in progress` · `blocked` · `planned` · `deprecated`.

## Módulos

| Módulo | Estado | Atualizado | Notas |
|---|---|---|---|
| Arquitetura modular | stable | 2026-11-05 | Spec `✅completed_backend-modular-architecture.md`. `app/core/` + `app/modules/identity/`; snapshots de contrato gerados antes e inalterados depois; `lint-imports` (3 contratos), layout e cross-module verificados em `tests/test_contracts/`. |
| `identity` — tenancy e isolamento | stable | 2026-11-05 | Spec `✅completed_identity-core.md`. Tenant pelo domínio (`X-Tenant-Slug` em dev), RLS em 6 tabelas, role de runtime sem privilégio, `set_config(..., true)`. Testes em `test_identity/test_isolation.py` (mesmo e-mail em duas barbearias, token não cruza barbearias, equipe só vê a própria, domínio desconhecido 404, slug duplicado 409). |
| `identity` — autenticação | stable | 2026-11-05 | Login, refresh rotativo, logout, `/auth/me` com permissões do cargo, auto-cadastro de barbearia. Pendências: rate limit (ISS-007), reuso de refresh (ISS-003), recuperação de senha (ISS-008). |
| `identity` — equipe e convites | stable | 2026-11-05 | Convite com unidades e criação de barbeiro; aceite cria login (+ `Barber` para cargo barbeiro); desativação (nunca exclusão). Link volta na resposta (ISS-004). |
| `identity` — RBAC | stable | 2026-11-05 | 19 permissões × 4 cargos × escopo `all/unit/own` (`docs/PERMISSIONS_MAP.md`, verificado por teste). Permissões de módulos futuros já declaradas. |
| Admin da plataforma | in progress | 2026-11-05 | Seed pronto (`python -m app.management.seed platform-admin`, idempotente, 7 testes). Falta login (ISS-005). |
| Catálogo (serviços, combos, clubes, planos) | planned | — | Próximo bloco do README. Precisa de spec. Tela correspondente no frontend: Cadastros (mock). |
| Agenda (disponibilidade, agendamentos, bloqueios) | planned | — | O núcleo que a IA do WhatsApp vai chamar. Precisa de spec. Reavaliar onde mora `Barber` (DEC-007). |
| Clientes + autenticação do cliente final (telefone + OTP) | planned | — | Precisa de spec. Usa Redis (OTP). |
| Financeiro (comandas, comissões, pagamentos) | planned | — | Precisa de spec. |
| Conversas / WhatsApp + `ai-agent` | planned | — | Depende de eventos de domínio (RabbitMQ no plano original do README). |

## Qualidade

| Item | Estado | Notas |
|---|---|---|
| Suíte | 29 testes verdes (2026-11-05) | 21 de comportamento (`test_identity/`) + 8 de contrato (`test_contracts/`). Roda em ~3 s contra o Postgres de dev. |
| Lint | verde | `ruff check`, `ruff format --check`, `lint-imports` (3 contratos). |
| Banco | verde | `alembic check` sem operações pendentes. |
| CI | configurado | `.github/workflows/ci.yml` na raiz do repo: lint + import-linter + migrations + pytest com Postgres de serviço. |
