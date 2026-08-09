---
name: implement
description: "Executa um ticket do fluxo de implementação: reivindicação do ticket + implementação escopada + protocolo de erro de spec + verificação + commit/code-review/amend + encerramento + checkpoint de consistência a cada 5 tickets."
disable-model-invocation: true
---

# /ticket:implement

**Ticket desta sessão:** $ARGUMENTS

O argumento aponta o ticket e, se houver, o preâmbulo/spec obrigatório. Leia ambos antes de qualquer coisa. Escopo é sagrado: implemente **apenas** este ticket. Se o trabalho crescer, o excedente vira ticket novo.

**Pré-requisito:** o plugin `mattpocock-skills`. O `/tdd` do passo 2 e o `mattpocock-skills:code-review` do passo 5 vêm dele. Se qualquer um falhar por skill inexistente, pare e instrua a instalação — os comandos estão no README do plugin `ticket`. Improvisar um substituto é pior do que parar.

**Onde o ticket vive é decisão do projeto.** Leia `docs/agents/issue-tracker.md` primeiro: ele diz se os tickets são arquivos markdown ou issues de um tracker, e qual CLI usar. Toda vez que esta skill mandar escrever *no ticket*, é esse arquivo que decide se isso é editar um `.md` ou comentar numa issue. Se ele não existir, pergunte ao usuário onde vivem os tickets.

## 1. Reivindicar o ticket

**Bloqueadores antes de dono.** O `/to-tickets` grava em cada ticket quem o bloqueia. Confira antes de reivindicar. Bloqueador ainda aberto = ticket fora da frontier: **pare**, informe o usuário e pergunte qual pegar no lugar. Implementá-lo agora é construir sobre base que ainda não existe.

**O dono é o operador, nunca a sessão.** Você não é um ator no tracker: quem responde pelo ticket é o humano ao teclado.

Confira a atribuição antes de ler código, com o CLI que o `issue-tracker.md` definir (`gh issue view <n> --json assignees`, `glab issue view <n>`). Em modo arquivo a atribuição é a linha `Assignee:` no topo do `.md` — convenção deste fluxo, não do `to-tickets`. Repo que ainda não a tem trata o ticket como sem dono, e a linha nasce quando alguém assume.

Três casos, e só um segue em frente:

- **De outra pessoa** → **pare aqui.** Diga quem é o dono e pergunte ao usuário: assumir mesmo assim, ou trocar de ticket. A decisão é dele. Atribuição alheia costuma significar trabalho já em curso, e implementar por cima gera conflito de merge e trabalho jogado fora.
- **Sem dono** → atribua ao operador e siga. Em tracker, `--add-assignee @me` resolve para o usuário autenticado no CLI, que é ele. Em modo arquivo não há `@me`: o nome vem de `git config user.name`.
- **Já é do operador** → siga.

## 2. Implementar

Antes de escrever código, leia os ADRs e o glossário. Na convenção destas skills o glossário é o `CONTEXT.md` na raiz, e os ADRs ficam em `docs/adr/`. Cada sessão começa limpa e não viu os tickets anteriores: o que atravessa o `/clear` são esses registros. Decisão já tomada ali não se reabre aqui. Ticket que contradiz um ADR é conflito de spec — passo 3.

**Ticket que acrescenta um escritor a um campo governado por ADR muda o ADR.** Ler não basta. Leitura não produz a linha que o próximo ticket precisa encontrar, e o próximo ticket é uma sessão limpa que só tem o documento. O caso cai nos dois do passo 3, sem protocolo novo:

- O escritor **obedece** à regra já decidida — quem ganha no conflito, o que cada um faz quando não sabe o valor. Acrescentá-lo à lista do ADR é correção **factual**: entra no mesmo commit `docs:`, e o ticket segue.
- O escritor **não cabe** na regra — pede outro critério de desempate, ou o caso "não sabe" não estava previsto. Isso é **design**: registre no ticket, pare e escale.

Duas ressalvas, porque o roteamento para o passo 3 traz junto regras que **não** valem aqui:

