# Handoff — redesenho do plugin `ticket`

**Data:** 2026-08-09 · **Estado:** executado em 2026-08-10 (v2.0.0) · **Repo:** `~/ticket`

Executado com três ajustes sobre o desenho original, decididos ao cruzar o
histórico de commits com o plano:

1. **O hook contador (`runbook-checkpoint.py`) e a tag morreram junto.** Seis dos
   22 commits combatiam essa máquina; a v1.15.0 já tinha rebaixado o hook a
   confirmação (o ledger conta), e no fluxo-destino a detecção estrutural dele
   (v1.9.0) nunca dispararia — o modo manual invoca o `/implement` do Matt. O
   ciclo passou a ser delimitado pelos próprios commits do checkpoint
   (`refactor: checkpoint` / `docs(checkpoint):`), que viajam com o clone — coisa
   que a tag local não fazia. O modo manual ganhou a skill `/ticket:checkpoint`
   (model-invocable, para o `run` alcançá-la por nome em vez de resolver caminho).
2. **O brief manteve `mattpocock-skills:code-review`** — é a skill comprovadamente
   invocável por subagent; a `code-review` nativa do harness é acionável só pelo
   usuário. A ordem commit → review → amend segue no `CLAUDE.md` do projeto com a
   justificativa original.
3. **O portão de promoção ganhou dedup contra tickets fechados** (`achados.md`):
   âncora que bate em ticket `done` pode ser risco já aceito e documentado —
   caso real de 2026-08-10.

O passo 3 do plano original ("rodar uma fila real antes de apagar") foi pulado por
decisão do usuário; a primeira fila real da v2 é a validação.

---

## O diagnóstico

O plugin foi construído como **wrapper** em volta das skills do `mattpocock-skills`
(`skills/spec` envolve `/to-spec`, `skills/split` envolve `/to-tickets`,
`skills/implement` sombreia o `/implement` dele). Isso é herança num ecossistema que
só tem **composição em sequência** — no mapa do `ask-matt` nenhuma skill envolve outra,
todas encadeiam.

O custo dessa junta está escrito no próprio repo:

- `references/envolver-upstream.md` inteiro (resolver caminho da versão instalada, ler em
  vez de invocar, conferir a forma antes dos adendos)
- `scripts/upstream-skill.py`
- `skills/run/SKILL.md` passo 3 — `test -f`, `installed_plugins.json`, `sort -V`, o
  comentário "já aconteceu"

Nada disso é sobre o trabalho; é tudo para segurar o acoplamento à forma interna de
arquivo de terceiro. Cada release do plugin do Matt é uma quebra em potencial.

Comparação que fecha o argumento: `mattpocock-skills/skills/engineering/implement/SKILL.md`
tem **9 linhas de corpo**. O `skills/implement/SKILL.md` daqui tem 146 + 391 de references
— e ainda depende do plugin dele para `/tdd` e `/code-review`.

**As observações que motivaram o plugin são boas e sobrevivem; a embalagem é que sai.**

## As quatro descobertas que valem

Quatro coisas que o fluxo do Matt genuinamente não tem. O texto de cada uma já está
escrito no repo — não reescrever, realocar:

1. **Ordem commit → review → amend.** O `/implement` dele manda revisar e depois commitar,
   mas o `/code-review` diffa `<ponto-fixo>...HEAD` e só enxerga trabalho commitado —
   invocado antes, revisa o commit anterior sem erro visível. Texto atual em
   `skills/implement/SKILL.md` passo 5.
2. **Portão de invariante de conjunto.** Critério de aceite que afirma algo sobre um
   conjunto não se verifica pelo ramo editado. Texto em `skills/implement/SKILL.md`,
   bloco `<invariante>` do passo 4.
3. **Passada de estado compartilhado antes de fatiar.** O `/to-tickets` corta por
   comportamento visível e nunca faz a passada ortogonal sobre o estado que as fatias
   dividem. Evidência real: 7 de 64 tickets escrevendo nas mesmas colunas. Texto em
   `skills/split/SKILL.md` passo 2.
4. **Consistência entre tickets a cada 5.** O fluxo dele não tem passada transversal
   nenhuma. Já implementado em `skills/run` + `agents/checkpoint-reviewer.md` +
   `skills/implement/references/checkpoint.md`.

## O destino

```
1. /grill-with-docs             (Matt)   ─┐
2. /prototype + /handoff        (Matt)    │  uma janela só,
3. /to-spec                     (Matt)    │  sem compactar
4. /ticket:estado-compartilhado (TEU)     │  ← passada ortogonal, produz ADR
5. /to-tickets                  (Matt)   ─┘  ← consome o ADR do passo 4

   ────────── /clear ──────────

6a. manual:    /implement <ticket>   (Matt)  → /clear → próximo
6b. autônomo:  /ticket:run <feature> (TEU)   → despacha 6a por subagent,
                                               checkpoint a cada 5
```

