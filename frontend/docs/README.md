# Documentação do frontend

| Pasta / arquivo | O que é | Quem escreve |
|---|---|---|
| [`specs/`](specs/) | **Planejamento antes do código.** Uma spec por tela ou fluxo, criada a partir do [`_template.md`](specs/_template.md) *antes* de implementar, e atualizada até virar `✅completed_`: rotas, estados, chamadas à API, permissões e critérios de aceite. | pessoa ou IA, à mão |
| [`api/`](api/README.md) | **API consumida**: que endpoint do backend cada feature chama, ligado à referência completa em `backend/docs/api/`. | **gerada** das chamadas em `src/features/*/api` + contrato do backend — `make docs-api` |
| [`ENVIRONMENT_VARIABLES.md`](ENVIRONMENT_VARIABLES.md) | Variáveis do bundle (`VITE_*`) e do dev server. | à mão |

## Fluxo

```text
docs/specs/⚪draft_<dominio>-<feature>.md      planejar: telas, fluxos, estado, contrato
        ↓  aprovada (com a spec espelho do backend, se houver API)
docs/specs/⏳active_...                         implementar seguindo a spec
        ↓  make check-frontend · make docs-api · conferir no navegador
docs/specs/✅completed_...  +  docs/api/ regenerada
```

- `docs/api/` **não se edita à mão**: `tests/api-docs.test.ts` falha se ela estiver desatualizada
  **e** se alguma função do frontend chamar uma rota que não existe no contrato do backend
  (`backend/tests/test_contracts/snapshots/openapi.json`).
- Decisões (DEC-NNN), problemas conhecidos (ISS-NNN) e o estado de cada feature ficam em
  [`../.github/memory/`](../.github/memory/).
