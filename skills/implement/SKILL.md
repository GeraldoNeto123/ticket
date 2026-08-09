---
name: implement
description: "Executa um ticket do fluxo, do claim ao checkpoint, em 8 passos."
disable-model-invocation: true
---

# /ticket:implement

**Ticket desta sessão:** $ARGUMENTS

O argumento aponta o ticket e, se houver, o preâmbulo/spec obrigatório. Leia ambos antes de qualquer coisa. Escopo é sagrado: implemente **apenas** este ticket. Se o trabalho crescer, o excedente vira ticket novo.

**Escalar**, onde este arquivo disser, é parar o trabalho e entregar a decisão ao usuário — nunca seguir com um palpite.

**Pré-requisito:** o plugin `mattpocock-skills`. O `/tdd` do passo 2 e o `mattpocock-skills:code-review` do passo 5 vêm dele. Se qualquer um falhar por skill inexistente, escale e instrua a instalação — os comandos estão no README do plugin `ticket`. Improvisar um substituto é pior do que parar.

**Onde o ticket vive é decisão do projeto.** Leia `docs/agents/issue-tracker.md` primeiro: ele diz se os tickets são arquivos markdown ou issues de um tracker, e qual CLI usar. Toda vez que esta skill mandar escrever *no ticket*, é esse arquivo que decide se isso é editar um `.md` ou comentar numa issue. Se ele não existir, pergunte ao usuário onde vivem os tickets.

## 1. Reivindicar o ticket

**Bloqueadores antes de dono.** O `/to-tickets` grava em cada ticket quem o bloqueia. Confira antes de reivindicar. Bloqueador ainda aberto = ticket fora da frontier: **escale** e pergunte qual pegar no lugar. Implementá-lo agora é construir sobre base que ainda não existe.

**O dono é o operador, nunca a sessão.** Você não é um ator no tracker: quem responde pelo ticket é o humano ao teclado.

Confira a atribuição antes de ler código, com o CLI que o `issue-tracker.md` definir (`gh issue view <n> --json assignees`, `glab issue view <n>`). Em modo arquivo a atribuição é a linha `Assignee:` no topo do `.md` — convenção deste fluxo, não do `to-tickets`. Repo que ainda não a tem trata o ticket como sem dono, e a linha nasce quando alguém assume.

Três casos, e só um segue em frente:

- **De outra pessoa** → **escale.** Diga quem é o dono e pergunte: assumir mesmo assim, ou trocar de ticket. Atribuição alheia costuma significar trabalho já em curso, e implementar por cima gera conflito de merge e trabalho jogado fora.
- **Sem dono** → atribua ao operador e siga. Em tracker, `--add-assignee @me` resolve para o usuário autenticado no CLI, que é ele. Em modo arquivo não há `@me`: o nome vem de `git config user.name`.
- **Já é do operador** → siga.

## 2. Implementar

Antes de escrever código, leia os ADRs e o glossário. Na convenção destas skills o glossário é o `CONTEXT.md` na raiz, e os ADRs ficam em `docs/adr/`. Cada sessão começa limpa e não viu os tickets anteriores: o que atravessa o `/clear` são esses registros. Decisão já tomada ali não se reabre aqui. Ticket que contradiz um ADR é conflito de spec — passo 3.

**Ticket que acrescenta um escritor a um campo governado por ADR muda o ADR — o procedimento está em [`references/adr-escritor.md`](references/adr-escritor.md).** Ler não basta: leitura não produz a linha que o próximo ticket precisa encontrar. Leia-o quando este ticket criar escritor; nos outros, não.

**Número de linha no ticket é pista; a âncora é o símbolo ou o trecho descrito.** Localize pelo alvo descrito, mesmo quando o número ainda bate. Alvo que não existe em lugar nenhum — símbolo renomeado, arquivo dividido, código já removido — não é ticket difícil: é o spec descrevendo um código que mudou, e o passo 3 trata.

Implemente restrito ao escopo deste ticket:

