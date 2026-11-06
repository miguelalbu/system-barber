<!-- Template de spec — copie e renomeie: <ícone><status>_<dominio>-<feature>.md
     ⚪draft_ · ⏳active_ · ✅completed_ — renomeie o arquivo quando o **Status** mudar.
     Apague este bloco de comentário depois de copiar. -->

# Nome da funcionalidade

**Priority:** high | medium | low
**Status:** draft | active | completed
**Espelho no backend:** `backend/.github/specs/<arquivo>.md` | não se aplica

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

## Telas e fluxos

<!-- Rota, tela (Screen) e fluxos (pastas em pages/). Link do design, se houver. -->

| Rota | Tela | Fluxos |
|---|---|---|
| | | |

## Data Contract

<!-- Endpoints consumidos (do backend: rota, método, payload). Tipos de domínio em model/*.types.ts.
     Nunca invente campo: confira em backend/tests/test_contracts/snapshots/openapi.json. -->

```text
GET  /...

Resposta:
```

## Estado

<!-- Onde mora cada estado: TanStack Query, local, URL, context da feature. -->

## Permissões

<!-- Quais permissões de GET /auth/me escondem navegação ou ações nesta tela. -->

## Acceptance Criteria

<!-- Checklist verificável. Marque [x] conforme cada critério for atendido. -->

- [ ]
- [ ]
- [ ] Testes em `tests/` cobrindo as regras puras da feature
- [ ] Tela conferida no navegador (estados vazio, carregando, erro)
- [ ] `make check-frontend` verde

## Dependencies

<!-- Specs, módulos ou serviços externos dos quais esta funcionalidade depende. -->

-

## Notes

<!-- Casos de borda, perguntas em aberto, divergências encontradas durante a implementação
     (registre a resolução com data: "> Resolvido em AAAA-MM-DD: ..."). -->

-