### Onde cada descoberta passa a morar

| Descoberta | Casa nova |
|---|---|
| Ordem commit → review → amend | `CLAUDE.md` **do projeto** (não o global) |
| Portão de invariante de conjunto | `CLAUDE.md` do projeto |
| Âncora, nunca `arquivo:linha` | `hooks/referencias-de-linha.py` — já é código, fica |
| Passada de estado compartilhado | `/ticket:estado-compartilhado`, skill solta |
| Checkpoint a cada 5 | `skills/run` + agent + references — fica |
| done vs closed, claim/`Assignee` | `docs/agents/issue-tracker.md` do projeto; o `run` confere no cálculo da frontier |

As duas regras de julgamento ficam só no `CLAUDE.md` do projeto, sem repetição no brief
do `run` — o subagent herda esse arquivo. **Não verificado ainda:** confirmar na primeira
fila real que a regra chega mesmo no subagent.

### A mudança que destrava o resto

O brief de dispatch do `run` passa a ser **prosa inline**, não ponteiro para arquivo.
Cabe, porque o do Matt tem 9 linhas e os adendos são 2–3 frases:

```
Implemente o ticket <ref>. Spec em <caminho>.
Use /tdd nas costuras nomeadas no spec.
Typecheck e testes do arquivo enquanto trabalha; suíte completa uma vez, no fim.
Commite. Depois revise com mattpocock-skills:code-review contra <sha-anterior>,
e aplique o que couber via --amend. Um ticket = um commit.
Erro de spec de design: registre no ticket, devolva SPEC_DESIGN, não implemente por cima.
Devolva só o contrato: STATUS / SHA / testes em uma linha / até 3 de observação.
```

Com isso a única dependência do upstream vira o **nome** `mattpocock-skills:code-review`,
que é interface pública e estável.

### O que deleta

- `skills/spec/` — o único adendo real (âncora) já é o hook
- `skills/implement/` — usa o do Matt
- `references/envolver-upstream.md`
- `scripts/upstream-skill.py`
- `skills/run/SKILL.md` passo 3 inteiro (resolução de caminho)

Alvo: ~730 linhas → ~200–250.

## Plano de execução

Nesta ordem, pelo motivo de cada passo ser reversível sozinho:

1. **Extrair `/ticket:estado-compartilhado`** a partir do passo 2 do `skills/split/SKILL.md`.
   Aditivo — não quebra nada que já roda. Roda entre `/to-spec` e `/to-tickets`.
   Levar junto `skills/implement/references/adr-escritor.md`, que é o procedimento de ADR
   que ela usa.
2. **Reescrever `skills/run`** com brief inline, deletando o passo 3.
3. **Rodar uma fila real** antes de apagar qualquer coisa.
4. Só então **apagar** `spec/`, `implement/`, `envolver-upstream.md`, `upstream-skill.py`.

## Restrições

- **Nada de PR upstream no `mattpocock-skills`.** Decisão explícita do usuário: os deltas
  são específicos deste fluxo e ficam locais. As descobertas 1 e 2 vão para o `CLAUDE.md`
  do projeto, não para o repo dele.
- Multi-operador real (tag escopada por operador) continua valendo — ver
  `references/checkpoint.md`.
- Push é manual, fora das skills.
- Mensagens de commit em português, sem autorreferência de IA (`~/.claude/CLAUDE.md`).

## Assunto resolvido, não reabrir

`vercel-labs/skills@find-skills` — avaliada e **descartada**. Gatilho largo demais
("how do I do X") num ambiente com ~30 skills, régua de qualidade por contagem de
instalação, e o passo final é `npx skills add -g -y` (instalação global não-interativa de
instruções de terceiros). Substituto: uma linha no `CLAUDE.md` lembrando que
`npx skills find <termo>` existe.

Busca no registro por alternativa pronta ao que este plugin faz: 19 resultados, nada
melhor. O mais relevante é `liatrio-labs/spec-driven-workflow@sdd` (97 installs), mesmo
gênero e mais cerimonioso. Runner autônomo com ledger retomável + passada de consistência
não existe em lugar nenhum do registro — é a parte original daqui.

## Skills sugeridas para a próxima sessão

- **`/writing-for-agents`** — obrigatória ao escrever a `estado-compartilhado` e reescrever
  o `run`. É a referência de como escrever documento que agente consome.
- **`/grill-with-docs`** — se algum ponto do plano ainda parecer frouxo antes de mexer no
  código. Este repo tem `CONTEXT.md`? Se não, ela cria.
- **`/code-review`** — ao fim de cada passo do plano, contra o SHA anterior.
- **`/ask-matt`** — para reconferir o mapa dele se surgir dúvida sobre onde uma peça encaixa.

Não usar: `/to-spec` e `/to-tickets` aqui. O plano acima já é fino demais para virar spec.
