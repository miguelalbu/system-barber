# Mapa de permissões

Quem pode o quê, por cargo. **Fonte da verdade:** `app/modules/identity/permissions.py` — a tabela
abaixo é gerada a partir dele e verificada por `tests/test_contracts/test_permissions_doc.py`.
Depois de mudar o mapa, regenere com:

```bash
UPDATE_CONTRACT_SNAPSHOTS=1 .venv/bin/python -m pytest tests/test_contracts/test_permissions_doc.py
```

## Escopos

| Escopo | Alcance |
|---|---|
| `all` | toda a barbearia |
| `unit` | só as unidades ligadas ao usuário (`user_units`; lista vazia = todas) |
| `own` | só os registros do próprio barbeiro (`barber_id` do token) |
| — | sem a permissão: a rota responde 403 |

## Regras

- O código pergunta a permissão, nunca o cargo (`Depends(require(Permission.X))`, DEC-004).
- As permissões **não** vão no JWT: são resolvidas no servidor a cada request, então mudar o mapa
  vale imediatamente.
- O frontend recebe o mapa do próprio usuário em `GET /auth/me` (`permissions`) para montar a
  navegação e esconder ações — mas quem decide é sempre o backend.
- Permissões declaradas para módulos que ainda não existem (agenda, clientes, financeiro…) já estão
  no mapa para o frontend poder se orientar; a rota que as usa nasce com a spec do módulo.

## Tabela

<!-- BEGIN:permissions -->
| Permissão | `owner` | `manager` | `receptionist` | `barber` |
|---|---|---|---|---|
| `appointment:read` | all | unit | unit | own |
| `appointment:create` | all | unit | unit | own |
| `appointment:update` | all | unit | unit | own |
| `appointment:cancel` | all | unit | unit | — |
| `client:read` | all | unit | unit | own |
| `client:write` | all | unit | unit | — |
| `catalog:read` | all | unit | unit | unit |
| `catalog:write` | all | unit | — | — |
| `ticket:read` | all | unit | unit | own |
| `ticket:write` | all | unit | unit | — |
| `finance:read` | all | unit | — | — |
| `finance:write` | all | unit | — | — |
| `commission:read` | all | unit | — | own |
| `conversation:read` | all | unit | unit | own |
| `conversation:reply` | all | unit | unit | — |
| `team:read` | all | unit | unit | — |
| `team:manage` | all | unit | — | — |
| `tenant:configure` | all | — | — | — |
| `unit:configure` | all | unit | — | — |
| `subscription:manage` | all | — | — | — |
<!-- END:permissions -->
