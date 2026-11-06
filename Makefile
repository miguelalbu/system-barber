# ==============================================================================
# Navalha — atalhos do monorepo (backend + frontend).
#
# Uso: make <alvo>        Rode `make help` para ver todos os alvos.
# Containers: backend/docker-compose.yml (db, redis, core-api) e
#             frontend/docker-compose.yml (web), ligados pela rede `navalha`.
# ==============================================================================

SHELL := bash

BE_DC := docker compose -f backend/docker-compose.yml
FE_DC := docker compose -f frontend/docker-compose.yml

# The virtualenv layout differs on Windows (Git Bash).
ifeq ($(OS),Windows_NT)
VENV_BIN := .venv/Scripts
else
VENV_BIN := .venv/bin
endif
PYTHON ?= $(shell command -v python3.12 || command -v python3)

SERVICE ?= core-api

.DEFAULT_GOAL := help

# ── Ajuda ─────────────────────────────────────────────────────────────────────
.PHONY: help
help: ## Mostra esta ajuda
	@echo "Navalha - comandos disponiveis:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

# ── Ambiente Docker ───────────────────────────────────────────────────────────
.PHONY: up
up: ## Sobe backend (db, redis, core-api) e frontend (web)
	$(BE_DC) up -d
	$(FE_DC) up -d

.PHONY: build
build: ## Rebuilda as imagens e sobe (dependencia nova, Dockerfile)
	$(BE_DC) up -d --build
	$(FE_DC) up -d --build

.PHONY: down
down: ## Para os containers (os dados do banco ficam)
	$(FE_DC) down
	$(BE_DC) down

.PHONY: ps
ps: ## Status dos containers
	@$(BE_DC) ps
	@$(FE_DC) ps

.PHONY: logs
logs: ## Logs de um servico (SERVICE=core-api|db|redis|web)
	@if [ "$(SERVICE)" = "web" ]; then $(FE_DC) logs -f web; else $(BE_DC) logs -f $(SERVICE); fi

.PHONY: shell
shell: ## Shell no container da API
	$(BE_DC) exec core-api sh

.PHONY: psql
psql: ## psql no banco como dono do schema (ignora RLS!)
	$(BE_DC) exec db psql -U navalha -d navalha

.PHONY: migrate
migrate: ## Migra o controle e depois cada barbearia (servico one-shot)
	$(BE_DC) run --rm migrate

.PHONY: core-key
core-key: ## Cria uma chave do Core (NAME=... SCOPES=tenant:read,tenant:provision)
	$(BE_DC) exec core-api python -m app.management.core_key create \
		--name "$(or $(NAME),core-dev)" --scopes "$(or $(SCOPES),tenant:read,tenant:provision)"

.PHONY: seed-admin
seed-admin: ## Cria a conta de suporte da plataforma (SEED_ADMIN_*)
	$(BE_DC) exec core-api python -m app.management.seed platform-admin

# ── Backend (venv local) ──────────────────────────────────────────────────────
.PHONY: setup-backend
setup-backend: ## Cria backend/.venv e instala as dependencias de dev
	cd backend && $(PYTHON) -m venv .venv && $(VENV_BIN)/python -m pip install -q --upgrade pip \
		&& $(VENV_BIN)/python -m pip install -q -e ".[dev]"
	@[ -f backend/.env ] || { cp backend/.env.example backend/.env; echo "backend/.env criado a partir do .env.example"; }

.PHONY: test-backend
test-backend: ## pytest (comportamento + snapshots de contrato) contra o Postgres de dev
	cd backend && $(VENV_BIN)/python -m pytest -q

.PHONY: lint-backend
lint-backend: ## ruff (lint + formato) e lint-imports (fronteiras entre modulos)
	cd backend && $(VENV_BIN)/ruff check app tests tools && $(VENV_BIN)/ruff format --check app tests tools \
		&& $(VENV_BIN)/lint-imports

.PHONY: check-backend
check-backend: lint-backend test-backend ## Portao do backend: lint + testes + os dois alembic check
	cd backend && $(VENV_BIN)/python -m app.management.migrate --apply --template \
		&& $(VENV_BIN)/alembic -n control check \
		&& $(VENV_BIN)/alembic -n tenant -x schema=tenant_template check

.PHONY: docs-api
docs-api: ## Regenera backend/docs/api e frontend/docs/api a partir do OpenAPI
	cd backend && $(VENV_BIN)/python -m tools.api_docs
	cd frontend && npm run docs:api

# ── Frontend ──────────────────────────────────────────────────────────────────
.PHONY: setup-frontend
setup-frontend: ## Instala as dependencias do frontend (npm ci)
	cd frontend && npm ci

.PHONY: lint-frontend
lint-frontend: ## ESLint (inclui fronteiras entre features)
	cd frontend && npm run lint

.PHONY: test-frontend
test-frontend: ## Vitest
	cd frontend && npm run test

.PHONY: check-frontend
check-frontend: ## Portao do frontend: lint + typecheck + testes + build
	cd frontend && npm run check && npm run build

# ── Tudo ──────────────────────────────────────────────────────────────────────
.PHONY: check
check: check-backend check-frontend ## Portao completo (o mesmo que o CI roda)
