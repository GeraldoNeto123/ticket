---
name: implement
description: "Executa um ticket do fluxo de implementação: reivindicação do ticket + implementação escopada + protocolo de erro de spec + verificação + commit/code-review/amend + encerramento + checkpoint de consistência a cada 5 tickets."
disable-model-invocation: true
---

# /ticket:implement

**Ticket desta sessão:** $ARGUMENTS

O argumento aponta o ticket e, se houver, o preâmbulo/spec obrigatório. Leia ambos antes de qualquer coisa. Escopo é sagrado: implemente **apenas** este ticket — se o trabalho crescer, o excedente vira ticket novo, não escopo deste.

**Pré-requisito:** o plugin `mattpocock-skills` — o `/tdd` do passo 2 e o `mattpocock-skills:code-review` do passo 5 vêm dele. Se a invocação de qualquer um falhar por skill inexistente, não improvise um substituto: pare e instrua a instalação (comandos no README do plugin `ticket`).

**Onde o ticket vive é decisão do projeto, não desta skill.** Leia `docs/agents/issue-tracker.md` primeiro: ele diz se os tickets são arquivos markdown, issues do GitHub, do GitLab ou de outro tracker, e qual CLI usar (`gh`, `glab`, ...). Toda vez que esta skill mandar escrever *no ticket*, é esse arquivo que define se isso é editar um `.md` ou comentar numa issue. Se ele não existir, pergunte ao usuário onde vivem os tickets — não presuma arquivo.

## 1. Reivindicar o ticket

**Bloqueadores antes de dono.** O `/to-tickets` grava em cada ticket quem o bloqueia — campo `Blocked by` no `.md`, links de bloqueio nativos no tracker. Confira antes de reivindicar: se algum bloqueador ainda está aberto, **pare** — o ticket está fora da frontier, e implementá-lo agora é construir sobre base que ainda não existe. Informe o usuário e pergunte qual ticket pegar no lugar.

**Antes de ler código.** Confira a quem o ticket está atribuído, do jeito que o `issue-tracker.md` definir:

```bash
gh issue view <n> --json assignees        # GitHub
glab issue view <n>                       # GitLab
```

Em modo arquivo, use a linha `Assignee:` no topo do `.md`; se o repo ainda não tem essa convenção, trate como sem dono e crie a linha ao assumir.

**O dono é sempre a pessoa que está operando, nunca a sessão.** Você não é um ator no tracker: quem responde pelo ticket é o humano ao teclado. Em tracker, `@me` já resolve para o usuário autenticado no CLI, que é ele. Em modo arquivo não há `@me`, então leia a identidade do git:

```bash
git config user.name     # é esse nome que vai na linha Assignee
```

Três casos, e só um deles segue em frente:

- **De outra pessoa** → **pare aqui.** Não implemente, não atribua a ninguém. Diga quem é o dono e pergunte ao usuário qual caminho: assumir mesmo assim ou trocar de ticket. A decisão é dele — atribuição alheia costuma significar trabalho já em curso, e implementar por cima gera conflito de merge e trabalho jogado fora.
- **Sem dono** → atribua ao operador e siga:

  ```bash
  gh issue edit <n> --add-assignee @me          # GitHub
  glab issue update <n> --assignee @me          # GitLab
  # arquivo: **Assignee:** <git config user.name>
  ```

- **Já é do operador** → siga.

## 2. Implementar

Antes de escrever código, leia os ADRs e o glossário do projeto — na convenção destas skills o glossário é o `CONTEXT.md` na raiz, e os ADRs ficam em `docs/adr/` se o projeto não documentar outro lugar. Cada sessão começa limpa e não viu os tickets anteriores — o que atravessa o `/clear` são esses registros. Decisão já tomada ali não se reabre aqui; se o ticket contradiz um ADR, isso é conflito de spec (passo 3).

Implemente restrito ao escopo deste ticket:

- Use `/tdd` nas costuras pré-acordadas — elas vêm do spec/preâmbulo, onde o `/to-spec` as registrou. Se o spec não nomeia costura nenhuma, isso é lacuna de spec: trate pelo passo 3 em vez de deixar o `/tdd` parar o fluxo para perguntar ao usuário.
- Rode typecheck e os testes do arquivo com frequência durante o trabalho.
- Rode a suite completa uma vez ao final.

