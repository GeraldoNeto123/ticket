---
name: run
description: "Orquestra a fila de tickets de uma feature, um subagent fresco por ticket."
disable-model-invocation: true
---

# /ticket:run

**Argumento desta sessão:** $ARGUMENTS

O argumento aponta o spec/preâmbulo da feature e onde vivem os tickets dela (diretório, rótulo ou issue-mãe). Você é o **orquestrador**: despacha um subagent fresco por ticket, sequencialmente, e nunca implementa nada você mesmo. Cada ticket foi dimensionado pelo `/to-tickets` para caber numa janela limpa — é o subagent que ganha essa janela; se a implementação acontecesse aqui, o terceiro ticket já rodaria sobre o contexto acumulado dos dois primeiros, exatamente o que o fluxo existe para evitar.

Um ticket de cada vez, sempre: tickets são fatias verticais e colidem nos arquivos de junção (rotas, schema, registro de DI), então paralelismo de implementação fica de fora por design.

**Pré-requisito:** o plugin `mattpocock-skills` — o `/tdd` e o `code-review` que o brief nomeia vêm dele. É a única dependência de upstream, e é pelo **nome público** das skills, que é interface estável.

**Escalar**, onde este arquivo disser, é parar a fila e entregar a decisão ao usuário — nunca seguir com um palpite.

## 1. Montar a fila

Leia `docs/agents/issue-tracker.md` para saber o modo (arquivo ou tracker) e o CLI. Liste os tickets da feature com o campo **Blocked by** de cada um e monte a **frontier**: os tickets cujos bloqueadores estão todos done. Trabalhe sempre a frontier; quando um ticket termina, recalcule.

Ticket com dono alheio (`Assignee:` de outra pessoa, no formato que o `issue-tracker.md` definir) sai da frontier — **escale**: atribuição alheia costuma significar trabalho já em curso, e implementar por cima gera conflito de merge e trabalho jogado fora. O dono dos demais é o operador, nunca a sessão: quem responde pelo ticket é o humano ao teclado.

Leia o spec só o suficiente para saber referenciá-lo. **Nos prompts de dispatch, passe caminhos e referências** — o conteúdo do spec e dos tickets fica de fora. Tudo que você cola num prompt fica residente no seu contexto até o fim da fila; um caminho custa uma linha.

## 2. Ledger

Antes do primeiro dispatch, crie `.scratch/ticket-run/<slug-da-feature>.md` com uma linha por ticket: referência, status, SHA (quando houver), observação de uma linha. Atualize **após cada ticket**, não em lote.

Todo checkpoint que rodar ganha **linha própria** no ledger, com o SHA em que o ciclo fechou. É ela que separa um ciclo do seguinte, e é dela que sai a contagem do passo 3.

O ledger é seu mapa de recuperação: os SHAs que ele nomeia existem no git mesmo quando seu contexto já não lembra deles. Se esta sessão for compactada no meio da fila, o ledger é o que permite retomar sem reexecutar nada.

**Se o ledger já existe, esta fila está sendo retomada — e retomar não é recomeçar.** Uma sessão que morre no meio de um ticket deixa um estado que nenhum retorno de subagent descreveu: o commit pode existir sem o ticket estar `done`, o `Assignee` pode ter sido escrito e não commitado. Antes do primeiro dispatch, cruze três fontes para cada ticket da frontier — a linha do ledger, o `git log` do intervalo e o `Status:` do próprio ticket. Quatro desfechos:

- **Sem commit e sem `done`** — execução normal, dispatch como sempre.
- **Com commit e sem `done`** — **retomada**. O trabalho existe; reimplementá-lo produz um segundo commit do mesmo ticket e joga fora o primeiro. O dispatch precisa dizer isso na primeira linha: *não reimplemente; o commit `<sha>` já entrega este ticket; confira-o, retome do ponto em que parou e use `<sha>^` como ponto fixo da revisão*. Sem o ponto fixo explícito, a revisão do subagent diffa contra o lugar errado e passa em branco.
- **`done`** — sai da frontier, não vira dispatch.
- **Ambíguo** — o commit toca mais do que o ticket, há mais de um commit para ele, ou não existe ledger porque a sessão morreu antes de criá-lo: **escale.** Aqui é onde menos se sabe o que aconteceu com o repositório, e portanto a pior hora para adivinhar. Marcar como `done` um ticket cuja revisão nunca rodou custa tanto quanto reimplementar por cima.

Reconciliado, registre no ledger o que você concluiu de cada um antes de despachar — a reconciliação também é trabalho que se perde se a sessão cair de novo.

Ele é memória de **execução**, não conhecimento do projeto — os fatos duráveis já vivem no git e nos tickets — portanto **não é versionado**. Garanta isso antes de criá-lo: se `git check-ignore .scratch/ticket-run` falhar, acrescente `.scratch/ticket-run/` ao `.git/info/exclude` (ignore local do clone; não use `.gitignore`, que geraria um commit de ruído no repo).

## 3. O loop

