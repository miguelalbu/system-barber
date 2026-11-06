# Camada de contexto — backend

Pasta de contexto para assistentes de IA, no modelo do backend da ClaraAI.

**Para humanos:** este arquivo explica a estrutura, as permissões e a governança.
**Para a IA:** leia `index.toml` primeiro — ele dita o que carregar em cada situação.

> Por que `.github/` dentro de `backend/`? O repositório é um monorepo (DEC-010): cada projeto tem a
> sua camada de contexto, como no Clara, onde backend e frontend são repositórios separados. O
> GitHub só lê workflows e templates da `.github/` **da raiz**; esta aqui é só contexto.

## Estrutura

As **specs** e a **referência da API** não ficam aqui: vivem em `../docs/` (ver
`../docs/README.md`), junto da documentação do projeto. Esta pasta guarda só o que orienta a IA.

```text
backend/.github/
├── README.md          ← este arquivo (governança e permissões)
├── index.toml         ← roteador da IA: o que ler/escrever por tipo de tarefa
├── project.toml       ← identidade, stack, URLs
├── rules.md           ← padrões técnicos inegociáveis + layout de pastas
├── soul.md            ← comportamento e restrições da IA
├── .contextignore     ← o que a IA não deve ler
├── memory/
│   ├── progress.md    ← o que existe e em que estado
│   ├── issues.md      ← bugs, workarounds, áreas frágeis (ISS-NNN)
│   └── decisions.md   ← decisões de arquitetura (DEC-NNN), só acrescentar
└── skills/
    ├── _template.md
    └── *.md           ← guias de tarefas recorrentes
```

## Permissões

| Arquivo | Ler | IA escreve |
|------|:----:|:--------:|
| `index.toml` | ✅ | ❌ |
| `project.toml` | ✅ | ❌ |
| `rules.md` | ✅ | ❌ |
| `soul.md` | ✅ | ❌ |
| `.contextignore` | ✅ | ❌ |
| `memory/progress.md` | ✅ | ✅ |
| `memory/issues.md` | ✅ | ✅ |
| `memory/decisions.md` | ✅ | ✅ só acrescentar |
| `../docs/specs/*.md` | ✅ | ✅ |
| `skills/*.md` | ✅ | ❌ (só com pedido explícito) |

Arquivos ❌ só mudam com instrução explícita de um humano. Se a IA perceber que um deles está
desatualizado, ela avisa e propõe o diff.

## Specs

- Nome: `<ícone><status>_<dominio>-<feature>.md` — `⚪draft_`, `⏳active_`, `✅completed_`.
  Renomeie o arquivo quando o **Status** mudar.
- Toda funcionalidade nova nasce como spec **antes** do código (`../docs/specs/_template.md`).
- Spec que toca backend e frontend tem espelho na pasta do outro projeto, e cada uma aponta para a
  outra no cabeçalho (`Espelho no frontend:`).
- Checkboxes `[ ]` → `[x]` conforme os critérios forem atendidos *e testados*.
- Divergência descoberta na implementação vira nota datada na própria spec.

## Regras de governança

1. Nunca modificar arquivos somente-leitura sem instrução humana explícita.
2. Atualizar `memory/progress.md` ao concluir uma tarefa.
3. Registrar bugs encontrados em `memory/issues.md`, mesmo os que não forem corrigidos agora.
4. Registrar decisões de arquitetura em `memory/decisions.md` (só acrescentar; para mudar uma
   decisão, crie outra que a substitua: `Status: superseded by DEC-NNN`).
5. Seguir `rules.md` sem exceção — ele prevalece sobre o conhecimento geral da IA.
6. Respeitar `soul.md` em tom, formato e restrições.
7. Não acessar o que está em `.contextignore`.
8. Specs são o contrato: a implementação respeita a spec; se precisar divergir, a spec é atualizada.
9. Compactar a memória quando um arquivo passar de ~300 linhas.
