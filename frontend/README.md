# Navalha.app — frontend

React 18 + Vite + TypeScript. Conversão fiel dos dois protótipos do Claude Design
em código de produção.

> **Para quem vai desenvolver (pessoa ou IA):** comece por [`CLAUDE.md`](CLAUDE.md)
> e pela camada de contexto em [`.github/`](.github/README.md) — regras, specs,
> decisões (DEC-NNN) e problemas conhecidos (ISS-NNN).

## Rodar

Com Docker (recomendado — não precisa de Node na máquina):

```bash
docker compose up -d          # http://localhost:5173
docker compose logs -f
```

Sobe sozinho, sem o backend: as telas usam os dados de demonstração de
`src/features/*/api/*.mock.ts`. Quando o backend está no ar, o dev server proxya `/api` para o
container `core-api` pela rede `navalha`.

Direto na máquina:

```bash
npm install
npm run dev        # http://localhost:5173
npm run build      # typecheck + bundle em dist/
npm run typecheck
npm run lint       # ESLint + fronteiras entre features
npm run test       # Vitest (tests/)
npm run check      # lint + typecheck + test
```

## Rotas

| Rota               | Tela                                              |
| ------------------ | ------------------------------------------------- |
| `/`                | Landing page (hero, planos, FAQ, captura de lead) |
| `/entrar`          | Login — **ligado ao backend de verdade**          |
| `/convite/:token` | Primeiro acesso / aceite de convite — **API real** |
| `/app/dashboard`   | KPIs, próximos agendamentos, ocupação, conversas  |
| `/app/agenda`      | Agenda do dia por barbeiro                        |
| `/app/conversas`   | Central de conversas (WhatsApp + IA)              |
| `/app/clientes`    | Placeholder (fora do escopo do protótipo)         |
| `/app/cadastros`   | Cadastro de barbeiros com formulário              |
| `/app/financeiro`  | Placeholder (fora do escopo do protótipo)         |
| `/app/tokens`      | Documentação do design system                     |

## Estrutura

Vertical slice por feature (DEC-003). Regras completas em
[`.github/rules.md`](.github/rules.md); para criar uma feature,
[`.github/skills/new-feature.md`](.github/skills/new-feature.md).

```
src/
├── main.tsx           providers + router
├── app/
│   ├── router.tsx     rotas → telas, sempre pelo index.ts da feature
│   └── _shell/        layout do painel (AppLayout, Sidebar, Topbar)
├── features/<f>/      index.ts (API pública) + api/ model/ pages/ ui/
│   auth · landing · dashboard · scheduling · conversations
│   customers · registry · finance · design-system
└── shared/
    ├── api/http.ts    fetch com tenant, bearer e renovação de token
    ├── session/       tokens e slug da barbearia
    ├── ui/            Icon, Badge/Tag, ModulePlaceholder
    ├── text/          formatação
    └── styles/        tokens.css (design tokens), global.css, panel.css
tests/                 Vitest
```

Uma feature só importa outra pelo `index.ts` dela, `shared/` não conhece
features e features não importam `app/` — o ESLint barra o import errado.

## Autenticação

O login é real: `/entrar` chama `POST /auth/login`, guarda os tokens e hidrata a
sessão com `GET /auth/me`. Tudo em `src/features/auth/` e `src/shared/`.

- **Rotas protegidas** — tudo sob `/app` passa por `RequireAuth`, que manda quem
  não tem sessão para `/entrar` e lembra o destino original.
- **Sessão** — `AuthProvider` valida o token guardado chamando `/auth/me` na
  subida; token revogado ou expirado cai para anônimo em vez de fingir sessão.
- **Renovação** — o access token vale 15 min. Um 401 dispara `/auth/refresh` e
  refaz a chamada, uma vez só. Chamadas simultâneas compartilham a mesma
  renovação, senão a rotação invalidaria os tokens umas das outras.
- **Qual barbearia** — em produção vem do subdomínio (`central.navalha.app`), e
  o backend lê do header `Host`. Em `localhost` não há subdomínio, então a tela
  de login pede o endereço da barbearia e ele vai como `X-Tenant-Slug`.

> Os tokens ficam em `localStorage`, porque a API os devolve no corpo da
> resposta. É legível por qualquer script da página — o formato mais seguro é
> refresh em cookie httpOnly com o access em memória, e isso depende de mudança
> no backend. Está anotado nas pendências.

**Primeiro acesso** — barbearias nascem pelo control plane do backend (não há
cadastro público). O provisionamento devolve um link de convite; a tela
`/convite/:token` valida o link **antes** de pedir a senha, a pessoa define a
senha e já entra no painel. A mesma tela serve aos convites de equipe. Passo a
passo para criar uma barbearia em dev:
[docs/DEVELOPMENT.md](../docs/DEVELOPMENT.md#primeiro-acesso-ao-painel).

## Dados que ainda são mock

O restante do painel (agenda, conversas, cadastros) continua com os dados de
`src/features/<f>/api/*.mock.ts`, porque esses módulos ainda não existem no
backend. Cada módulo novo do backend troca o mock da feature correspondente por
um `*.api.ts` real — passo a passo em `.github/skills/new-feature.md`.

O dev server proxya `/api` para o backend, removendo o prefixo — o alvo vem de
`VITE_PROXY_TARGET` (padrão `http://localhost:8000`; no compose, o nome do
serviço `http://core-api:8000`). Como tudo passa pelo proxy, não há CORS em
desenvolvimento.

Ver os endpoints disponíveis em [backend/README.md](../backend/README.md).

## Docker

`Dockerfile` tem dois alvos:

- **`dev`** — Vite com HMR. É o que o compose usa. O código é montado por bind
  mount, e `VITE_USE_POLLING=true` liga o polling do watcher, porque bind mounts
  no Windows e macOS não propagam eventos de inotify para o container.
- **`prod`** — build estático servido por nginx, com fallback de SPA e cache
  correto (`index.html` sem cache, assets com hash por um ano).

```bash
docker build -t navalha-web:prod --target prod .
docker run --rm -p 8080:80 navalha-web:prod
```

## Notas da conversão

- O protótipo do painel usava a marca "Pauta" na sidebar e a landing usava
  "Navalha.app". Unificado em **Navalha** nas duas telas.
- Os estilos inline do protótipo viraram classes CSS com tokens; a tela
  `/app/tokens` continua sendo a documentação viva desses valores.
- O acento do painel é a variável `--accent`; trocá-la repinta a interface toda,
  como fazia a prop `accentColor` do protótipo.
- Os seletores "Demo" da agenda (dia cheio / vazio / conflito) e o botão
  "Selo IA" são controles de demonstração — remova-os quando os dados forem reais.
- Os protótipos originais não estão versionados neste repositório (ISS-008).