**Não commite aqui.** O commit é o passo 5, depois da verificação e do protocolo de erro de spec.

## 3. Protocolo de erro de spec

Se o spec conflitar com a realidade do código, pare e triageie — nunca implemente por cima do conflito:

- **Factual** (só existe um jeito certo: nome de coluna errado, assinatura desatualizada, arquivo movido): corrija o spec agora e siga o ticket. Em modo arquivo isso é editar o doc e commitar `docs:` separado; em tracker o spec é uma issue (o `/to-spec` publica lá), então edite o corpo dela — sem commit.
- **De design** (a correção reabre uma decisão com alternativas reais): registre **no ticket** três coisas — o que o spec diz, o que o código mostra, por que conflitam. Em modo arquivo isso é editar o `.md`; em tracker, um comentário na issue (`gh issue comment`, `glab issue note`). Depois **pare o ticket** e informe o usuário: a decisão pertence a uma sessão de effort alto apontada para esse registro. Não decida design aqui.

**Na dúvida, é design.** Classificar como factual e seguir é o caminho de menor resistência — resista: o custo de escalar à toa é uma sessão; o de decidir design aqui é o bug que este protocolo existe para impedir.

## 4. Verificar

Evidência antes de alegação: rode as verificações de verdade e confira a saída antes de dizer que está pronto. São typecheck, testes e — quando o projeto os configura — lint e checagem de formatação. Descubra os comandos onde o projeto os declara (`package.json`, `Makefile`, `pyproject.toml`, CI) em vez de assumir um stack: projeto sem linter não ganha um aqui, e o comando ausente é resposta, não falha do ticket.

Rode a checagem em modo verificação, nunca em modo correção (`--check`, não `--write`): formatador reescrevendo arquivo no passo 4 mistura mudança de estilo com a do ticket e polui o diff que o passo 5 vai revisar.

## 5. Commit, revisar, amend

Nesta ordem — a revisão vem **depois** do commit, não antes:

1. **Commite.** Anote o SHA anterior (`git rev-parse HEAD`) antes de commitar; ele é o ponto fixo do passo seguinte.
2. **Revise** com `mattpocock-skills:code-review` passando `<sha-anterior>` como ponto fixo. Use o nome com escopo: é assim que ela aparece na listagem (skills de plugin são registradas como `plugin:skill`), e o harness ainda tem um `/code-review` próprio, acionável só pelo usuário.
3. **Aplique o que couber via `--amend`**, mantendo **1 ticket = 1 commit**. Antes de qualquer `--amend`, duas conferências:
   - `git log -1` — o amend acerta o HEAD, não o commit que você tem em mente.
   - O commit ainda não subiu. O push da branch é **manual e fora desta skill**, mas nada impede o operador de ter pushado no meio: se `git log @{u}..HEAD` vier vazio, o commit já está no upstream e amendar reescreveria histórico publicado — aplique os achados num commit novo e registre a exceção à regra de 1 commit. Sem upstream configurado não houve push; amend seguro.

A ordem importa: o `code-review` diffa `<ponto-fixo>...HEAD`, então só enxerga trabalho **commitado**. Invocado antes do commit ele não tem ponto fixo válido e revisa o commit anterior ou nada — sem erro visível, com relatório de aparência normal.

Commits `docs:` do passo 3 e `refactor:` do passo 8 são exceções à regra de um commit por ticket.

## 6. Encerrar o ticket

Separe dois fatos que costumam ser confundidos:

- **Feito** — o trabalho acabou e está commitado. É o que você sabe agora.
- **Fechado** — o código está na branch principal. Isso só é verdade depois do merge, e você não controla quando acontece.

Marque o primeiro; **deixe o segundo para o merge**. Fechar a issue no push mente sobre o estado do código, e é o que quebra o board de quem confia nele.

Na prática, por modo:

- **Arquivo `.md`:** o que separa feito de fechado não é onde o ticket vive, e sim se o commit passa por PR/branch de integração. Commit direto na branch principal → feito *é* o fim: marque `Status: done` (ou o rótulo equivalente no `triage-labels.md`) e pronto. Se o projeto usa PR mesmo com tickets em arquivo, trate como tracker: marque o equivalente a "aguardando merge" e só `done` depois do merge.
- **Tracker:** garanta que o commit carrega o trailer de referência (`Closes #<n>`, `Fecha #<n>`) e mova o ticket para o estado de "aguardando merge" que o projeto usar. **Não feche à mão** — GitHub e GitLab fecham sozinhos quando o commit chega na branch default, e projetos com branch de integração podem ter CI cobrindo o resto.

