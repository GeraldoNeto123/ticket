# ticket

Plugin do Claude Code com o fluxo **`/ticket:implement`**: implementação disciplinada de um ticket por sessão — reivindicação, escopo sagrado, TDD, protocolo de erro de spec, commit → review → amend e um checkpoint de consistência automático a cada 5 tickets.

## O que vem no pacote

| Componente | O que faz |
|---|---|
| Skill `spec` | `/ticket:spec` — segue o `to-spec` do `mattpocock-skills` e acrescenta o que este fluxo consome depois: costuras registradas de forma que uma sessão nova ache, e referência de código por símbolo |
| Skill `split` | `/ticket:split <spec>` — roda o portão de modelagem (campo → escritores por fluxo, conflito vira ADR) e só então segue o `to-tickets`, com o ADR como entrada |
| Skill `implement` | O fluxo em 8 passos, invocado com `/ticket:implement <ticket>` |
| Skill `run` | Orquestrador da fila: `/ticket:run <spec/feature>` executa os tickets da frontier em sequência, um subagent fresco por ticket, com ledger de progresso e escalada explícita |
| Agent `checkpoint-reviewer` | Revisão de consistência **entre** tickets acumulados (Opus, effort high) — o olhar que nenhuma sessão isolada tem |
| Hook `runbook-checkpoint.py` | PostToolUse em todo `git commit`: abre o primeiro ciclo, conta os commits de ticket do operador e avisa quando o checkpoint vence. Registrado automaticamente na instalação do plugin |
| Hook `referencias-de-linha.py` | PostToolUse em todo `Write`/`Edit` de `.md`: acusa documento que nasce com âncora `arquivo:linha`, que envelhece a cada ticket. Aviso, não bloqueio; silencioso fora dos repos que usam o fluxo |

## Pré-requisitos

1. **Plugin `mattpocock-skills`** — o `/tdd`, o `code-review`, o `domain-modeling` e os `to-spec`/`to-tickets` que as skills `spec` e `split` envolvem vêm dele:

   ```
   /plugin marketplace add mattpocock/skills
   /plugin install mattpocock-skills@mattpocock
   ```

2. **Setup por projeto** — no repo em que o fluxo vai rodar, rode uma vez:

   ```
   /setup-matt-pocock-skills
   ```

   Isso cria `docs/agents/issue-tracker.md` (onde os tickets vivem: arquivos `.md`, GitHub, GitLab...) e o vocabulário de rótulos que a skill consulta.

## Instalação

```
/plugin marketplace add GeraldoNeto123/ticket
/plugin install ticket@ticket
```

Reinicie a sessão (ou `/reload-plugins`) e invoque:

```
/ticket:spec                                               # a conversa vira spec
/ticket:split <spec>                                       # portão de modelagem e então a fila de tickets
/ticket:implement <número da issue ou caminho do ticket>   # um ticket, modo assistido
/ticket:run <spec/feature>                                 # a fila inteira, modo autônomo
```

As duas primeiras **envolvem** o `to-spec` e o `to-tickets` do `mattpocock-skills` em vez de duplicá-los: leem o `SKILL.md` de lá (os dois são `disable-model-invocation`, e o Skill tool recusa invocação vinda de modelo) e acrescentam o que só quem conhece o resto do fluxo sabe — o portão de modelagem antes do fatiamento, o ADR como entrada dos tickets, a issue pai que o checkpoint vai precisar, e referência de código por símbolo. O upstream segue se atualizando sem merge; em troca, as duas conferem se o arquivo lido ainda tem a forma que os adendos pressupõem e param se não tiver. O `scripts/upstream-skill.py` resolve o caminho da cópia instalada, que carrega a versão e por isso não pode ser fixado.

O `run` segue a filosofia *subagent-driven*: um subagent fresco por ticket (cada um foi dimensionado para uma janela limpa), estritamente sequencial — tickets são fatias verticais e colidem nos arquivos de junção, então paralelismo de implementação fica de fora por design. O orquestrador mantém um ledger de progresso e para apenas nos casos que exigem decisão humana (erro de spec de design, bloqueio).

