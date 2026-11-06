# CLAUDE.md — Navalha · Backend (core-api)

Instruções de trabalho para qualquer sessão de agente de IA (Claude Code, Copilot etc.) neste
projeto.

`.github/specs/` é o plano de execução e a memória arquitetural escrita do projeto.
`.github/index.toml` descreve o resto do sistema de instruções (`rules.md`, `soul.md`, `memory/`).
`.github/rules.md` é a fonte das regras técnicas; este arquivo resume o essencial e aponta para lá.

## O projeto

Backend do **Navalha**, SaaS de gestão para barbearias com atendimento automatizado no WhatsApp.
É o sistema de registro: barbearias (tenants), equipe, permissões e, nos próximos blocos, catálogo,
agenda, clientes, financeiro e conversas. O frontend (`../frontend`, React + Vite) fala com ele só
pela API HTTP, com JWT. A API é o contrato entre os dois.

Resumo:

* Python 3.12 + FastAPI, async. PostgreSQL 16 com **Row-Level Security** via SQLAlchemy 2 async;
  migrations Alembic. Redis provisionado, ainda não usado.
* **Multi-tenant em banco compartilhado** (DEC-001): toda tabela de barbearia tem `tenant_id` e
  policy RLS; a API conecta com um role sem privilégio; o tenant vem do domínio (DEC-002).
* **Monólito modular por feature** (DEC-006): `app/core/` (infraestrutura) e `app/modules/<modulo>/`,
  todos com a forma `router/ service/ repository/ model/` + `schemas.py` + `public.py`. Hoje há um
  módulo, `identity`; os próximos seguem `.github/skills/new-module.md`.
* Um módulo importa outro **só pelo `public.py`**; dentro do módulo, `router → service → repository
  → model`. Verificado por `lint-imports` e por `tests/test_contracts/`.
* RBAC por permissão com escopo (`all/unit/own`), mapa único em
  `app/modules/identity/permissions.py` (DEC-004).
* Testes com `pytest` contra o Postgres de dev; snapshots de contrato em `tests/test_contracts/`.

Comandos (na **raiz do repositório**; ver `make help`):

| para | comando |
|---|---|
| subir backend + frontend | `make up` · `make down` · `make ps` |
| logs / shell / psql | `make logs SERVICE=core-api` · `make shell` · `make psql` |
| criar o venv local (uma vez) | `make setup-backend` |
| testes | `make test-backend` |
| lint (ruff + fronteiras) | `make lint-backend` |
| portão completo | `make check-backend` (pytest + ruff + lint-imports + alembic check) |
| migrations | `make migrate` · nova: `cd backend && .venv/bin/alembic revision --autogenerate -m "..."` |
| conta de suporte | `make seed-admin` |

A API sobe em `http://localhost:8000` (docs em `/docs`). Em dev, use o header `X-Tenant-Slug`.
Variáveis de ambiente: `docs/ENVIRONMENT_VARIABLES.md`. Permissões: `docs/PERMISSIONS_MAP.md`.

---

## Idioma e convenções de nomenclatura

* Identificadores em **inglês**, `snake_case`; classes `PascalCase`; constantes
  `SCREAMING_SNAKE_CASE`.
* Docs, specs e mensagens ao usuário final em **português**.
* Arquivo de `router/` = um por recurso; de `service/` = um por ação (verbo + objeto); de
  `repository/` = um por agregado; de `model/` = um por agregado + `enums.py`.
* Mensagem de erro ao usuário nunca expõe detalhe interno.

---

## Manter este CLAUDE.md atualizado

Revise este arquivo quando uma mudança estrutural tornar uma regra, convenção, tecnologia ou caminho
daqui desatualizado. Não edite a cada alteração pequena, e só altere com pedido ou autorização
explícita — se perceber defasagem, avise e proponha o diff.

Este arquivo contém **instruções e convenções**, não um diário de alterações. Decisões de
funcionalidade e regras de negócio vão para `.github/specs/` e `.github/memory/`.

