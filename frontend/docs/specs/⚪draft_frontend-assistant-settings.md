# Configuração da IA no painel (S11)

**Priority:** high
**Status:** draft
**Espelho no backend:** `backend/docs/specs/⚪draft_assistant-ai-agent.md`

## Overview

Tela `/app/configuracoes/ia`, na feature `settings` criada pela S10, onde o dono **liga e desliga a
IA**, escolhe o **tom**, define **quando ela atende**, escreve a **base de conhecimento** (o que a IA
pode responder além de horários e preços), ajusta o que ela pode fazer sozinha (cancelar, remarcar,
oferecer clube e pacote, recuperar abandono, ouvir áudio), **testa** a IA num chat de ensaio antes de
soltar para os clientes e acompanha o **uso do mês**, o **saldo de créditos de IA** e o consumo em
créditos e em US$ (PD-40, PD-43, PD-44). Regras do agente, guardrails
e contrato estão no espelho do backend.

## Decisões de produto já tomadas

| Parâmetro | Valor |
|---|---|
| PD-16 | A escolha de provedor e modelo é da plataforma: **não aparece** para a barbearia. |
| PD-17 | Base de conhecimento editada pelo dono; clube/pacote (refinado pela PD-37); áudio; recuperação de abandono. |
| PD-29 | A IA cancela sozinha dentro da política e deixa nota para a recepção. |
| PD-37 | A IA **não fecha venda** de clube ou pacote: explica, registra o interesse e passa para "Aguardando humano" (motivo "Venda de clube/pacote"). |
| PD-40 | IA por **créditos** comprados no Core; sem créditos, conversas novas vão para "Aguardando humano". Saldo e extrato moram na página Plano (S15). |
| PD-43 | Crédito **proporcional ao custo real** de cada resposta da IA e de cada áudio transcrito; o plano inclui créditos por mês que não acumulam; comprados não vencem. Valores chegam em milicréditos. |
| PD-44 | O dono vê o consumo **em créditos e o custo estimado em US$**. |
| PD-19 | A tela explica, em uma linha, como a IA se comporta: "responde como a recepção, nunca diz ser uma pessoa e oferece alguém da equipe quando perguntam". Não há campo de nome da atendente (a IA não inventa nome). |
| PD-18 | Mensagem de handoff editável; não há configuração de retomada automática. |

## Business Rules

### Liga/desliga e plano

- [ ] Sem o recurso `ai_assistant` no plano (`plan_has_ai = false` ou `402`): a tela mostra o que a IA
      faz e o caminho de upgrade; nada é editável.
- [ ] Sem WhatsApp conectado: aviso "Conecte o WhatsApp para a IA atender" com link para
      `/app/configuracoes/whatsapp`; a configuração pode ser preparada mesmo assim.