Uma armadilha que vale conhecer: o fechamento automático nativo só dispara na **branch default**. Se o time trabalha numa branch de integração (`development`) e a default é outra (`main`), a issue fica aberta depois do commit e só fecha quando a integração sobe. Isso é esperado, não é bug — e os verbos em português (`Fecha`, `Resolve`) não são reconhecidos nativamente por nenhuma das duas plataformas, só por CI própria.

## 7. Métrica

Se o passo 3 disparou, registre uma linha: data, ticket, tipo (factual | design), resumo de uma linha.

Onde gravar depende do modo, e o arquivo é sempre versionado — a métrica é sobre a qualidade do spec ao longo do tempo, então precisa sobreviver ao ticket:

- **Tickets como arquivo:** `spec-errors.md` ao lado deles (ex.: `.scratch/<feature>/issues/spec-errors.md`).
- **Tickets num tracker:** `docs/spec-errors.md` no repo, com o número da issue na linha. Não sirva a métrica só como comentário na issue — comentário espalhado não se soma.

O commit da linha acompanha o desfecho: no caso **factual**, ela entra no mesmo `docs:` do passo 3; no caso **design**, commit `docs:` próprio antes de parar o ticket — parar sem commitar a métrica é perdê-la.

## 8. Checkpoint de consistência

**Se um orquestrador `/ticket:run` despachou você, este passo não é seu.** Termine o passo 7, inclua `CHECKPOINT_DUE` no seu retorno caso o aviso do hook tenha chegado, e pare por aí. O checkpoint pertence a quem enxerga a fila inteira — e subagent não despacha agent, então tentar aqui não falha com erro, falha em silêncio.

A contagem é feita pelo hook `runbook-checkpoint.py` (PostToolUse, roda sozinho depois de todo `git commit`) — você não precisa contar. Ele avisa quando o limite de **5** commits de ticket é atingido, e também quando a tag do ciclo está ausente, legada ou ficou para trás. Os avisos trazem o nome exato da sua tag e o comando a rodar; use-os como vieram (na dúvida, `git tag -l 'runbook-checkpoint*'` lista as existentes).

A tag do ciclo é **escopada por operador**: `runbook-checkpoint-<slug>`, com o slug derivado da parte local do `git config user.email` (minúsculas, sequências não alfanuméricas viram um `-`). Cada operador tem ciclo próprio e o hook conta só os commits dele — é o que permite mais de uma pessoa rodar o fluxo no mesmo repo sem uma sobrescrever a tag da outra.

**Confira por conta própria.** O hook é infraestrutura da máquina, não do repo — e ausente, falha em silêncio: o checkpoint simplesmente nunca é pedido. Por isso, ao fim do passo 5, se nenhum aviso chegou:

```bash
git log --oneline --no-merges --author="$(git config user.email)" \
  -E --invert-grep --grep='^(docs|chore|refactor|ci|style|test)[(:]' \
  "runbook-checkpoint-<slug>..HEAD"
```

O filtro e o limiar acompanham os do hook de propósito — conferência que conta diferente do contador acusa problema onde não há. **5 linhas ou mais sem nenhum aviso ter chegado** = hook não instalado nesta máquina: rode o checkpoint manualmente e avise o usuário para reinstalar o plugin `ticket`, que é de onde o hook vem. Se o comando falhar dizendo que a revisão não existe, é a tag que falta — o ciclo nunca foi aberto, e o caso está tratado no arquivo de referência abaixo.

O aviso chega no commit do passo 5.1, ainda antes da revisão e do amend. **Termine o passo 5 primeiro** — o checkpoint revisa o acumulado, e o commit deste ticket só está pronto depois do amend.

**O procedimento vive em `references/checkpoint.md`, no diretório desta skill — leia-o quando o checkpoint vencer.** Ele cobre o disparo do agent, o que fazer com cada uma das quatro classes do relatório, onde os achados ficam em quarentena e como fechar o ciclo movendo a tag. Está fora daqui porque roda uma vez a cada cinco tickets: nas outras quatro, seria contexto carregado à toa.