Na fila, **quem conta os cinco tickets do ciclo é o orquestrador, pelo ledger** — não o hook. O aviso do hook só alcança a sessão que entrou no fluxo pela invocação, e o subagent chega à `implement` lendo o arquivo; além disso o hook é infraestrutura da máquina, então numa máquina sem ele nenhum aviso chega. Um `CHECKPOINT_DUE` que volte confirma a contagem, e a ausência dele não diz nada. Em sessão manual (`/ticket:implement`) quem avisa continua sendo o hook, com conferência própria descrita no `references/checkpoint.md`.

## O fluxo, em uma linha por passo

Antes da fila existir: **`/ticket:spec`** sintetiza a conversa em spec, e **`/ticket:split`** roda o portão de modelagem — mapa de campo → escritores por fluxo, conflito virando ADR — antes de fatiar. O portão existe porque fatiar por comportamento visível é a fatia certa para entregar valor e mesmo assim deixa passar o conflito de escritor: numa etapa real de 64 tickets, sete tinham essa forma, e nenhum foi falha de implementação — cada um passou na própria revisão. Ele tem critério de entrada: etapa que não escreve em estado compartilhado por mais de um fluxo pula o portão e diz isso.

Depois, por ticket:

1. **Reivindicar** — bloqueadores primeiro (frontier), depois dono; ticket de outra pessoa para o fluxo.
2. **Implementar** — escopo restrito ao ticket, `/tdd` nas costuras que o spec registrou.
3. **Erro de spec** — factual corrige na hora; design registra, para o ticket e escala. Na dúvida, é design.
4. **Verificar** — evidência antes de alegação.
5. **Commit → review → amend** — a revisão só enxerga trabalho commitado; 1 ticket = 1 commit. Push é manual, fora do fluxo.
6. **Encerrar** — *feito* ≠ *fechado*: quem fecha issue é o merge, não o push.
7. **Métrica** — cada erro de spec vira uma linha versionada em `spec-errors.md`.
8. **Checkpoint** — a cada 5 tickets, o agent revisa o acumulado com um portão de materialidade: correções pequenas viram um `refactor:`; defeitos reais viram achados em quarentena no contêiner de checkpoint da demanda (pasta `checkpoint/` irmã de `issues/`; comentário na issue pai em modo tracker), sempre `needs-triage` — promover à fila é decisão humana, e a issue só nasce na promoção; inconsistências sem defeito viram linha num registro por checkpoint, que só sai de lá quando vira ticket; achados sobre o próprio processo viram proposta de mudança na skill, nunca ticket. A fila da feature converge para o escopo original. O procedimento fica em `skills/implement/references/checkpoint.md` (ciclo, disparo do agent, fechamento da tag) e `achados.md` ao lado (destino de cada achado, critério de promoção, dedup) — lidos só quando o checkpoint vence.

## O ciclo de checkpoint

A tag que ancora o ciclo é escopada por operador (`runbook-checkpoint-<slug do e-mail do git>`), e o hook conta apenas commits do próprio autor — mais de uma pessoa pode rodar o fluxo no mesmo repo sem sobrescrever o ciclo alheio.

O hook cuida do ciclo de vida da tag inteiro, porque um checkpoint que depende de alguém lembrar de criar uma tag não é um checkpoint:

- **Primeiro ciclo** — repo com `docs/agents/issue-tracker.md` e sem tag: o hook instrui a criação da tag no HEAD. Sem isso o contador nunca começava a contar, e o fluxo passava por funcionando.
- **Tag legada** — repos anteriores ao escopo por operador seguem sendo contados pela tag sem sufixo enquanto o aviso de migração se repete. Falta de migração atrasa o checkpoint; não o cancela.
- **Tag ausente num repo que já usou o fluxo** — o hook para e manda perguntar, em vez de recriar a tag e dar o acumulado por revisado.

O hook filtra `git commit` pelo comando literal, dentro do próprio script, e não pelo campo `if` do `hooks.json`: aquele campo usa sintaxe de regra de permissão, que não enxerga dentro de comando composto (`git add -A && git commit ...`) nem de substituição `$(...)` — as duas formas mais comuns de commitar.

## Licença

[MIT](./LICENSE)