- Use `/tdd` nas costuras pré-acordadas, que vêm do spec/preâmbulo. Spec que não nomeia costura nenhuma é lacuna de spec: trate pelo passo 3, em vez de deixar o `/tdd` parar o fluxo para perguntar ao usuário.
- Enquanto trabalha, rode **só** typecheck e os testes do arquivo que está mexendo. A suíte completa é do passo 4 e roda **uma vez por ticket**: repeti-la aqui dobra a parte mais cara da fila sem descobrir nada novo.

O commit é o passo 5, depois da verificação e do protocolo de erro de spec.

## 3. Protocolo de erro de spec

Spec que conflita com a realidade do código para o trabalho e vai para triagem. Implementar por cima do conflito é o que este protocolo existe para impedir.

- **Factual** — só existe um jeito certo: nome de coluna errado, assinatura desatualizada, arquivo movido. Corrija o spec agora e siga o ticket.
- **De design** — a correção reabre uma decisão com alternativas reais. Registre **no ticket** três coisas: o que o spec diz, o que o código mostra, por que conflitam. Depois **escale.** A decisão pertence a uma sessão de effort alto apontada para esse registro.

**Onde gravar cada um, por modo, está em [`references/erro-de-spec.md`](references/erro-de-spec.md)** — junto da métrica do passo 7, que só existe quando este passo dispara.

**Na dúvida, é design.** Classificar como factual e seguir é o caminho de menor resistência. O custo de escalar à toa é uma sessão; o de decidir design aqui é o bug que este protocolo existe para impedir.

## 4. Verificar

Evidência antes de alegação: rode as verificações e confira a saída antes de dizer que está pronto. São typecheck, testes e — quando o projeto os configura — lint e checagem de formatação. Descubra os comandos onde o projeto os declara: `package.json`, `Makefile`, `pyproject.toml`, CI. Projeto sem linter não ganha um aqui; comando ausente é resposta, não falha do ticket.

Rode a checagem em modo verificação (`--check`), nunca em modo correção (`--write`). Formatador reescrevendo arquivo aqui mistura mudança de estilo com a do ticket e polui o diff que o passo 5 vai revisar.

<invariante>

**Critério de aceite que afirma algo sobre um conjunto não se verifica pelo ramo que você editou.** Duas formas, que enganam por parecerem opostas:

- *todos* os membros obedecem — "sempre", "nenhum", "em qualquer fluxo";
- existe *um só* — "uma política só", "um único escritor", "o único formato".

Suíte verde prova que o caminho testado funciona, não que os outros obedecem.

Enumere os caminhos e diga o que viu em cada um. Havendo ADR que mapeie os escritores daquele campo, ele já é a lista, e o `grep` pelo nome do campo fecha o que faltar. Sem a enumeração, o `[x]` não é marcado: invariante marcada por amostragem é uma suposição virando fato conhecido, e o próximo ticket constrói em cima dela.

</invariante>

### Critério de conclusão

- [ ] Typecheck rodou e passou — saída conferida, não presumida
- [ ] A suíte completa rodou **uma vez** e passou
- [ ] Lint e formatação rodaram em `--check`, ou o projeto não os declara
- [ ] Todo critério de aceite do ticket está marcado, e os que afirmam algo sobre um conjunto vieram com a enumeração

## 5. Commit, revisar, amend

Nesta ordem. A revisão vem **depois** do commit:

1. **Commite.** Anote o SHA anterior (`git rev-parse HEAD`) antes de commitar — ele é o ponto fixo do passo seguinte.
2. **Revise** com `mattpocock-skills:code-review`, passando `<sha-anterior>` como ponto fixo. Use o nome com escopo: é assim que ela aparece na listagem, e o harness ainda tem um `/code-review` próprio, acionável só pelo usuário.
3. **Aplique o que couber via `--amend`**, mantendo **1 ticket = 1 commit**. Antes de qualquer `--amend`, duas conferências:
   - `git log -1` — o amend acerta o HEAD, não o commit que você tem em mente.
   - `git log @{u}..HEAD` — o push da branch é manual e fora desta skill, mas o operador pode ter pushado no meio. Vindo vazio, o commit já está no upstream e amendar reescreveria histórico publicado: os achados vão num commit novo, e o formato está em [`references/commit-de-excecao.md`](references/commit-de-excecao.md). Sem upstream configurado não houve push, e o amend é seguro.

