# Primeiros passos e importação no painel

**Priority:** medium
**Status:** draft
**Espelho no backend:** `backend/docs/specs/⚪draft_imports-onboarding.md`

## Overview

Feature nova `onboarding` com duas telas: o **checklist de primeiros passos** que o dono vê ao entrar
numa barbearia recém-criada (com progresso e atalhos para cada cadastro) e o **assistente de
importação** por planilha (clientes, serviços, agendamentos futuros) em cinco etapas: escolher o tipo
→ enviar o arquivo → mapear colunas → conferir a prévia → importar e ver o relatório.

## Decisões de produto já tomadas

| Parâmetro | Valor |
|---|---|
| PD-23 | Assistente de primeiros passos no painel; sem cadastro self-service. |
| PD-24 | Importação CSV/Excel com prévia e relatório de erros. |
| Forma | Checklist (não um wizard bloqueante): cada passo leva à tela real do cadastro; o painel continua usável o tempo todo. |

## Business Rules

### Primeiros passos

- [ ] Enquanto o checklist não estiver concluído nem dispensado, o dono entra em
      `/app/primeiros-passos` em vez do dashboard, e a sidebar mostra o item com o progresso
      ("Primeiros passos 3/6").
- [ ] Cada passo: título, explicação de uma linha, estado (feito ✓, pendente, pulado, travado pelo
      plano), contagem quando houver ("2 barbeiros sem horário"), botão para a tela real
      (`/app/cadastros/servicos`, `/app/cadastros/barbeiros`, `/app/configuracoes/whatsapp`…) e
      "Pular" nos recomendados.
- [ ] Barra de progresso com o `progress_pct` do backend. Concluir os obrigatórios mostra
      "Sua barbearia está pronta para agendar" com o link público (S04), se o plano tiver.
- [ ] Ao voltar de uma tela de cadastro, o checklist recarrega (`refetchOnWindowFocus` + invalidação
      pelas mutações de serviço/barbeiro).
- [ ] "Dispensar" pede confirmação; "Reabrir primeiros passos" fica em Configurações.

### Importação (`/app/importar`)

- [ ] **1. Tipo**: cartões Clientes, Serviços, Agendamentos futuros (só os que a pessoa pode
      importar), cada um com "Baixar modelo" (`/imports/templates/...`) e a lista de importações
      anteriores dessa entidade.
- [ ] **2. Arquivo**: arrastar ou escolher `.csv`/`.xlsx`; checa extensão e 5 MB antes de enviar;
      barra de envio; erros `413`/`422` com a mensagem do backend.
- [ ] **3. Colunas**: para cada campo do destino (obrigatórios marcados), um seletor com as colunas
      do arquivo, já preenchido pela sugestão; ao lado, os 3 primeiros valores da coluna escolhida.
      Opções: formato de data, unidade padrão (agendamentos), "Se já existir: ignorar | atualizar".
      Não avança sem os obrigatórios; coluna usada duas vezes é avisada.
