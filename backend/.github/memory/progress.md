# Progress

Estado atual do backend. Atualizado ao fim de cada tarefa concluída.
Estados: `stable` · `in progress` · `blocked` · `planned` · `deprecated`.

## Módulos

| Módulo | Estado | Atualizado | Notas |
|---|---|---|---|
| Arquitetura modular | stable | 2026-11-05 | Spec `✅completed_backend-modular-architecture.md`. `app/core/` + `app/modules/{identity,provisioning}`; `lint-imports` (4 contratos), layout e cross-module verificados em `tests/test_contracts/`. |
| Multi-tenancy: schema por barbearia | stable | 2026-11-05 | Spec `✅completed_identity-schema-per-tenant.md` (desenho do ClaraCRM v2, com subdomínio personalizado). `public` = control plane; `tenant_<slug>` por barbearia; `schema_translate_map` sem search_path; app sem DDL; role por barbearia; `schema_version` + 503 se atrasado; migrations fora do boot (serviço `migrate`). DEC-011 a DEC-014. |
| `provisioning` — control plane `/core/*` | stable | 2026-11-05 | `X-Core-Key` (escopos, allowlist, rate limit por processo, auditoria inclusive negadas), job 202 idempotente (slug e `Idempotency-Key`), convite de 1º acesso entregue uma vez, suspend/resume, retry, reemissão, destroy com 4 portões, OpenAPI privado. CLI `core_key`. Pendências: ISS-012, ISS-013, ISS-014. |
| `identity` — autenticação | stable | 2026-11-05 | Login com hash descartável para e-mail desconhecido, refresh rotativo, logout, `/auth/me`. Pendências: rate limit (ISS-007), reuso de refresh (ISS-003), recuperação de senha (ISS-008). |
| `identity` — equipe e convites | stable | 2026-11-05 | Convite com unidades e, para o cargo barbeiro, ligado a um barbeiro cadastrado (não cria mais barbeiro, DEC-016); `lookup` sem gastar; aceite atômico (UPDATE condicional, testado com concorrência); desativação. Link volta na resposta (ISS-004). |
| `identity` — RBAC | stable | 2026-11-05 | 19 permissões × 4 cargos × escopo `all/unit/own` (`docs/PERMISSIONS_MAP.md`, verificado por teste). Permissões de módulos futuros já declaradas. |
| `identity` — barbeiros | stable | 2026-11-06 | CRUD `/barbers` com escopo de unidade; cadastro separado dos logins; vínculo explícito (convite com `barber_id` ou `user_id`). Spec `✅completed_registry-basic-crud.md`, DEC-016. ISS-018. |
| `identity` — unidades, expediente e configurações | in progress | 2026-11-06 | Spec `⏳active_identity-units-hours.md` (S01), DEC-017. CRUD `/tenant/units`, `/hours` (semana inteira), `/tenant/unit-exceptions` (multi-unidade, sobreposição barrada por `btree_gist`), `/tenant/holidays` (nacionais com móveis), `/tenant/settings`; permissão `unit:configure`; `get_unit_calendar` no `public`. Falta o `402` do plano (ISS-021, S15). |
| Admin da plataforma | in progress | 2026-11-05 | Seed pronto (`python -m app.management.seed platform-admin`, no `public`). Falta login (ISS-005). |
| `catalog` — serviços | stable | 2026-11-06 | CRUD `/services` (nome único sem caixa, preço em centavos, só quem vê todas as unidades escreve) e `PUT /barbers/{id}/services`. Spec `✅completed_registry-basic-crud.md`. Combos, clubes e planos: spec própria depois. |
| `scheduling` — jornada, turnos especiais, ausências | in progress | 2026-11-07 | Spec `⏳active_scheduling-barber-schedule.md` (S02), DEC-018. `/schedules`, `/barbers/{id}/schedule`, `/barbers/{id}/shift-overrides/{date}`, `/time-off` (permissão por tipo), `/working-time`; `capacity_minutes` e `barbers_without_hours` no `public`. Backend completo; falta o navegador no frontend. |
| Agenda (disponibilidade, agendamentos) | planned | 2026-11-07 | Spec `⚪draft_scheduling-appointments.md` (S03), no módulo `scheduling`. |
| `clients` — cadastro | stable | 2026-11-06 | CRUD `/clients`, telefone E.164 único, busca paginada por nome/telefone; `own` vazio até a agenda. Spec `✅completed_registry-basic-crud.md`. ISS-020. |
| Link público + OTP do cliente (`booking`) | planned | 2026-11-06 | Spec `⚪draft_booking-public-link.md` (S04). Redis (OTP), Turnstile. |
| Comanda, comissões, caixa e despesas, clubes e pacotes | planned | 2026-11-06 | Specs `⚪draft_sales-tickets.md` (S06), `⚪draft_commissions-rules-closing.md` (S08), `⚪draft_finance-cash-expenses.md` (S09), `⚪draft_memberships-clubs-packages.md` (S07), `⚪draft_catalog-products-combos.md` (S05). Sem gateway (PD-10). |
| Conversas / WhatsApp + `ai-agent` | planned | 2026-11-06 | Specs `⚪draft_messaging-whatsapp-inbox.md` (S10), `⚪draft_assistant-ai-agent.md` (S11), `⚪draft_automations-messages-campaigns.md` (S12); eventos e worker em `⚪draft_platform-events-jobs.md` (S00). Depende de eventos de domínio. Desenho já decidido (doc §5): App Secret e verify token **globais** no `public`, `whatsapp_number_routes` (`phone_number_id` UNIQUE → tenant) espelhando o número do schema, tokens Meta por barbearia com envelope encryption (DEK por tenant, doc Camada 4), relay fatiado por tenant, API key por tenant no lugar de token compartilhado. |

## Planejamento

Produto inteiro planejado em 2026-11-06: [`docs/ROADMAP.md`](../../../docs/ROADMAP.md) (decisões
PD-01–PD-42, módulos, eventos, ordem em 4 fases) e specs `⚪draft_` S00–S18 em `docs/specs/`.
Também em draft: unidades e expediente (S01), ficha do cliente (S13), relatórios (S14), plano e
créditos de IA (S15), importação (S16), endurecer a autenticação (S17).

## Qualidade

| Item | Estado | Notas |
|---|---|---|
| Suíte | 154 testes verdes (2026-11-07) | Inclui 35 dos cadastros (barbeiros, serviços, clientes: regras, escopos e cruzamento entre duas barbearias). Provisionamento real por teste; limpeza total no fim da sessão. ~18 s. |
| Lint | verde | `ruff check`, `ruff format --check`, `lint-imports` (4 contratos). |
| Banco | verde | `alembic check` sem pendências no controle e no conjunto de tenant (`tenant_template`). |
| CI | configurado | `.github/workflows/ci.yml`: lint + fronteiras + `migrate --apply --template` + os dois `alembic check` + pytest. Simulado num Postgres zerado em 2026-11-05. |
