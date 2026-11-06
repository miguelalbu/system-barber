# CLAUDE.md — Navalha (monorepo)

SaaS de gestão para barbearias, com atendimento automatizado no WhatsApp. Este repositório tem
dois projetos, cada um com o **próprio** `CLAUDE.md` e a própria camada de contexto `.github/`
(DEC-010 do backend). Este arquivo só orienta; as regras de verdade estão lá.

| Projeto | Stack | Comece por |
|---|---|---|
| `backend/` | FastAPI + PostgreSQL (RLS) — core-api | [`backend/CLAUDE.md`](backend/CLAUDE.md) → `backend/.github/index.toml` |
| `frontend/` | React 18 + Vite + TypeScript — landing e painel | [`frontend/CLAUDE.md`](frontend/CLAUDE.md) → `frontend/.github/index.toml` |
| `infra/` | init do Postgres (role de runtime sem privilégio) | `backend/.github/memory/decisions.md` (DEC-001) |
| `docs/` | desenvolvimento e contribuição, para o repo todo | [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md), [`docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md) |

## Como trabalhar aqui

1. Identifique o projeto do pedido e siga o `CLAUDE.md` dele (sequência obrigatória, regras,
   portão de testes). Pedido que toca os dois lados segue os dois.
2. **Funcionalidade nova começa pela spec**, escrita a partir do `_template.md` em
   `<projeto>/.github/specs/`. Se tocar backend e frontend, a spec existe nas duas pastas, uma
   apontando para a outra (`Espelho no ...:`). Guias: `backend/.github/skills/new-module.md` e
   `frontend/.github/skills/new-feature.md`.
3. A API é o contrato entre os projetos; o contrato congelado está em
   `backend/tests/test_contracts/snapshots/openapi.json`.
4. Portão: `make check` na raiz (o mesmo que o CI roda). Por projeto: `make check-backend`,
   `make check-frontend`.
5. Ao terminar: spec (checkboxes e status), `memory/progress.md`, `memory/issues.md` e
   `memory/decisions.md` do projeto afetado.

## Comandos (raiz)

```bash
make help            # todos os alvos
make up / down       # sobe/para backend + frontend (Docker)
make setup-backend   # venv local do backend (uma vez)
make check           # portão completo
```

## Fonte da verdade

Código atual → specs → decisões explícitas da conversa → `CLAUDE.md`/`.github/` → inferências.
Se houver conflito, o código vence e a documentação é atualizada.
