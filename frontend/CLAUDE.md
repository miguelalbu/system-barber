# CLAUDE.md — Navalha · Frontend

Instruções de trabalho para qualquer sessão de agente de IA (Claude Code, Copilot etc.) neste
projeto.

`docs/specs/` é o plano de execução e a memória arquitetural escrita do projeto.
`.github/index.toml` descreve o resto do sistema de instruções (`rules.md`, `soul.md`, `memory/`).
`.github/rules.md` é a fonte das regras técnicas; este arquivo resume o essencial e aponta para lá.

## O projeto

Frontend do **Navalha**, SaaS de gestão para barbearias com atendimento automatizado no WhatsApp:
a landing page (`/`), o login (`/entrar`) e o painel da equipe (`/app/*` — agenda, conversas,
clientes, cadastros, financeiro, dashboard). Fala com o backend (`../backend`, FastAPI) só pela API
HTTP, com JWT. A API é o contrato entre os dois.

Resumo:

* React 18 + TypeScript estrito + Vite 5 + React Router 6. CSS puro com design tokens (DEC-007).
* **Vertical slice por feature** (DEC-003): `src/features/<feature>/` com `index.ts` (API pública)
  e as pastas `api/ model/ pages/ ui/`; `src/shared/` para o que não é de domínio; `src/app/` para
  rotas e o shell do painel.
* Uma feature importa outra **só pelo `index.ts`**; `shared` não importa feature; feature não importa
  `app`. Verificado pelo ESLint (`import/no-restricted-paths`).
* **Estado real hoje:** só a sessão (`features/auth`) usa a API. As demais telas usam
  `api/*.mock.ts` até o backend ter o módulo correspondente (ISS-002). TanStack Query entra com a
  primeira feature real (DEC-005).
* Testes com Vitest em `tests/` (DEC-004).

Comandos (na **raiz do repositório**; ver `make help`):

| para | comando |
|---|---|
| subir backend + frontend | `make up` · `make down` · `make logs SERVICE=web` |
| lint (ESLint + fronteiras) | `make lint-frontend` |
| testes | `make test-frontend` |
| portão completo | `make check-frontend` (lint + typecheck + testes + build) |
| direto na pasta | `npm run dev` · `npm run lint` · `npm run test` · `npm run build` |
| API consumida (`docs/api/`) | `make docs-api` (gerada; nunca à mão) |

O painel sobe em `http://localhost:5173`. Em localhost, o login pede a barbearia (slug). Variáveis
de ambiente: `docs/ENVIRONMENT_VARIABLES.md`.

---

## Idioma e convenções de nomenclatura

* Identificadores e nomes de arquivo/pasta em **inglês**; todo texto de tela em **português**;
  URLs em português (`/app/agenda`).
* Componentes e telas em `PascalCase.tsx`; tela termina em `Screen`; hooks `useX`; demais
  `camelCase.ts` ou `<dominio>.<papel>.ts` (`scheduling.types.ts`, `auth.api.ts`).
* Tipo de domínio em `model/`, DTO de request/response em `api/`, props junto do componente.

---

## Manter este CLAUDE.md atualizado

Revise este arquivo quando uma mudança estrutural tornar uma regra, convenção, tecnologia ou caminho
daqui desatualizado. Não edite a cada alteração pequena, e só altere com pedido ou autorização
explícita — se perceber defasagem, avise e proponha o diff.

Este arquivo contém **instruções e convenções**, não um diário de alterações. Decisões de
funcionalidade e regras de negócio vão para `docs/specs/` e `.github/memory/`.

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
2. **Consultar a spec** — tela, fluxo ou integração nova tem spec em `docs/specs/`. Funcionalidade
   nova **começa** pela spec (`docs/specs/_template.md`); se consumir API, a spec do backend é o espelho e
   o contrato está em `backend/tests/test_contracts/snapshots/openapi.json`.
3. **Planejar** — identificar a feature, as pastas (`api/ model/ pages/ ui/`), o que muda no shell e
   no router, e onde mora cada estado.
4. **Implementar** — respeitando a arquitetura por feature. Reaproveite `shared/ui/` e o que a
   feature já tem; não adicione dependência sem aprovação.
5. **Validar** — `make check-frontend` e a tela conferida no navegador. Uma etapa só termina com
   tudo verde.
6. **Atualizar a documentação** — `make docs-api` se uma chamada à API mudou; checkboxes e status da spec, `memory/progress.md`,
   `memory/issues.md`, `memory/decisions.md`, `README.md` (rotas e estado das telas).
7. **Sinalizar defasagem deste CLAUDE.md** — avise e proponha o diff.

---

## Depois de implementar

Verifique:

* A direção de dependência foi respeitada (o lint garante — nunca desligue a regra).
* Nenhum componente com tipo de negócio foi parar em `shared/`.
* Nenhuma pasta de topo herdada (`components/`, `hooks/`, `lib/`, `utils/`, `types.ts`, `data/`,
  `api/`, `auth/`) foi recriada em `src/`.
* O estado novo está na camada certa (servidor, local, URL, context da feature).
* Nenhum `*.api.ts` importa componente React.
* Cores e espaçamentos vêm de `tokens.css`.
* Todo texto novo está em português.
* Os testes relevantes rodaram e passaram.
* Decisão arquitetural nova está em `memory/decisions.md`.

---

## Controle de versão

* Commits `type(scope): description` (`feat`, `fix`, `refactor`, `docs`, `test`, `chore`); SemVer.
* O CI (`.github/workflows/ci.yml`, na raiz do repo) roda lint, typecheck, testes e build.
* O histórico é o backup: nada de cópias de arquivo; `git diff` revisa e `git revert` desfaz.

---

## Fonte da verdade

1. **Código atual**
2. **Specs em `docs/specs/`**
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
Testes  (make check-frontend + navegador)
        ↓
Documentação  (spec + memory/)
```
