# Rules

Padrões inegociáveis deste projeto. Prevalecem sobre o conhecimento geral da IA.

## Code

- Código autoexplicativo; comentário explica o "porquê", nunca o "o quê".
- DRY: reaproveite `shared/ui/`, hooks e clients existentes antes de criar.
- Preferir solução nativa antes de dependência nova; nada de dependência por poucas linhas.
- TypeScript estrito (`strict`, `noUnusedLocals`, `noUnusedParameters`); sem `any` explícito.
- Todo erro tratado explicitamente; mensagem ao usuário nunca expõe detalhe interno.

## Architecture

Vertical slice por feature (DEC-003), no modelo do frontend da ClaraAI, adaptado para SPA com Vite.
Spec: `.github/specs/✅completed_frontend-feature-architecture.md`.

- **`features/<feature>/`** — cada domínio tem uma pasta com tudo o que precisa:
  - `index.ts` — a API pública da feature; o **único** ponto que outro código pode importar.
  - `model/` — `*.types.ts` (tipos de domínio), `*.constants.ts`, regras puras, contexts/estado
    da feature.
  - `api/` — `*.api.ts` (HTTP puro, via `shared/api/http.ts`), `*.mock.ts` (dados de
    demonstração enquanto o backend não tem o módulo) e, quando adotado, `*.queries.ts`
    (TanStack Query, DEC-005).
  - `pages/` — as telas (`<Nome>Screen.tsx`) no topo e uma pasta por fluxo (`login/`, `list/`,
    `create/`, `detail/`). Uma tela por rota.
  - `ui/` — componentes reaproveitados por mais de um fluxo da feature, ou exportados pelo
    `index.ts` para o shell/outras features.
- A raiz da feature tem **só** `index.ts` + as pastas `api/ model/ pages/ ui/`. Sem `index.tsx`
  aninhado, sem `utils/`, sem `types/` dentro de feature.
- **`shared/`** — o que não pertence a domínio nenhum: `api/` (cliente HTTP), `session/` (tokens e
  slug da barbearia), `ui/` (componentes visuais genéricos), `text/` (formatação), `styles/`
  (tokens e folhas globais). `shared/` **nunca** conhece tipo de negócio (`Appointment`, `Thread`,
  `Me`…).
- **`app/`** — composição: `router.tsx` (rotas → telas pelos barrels) e `_shell/` (layout do
  painel: sidebar, topbar).
- **Direção de dependência** (verificada pelo ESLint, `import/no-restricted-paths`):
  - `app` importa `features` e `shared`; nunca o contrário.
  - `features` importa `shared` e outra feature **só pelo `index.ts`** dela.
  - `shared` não importa `features` nem `app`.
  - Um `*.api.ts` nunca importa componente React.
- **Onde colocar um componente:** usado por um fluxo → na pasta do fluxo; por vários fluxos da
  mesma feature (ou exportado) → `features/<f>/ui/`; por 2+ features **e** sem tipo de negócio →
  `shared/ui/`; layout global → `app/_shell/`.
- **Pastas de topo proibidas** (o ESLint barra o import): `components/`, `hooks/`, `lib/`,
  `utils/`, `types.ts`, `data/`, `api/`, `auth/` na raiz de `src/`. Ou o arquivo é de uma feature,
  ou é de `shared/`.
- **Rotas:** caminhos de URL em português (`/entrar`, `/app/agenda`, `/app/cadastros`), nomes de
  feature e de arquivo em inglês.

## State

- Dado do servidor → TanStack Query quando adotado (DEC-005); até lá, `api/*.api.ts` + estado da
  tela.
- Formulário, modal local, aba, editor → estado local ou `useReducer`.
- Filtro e aba que devem sobreviver a refresh → URL (search params).
- Context só para provider estável e transversal, e ele mora na feature dona: sessão
  (`auth/model/authContext.tsx`), unidade selecionada (`auth/model/unitSelection.tsx`), modal de
  agendamento (`scheduling/model/appointmentModal.tsx`).

## Integration with the backend