- **ADR sempre commita, inclusive em tracker.** Editar o corpo da issue vale para o spec, que o `/to-spec` publica lá. O ADR mora em `docs/adr/` nos dois modos, então a correção é sempre um `docs:`.
- **Só o caso de design entra na métrica do passo 7.** Escritor que obedece à regra é evolução normal do código e não diz nada sobre a qualidade do spec; contá-lo infla o `spec-errors.md` com trabalho saudável. Escritor que exige critério novo é o portão de modelagem tendo saído incompleto — que é exatamente o que a métrica mede.

O portão do `/ticket:split` enumerou os escritores antes de a fila existir. Ticket que cria escritor sem devolver a informação ao ADR desfaz o portão um passo adiante, e o defeito reaparece no checkpoint, caro.

**Número de linha no ticket é pista; a âncora é o símbolo ou o trecho descrito.** Localize pelo alvo descrito, mesmo quando o número ainda bate. Alvo que não existe em lugar nenhum — símbolo renomeado, arquivo dividido, código já removido — não é ticket difícil: é o spec descrevendo um código que mudou, e o passo 3 trata.

Implemente restrito ao escopo deste ticket:

- Use `/tdd` nas costuras pré-acordadas, que vêm do spec/preâmbulo. Spec que não nomeia costura nenhuma é lacuna de spec: trate pelo passo 3, em vez de deixar o `/tdd` parar o fluxo para perguntar ao usuário.
- Enquanto trabalha, rode **só** typecheck e os testes do arquivo que está mexendo. A suíte completa é do passo 4 e roda **uma vez por ticket**: repeti-la aqui dobra a parte mais cara da fila sem descobrir nada novo.

O commit é o passo 5, depois da verificação e do protocolo de erro de spec.

## 3. Protocolo de erro de spec

Spec que conflita com a realidade do código para o trabalho e vai para triagem. Implementar por cima do conflito é o que este protocolo existe para impedir.

- **Factual** — só existe um jeito certo: nome de coluna errado, assinatura desatualizada, arquivo movido. Corrija o spec agora e siga o ticket.
- **De design** — a correção reabre uma decisão com alternativas reais. Registre **no ticket** três coisas: o que o spec diz, o que o código mostra, por que conflitam. Depois **pare o ticket** e informe o usuário. A decisão pertence a uma sessão de effort alto apontada para esse registro.

**Onde gravar cada um, por modo, está em [`references/erro-de-spec.md`](references/erro-de-spec.md)** — junto da métrica do passo 7, que só existe quando este passo dispara.

**Na dúvida, é design.** Classificar como factual e seguir é o caminho de menor resistência. O custo de escalar à toa é uma sessão; o de decidir design aqui é o bug que este protocolo existe para impedir.

## 4. Verificar

Evidência antes de alegação: rode as verificações e confira a saída antes de dizer que está pronto. São typecheck, testes e — quando o projeto os configura — lint e checagem de formatação. Descubra os comandos onde o projeto os declara: `package.json`, `Makefile`, `pyproject.toml`, CI. Projeto sem linter não ganha um aqui; comando ausente é resposta, não falha do ticket.

Rode a checagem em modo verificação (`--check`), nunca em modo correção (`--write`). Formatador reescrevendo arquivo aqui mistura mudança de estilo com a do ticket e polui o diff que o passo 5 vai revisar.

<invariante>

**Critério de aceite que afirma algo sobre um conjunto não se verifica pelo ramo que você editou.** O teste é o conjunto. Ele tem duas formas, que enganam por parecerem opostas:

- *todos* os membros obedecem — "sempre", "nenhum", "em qualquer fluxo";
- existe *um só* — "uma política só", "um único escritor", "o único formato".

As duas afirmam a mesma coisa sobre o conjunto inteiro, e nenhuma se verifica olhando o membro que você mexeu. Suíte verde prova que o caminho testado funciona, não que os outros obedecem.

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
   - O commit ainda não subiu. O push da branch é manual e fora desta skill, mas o operador pode ter pushado no meio. Se `git log @{u}..HEAD` vier vazio, o commit já está no upstream, e amendar reescreveria histórico publicado: aplique os achados num commit novo e registre a exceção à regra de 1 commit. Sem upstream configurado não houve push, e o amend é seguro.

