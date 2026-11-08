# Primeiros passos e importação por planilha

**Priority:** medium
**Status:** draft
**Espelho no frontend:** `frontend/docs/specs/⚪draft_frontend-onboarding-import.md`

## Overview

A barbearia nasce pelo Core (venda assistida, PD-23) com uma unidade e o convite do dono — e mais
nada. Esta spec cria o módulo `imports` com duas coisas que levam a barbearia do "vazio" ao "uso real"
em uma tarde:

1. **Primeiros passos**: um checklist calculado do estado real dos outros módulos (unidade,
   horários, serviços, barbeiros, WhatsApp…), com progresso, que o dono vê ao entrar até concluir ou
   dispensar.
2. **Importação por planilha** (PD-24) de **clientes**, **serviços** e **agendamentos futuros**,
   vinda do sistema anterior (Trinks, AppBarber, Avec, planilha própria): envio do CSV/Excel,
   mapeamento de colunas, prévia com validação linha a linha, importação **assíncrona pelo worker**
   (S00), relatório de erros e **idempotência** (reimportar a mesma planilha não duplica).

Referência: Fresha e Booksy fazem a importação de clientes com mapeamento + prévia; o Trinks faz a
migração com o time de implantação. Aqui o time de venda assistida (PD-23) usa a mesma tela que o dono.

## Decisões de produto já tomadas

| Parâmetro | Valor |
|---|---|
| PD-23 | Venda assistida; no painel só o assistente de primeiros passos (unidade, horários, serviços, barbeiros, WhatsApp). Sem cadastro self-service. |
| PD-24 | Importação CSV/Excel de clientes, serviços e agendamentos futuros, com prévia e relatório de erros. |
| PD-03 | Cliente identificado pelo telefone E.164 — é a chave de idempotência da importação de clientes. |
| PD-08 | Sem agendamento recorrente: cada linha é um agendamento. |
| Fora | Barbeiros e produtos por planilha (poucos registros: cadastro manual); histórico de atendimentos e comandas passadas (ver Q-S16-1 para o resumo). |

## Business Rules

### Primeiros passos

- [ ] Passos e o que conta como feito, consultando o `public.py` de cada módulo (o `imports` está no
      topo do grafo e só lê):
      `unit` (unidade com endereço e expediente — S01), `services` (≥ 1 serviço ativo), `barbers`
      (≥ 1 barbeiro ativo com ≥ 1 serviço habilitado), `barber_hours` (todo barbeiro ativo com
      jornada — S02), `payment_methods` (≥ 1 forma ativa — S05), `whatsapp` (número conectado — S10),
      `assistant` (IA configurada — S11), `clients` (≥ 1 cliente ou importação concluída), `team`
      (opcional: ≥ 1 convite).
- [ ] Obrigatórios: `unit`, `services`, `barbers`, `barber_hours`. Os demais são recomendados; passo
      cujo recurso não está no plano (S15) aparece como `locked` e não conta no progresso.
- [ ] Progresso = feitos ÷ contáveis (obrigatórios + recomendados não pulados e não travados).
- [ ] Dono pode **pular** um passo recomendado e **dispensar** o checklist; `completed_at` é gravado
      quando todos os obrigatórios ficam prontos pela primeira vez (não volta atrás se algo for
      desfeito — o checklist só reaparece se o dono reabrir).
- [ ] Nenhum passo é "marcado à mão": o estado vem do dado real.
- [ ] Passo cujo módulo ainda não existe no build não é listado (entra quando a spec dele for
      implementada, registrando a função de status) — o checklist nunca aponta para tela "em breve".

### Importação: ciclo de vida

```text
uploaded → (mapping) → validating → validated → importing → completed
     ↘ cancelled (até validated)          ↘ failed (erro inesperado; retomável)
```

- [ ] **Envio**: CSV (`,` ou `;`, detectado; UTF-8 com/sem BOM, cai para Latin-1) ou XLSX (primeira
      aba). Máx. 5 MB e 20.000 linhas de dados (`413`/`422`). Linha 1 = cabeçalho. O arquivo é lido
      na request, as linhas cruas vão para `import_rows` e **o arquivo não é guardado**.
- [ ] A resposta traz colunas detectadas, 10 linhas de amostra e um **mapeamento sugerido** por
      sinônimos do cabeçalho (sem acento, minúsculas): "nome/cliente", "celular/telefone/whatsapp/
      fone", "e-mail/email", "nascimento/aniversário/data de nascimento", "observação/obs" etc.