### Sistema de contexto `.github/`

1. Ler `.github/index.toml` e carregar `project.toml`, `rules.md` e `soul.md`.
2. Casar o pedido com uma rota `on_*` do `index.toml` e ler os arquivos do `read` dela.
3. Escrever em `.github/` só o que está no `write` da rota.
4. `index.toml`, `project.toml`, `rules.md`, `soul.md`, `.contextignore` e `skills/` são somente
   leitura, salvo pedido explícito.
5. Specs: `⚪draft_` → `⏳active_` → `✅completed_`; o arquivo é renomeado quando o status muda.

---

## Sequência obrigatória para qualquer alteração pedida

1. **Ler o código atual** — ele é a fonte da verdade. Antes de editar, leia
   `.github/memory/issues.md`.
2. **Consultar a spec** — mudança de domínio, regra de negócio, rota ou tabela tem spec em
   `.github/specs/`. Funcionalidade nova **começa** pela spec (`specs/_template.md`); se tocar o
   frontend, a spec tem espelho em `frontend/.github/specs/`.
3. **Planejar** — identificar módulo, camadas (`router/ service/ repository/ model/`), migrations,
   permissões e o impacto no frontend.
4. **Implementar** — respeitando a arquitetura modular e as regras de multi-tenancy de `rules.md`.
   Reaproveite o que existe antes de criar; não adicione dependência sem aprovação.
5. **Validar** — `make check-backend`. Uma etapa só termina com tudo verde. Snapshot de contrato
   falhando: ache a causa; regenerar só se a mudança for intencional e estiver na spec.
6. **Atualizar a documentação** — checkboxes e status da spec, `memory/progress.md`,
   `memory/issues.md` (o que foi achado no caminho), `memory/decisions.md` (decisão nova),
   `README.md` (endpoints).
7. **Sinalizar defasagem deste CLAUDE.md** — avise e proponha o diff.

---

## Depois de implementar

Verifique:

* Toda tabela nova de barbearia tem `tenant_id` e policy RLS na migration, e um teste de
  isolamento prova que outra barbearia não a enxerga.
* Toda rota nova tem guarda de permissão (ou é explicitamente pública na spec) e aplica o escopo.
* Regra de negócio está em `service/`, SQL em `repository/`, o router está fino.
* Nenhum módulo importou outro por fora do `public.py`; `core` não importou módulo.
* Nenhuma pasta ou arquivo do layout plano antigo foi recriado.
* Os diffs de snapshot (`openapi`, `routes`, `db_schema`) contêm só o que a spec descreve.
* Variável de ambiente nova está em `.env.example` e em `docs/ENVIRONMENT_VARIABLES.md`.

---

## Controle de versão

* Commits `type(scope): description` (`feat`, `fix`, `refactor`, `docs`, `test`, `chore`); SemVer.
* O CI (`.github/workflows/ci.yml`, na raiz do repo) roda lint, fronteiras, migrations e testes.
* O histórico é o backup: nada de cópias de arquivo; `git diff` revisa e `git revert` desfaz.

---

## Fonte da verdade

Hierarquia para resolver conflitos:

1. **Código atual**
2. **Specs em `.github/specs/`**
3. **Decisões explícitas tomadas na conversa**
4. **Este CLAUDE.md e o resto do sistema de instruções** (`rules.md`, `soul.md`, `memory/`)
5. **Inferências**

Se houver conflito, o código vence e a documentação é atualizada — nunca o contrário.

---

## Regra geral para sessões futuras

```text
Código atual  (+ memory/issues.md)
        ↓
Specs
        ↓
Planejamento
        ↓
Implementação
        ↓
Testes  (make check-backend)
        ↓
Documentação  (spec + memory/)
```

O conhecimento arquitetural permanece nas specs e em `.github/memory/`; o código é sempre a
representação definitiva do estado atual.