Para cada ticket da frontier, despache **um** subagent com o brief abaixo, preenchido — prosa inline, sem mandar ler arquivo nenhum de skill:

<brief-de-dispatch>

> Implemente o ticket `<referência>`, em `<caminho ou nº>`. Spec em `<caminho>`. Leia ambos antes de qualquer coisa, e também `CONTEXT.md` e os ADRs de `docs/adr/` que tocarem a área. Escopo restrito ao ticket: excedente vira ticket novo, não código.
>
> Use a skill `mattpocock-skills:tdd` nas costuras nomeadas no spec. Enquanto trabalha, rode só typecheck e os testes do arquivo. Ao fim, rode a suíte completa **uma vez** — a menos que o repo declare cadência própria (ex.: `docs/agents/testing.md` ou seção do `CLAUDE.md`); havendo declaração, siga-a no lugar desta regra default.
>
> Anote o SHA do `HEAD`, commite, revise com a skill `mattpocock-skills:code-review` usando esse SHA como ponto fixo e aplique o que couber via `--amend`. **Um ticket = um commit.**
>
> Spec conflitando com o código: erro **factual** (nome, assinatura, caminho — só existe um jeito certo) corrija no spec e siga; erro **de design**, registre no ticket o que o spec diz, o que o código mostra e por que conflitam, devolva `SPEC_DESIGN` e não implemente por cima. Na dúvida, é design.
>
> Terminando, marque o ticket como feito conforme `docs/agents/issue-tracker.md` — e não feche issue à mão: fechar é do merge.
>
> Devolva **apenas**: `STATUS` (`DONE` | `SPEC_DESIGN` | `BLOCKED`) · SHA do commit, se houver · testes em uma linha · até três linhas de observação.

</brief-de-dispatch>

Status possíveis e o que fazer com cada um:

- **`DONE`** — registre no ledger e siga para o próximo da frontier. Não pause para aprovação entre tickets: este é o modo autônomo; quem quer acompanhar de perto roda o `/implement` do `mattpocock-skills` à mão, um ticket por sessão.
- **`SPEC_DESIGN`** — o subagent encontrou erro de spec de design, registrou o conflito no ticket e parou. A decisão pertence a uma sessão de effort alto apontada para esse registro — **essa sessão é esta**. Pare o loop, apresente o registro ao usuário e espere a decisão dele. Decidido, o ticket volta à frontier.
- **`BLOCKED`** — dono alheio, dependência externa, ou o subagent travou sem progresso. **Escale:** bloqueio é informação, e a fila espera a resposta na ordem em que está.
- **Qualquer outra coisa** — retorno fora do contrato, subagent que morreu, erro não classificado. Trate como `BLOCKED`: registre no ledger o que voltou **literalmente**, sem interpretar, e **escale**. Um retorno que você não reconhece é a situação em que menos se sabe o que aconteceu com o repositório, e portanto a pior hora para adivinhar um status e seguir. Reexecutar o ticket também é decisão do usuário: o subagent pode ter commitado antes de morrer.

Todo desfecho — inclusive os ruins — vira linha no ledger. Descarte silencioso é proibido: um ticket que "sumiu" da fila é um bug seu.

### Quando o checkpoint vence

**Quem conta é você, pelo ledger.** Cinco tickets fechados desde a última linha de checkpoint (ou desde o início da fila) fecham um ciclo, e o próximo dispatch só sai depois dele.

Vencido, **invoque a skill `ticket:checkpoint`** — aqui no orquestrador, nunca num subagent. O checkpoint é seu por dois motivos: subagent não despacha agent, e as duas entradas que a skill precisa só você tem — o intervalo (o SHA da última linha de checkpoint do ledger) e o lote (referência + SHA das linhas do ciclo).

Se o repo declarar (passo 3) que a suíte completa fica reservada pro checkpoint em vez de rodar por ticket, é aqui — no orquestrador, antes de invocar a skill — que ela roda; a `ticket:checkpoint` é estritamente leitura e não executa teste nenhum.

Registre o resultado em linha própria no ledger e siga. Achados novos vão para o contêiner de checkpoint da demanda, fora da fila, e nascem `needs-triage`: **nunca** entram nesta frontier. A frontier é a foto do início da fila; quem a amplia é o usuário, via triagem, nunca o checkpoint.

## 4. Encerramento

Frontier vazia = fila encerrada. Se o último lote não fechou um ciclo de checkpoint, invoque a `ticket:checkpoint` uma última vez antes do resumo — fila encerrada com acumulado não revisado é trabalho pela metade. Se a cadência declarada pelo repo (passo 3) reserva a suíte completa pro checkpoint, rode-a aqui também, cobrindo o que fechou depois do último ciclo.

Monte o resumo final **a partir do ledger**, não de memória: tickets concluídos com SHAs, observações acumuladas, achados registrados pelos checkpoints, e o que ficou bloqueado ou aguardando decisão. Se sobraram tickets inalcançáveis (bloqueador nunca resolvido, ciclo de dependência), aponte-os explicitamente — são a primeira coisa que o usuário precisa destravar.
