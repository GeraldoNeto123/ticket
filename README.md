# ticket

Plugin do Claude Code que **complementa** o fluxo de tickets do
[`mattpocock-skills`](https://github.com/mattpocock/skills) em vez de envolvê-lo:
as skills dele rodam puras, e este plugin acrescenta só o que aquele fluxo não
tem — a passada de estado compartilhado antes do fatiamento, o checkpoint de
consistência entre tickets e o orquestrador autônomo da fila.

## O fluxo

```
1. /grill-with-docs                  (mattpocock)  ─┐
2. /prototype + /handoff             (mattpocock)   │  uma janela só
3. /to-spec                          (mattpocock)   │
4. /ticket:estado-compartilhado      (este plugin)  │  ← passada ortogonal, produz ADR
5. /to-tickets                       (mattpocock)  ─┘  ← consome o ADR do passo 4

   ────────── /clear ──────────

6a. manual:    /implement <ticket>    (mattpocock)  → /clear → próximo
6b. autônomo:  /ticket:run <feature>  (este plugin) → um subagent fresco por ticket,
                                                      /ticket:checkpoint a cada 5
```

A única dependência do upstream é o **nome público** das skills
(`mattpocock-skills:tdd`, `mattpocock-skills:code-review`,
`mattpocock-skills:domain-modeling`), que é interface estável. A `code-review`
serve o caminho manual (6a); desde a 2.2.0 a `run` não a invoca — ela despacha
os dois eixos direto, do orquestrador, pelos motivos em `skills/run/references/revisao.md`.

## O que vem no pacote

| Componente | O que faz |
|---|---|
| Skill `estado-compartilhado` | `/ticket:estado-compartilhado <spec>` — entre o `/to-spec` e o `/to-tickets`: mapeia campo → escritores por fluxo e resolve conflito de escritor em ADR. O fatiamento corta por comportamento visível e nunca faz essa passada; numa etapa real de 64 tickets, 7 tinham conflito de escritor e todos passaram na própria revisão |
| Skill `checkpoint` | `/ticket:checkpoint` — a cada 5 tickets, dispara o agent revisor sobre o acumulado, aplica correções pequenas num `refactor: checkpoint` e roteia achados para quarentena fora da fila, com critério de promoção explícito |
| Skill `run` | `/ticket:run <spec/feature>` — orquestrador da fila: executa a frontier em sequência, um subagent fresco por ticket com brief inline, ledger de progresso retomável e escalada explícita; despacha a revisão de dois eixos e a devolve ao subagent que implementou; invoca a `checkpoint` a cada ciclo |
| Agent `checkpoint-reviewer` | Revisão de consistência **entre** tickets acumulados (Opus, effort high) — o olhar que nenhuma sessão isolada tem |
| Hook `referencias-de-linha.py` | PostToolUse em todo `Write`/`Edit` de `.md`: acusa documento que nasce com âncora `arquivo:linha`, que envelhece a cada ticket. Aviso, não bloqueio; silencioso fora dos repos que usam o fluxo |

O ciclo de checkpoint é delimitado pelos próprios commits que ele deixa no
histórico (`refactor: checkpoint ...` / `docs(checkpoint): ...`) — sem tag, sem
hook contador: os marcadores viajam com o clone. Numa fila, quem conta os cinco
tickets é o orquestrador, pelo ledger.

## Pré-requisitos

1. **Plugin `mattpocock-skills`**:

   ```
   /plugin marketplace add mattpocock/skills
   /plugin install mattpocock-skills@mattpocock
   ```

2. **Setup por projeto** — no repo em que o fluxo vai rodar, rode uma vez:

   ```
   /setup-matt-pocock-skills
   ```

   Isso cria `docs/agents/issue-tracker.md` (onde os tickets vivem: arquivos
   `.md`, GitHub, GitLab...) e o vocabulário de rótulos que as skills consultam.
   Acrescente ali a linha `**Onde vive o achado: arquivo.**` (ou `tracker`) se o
   contêiner de quarentena do projeto não for o default por plataforma que o
   `achados.md` da `ticket:checkpoint` enuncia.

3. **Duas regras no `CLAUDE.md` do projeto** — elas valem também na sessão
   manual (`/implement` puro), que nenhuma skill deste plugin embala:

   - **Commit → review → amend, nesta ordem.** O `code-review` diffa
     `<ponto-fixo>...HEAD` e só enxerga trabalho commitado; 1 ticket = 1 commit,
     achados aplicados via `--amend` (conferindo `git log @{u}..HEAD` antes).
   - **Critério de aceite sobre um conjunto não se verifica pelo ramo editado.**
     "Sempre", "nenhum", "um único" exigem enumerar os caminhos — o ADR que
     mapeia os escritores é a lista, o `grep` fecha o resto.

## Instalação

```
/plugin marketplace add GeraldoNeto123/ticket
/plugin install ticket@ticket
```

Reinicie a sessão (ou `/reload-plugins`) e invoque:

```
/ticket:estado-compartilhado <spec>   # entre o /to-spec e o /to-tickets
/ticket:run <spec/feature>            # a fila inteira, modo autônomo
/ticket:checkpoint                    # o acumulado de sessões manuais, a cada 5 tickets
```

O `run` segue a filosofia *subagent-driven*: um subagent fresco por ticket (cada
um foi dimensionado para uma janela limpa), um de cada vez por default — tickets
são fatias verticais e colidem nos arquivos de junção. A exceção é estreita:
clusters da frontier que comprovadamente não compartilham arquivo nenhum podem
correr em paralelo, um `git worktree` por cluster, obrigatório. O orquestrador
mantém um ledger de progresso e para apenas nos casos que exigem decisão humana
(erro de spec de design, bloqueio).

## O checkpoint, em uma linha por destino

Correções pequenas viram um `refactor:`; defeitos reais viram achados em
quarentena no contêiner de checkpoint da demanda (pasta `checkpoint/` irmã de
`issues/`, ou comentário na issue pai — o projeto declara qual, independente de
onde vivem os tickets), sempre `needs-triage` —
promover à fila é decisão humana, a issue só nasce na promoção, e o critério de
promoção é explícito: produz dado errado para o cliente, ou recorreu em dois
checkpoints; inconsistências sem defeito viram linha num registro por checkpoint;
achados sobre o próprio processo viram proposta de mudança na skill, nunca
ticket. A fila da feature converge para o escopo original.

## Licença

[MIT](./LICENSE)