- Toda chamada passa por `shared/api/http.ts`: base `/api` (proxy do Vite, mesma origem),
  `X-Tenant-Slug` em dev, bearer, renovação única de token em 401.
- Erro da API chega como `ApiError` com a mensagem de `{"detail"}` do backend; tela traduz status
  conhecidos (404 = barbearia não encontrada, etc.) e mostra o resto como veio.
- Tipos de payload espelham o backend (`backend/tests/test_contracts/snapshots/openapi.json`).
  Mudança de contrato na API exige spec espelhada nos dois projetos.
- Permissões do usuário vêm de `GET /auth/me` (`useAuth().can(...)`) e servem para esconder
  navegação e ações. Autorização de verdade é sempre do backend.

## Styling

- Toda cor, espaçamento, raio e fonte vem de `shared/styles/tokens.css` (`var(--...)`). Valor novo
  entra primeiro no token e na tela `/app/tokens`.
- Classes CSS em `kebab-case`, sem CSS-in-JS. Estilos do painel em `shared/styles/panel.css`;
  da landing em `features/landing/pages/landing/landing.css`.
- `style={{...}}` inline só para valor calculado em runtime (posição na agenda, largura de barra).

## Naming

- Componentes e telas em `PascalCase.tsx`; hooks `useX`; demais arquivos `camelCase.ts` ou
  `<dominio>.<papel>.ts` (`auth.types.ts`, `scheduling.mock.ts`).
- Tela termina em `Screen` (`AgendaScreen`); exportada como `default` no arquivo e nomeada no
  `index.ts`.
- Texto de UI em português; identificadores em inglês.

## Security

- Nunca colocar segredo no frontend: tudo em `import.meta.env` é público.
- Tokens em `localStorage` é um risco aceito e registrado (ISS-001); nada de HTML não sanitizado
  (`dangerouslySetInnerHTML`).

## Tests

- Testes em `tests/` na raiz do projeto (DEC-004), com Vitest; não dentro de `features/`. Quando o
  código testado se move, atualize só os imports do teste.
- Toda regra pura (formatação, cálculo, decisão de UI a partir de dados) tem teste.

## Directory Structure

```text
frontend/
├── src/
│   ├── main.tsx                  providers + router
│   ├── app/
│   │   ├── router.tsx            rotas → telas pelos barrels
│   │   └── _shell/               AppLayout · Sidebar · Topbar
│   ├── features/
│   │   ├── auth/                 sessão, login, guarda de rota, unidade selecionada (API real)
│   │   ├── landing/              site público em /
│   │   ├── dashboard/            /app/dashboard (mock)
│   │   ├── scheduling/           /app/agenda + modal de agendamento (mock)
│   │   ├── conversations/        /app/conversas (mock)
│   │   ├── customers/            /app/clientes (placeholder)
│   │   ├── registry/             /app/cadastros (mock)
│   │   ├── finance/              /app/financeiro (placeholder)
│   │   └── design-system/        /app/tokens — documentação viva dos tokens
│   └── shared/
│       ├── api/http.ts           cliente HTTP
│       ├── session/              tokens.ts · tenant.ts
│       ├── ui/                   Icon · Badge/Tag · ModulePlaceholder
│       ├── text/                 initials.ts
│       └── styles/               tokens.css · global.css · panel.css
├── tests/                        Vitest
├── docs/                         ENVIRONMENT_VARIABLES.md
├── .github/                      camada de contexto da IA (este diretório)
├── eslint.config.js              regras + fronteiras entre features
├── vite.config.ts · vitest.config.ts · tsconfig.json
└── CLAUDE.md
```

## Documentation

- `README.md` com setup, rotas e estado de cada tela atualizados.
- Variável de ambiente nova entra em `.env.example` e em `docs/ENVIRONMENT_VARIABLES.md`.

## Versioning

- SemVer: MAJOR.MINOR.PATCH.
- Commits `type(scope): description` — `feat`, `fix`, `refactor`, `docs`, `test`, `chore`.
  Escopo = feature ou área (`scheduling`, `auth`, `shell`, `ci`).