O commit de exceção leva **`achados de <sha-curto>`** no assunto, com o sha do commit revisado:

```
refactor(escopo): achados de 9d281b74 — <resumo>
```

O marcador não é enfeite. O contador do passo 8 conta commits, não tickets: sem ele, este commit passaria por um segundo ticket e fecharia o ciclo cedo. É o mesmo papel da palavra `checkpoint` no commit do passo 8, e ainda diz *qual* commit foi revisado.

A ordem importa. O `code-review` diffa `<ponto-fixo>...HEAD`, então só enxerga trabalho **commitado**. Invocado antes do commit, ele revisa o commit anterior ou nada — sem erro visível, com relatório de aparência normal.

Commits `docs:` do passo 3 e `refactor:` do passo 8 são exceções à regra de um commit por ticket.

## 6. Encerrar o ticket

Dois fatos que se confundem:

- **Feito** — o trabalho acabou e está commitado. É o que você sabe agora.
- **Fechado** — o código está na branch principal. Só é verdade depois do merge, e você não controla quando acontece.

Marque o primeiro; **deixe o segundo para o merge.** Fechar a issue no push mente sobre o estado do código, e é o que quebra o board de quem confia nele.

Na prática, por modo:

- **Arquivo `.md`:** o que separa feito de fechado é se o commit passa por PR ou branch de integração. Commit direto na principal → marque `Status: done`, ou o rótulo equivalente do `triage-labels.md`. Projeto que usa PR mesmo com tickets em arquivo → trate como tracker.
- **Tracker:** garanta que o commit carrega o trailer de referência (`Closes #<n>`) e mova o ticket para o estado de "aguardando merge" do projeto. **Não feche à mão:** GitHub e GitLab fecham sozinhos quando o commit chega na branch default.

<armadilha>

O fechamento automático nativo só dispara na **branch default**. Time que trabalha numa branch de integração (`development`) com a default em outra (`main`) vê a issue seguir aberta depois do commit; ela só fecha quando a integração sobe. Isso é esperado, não é bug.

Os verbos em português (`Fecha`, `Resolve`) não são reconhecidos nativamente por nenhuma das duas plataformas — só por CI própria.

</armadilha>

### Critério de conclusão

- [ ] O ticket está no estado que corresponde a *feito*, pelo modo do projeto
- [ ] Nenhuma issue foi fechada à mão

## 7. Métrica

Só se o passo 3 disparou. Onde gravar a linha e como commitá-la está em [`references/erro-de-spec.md`](references/erro-de-spec.md), que você já leu ao registrar o conflito.

## 8. Checkpoint de consistência

**Despachado por um `/ticket:run`?** Este passo não é seu: termine o passo 7, inclua `CHECKPOINT_DUE` no retorno caso o aviso do hook tenha chegado, e pare aí. O checkpoint pertence a quem enxerga a fila inteira — e subagent não despacha agent, então tentar aqui não falha com erro, falha em silêncio.

Em sessão manual, quem conta é o hook `runbook-checkpoint.py` (PostToolUse, roda sozinho depois de todo `git commit`). Ele avisa quando o ciclo de **5** commits de ticket vence, e traz o nome exato da sua tag e o comando a rodar — use-os como vieram.

O aviso chega no commit do passo 5.1, ainda antes da revisão e do amend. **Termine o passo 5 primeiro:** o checkpoint revisa o acumulado, e o commit deste ticket só está pronto depois do amend.

**O procedimento vive em [`references/checkpoint.md`](references/checkpoint.md) — leia-o quando o checkpoint vencer.** Ele cobre o ciclo escopado por operador, a conferência de que o hook está mesmo instalado, o disparo do agent e o fechamento do ciclo. Está fora daqui porque roda uma vez a cada cinco tickets: nas outras quatro, seria contexto carregado à toa.
