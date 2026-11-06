# Contribuindo

O Navalha é desenvolvido com apoio de IA, e o processo é desenhado para que qualquer sessão — de
pessoa ou de agente — encontre o contexto escrito, em vez de reconstruí-lo. Inspirado no fluxo da
ClaraAI.

## O fluxo

```text
issue (o pedido)
   ↓
spec  (<projeto>/.github/specs/⚪draft_ → ⏳active_)      ← o contrato: regras, payloads, tabelas, critérios
   ↓
implementação  (seguindo rules.md e as skills)
   ↓
make check  (+ navegador, se tem tela)
   ↓
spec ✅completed_ + memory/progress.md + issues.md + decisions.md
   ↓
PR  (template com checklist) → CI verde → merge
```

## Specs

- Toda funcionalidade nova nasce como spec **antes** do código, a partir do `_template.md` do
  projeto. Correção pequena dispensa spec — diga no PR por quê.
- Nome: `<ícone><status>_<dominio>-<feature>.md`; renomeie quando o status mudar.
- Funcionalidade com backend e tela: uma spec em cada projeto, apontando uma para a outra.
- A spec é a fonte da verdade do comportamento esperado. Divergência descoberta na implementação
  vira nota datada na spec — nunca um desvio silencioso.

## Memória do projeto (`<projeto>/.github/memory/`)

| Arquivo | O que vai | Regra |
|---|---|---|
| `progress.md` | estado de cada módulo/feature | atualizar ao fim de cada tarefa |
| `issues.md` | bugs, workarounds, áreas frágeis (`ISS-NNN`) | registrar mesmo o que não for corrigido agora |
| `decisions.md` | decisões de arquitetura (`DEC-NNN`) | só acrescentar; mudar = nova DEC que substitui a antiga |

## Commits e branches

- `type(scope): description` — `feat`, `fix`, `refactor`, `docs`, `test`, `chore`. Escopo = módulo,
  feature ou área (`identity`, `scheduling`, `frontend`, `ci`).
- Uma branch por spec (`feat/<dominio>-<feature>`); `main` sempre verde.
- Versionamento SemVer por projeto (`backend/pyproject.toml`, `frontend/package.json`).

## Portão

`make check` precisa passar antes do PR — é exatamente o que o CI roda:

- backend: `ruff`, `lint-imports` (fronteiras entre módulos), `pytest` (comportamento + snapshots
  de contrato), `alembic check`;
- frontend: ESLint (com fronteiras entre features), `tsc`, Vitest, build.

Snapshot de contrato falhando significa que o comportamento da API mudou. Ache a causa; regenere
(`UPDATE_CONTRACT_SNAPSHOTS=1`) só se a mudança for intencional e estiver descrita na spec.
