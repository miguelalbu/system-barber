# Documentação do backend

| Pasta / arquivo | O que é | Quem escreve |
|---|---|---|
| [`specs/`](specs/) | **Planejamento antes do código.** Uma spec por funcionalidade, criada a partir do [`_template.md`](specs/_template.md) *antes* de implementar, e atualizada até virar `✅completed_`. É o contrato: regras de negócio, payloads, tabelas, permissões e critérios de aceite. | pessoa ou IA, à mão |
| [`api/`](api/README.md) | **Referência da API**, um arquivo por grupo de rotas (auth, barbearia, equipe, control plane): parâmetros, corpos, respostas, schemas e quem pode chamar. | **gerada** do OpenAPI — `make docs-api` |
| [`PERMISSIONS_MAP.md`](PERMISSIONS_MAP.md) | Cargo → permissão → escopo. | tabela gerada de `permissions.py` |
| [`ENVIRONMENT_VARIABLES.md`](ENVIRONMENT_VARIABLES.md) | Variáveis lidas pelo `Settings`. | à mão |

## Fluxo

```text
docs/specs/⚪draft_<dominio>-<feature>.md      planejar: regras, contrato, critérios
        ↓  aprovada
docs/specs/⏳active_...                         implementar seguindo a spec
        ↓  make check-backend · make docs-api
docs/specs/✅completed_...  +  docs/api/ regenerada
```

- Nome da spec: `<ícone><status>_<dominio>-<feature>.md`; renomeie quando o status mudar.
- Spec que também toca o frontend tem espelho em `frontend/docs/specs/`, cada uma apontando para a
  outra no cabeçalho.
- `docs/api/` **não se edita à mão**: `tests/test_contracts/test_api_docs.py` falha se ela não for
  exatamente o que o OpenAPI do código gera. O *porquê* de uma regra mora na spec; o *como chamar*,
  na referência gerada.
- Decisões de arquitetura (DEC-NNN), problemas conhecidos (ISS-NNN) e o estado de cada módulo ficam
  na memória da IA, em [`../.github/memory/`](../.github/memory/).
