# Issues

Bugs conhecidos, workarounds e áreas frágeis. Remova a entrada (ou marque `resolved`, com data)
quando resolver. Numeração `ISS-NNN` nunca é reaproveitada.

| ID | Date | Area | Description | Impact | Status |
|----|------|------|-------------|--------|--------|
| ISS-001 | 2026-11-05 | config / .env | O `.env.example` usava nomes em português (`AMBIENTE`, `DOMINIO_BASE`, `PERMITIR_AUTOCADASTRO`, `ACCESS_TOKEN_MINUTOS`, `REFRESH_TOKEN_DIAS`, `CONVITE_VALIDADE_DIAS`) que não batem com os campos de `Settings`; como `extra="ignore"`, eram ignorados sem aviso e valiam os padrões (por coincidência, os mesmos valores). `PERMITIR_AUTOCADASTRO=false` não desligaria o auto-cadastro. `REDIS_URL` apontava para 6379 em vez de 6380. **Fix:** `.env.example` reescrito com os nomes certos e `docs/ENVIRONMENT_VARIABLES.md`. **Pendente:** o `.env` local de quem já copiou o exemplo antigo precisa ser refeito (`cp .env.example .env`). Considerar validar no boot que não há variável desconhecida com prefixo do projeto. | medium | workaround |
| ISS-002 | 2026-11-05 | security / JWT | O `JWT_SECRET` de dev do `docker-compose.yml` (`dev-secret-nao-use-em-producao`) tem 30 bytes; o PyJWT emite `InsecureKeyLengthWarning` (mínimo 32 para HS256) a cada token. Só dev, mas o log fica poluído e o padrão do `config.py` (`change-me-in-production`) também é curto. Fix: segredo de dev com 32+ bytes no compose e validação de tamanho no boot fora de dev. Trocar o segredo invalida as sessões abertas. | low | open |
| ISS-003 | 2026-11-05 | auth / refresh | Reuso de refresh token só falha (401); deveria revogar a família inteira de tokens do usuário e registrar o evento, porque reuso é sinal de vazamento. Previsto junto com auditoria. | medium | open |
| ISS-004 | 2026-11-05 | team / invites | Sem e-mail transacional: `POST /team/invites` devolve o link do convite na resposta para o dono repassar por WhatsApp. Trocar por envio de e-mail (e então remover `link` da resposta = mudança de contrato, vira spec). | medium | workaround |
| ISS-005 | 2026-11-05 | platform admin | A conta de plataforma existe (seed) mas nenhuma rota autentica com ela. Precisa de tipo de token próprio e auditoria de acesso cross-tenant (DEC-003). | low | open |
| ISS-006 | 2026-11-05 | tests | A suíte roda contra o banco de desenvolvimento (porta 5433): cada teste cria uma barbearia com slug aleatório e não apaga. O banco de dev acumula tenants `t<hex>`; dados de dev reais convivem com lixo de teste. Fix: banco de teste separado (ou Testcontainers, como no Clara) com limpeza por transação. | low | open |
| ISS-007 | 2026-11-05 | auth / rate limit | Sem rate limit em `/auth/login`, `/auth/register-shop` e `/team/invites/accept`. O Redis já está de pé mas não é usado. Login por força bruta e varredura de slugs livres. | high | open |
| ISS-008 | 2026-11-05 | auth | Falta verificação de e-mail e recuperação de senha (hoje: "fale com o dono para receber um novo convite"). | medium | open |
| ISS-009 | 2026-11-05 | infra / TLS | Sem TLS nem emissão automática de certificado para domínio próprio (Caddy/Traefik com ACME sob demanda). Bloqueia produção. | high | open |
| ISS-010 | 2026-11-05 | database / runtime role | A senha do role `navalha_app` está fixa no init SQL de dev (`infra/postgres/init/01-app-role.sql`). Em produção ela tem de vir de secret. | high | open |
