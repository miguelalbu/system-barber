<!-- Template de spec — copie e renomeie: <ícone><status>_<dominio>-<feature>.md
     ⚪draft_ · ⏳active_ · ✅completed_ — renomeie o arquivo quando o **Status** mudar.
     Apague este bloco de comentário depois de copiar. -->

# Nome da funcionalidade

**Priority:** high | medium | low
**Status:** draft | active | completed
**Espelho no frontend:** `frontend/docs/specs/<arquivo>.md` | não se aplica

## Overview

<!-- Um parágrafo: o que a funcionalidade faz e por que existe. A spec deve ser
     auto-contida — quem implementa não precisa abrir outra fonte para entender. -->

## Decisões de produto já tomadas

<!-- O que o dono do produto decidiu e NÃO deve ser reaberto na implementação. -->

| Parâmetro | Valor |
|---|---|
| | |

## Business Rules

<!-- Invariantes que sempre devem valer. Marque [x] quando implementado e testado. -->

- [ ]
- [ ]

## Data Contract

<!-- Rotas, métodos, payloads, tabelas e colunas. Mudar qualquer um deles depois
     é mudança de contrato com o frontend ou com o banco. -->

```text
Rota:

Input:

Output:

Erros:
```

### Banco de dados

<!-- Tabelas novas: tabela de barbearia herda TenantBase, sem tenant_id, migration no conjunto
     alembic/tenant e só expand/contract (DEC-011). -->

## Permissões

<!-- Quais Permission (app/modules/identity/permissions.py) e com qual escopo por cargo. -->

| Permissão | owner | manager | receptionist | barber |
|---|---|---|---|---|
| | | | | |

## Acceptance Criteria

<!-- Checklist verificável. Marque [x] conforme cada critério for atendido. -->

- [ ]
- [ ]
- [ ] Testes em `tests/test_<modulo>/` cobrindo as regras acima
- [ ] Snapshots de contrato revisados (`UPDATE_CONTRACT_SNAPSHOTS=1` só se a mudança for intencional)

## Dependencies

<!-- Specs, módulos ou serviços externos dos quais esta funcionalidade depende. -->

-

## Notes

<!-- Casos de borda, perguntas em aberto, divergências encontradas durante a implementação
     (registre a resolução com data: "> Resolvido em AAAA-MM-DD: ..."). -->

-
