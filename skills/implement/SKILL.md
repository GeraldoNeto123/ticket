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

A contagem é feita pelo hook `runbook-checkpoint.py` (PostToolUse, roda sozinho depois de todo `git commit`) — você não precisa contar. Ele avisa quando o limite de **5** commits de ticket é atingido, e também quando a tag sumiu ou ficou para trás.

A tag do ciclo é **escopada por operador**: `runbook-checkpoint-<slug>`, com o slug derivado da parte local do `git config user.email` (minúsculas, sequências não alfanuméricas viram um `-`). Cada operador tem ciclo próprio e o hook conta só os commits dele — é o que permite mais de uma pessoa rodar o fluxo no mesmo repo sem uma sobrescrever a tag da outra. Os avisos do hook trazem o nome exato da sua tag; use-o como veio (na dúvida, `git tag -l 'runbook-checkpoint-*'` lista as existentes).

O hook é infraestrutura **da máquina, não do repo** — e ausente, falha em silêncio: o checkpoint simplesmente nunca é pedido. Por isso, ao fim do passo 5, se a sua tag existe e nenhum aviso chegou, confira por conta própria:

```bash
git log --oneline --no-merges --author="$(git config user.email)" "runbook-checkpoint-<slug>..HEAD"
```

3+ commits de ticket acumulados sem aviso = hook não instalado nesta máquina. Rode o checkpoint manualmente e avise o usuário para reinstalar o plugin `ticket` — o hook faz parte dele.

O aviso chega no commit do passo 5.1, ainda antes da revisão e do amend. **Termine o passo 5 primeiro** — o checkpoint revisa o acumulado, e o commit deste ticket só está pronto depois do amend.

Ao receber o aviso, dispare o agent `checkpoint-reviewer` passando o intervalo (`runbook-checkpoint-<slug>..HEAD`) e **onde vivem os tickets e o spec** — o diretório, em modo arquivo; o repo/projeto e o CLI de leitura, em modo tracker.

Com o relatório em mãos, correções pequenas viram um único commit `refactor:` seu — com a palavra `checkpoint` na mensagem (ex.: `refactor: checkpoint <sha..sha> — <resumo>`): é por ela que o hook detecta um checkpoint que rodou sem a tag ter sido movida.

O resto do relatório **nunca entra na fila da feature**. A regra existe por experiência: quando todo achado virava ticket na mesma pasta numerada, a fila crescia mais rápido do que era consumida (13 tickets viraram 39) e o "done" virou alvo móvel. A fila converge para o escopo original; achado fica em quarentena até um humano promovê-lo.

Em modo arquivo, tudo que o checkpoint produz vive num `checkpoint/` único na **raiz da árvore de tickets** — a pasta que contém as pastas de feature, não a da feature da vez (tickets em `.scratch/<feature>/issues/` → `.scratch/checkpoint/`). Um intervalo de commits atravessa duas features com frequência, e ancorar o registro na feature do HEAD fragmenta a memória e cega o dedup, que passaria a enxergar só a feature atual. Em modo tracker não há pasta: o equivalente é o rótulo `checkpoint`, que já é global no projeto. Por classe do relatório:

1. **Defeitos reais** → registro de achado **fora da fila**. Em modo arquivo: um arquivo por achado em `<raiz-dos-tickets>/checkpoint/<slug-da-âncora>.md` — sem número da sequência da feature. Em modo tracker: issue com rótulos `checkpoint` + `needs-triage`. Nos dois modos o status de nascença é **sempre** `needs-triage` — nunca `ready-for-agent`: promover achado a item de fila é decisão humana, via triagem, não sua. Antes de criar, confirme a duplicata você mesmo:

   ```bash
   grep -ril "<âncora>" <raiz-dos-tickets>/checkpoint/         # arquivo
   gh issue list --search "<âncora>" --state all --limit 20    # GitHub
   glab issue list --search "<âncora>" --all                   # GitLab
   ```

   Se já existe: acrescente ao registro existente o que o novo checkpoint adiciona e **não crie outro**. Corpo mínimo de cada achado:

   ```markdown
   ## Achado
   <uma frase: o defeito, do ponto de vista de quem sofre o efeito>

   ## Onde
   <arquivo por ocorrência, apontando símbolo ou trecho — sem número de linha, que envelhece>

   ## Por que nenhum ticket isolado viu
   <a justificativa de ter vindo do checkpoint>

   ## Âncora de busca
   `<termo exato: código de erro, símbolo, constraint>`

   **Status:** needs-triage

   ---
   Origem: checkpoint-reviewer · intervalo `<sha..sha>`
   ```

2. **Inconsistências sem defeito** → uma linha cada em `<raiz-dos-tickets>/checkpoint/registro/<sha-curto>..<sha-curto>.md`: **um arquivo por checkpoint**, nomeado pelo intervalo revisado (sem inconsistência nenhuma, não crie o arquivo). Não abrem arquivo de achado nem issue — são memória para a triagem humana e para o dedup do próximo checkpoint, que já as alcança pelo `grep -r` acima.

   Uma entrada dessas sai por **um único motivo: ter virado ticket** — e quem a remove é o humano que a promoveu na triagem, nunca você e nunca o checkpoint seguinte. Não há expiração por idade, por volume nem por "parecer obsoleta": entrada antiga que ninguém resolveu é precisamente o que o registro existe para manter à vista. Encontrar entradas repetidas de checkpoints anteriores é o funcionamento esperado, não sujeira a limpar. O rastro sobrevive do outro lado — o ticket promovido carrega a origem do achado.

3. **Propostas de processo** → reporte ao usuário no encerramento, textualmente. Mudam a skill ou o agent, nunca viram ticket do projeto — achado meta que vira ticket é o fluxo gerando trabalho sobre a própria burocracia.

4. **Respeite o que é issue e o que não é.** Se o `issue-tracker.md` do projeto separa issue (unidade de trabalho) de spec/plano/ADR (documento), um achado que é documento vai para `docs/`, não para o tracker.

Por fim **mova e publique** a tag — as duas coisas, sempre:

```bash
git tag -f "runbook-checkpoint-<slug>" && git push -f origin "runbook-checkpoint-<slug>"
```

O `push -f` aqui só alcança a **sua** tag — as dos outros operadores ficam intactas.

Sem o push a tag fica só na máquina: um clone novo não a encontra e o acumulado inteiro passa por revisado sem nunca ter sido revisado. Exceção: repo sem remoto (comum em modo arquivo) — aí só mova a tag; não há para onde publicar e o push falharia.

Se a sua tag não existir, **não a crie em silêncio**. Tente `git fetch origin --tags` primeiro; se ela não estiver no remoto, pergunte ao usuário se deve revisar o acumulado ou recomeçar do HEAD. Caso especial: repo que usava o fluxo antes do escopo por operador tem a tag legada `runbook-checkpoint` sem sufixo — o hook detecta e instrui a migração (`git tag runbook-checkpoint-<slug> runbook-checkpoint`), que preserva o intervalo em vez de descartá-lo.