- [ ] Ligar mostra confirmação com o resumo do que vai acontecer ("A partir de agora, mensagens novas
      são respondidas pela IA; conversas com alguém da equipe continuam com a equipe"). Desligar avisa
      que as conversas novas vão para "Aguardando humano".

### Comportamento

- [ ] Tom em três opções com um exemplo de resposta para cada (Descontraído, Equilibrado, Formal) e
      o liga/desliga de emoji.
- [ ] Quando atende: "Sempre", "Só fora do expediente" (lê o expediente das unidades, S01) ou
      "Personalizado" (grade por dia da semana, início/fim em passos de 15 min; validação fim > início).
- [ ] Textos editáveis com contador: mensagem fora do horário, mensagem de handoff, saudação
      (opcional), até 300 caracteres cada.
- [ ] Permissões da IA (chaves): remarcar, cancelar ("a IA cancela dentro da sua política e deixa
      uma nota na conversa para a recepção"; ligado por padrão), oferecer clube e pacote ("a IA
      explica e passa para a equipe fechar a venda" — o campo continua `sell_memberships`), ouvir
      áudios, recuperar abandono (+ "esperar N minutos", 30–240).
- [ ] "Quando atende" vem marcado em "Sempre" ao ligar pela primeira vez (Q-S11-3).
- [ ] Salvar com `PUT /assistant/settings`; alteração não salva pede confirmação ao sair.

### Base de conhecimento

- [ ] Lista de entradas (título, categoria, ativa) com reordenação por arrastar ou setas
      (`PUT /assistant/knowledge/order`) e busca local.
- [ ] Criar/editar em painel abaixo da lista (padrão de Cadastros): título (2–120), categoria,
      conteúdo (até 2000) e ativa.
- [ ] Sugestões de entradas comuns para começar (um clique preenche o título e uma pergunta-guia no
      conteúdo): formas de pagamento, estacionamento, atende criança, tempo de tolerância de atraso,
      política de cancelamento, produtos à venda, Wi-Fi/conforto.
- [ ] Medidor de uso do teto (entradas e caracteres); `409` do backend mostra a mensagem dele.
- [ ] Aviso fixo: "Preços, serviços, barbeiros e horários vêm dos Cadastros e da Agenda — não precisa
      repetir aqui."

### Testar a IA (playground)

- [ ] Chat de ensaio ao lado (ou abaixo, no celular) com o visual da Central: o dono escreve como
      cliente e vê a resposta, os botões oferecidos e, recolhido, "o que a IA fez" (ferramentas
      chamadas, com a marca **simulado** nas que alteram a agenda).
- [ ] O ensaio usa a configuração **salva**; com alterações pendentes, aviso "Salve para testar com as
      mudanças".
- [ ] Handoff no ensaio aparece como faixa "A conversa iria para Aguardando humano: <resumo>".
- [ ] "Recomeçar" limpa o ensaio (estado local). `429` mostra "Limite de testes por hora atingido".
- [ ] Aviso no ensaio: "Testes não gastam créditos de IA."

### Uso do mês

- [ ] Cartão de **créditos**, o mesmo resumo da página Plano (S15, de `UsageOut.credits`): saldo
      atual, inclusos (só se houver) e comprados, consumo do mês **em créditos e em US$** ("86,2
      créditos · custo estimado US$ 0,86"), separado em conversas e transcrição de áudio, e a média
      por conversa e por agendamento feito pela IA (`per_conversation`, `per_booking`). Formatação
      pelas regras exportadas da feature `plan` (`formatCredits`, `formatUsdMicros`). Link "Ver
      extrato e comprar" para `/app/configuracoes/plano`. Não há barra de limite: o uso da IA não
      tem cota mensal (PD-40).
- [ ] Cartão do mês: conversas atendidas, agendamentos feitos pela IA, cancelamentos feitos pela IA,
      interesses em clube/pacote encaminhados à equipe, handoffs por motivo e abandonos recuperados.
- [ ] Saldo baixo (`credits.low`): cartão em destaque; saldo zerado (`credits.empty`): faixa "Seus
      créditos de IA acabaram — novas conversas vão para a equipe" com o link para a página Plano.

## Telas e fluxos

| Rota | Tela | Fluxos |
|---|---|---|
| `/app/configuracoes/ia?aba=comportamento\|conhecimento\|testar\|uso` | `features/settings/pages/AssistantSettingsScreen.tsx` | `pages/assistant/behavior/`, `pages/assistant/knowledge/`, `pages/assistant/playground/`, `pages/assistant/usage/` |

## Data Contract

Contrato completo no espelho do backend. Endpoints consumidos:

```text
GET/PUT  /assistant/settings
GET/POST /assistant/knowledge · PATCH/DELETE /assistant/knowledge/{id} · PUT /assistant/knowledge/order
GET      /assistant/usage?month=
POST     /assistant/playground
GET      /whatsapp/numbers        (aviso de WhatsApp não conectado)
GET      /tenant/units            (expediente, para "só fora do expediente")
```

Arquivos:

```text
features/settings/model/assistant.types.ts     AssistantSettings, KnowledgeEntry, AssistantUsage, PlaygroundTurn
features/settings/model/assistant.rules.ts     validação, grade personalizada, exemplos de tom, medidor da base
features/settings/api/assistant.api.ts · assistant.queries.ts
```

O componente de bolha de mensagem do playground é o mesmo da Central: exportado pelo `index.ts` de
`conversations` (não vai para `shared/`, porque conhece o tipo `Message`).

## Estado

| Estado | Onde |
|---|---|
| Configuração, base, uso | TanStack Query (`['assistant-settings']`, `['assistant-knowledge']`, `['assistant-usage', mês]`) |
| Aba | URL (`?aba=`) |
| Formulários | local |
| Conversa de ensaio | local (não persiste; some ao sair) |

## Permissões

| Ação | Permissão em `/auth/me` |
|---|---|
| ver "Configurações → IA" e tudo nesta tela | `tenant:configure` |
| link "Ver extrato e comprar" (página Plano) | `subscription:manage` (sem ela, só o saldo) |

## Acceptance Criteria

- [ ] Item "IA do WhatsApp" na lista de `/app/configuracoes`, com o estado (Ligada/Desligada/Fora do
      plano).
- [ ] Testes em `tests/`: validação da grade personalizada; contadores e limites de texto; medidor
      da base; derivação do estado do cartão de créditos (normal, baixo, zerado); montagem do resumo
      de consumo (créditos + US$, por tipo, médias `null` sem conversa/agendamento); mapeamento de motivo
      de handoff para texto (inclui `sale` e `no_ai_credits`).
- [ ] Tela conferida no navegador: ligar/desligar, salvar, base (criar, editar, reordenar, apagar),
      ensaio com agendamento simulado e com handoff, plano sem IA.
- [ ] `make docs-api` regenerado; `README.md` e `memory/progress.md` atualizados.
- [ ] Testes em `tests/` cobrindo as regras puras da feature
- [ ] Tela conferida no navegador (estados vazio, carregando, erro)
- [ ] `make check-frontend` verde

## Dependencies

- Backend: `⚪draft_assistant-ai-agent.md` implementado e congelado no `openapi.json`.
- `⚪draft_frontend-inbox.md` (S10): feature `settings` e o componente de bolha da Central.
- S01 (`frontend-units-settings`): expediente das unidades.
- S15 (`frontend-plan-limits`): padrão visual de "recurso fora do plano"; página Plano com saldo e
  extrato dos créditos de IA; `formatCredits` e `formatUsdMicros` pelo `index.ts` de `plan`.

## Notes

- Perguntas que mudam esta tela estão no backend: **Q-S11-1** (o que o medidor de uso mostra:
  conversas ou outra unidade; o número vem de `GET /assistant/usage`, que lê a cota da S15),
  **Q-S11-3** (opção marcada por padrão em "quando atende"), **Q-S11-4** (se "cancelar" aparece
  ligado por padrão) e **Q-S15-3** (o que acontece ao esgotar a cota).
  > Resolvido em 2026-11-06: Q-S11-1 — créditos de IA, sem cota mensal: a tela mostra saldo e consumo do mês em créditos e em US$ (PD-40, PD-43, PD-44). Q-S11-2 — a IA não fecha venda; a chave vira "oferecer clube e pacote" (PD-37). Q-S11-3 — "Sempre" por padrão (ROADMAP §7). Q-S11-4 — "cancelar" ligado por padrão, com nota para a recepção (PD-29). Q-S15-3 — créditos acabaram → conversas novas vão para "Aguardando humano" (PD-40 | ROADMAP §7).
- ✅ **Q-S15-6** (backend): o que gasta um crédito. A tela não fixa a regra: mostra o que a página
  Plano mostra (frase montada da política).
  > Resolvido em 2026-11-06: 1(c) proporcional ao custo (credits_per_usd, milicréditos, reserva e acerto), 2(b), 3(a) (PD-43); custo em US$ visível ao dono (PD-44).
- O ensaio custa uso real do provedor; por isso o limite por hora. Ele não gasta créditos e não entra
  no consumo mostrado ao dono (o custo conta só no teto técnico da plataforma).