- [ ] **4. Prévia**: enquanto `validating`, indicador com polling (2 s); depois, resumo ("1.842 serão
      criados · 37 já existem · 12 com erro") e tabela filtrável por status com as mensagens por
      campo. "Voltar às colunas" refaz o mapeamento; "Baixar erros" (CSV); "Importar 1.842".
- [ ] Na importação de **clientes**, aviso fixo na prévia: "Clientes importados recebem lembretes
      dos agendamentos, mas só recebem promoções (reativação, aniversário, campanhas) depois de
      autorizar ou de serem atendidos aqui" (PD-30). Não há opção para marcar consentimento em massa.
- [ ] **5. Importação**: barra de progresso (`processed/total`, polling 2 s; a pessoa pode sair e
      voltar — o estado vem do servidor); ao fim, relatório com contagens, "Baixar erros" e atalho
      para a lista importada (Clientes, Serviços ou Agenda).
- [ ] Importação em andamento da mesma entidade (`409`) leva à importação existente.
- [ ] Nenhum dado da planilha fica no navegador além do arquivo em envio.

## Telas e fluxos

| Rota | Tela | Fluxos |
|---|---|---|
| `/app/primeiros-passos` | `features/onboarding/pages/OnboardingScreen.tsx` | `pages/checklist/` |
| `/app/importar` | `features/onboarding/pages/ImportScreen.tsx` | `pages/import/choose/` |
| `/app/importar/:id` | `features/onboarding/pages/ImportScreen.tsx` | `pages/import/mapping/`, `preview/`, `progress/`, `report/` (etapa pelo `status`) |

A etapa vem do `status` da importação, não de estado local: recarregar a página continua de onde
parou.

## Data Contract

```text
GET  /onboarding · POST /onboarding/steps/{key}/skip|unskip · POST /onboarding/dismiss|reopen
POST /imports (multipart) · GET /imports · GET /imports/{id} · PUT /imports/{id}/mapping
GET  /imports/{id}/rows · POST /imports/{id}/commit|cancel|retry
GET  /imports/{id}/errors.csv · GET /imports/templates/{entity}.csv
```

`shared/api/http.ts` ganha envio `FormData` (sem `Content-Type` fixo — o navegador põe o boundary) e
`requestBlob()` (compartilhado com a S14).

```text
features/onboarding/model/onboarding.types.ts   OnboardingStep, Import, ImportRow, Mapping
features/onboarding/model/onboarding.constants.ts  título, texto e rota de cada passo; campos por entidade
features/onboarding/model/import.rules.ts       etapa a partir do status, validação do mapeamento, texto do resumo
features/onboarding/api/onboarding.api.ts · onboarding.queries.ts
```

## Estado

| Estado | Onde |
|---|---|
| Checklist | TanStack Query `['onboarding']` |
| Importação e linhas | TanStack Query `['import', id]` (com `refetchInterval` 2 s em `validating`/`importing`), `['import', id, 'rows', filtro]` |
| Mapeamento em edição | estado local da etapa 3 |
| Filtro da prévia | URL (`?status=invalid`) |

## Permissões

| Ação | Permissão em `/auth/me` |
|---|---|
| ver/pular/dispensar primeiros passos | `tenant:configure` |
| importar clientes | `client:write` (escopo ≠ `own`) |
| importar serviços | `catalog:write` e todas as unidades |
| importar agendamentos | `appointment:create` (escopo ≠ `own`) |
| item "Importar" (em Clientes e em Configurações) | qualquer uma das três |

## Acceptance Criteria

- [ ] Testes em `tests/`: etapa a partir do status, validação do mapeamento (obrigatório faltando,
      coluna repetida), texto do resumo (singular/plural), checagem de extensão/tamanho, ordem e
      rota dos passos.
- [ ] Importação de 2.000 clientes de uma planilha real conferida no navegador, inclusive sair e voltar
      durante a importação e reimportar a mesma planilha (zero criados).
- [ ] Testes em `tests/` cobrindo as regras puras da feature
- [ ] Tela conferida no navegador (estados vazio, carregando, erro)
- [ ] `make check-frontend` verde

## Dependencies

- Backend `⚪draft_imports-onboarding.md`.
- Telas de destino dos passos: S01 (unidade/expediente), S02 (jornada), S05 (formas de pagamento),
  S10 (WhatsApp), S11 (IA) — o checklist só linka. Passo de módulo ainda não implementado não vem do
  backend (não aparece nem conta no progresso).
- `⚪draft_frontend-plan-limits.md` (S15): passo travado e `PlanUpgradeNotice`.

## Notes

- Sem biblioteca de upload nem de planilha no navegador: o backend lê o arquivo; o frontend só envia.
- Perguntas de produto no espelho do backend (Q-S16-1 a Q-S16-3).
  > Resolvido em 2026-11-06: Q-S16-1 = importa o resumo do histórico (última visita, nº de visitas,
  > total gasto — colunas opcionais no mapeamento); Q-S16-2 = agendamento importado não pede
  > confirmação, lembretes normais; Q-S16-3 = só o dono faz os primeiros passos (PD-30 |
  > ROADMAP §7).