- [ ] **Mapeamento** (`PUT …/mapping`): campo de destino → coluna; opções (formato de data, unidade
      padrão, política de duplicado `skip | update`). Gravar o mapeamento enfileira a **validação**
      no worker; pode ser regravado enquanto `validated` (revalida).
- [ ] **Validação** normaliza cada linha com as mesmas regras do módulo dono (telefone E.164 de
      `clients.public.normalize_phone`, tamanhos, duração múltipla de 5 etc.) e classifica:
      `valid` (vai criar), `duplicate` (já existe → `skip` ou `update`), `invalid` (com mensagens
      por campo). Duplicado dentro da própria planilha: a primeira ocorrência vale, as outras são
      `invalid` "Repetido na linha N".
- [ ] **Importar** (`POST …/commit`, só em `validated`) enfileira o job: processa em lotes de 200,
      cada linha num savepoint — a linha que falha vira `failed` com a mensagem, as outras seguem.
      Progresso (`processed/total`) consultável.
- [ ] **Relatório**: contagens (criados, atualizados, ignorados, com erro) e `GET …/errors.csv` com a
      planilha original + coluna "Erro" — o usuário corrige e reenvia só ela.
- [ ] Importação expira em 7 dias se não for concluída (linhas apagadas pelo worker); concluída
      guarda as linhas por 30 dias para o relatório e depois só as contagens.
- [ ] Uma importação em `validating`/`importing` por entidade de cada vez (`409`).

### Idempotência

- [ ] `import_keys (entity, key_hash)` guarda a chave natural de tudo que a importação criou →
      reimportar a mesma planilha encontra a chave e trata como duplicado (nunca cria de novo), mesmo
      que o registro tenha mudado depois.
- [ ] Chaves: cliente = telefone E.164 (e o próprio `UNIQUE` do `clients` como segunda barreira);
      serviço = `lower(nome)`; agendamento = coluna "id no sistema anterior" quando mapeada, senão
      `telefone + início (UTC) + barbeiro`.
- [ ] O job é retomável: reexecutar depois de queda pula linhas já `imported` (status por linha).

### Por entidade

- [ ] **Clientes**: nome, telefone (obrigatórios), e-mail, nascimento, observações, tags (separadas
      por vírgula; cria tag que não existe — S13), e os campos de resumo de Q-S16-1 (última visita,
      nº de visitas, total gasto). Criados por `clients.public.create_client(..., source="import")`.
- [ ] **Consentimento** (PD-30): cliente importado ganha só o opt-in de WhatsApp com
      `whatsapp_opt_in_source = import` (utilidade: lembrete e confirmação de agendamento). A
      importação **nunca** grava consentimento de marketing (`marketing_consent_at` fica nulo) — o
      importado só recebe reativação, aniversário e campanha depois de um "sim" explícito ou de um
      atendimento no Navalha. A visita-resumo `imported` de Q-S16-1 **não** conta como atendimento
      para essa regra. Não há coluna "aceita promoções" na planilha: um "sim" dado ao sistema
      anterior não é registrável aqui.
- [ ] **Serviços**: nome, duração (aceita "45", "45 min", "1h30"), preço (aceita "45", "45,00",
      "R$ 45,00"), descrição. Criados pelo `catalog.public`. Exige `catalog:write` + todas as
      unidades (DEC-016 P4).
- [ ] **Agendamentos futuros**: data, hora (fuso da unidade), telefone e nome do cliente (cria o
      cliente se não existir), barbeiro (casado por nome ou iniciais na unidade, sem acento),
      serviço (por nome; vários separados por "+" → PD-05 em sequência), unidade (padrão da opção),
      observação, id anterior. Só datas **futuras**; conflito de horário, barbeiro sem o serviço ou
      fora da jornada → `invalid` com a mensagem do `scheduling`. Criados por
      `scheduling.public.create_appointment(session, BookingRequest, source="import", actor=staff,
      origin_ref=<import_id:linha>, idempotency_key=<key_hash>)` — o `origin = import` no
      `appointment.created` é o que S10/S12 usam para não mandar confirmação (Q-S16-2).
