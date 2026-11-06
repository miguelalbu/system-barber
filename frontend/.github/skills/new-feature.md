# Criar uma feature nova (ou ligar uma feature mock à API)

**Quando usar:** ao criar uma tela/domínio novo no painel, ou ao trocar o mock de uma feature
existente pela API real quando o módulo correspondente chegar no backend.

## Antes de começar

- A spec existe e está `⏳active` em `docs/specs/`. Se a feature consome API, a spec do backend
  existe (espelho) e a rota já está no `openapi.json` do backend.
- Leia `memory/issues.md` e as decisões DEC-003 (forma da feature) e DEC-005 (TanStack Query).

## Passos — feature nova

1. **Pasta** — `src/features/<nome>/` (inglês, singular ou nome do domínio do backend). O ESLint já
   protege a feature nova: as zonas são geradas a partir das pastas.
2. **Tipos** — `model/<nome>.types.ts` com os tipos de domínio, espelhando o payload do backend.
3. **API** — `api/<nome>.api.ts` com funções puras sobre `request()` de `@/shared/api/http`. Sem
   React aqui.
4. **Tela** — `pages/<Nome>Screen.tsx` (export default): busca, guarda e compõe. Corpo
   apresentacional em `pages/<fluxo>/` (`list/`, `detail/`, `create/`). Nunca uma pasta genérica
   (`components/`, `view/`).
5. **Barrel** — `index.ts` exporta a tela (`export { default as XScreen } from ...`) e só o que
   outros precisam.
6. **Rota** — `src/app/router.tsx`, importando do barrel. Título da topbar em
   `app/_shell/AppLayout.tsx` (`TITLES`) e item de menu em `app/_shell/Sidebar.tsx` (`NAV`).
7. **Estilo** — classes em `shared/styles/panel.css` usando só `var(--token)`.
8. **Testes** — regra pura em `tests/<nome>-*.test.ts`.

## Passos — trocar o mock pela API real

1. Crie `api/<nome>.api.ts` e substitua os imports de `api/<nome>.mock.ts` nas telas.
2. Crie `api/<nome>.queries.ts` com os hooks do TanStack Query (já instalado, DEC-010). Modelo:
   `features/registry/api/registry.queries.ts`. Caminho do `request()` sempre literal; filtro e
   paginação vão em `query` (senão o gerador de `docs/api/` não casa a chamada com o contrato).
3. Trate os estados de carregando, vazio e erro com `shared/ui/TableState` (`errorMessage()` traduz
   o `ApiError`); apagar com `shared/ui/DeleteRecordDialog`.
4. Apague o `*.mock.ts` quando nenhuma tela o usar e feche a entrada correspondente da ISS-002.
5. Aplique as permissões do `/auth/me` para esconder ações que o cargo não tem (ISS-005).

## Verificação

```bash
make check-frontend   # lint + typecheck + testes + build
```

E confira a tela em http://localhost:5173 com a barbearia `demo` (ver `docs/DEVELOPMENT.md`).

## Armadilhas conhecidas

- Importar `@/features/x/api/...` de outra feature: o ESLint barra — exporte pelo `index.ts`.
- Componente com tipo de negócio em `shared/ui/`: o lugar é `features/<f>/ui/`.
- Dependência de runtime nova não chega ao container `web` sem rebuild (ISS-007).
