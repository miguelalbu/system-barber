# Variáveis de ambiente — frontend

Duas famílias, com regras diferentes:

- **`import.meta.env.VITE_*`** — embutidas no bundle no momento do build. **São públicas**: nunca
  coloque segredo aqui. Lidas de `.env` / `.env.local` (ver `.env.example`).
- **`process.env.*` em `vite.config.ts`** — só o servidor de desenvolvimento do Vite as lê; não vão
  para o bundle.

## No bundle (`import.meta.env`)

| Variável | Padrão | Onde | Para quê |
|---|---|---|---|
| `VITE_API_URL` | `/api` | `src/shared/api/http.ts` | Base das chamadas. O padrão passa pelo proxy do Vite (mesma origem, sem CORS). Aponte para a API só para pular o proxy. |
| `VITE_BASE_DOMAIN` | `navalha.local` | `src/shared/session/tenant.ts` | Lê o slug da barbearia do hostname (`<slug>.<VITE_BASE_DOMAIN>`). Tem de bater com o `BASE_DOMAIN` do backend. Em localhost, a tela de login pede o slug. |

## Só no dev server (`vite.config.ts`)

| Variável | Padrão | Para quê |
|---|---|---|
| `VITE_PROXY_TARGET` | `http://localhost:8000` | Para onde o proxy `/api` encaminha. No compose: `http://core-api:8000` (nome do serviço na rede `navalha`). |
| `VITE_USE_POLLING` | desligado | `true` liga polling no watcher — necessário com bind mount no Windows/macOS dentro do Docker. O compose já liga. |