A ordem importa. O `code-review` diffa `<ponto-fixo>...HEAD`, então só enxerga trabalho **commitado**. Invocado antes do commit, ele revisa o commit anterior ou nada — sem erro visível, com relatório de aparência normal.

São três as exceções à regra de um commit por ticket, e todas carregam marcador próprio: o `docs:` do passo 3, o `achados de <sha>` deste passo, e o `refactor: checkpoint` do passo 8.

### Critério de conclusão

- [ ] O SHA anterior foi anotado **antes** do commit
- [ ] O `code-review` rodou com esse SHA como ponto fixo, sobre trabalho já commitado
- [ ] `git log -1` conferido: o HEAD é o commit deste ticket
- [ ] `git log @{u}..HEAD` conferido antes do amend, ou o commit de exceção foi usado no lugar dele
- [ ] Todo achado da revisão foi aplicado ou descartado com motivo — nenhum pendente sem registro

## 6. Encerrar o ticket

Dois fatos que se confundem:

- **Feito** — o trabalho acabou e está commitado. É o que você sabe agora.
- **Fechado** — o código está na branch principal. Só é verdade depois do merge, e você não controla quando acontece.

Marque o primeiro; **deixe o segundo para o merge.** Fechar a issue no push mente sobre o estado do código, e é o que quebra o board de quem confia nele.

Na prática, por modo:

- **Arquivo `.md`:** o que separa feito de fechado é se o commit passa por PR ou branch de integração. Commit direto na principal → marque `Status: done`, ou o rótulo equivalente do `triage-labels.md`. Projeto que usa PR mesmo com tickets em arquivo → trate como tracker.
- **Tracker:** garanta que o commit carrega o trailer de referência (`Closes #<n>`) e mova o ticket para o estado de "aguardando merge" do projeto. Deixe o fechamento para o automático: GitHub e GitLab fecham sozinhos quando o commit chega na branch default.

<armadilha>

O fechamento automático nativo só dispara na **branch default**. Time que trabalha numa branch de integração (`development`) com a default em outra (`main`) vê a issue seguir aberta depois do commit; ela só fecha quando a integração sobe. Isso é esperado, não é bug.

Os verbos em português (`Fecha`, `Resolve`) não são reconhecidos nativamente por nenhuma das duas plataformas — só por CI própria.

</armadilha>

### Critério de conclusão

- [ ] O ticket está no estado que corresponde a *feito*, pelo modo do projeto
- [ ] O fechamento ficou por conta do merge — nenhuma issue fechada à mão

## 7. Métrica

Só se o passo 3 disparou. Onde gravar a linha e como commitá-la está em [`references/erro-de-spec.md`](references/erro-de-spec.md), que você já leu ao registrar o conflito.

## 8. Checkpoint de consistência

**Despachado por um `/ticket:run`?** Este passo não é seu: termine o passo 7, inclua `CHECKPOINT_DUE` no retorno caso o aviso do hook tenha chegado, e pare aí. O checkpoint pertence a quem enxerga a fila inteira — e subagent não despacha agent, então tentar aqui não falha com erro, falha em silêncio.

Em sessão manual, quem conta é o hook `runbook-checkpoint.py` (PostToolUse, roda sozinho depois de todo `git commit`). Ele avisa quando o ciclo de **5** commits de ticket vence, e traz o nome exato da sua tag e o comando a rodar — use-os como vieram.

O aviso chega no commit do passo 5.1, ainda antes da revisão e do amend. **Termine o passo 5 primeiro:** o checkpoint revisa o acumulado, e o commit deste ticket só está pronto depois do amend.

**O procedimento vive em [`references/checkpoint.md`](references/checkpoint.md) — leia-o quando o checkpoint vencer.** Ele cobre o ciclo escopado por operador, a conferência de que o hook está mesmo instalado, o disparo do agent e o fechamento do ciclo. Está fora daqui porque roda uma vez a cada cinco tickets: nas outras quatro, seria contexto carregado à toa.