- [ ] Barbeiro ou serviço não encontrado lista os nomes disponíveis na mensagem ("Barbeiro 'Dieguinho'
      não encontrado. Cadastrados: Diego Martins, Paulo Renato").
- [ ] Limites do plano (S15) valem: importação nunca cria registro acima do limite (o `402` vira
      erro da linha).

## Data Contract

```text
# Primeiros passos — módulo imports, tag "onboarding"
GET  /onboarding                          → 200 OnboardingOut
POST /onboarding/steps/{key}/skip         → 200 OnboardingOut | 404 | 409 (obrigatório)
POST /onboarding/steps/{key}/unskip       → 200 OnboardingOut
POST /onboarding/dismiss                  → 200 OnboardingOut
POST /onboarding/reopen                   → 200 OnboardingOut

OnboardingOut {steps: [{key, required, status: done|pending|skipped|locked, count?, detail?}],
               progress_pct, completed_at|null, dismissed_at|null}

# Importação — tag "imports"
POST   /imports            multipart {entity: clients|services|appointments, file}
                           → 201 ImportOut (+ columns[], sample[][], suggested_mapping) | 403 | 409 | 413 | 422
GET    /imports?entity=&limit=20                 → 200 ImportOut[] (mais novas primeiro)
GET    /imports/{id}                             → 200 ImportOut | 404
PUT    /imports/{id}/mapping   MappingIn         → 202 ImportOut (validating) | 409 | 422
GET    /imports/{id}/rows?status=&limit=50&offset=  → 200 {items: ImportRowOut[], total}
POST   /imports/{id}/commit                      → 202 ImportOut (importing) | 409
POST   /imports/{id}/cancel                      → 200 ImportOut | 409
POST   /imports/{id}/retry                       → 202 ImportOut | 409 (só failed)
GET    /imports/{id}/errors.csv                  → 200 text/csv
GET    /imports/templates/{entity}.csv           → 200 text/csv (cabeçalho + 2 linhas de exemplo)

ImportOut    {id, entity, status, file_name, total_rows, mapping|null, options|null,
              counts: {valid, duplicate, invalid, created, updated, skipped, failed},
              progress: {processed, total}, created_by: {id, name}, created_at, finished_at|null,
              expires_at, error|null}
MappingIn    {mapping: {<campo>: <coluna>}, options: {date_format: "dd/mm/aaaa"|"aaaa-mm-dd"|
              "mm/dd/aaaa", default_unit_id?, duplicate_policy: skip|update}}
ImportRowOut {row_number, status, raw{}, normalized{}|null, messages: [{field|null, message}],
              record_id|null}
Erros: {"detail"}; 409 "Já existe uma importação de clientes em andamento".
```

### Banco de dados

Migration de tenant (próxima `tNNNN_imports`):

```text
imports           id uuid pk · entity varchar(20) CHECK in (clients, services, appointments) ·
                  status varchar(12) · file_name varchar(255) · file_format varchar(4) ·
                  total_rows int · mapping jsonb null · options jsonb null · counts jsonb ·
                  processed int default 0 · created_by uuid → users.id ON DELETE RESTRICT ·
                  created_at · validated_at · committed_at · finished_at · expires_at · error text null
                  INDEX (entity, created_at desc)
                  UNIQUE INDEX uq_import_running ON (entity) WHERE status IN ('validating','importing')
import_rows       id uuid pk · import_id → imports.id ON DELETE CASCADE · row_number int ·
                  raw jsonb · normalized jsonb null · status varchar(10) · messages jsonb ·
                  record_id uuid null · UNIQUE (import_id, row_number) · INDEX (import_id, status)
import_keys       entity varchar(20) · key_hash char(64) · record_id uuid · import_id uuid ·
                  created_at · PRIMARY KEY (entity, key_hash)
onboarding_state  id smallint pk CHECK (id = 1) · skipped_steps text[] · dismissed_at · completed_at ·
                  updated_at
```

Dependência nova de runtime: **`openpyxl`** (leitura de XLSX, modo `read_only`) — precisa de
aprovação. CSV com a biblioteca padrão.

## Permissões

Nenhuma permissão nova: importar é criar registros, e quem cria cada um já tem permissão.

| Ação | Permissão | owner | manager | receptionist | barber |
|---|---|---|---|---|---|
| ver/pular/dispensar primeiros passos | `tenant:configure` | all | — | — | — |
| importar clientes | `client:write` | all | unit | unit | — |
| importar serviços | `catalog:write` + todas as unidades | all | só se vê todas | — | — |
| importar agendamentos | `appointment:create` (unidade do agendamento no escopo) | all | unit | unit | — |
| ver importações | a permissão da entidade; recepção vê só as que criou | | | | |

Importar exige escopo ≠ `own` (o barbeiro tem `appointment:create own`, mas importação é operação da
casa).

## Acceptance Criteria

- [ ] Módulo `imports` com layout completo e `jobs/` (worker); ninguém importa `imports`.
- [ ] `tests/test_imports/`: detecção de separador/encoding; XLSX; sinônimos de cabeçalho; cada
      regra de validação por entidade; duplicado na planilha e no banco; reimportação não duplica;
      job retomado depois de queda simulada; limite do plano por linha; agendamento passado e
      conflito recusados; cruzamento entre duas barbearias (importação de A invisível em B).
- [ ] `tests/test_imports/test_onboarding.py`: cada passo muda de estado com o dado real; recurso
      fora do plano → `locked`.
- [ ] Planilhas de exemplo exportadas de outros sistemas guardadas em `tests/fixtures/imports/`
      (anonimizadas).
- [ ] Testes em `tests/test_imports/` cobrindo as regras acima
- [ ] Snapshots de contrato revisados (`UPDATE_CONTRACT_SNAPSHOTS=1` só se a mudança for intencional)

## Dependencies

- **S00**: `schedule_job(session, "imports.validate" | "imports.commit", run_at=now, payload,
  dedupe_key=<import_id:fase>)` com handlers em `JOB_HANDLERS`, e `PeriodicTask("imports.expire",
  daily_at=…)`. O job roda na sessão do schema (`JobContext`).
- **S01** (`identity`): `list_units(session)` e `get_unit_calendar(session, unit_id, start, end)`
  (unidade com expediente) — o `imports` monta o status a partir delas, sem função nova no `identity`;
  **S02**: `barbers_without_hours(session) -> list[id]`; **S05** (`catalog`):
  `count_active_services`, `count_active_payment_methods`, `create_service(..)`;
  **S10**: `whatsapp_connected(session) -> bool`; **S11**: `assistant_configured(session) -> bool`.
- **S03** (`scheduling.public`): `create_appointment(..., source="import", origin_ref,
  idempotency_key)` com as exceções dela (`SlotUnavailable`, `BookingWindowError`…) em português —
  viram a mensagem da linha. As regras de canal do cliente (antecedência, horizonte) só valem para `assistant` e
  `booking_link` (S03), então não se aplicam a `source = import`.
- **S13** (`clients.public`): `create_client(..., source="import")`, `normalize_phone`, criação de
  tag, e o recálculo de indicadores (`clients_stats`) para os campos de resumo de Q-S16-1.
  **Assumido**: `get_contact_policy` não conta a visita-resumo `imported` como atendimento para o
  consentimento de marketing (PD-30).
- **S10/S12**: não enviar confirmação de agendamento com `origin = import`; lembretes seguem
  (Q-S16-2). Ignorar `client.created` com `source = "import"` (nada de "boas-vindas" para 2.000
  clientes importados).
- **S15**: `has_feature` (passos travados) e `assert_within_limit`.

## Notes

- O CSV de erros devolve as colunas originais na ordem original: o usuário abre, corrige e reenvia
  sem remapear (o mapeamento sugerido acerta pelos mesmos nomes).
- Excel transforma telefone em número (`5.511987654321E+12`) — a validação detecta notação científica
  e pede para formatar a coluna como texto.
- Datas do Excel chegam como número de série; o leitor converte antes da validação.

### Perguntas em aberto

- ✅ **Q-S16-1 — Trazer o resumo do histórico dos clientes do sistema anterior?**
  (a) não: indicadores começam do zero; (b) sim, colunas opcionais "última visita", "total de
  visitas" e "total gasto" viram uma visita-resumo `imported` no ledger da S13; (c) importar o
  histórico completo de atendimentos.
  **Recomendação: (b)** — a reativação de inativos (PD-20) e o "barbeiro preferido" funcionam desde o
  primeiro dia sem o custo de (c), que cada sistema exporta de um jeito.
  > Resolvido em 2026-11-06: (b) — a importação traz o resumo do histórico (última visita, nº de
  > visitas, total gasto) como visita-resumo `imported`, que não libera marketing (PD-30)
  > (ROADMAP §7).
- ✅ **Q-S16-2 — Agendamento importado avisa o cliente?**
  (a) não envia confirmação, mas os lembretes (PD-07) seguem normais; (b) envia confirmação a todos;
  (c) não envia nada, nem lembrete.
  **Recomendação: (a)** — o cliente já marcou no sistema anterior; um "seu horário foi agendado" em
  massa confunde, mas o lembrete é justamente o que reduz falta.
  > Resolvido em 2026-11-06: (a) — agendamento importado não pede confirmação; lembretes normais
  > (ROADMAP §7).
- ✅ **Q-S16-3 — O gerente vê e conclui os primeiros passos?**
  (a) só o dono; (b) dono e gerente com todas as unidades.
  **Recomendação: (b)** se for comum o dono delegar a implantação; senão (a). Sem preferência forte —
  a spec usa (a) até a resposta.
  > Resolvido em 2026-11-06: (a) — só o dono faz os primeiros passos (`tenant:configure`, como na
  > tabela de permissões) (ROADMAP §7).
