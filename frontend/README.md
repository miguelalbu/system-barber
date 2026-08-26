# Navalha.app — frontend

React 18 + Vite + TypeScript. Conversão fiel dos dois protótipos do Claude Design
(`design-reference/`) em código de produção.

## Rodar

```bash
npm install
npm run dev        # http://localhost:5173
npm run build      # typecheck + bundle em dist/
npm run typecheck
```

## Rotas

| Rota               | Tela                                              |
| ------------------ | ------------------------------------------------- |
| `/`                | Landing page (hero, planos, FAQ, captura de lead) |
| `/app/dashboard`   | KPIs, próximos agendamentos, ocupação, conversas  |
| `/app/agenda`      | Agenda do dia por barbeiro                        |
| `/app/conversas`   | Central de conversas (WhatsApp + IA)              |
| `/app/clientes`    | Placeholder (fora do escopo do protótipo)         |
| `/app/cadastros`   | Cadastro de barbeiros com formulário              |
| `/app/financeiro`  | Placeholder (fora do escopo do protótipo)         |
| `/app/tokens`      | Documentação do design system                     |

## Estrutura

```
src/
├── styles/tokens.css   Design tokens (cores, espaçamento, raio, fontes)
├── styles/global.css   Reset e utilitários
├── types.ts            Tipos de domínio — contrato esperado do backend
├── data/               Dados de demonstração vindos do protótipo
├── api/client.ts       Ponte para o backend (hoje devolve os mocks)
├── landing/            Landing page e suas seções
└── app/                Painel: shell, componentes e telas
```

## Ligar ao backend

`src/api/client.ts` decide entre mock e HTTP pela variável `VITE_API_URL`:

```bash
# frontend/.env.local
VITE_API_URL=http://localhost:3000
```

Sem a variável, as telas continuam rodando com os dados de `src/data/app.ts`.
Com ela, `api.*` passa a chamar os endpoints reais — os componentes não mudam,
porque já consomem os tipos de `src/types.ts`.

O `vite.config.ts` também deixa um proxy de `/api` para `http://localhost:3000`
pronto para uso durante o desenvolvimento.

### Endpoints esperados

```
GET  /api/barbers
GET  /api/appointments?day=YYYY-MM-DD
GET  /api/dashboard/kpis
GET  /api/dashboard/upcoming
GET  /api/dashboard/occupancy
GET  /api/threads
GET  /api/threads/:id/messages
GET  /api/staff
POST /api/leads              (formulário do CTA final da landing)
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
- Os protótipos originais ficam em `design-reference/` para consulta.
