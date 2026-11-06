# Progress

Estado atual do backend. Atualizado ao fim de cada tarefa concluída.
Estados: `stable` · `in progress` · `blocked` · `planned` · `deprecated`.

## Módulos

| Módulo | Estado | Atualizado | Notas |
|---|---|---|---|
| Arquitetura modular | stable | 2026-11-05 | Spec `✅completed_backend-modular-architecture.md`. `app/core/` + `app/modules/{identity,provisioning}`; `lint-imports` (3 contratos), layout e cross-module verificados em `tests/test_contracts/`. |
| Multi-tenancy: schema por barbearia | stable | 2026-11-05 | Spec `✅completed_identity-schema-per-tenant.md` (desenho do ClaraCRM v2, com subdomínio personalizado). `public` = control plane; `tenant_<slug>` por barbearia; `schema_translate_map` sem search_path; app sem DDL; role por barbearia; `schema_version` + 503 se atrasado; migrations fora do boot (serviço `migrate`). DEC-011 a DEC-014. |
| `provisioning` — control plane `/core/*` | stable | 2026-11-05 | `X-Core-Key` (escopos, allowlist, rate limit por processo, auditoria inclusive negadas), job 202 idempotente (slug e `Idempotency-Key`), convite de 1º acesso entregue uma vez, suspend/resume, retry, reemissão, destroy com 4 portões, OpenAPI privado. CLI `core_key`. Pendências: ISS-012, ISS-013, ISS-014. |
| `identity` — autenticação | stable | 2026-11-05 | Login com hash descartável para e-mail desconhecido, refresh rotativo, logout, `/auth/me`. Pendências: rate limit (ISS-007), reuso de refresh (ISS-003), recuperação de senha (ISS-008). |
| `identity` — equipe e convites | stable | 2026-11-05 | Convite com unidades e criação de barbeiro; `lookup` sem gastar; aceite atômico (UPDATE condicional, testado com concorrência); desativação. Link volta na resposta (ISS-004). |
| `identity` — RBAC | stable | 2026-11-05 | 19 permissões × 4 cargos × escopo `all/unit/own` (`docs/PERMISSIONS_MAP.md`, verificado por teste). Permissões de módulos futuros já declaradas. |
| Admin da plataforma | in progress | 2026-11-05 | Seed pronto (`python -m app.management.seed platform-admin`, no `public`). Falta login (ISS-005). |
| Catálogo (serviços, combos, clubes, planos) | planned | — | Próximo bloco do README. Precisa de spec. Tela correspondente no frontend: Cadastros (mock). |
| Agenda (disponibilidade, agendamentos, bloqueios) | planned | — | O núcleo que a IA do WhatsApp vai chamar. Precisa de spec. Reavaliar onde mora `Barber` (DEC-007). |
| Clientes + autenticação do cliente final (telefone + OTP) | planned | — | Precisa de spec. Usa Redis (OTP). |
| Financeiro (comandas, comissões, pagamentos) | planned | — | Precisa de spec. |
| Conversas / WhatsApp + `ai-agent` | planned | — | Depende de eventos de domínio. Desenho já decidido (doc §5): App Secret e verify token **globais** no `public`, `whatsapp_number_routes` (`phone_number_id` UNIQUE → tenant) espelhando o número do schema, tokens Meta por barbearia com envelope encryption (DEK por tenant, doc Camada 4), relay fatiado por tenant, API key por tenant no lugar de token compartilhado. |

## Qualidade

| Item | Estado | Notas |
|---|---|---|
| Suíte | 85 testes verdes (2026-11-05) | 21 de comportamento herdados + 54 de tenancy/control plane/endurecimento + 10 de contrato. Provisionamento real por teste; limpeza total no fim da sessão. ~18 s. |
| Lint | verde | `ruff check`, `ruff format --check`, `lint-imports` (3 contratos). |
| Banco | verde | `alembic check` sem pendências no controle e no conjunto de tenant (`tenant_template`). |
| CI | configurado | `.github/workflows/ci.yml`: lint + fronteiras + `migrate --apply --template` + os dois `alembic check` + pytest. Simulado num Postgres zerado em 2026-11-05. |
