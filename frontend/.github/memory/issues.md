# Issues

Bugs conhecidos, workarounds e áreas frágeis. Remova a entrada (ou marque `resolved`, com data)
quando resolver. Numeração `ISS-NNN` nunca é reaproveitada.

| ID | Date | Area | Description | Impact | Status |
|----|------|------|-------------|--------|--------|
| ISS-001 | 2026-11-05 | session / security | Access e refresh token em `localStorage` (DEC-002): qualquer script da página lê. O formato seguro (refresh em cookie httpOnly + access em memória) exige o backend setar o cookie — spec espelhada nos dois projetos. | medium | open |
| ISS-002 | 2026-11-05 | panel / mock data | Fora a sessão, todo o painel usa dados de demonstração (`features/*/api/*.mock.ts`): agenda, dashboard, conversas, cadastros. A data do dia é fixa (`AGENDA_DAY`, `DASHBOARD_DAY`, `17/08/2026` no modal). Cada módulo do backend troca o mock da feature correspondente. | high | workaround |
| ISS-003 | 2026-11-05 | scheduling | Controles de demonstração na Agenda (seletor "Demo" dia cheio/vazio/conflito e o botão "Selo IA") — remover quando os dados forem reais. | low | workaround |
| ISS-004 | 2026-11-05 | shell / sidebar | O badge de "Conversas" na sidebar é fixo (`badge: '4'` em `app/_shell/Sidebar.tsx`) e a busca da topbar é decorativa (`fake-search`). | low | open |
| ISS-005 | 2026-11-05 | shell / permissions | A navegação mostra todos os módulos para qualquer cargo. `useAuth().can(...)` existe mas nenhuma tela/menu usa — um barbeiro vê "Financeiro" (o backend negaria os dados quando o módulo existir). | medium | open |
| ISS-006 | 2026-11-05 | auth / login | O login envia a senha sem `trim` (correto: senha pode ter espaço), mas uma senha colada com espaço no fim falha com o mesmo 401 genérico de senha errada, sem pista. Visto em 2026-11-05 ao testar o login de dev. Avaliar aviso "sua senha termina com espaço" no formulário. | low | open |
| ISS-007 | 2026-11-05 | docker / dev | `docker-compose.yml` usa um volume anônimo para `node_modules`: dependência nova no `package.json` só chega ao container com `docker compose build web` (ou `up --build`). As devDependencies de lint/teste não são necessárias no container, mas uma dependência de runtime nova quebra o dev server até o rebuild. | low | workaround |
| ISS-008 | 2026-11-05 | landing | O README antigo citava `design-reference/` (protótipos originais), mas a pasta não está no repositório. As referências de design não estão versionadas. | low | open |
| ISS-009 | 2026-11-05 | auth / invite screen | A tela `/convite/:token` foi verificada por lint, tipos, testes de regra e chamadas reais à API, mas não clicada num navegador. Conferir os três caminhos (link válido, link morto, barbearia errada em localhost). | low | open |
