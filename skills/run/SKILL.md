---
name: run
description: "Orquestra a fila de tickets de uma feature, um subagent fresco por ticket."
disable-model-invocation: true
---

# /ticket:run

**Argumento desta sessão:** $ARGUMENTS

O argumento aponta o spec/preâmbulo da feature e onde vivem os tickets dela (diretório, rótulo ou issue-mãe). Você é o **orquestrador**: despacha um subagent fresco por ticket, sequencialmente, e nunca implementa nada você mesmo. Cada ticket foi dimensionado pelo `/to-tickets` para caber numa janela limpa — é o subagent que ganha essa janela; se a implementação acontecesse aqui, o terceiro ticket já rodaria sobre o contexto acumulado dos dois primeiros, exatamente o que o fluxo existe para evitar.

Um ticket de cada vez é o **default**: tickets são fatias verticais e colidem nos arquivos de junção (rotas, schema, registro de DI), e duas sessões no mesmo checkout ainda corrompem o cache de build uma da outra.

A exceção é estreita e precisa ser **provada, não suposta**. Se ao montar a frontier você conseguir particioná-la em clusters que não compartilham arquivo nenhum — não "parecem de áreas diferentes", mas você conferiu os caminhos que cada ticket nomeia —, esses clusters podem correr em paralelo, **um `git worktree` por cluster, obrigatório**. Dentro de cada cluster segue valendo um ticket de cada vez. Sem worktree o paralelismo não é permitido: o que quebra primeiro é o diretório de build compartilhado, não o merge.

Vale a pena quando o cluster menor é grande o bastante para pagar o setup — na prática, dois ou mais tickets. Na dúvida, série: o custo de errar o particionamento (conflito, trabalho jogado fora, cache corrompido no meio da fila) é maior que o tempo que ele economiza.

**Pré-requisito:** o plugin `mattpocock-skills` — o `/tdd` que o brief nomeia vem dele. É a única dependência de upstream, e é pelo **nome público** da skill, que é interface estável.

**Uma invariante governa todo este arquivo: quem despacha agente é você, nunca um subagent.** Agente-dentro-de-agente é onde o trabalho assíncrono se perde — a camada de dentro encerra a vez esperando um resultado que já chegou, e a fila para até alguém cutucar por fora. Por isso a revisão (passo 3.1) e o checkpoint (passo 3.3) moram aqui, e o subagent do ticket só implementa.

**Escalar**, onde este arquivo disser, é parar a fila e entregar a decisão ao usuário — nunca seguir com um palpite.

## 1. Montar a fila

Leia `docs/agents/issue-tracker.md` para saber o modo (arquivo ou tracker) e o CLI. Liste os tickets da feature com o campo **Blocked by** de cada um e monte a **frontier**: os tickets cujos bloqueadores estão todos done. Trabalhe sempre a frontier; quando um ticket termina, recalcule.

Ticket com dono alheio (`Assignee:` de outra pessoa, no formato que o `issue-tracker.md` definir) sai da frontier — **escale**: atribuição alheia costuma significar trabalho já em curso, e implementar por cima gera conflito de merge e trabalho jogado fora. O dono dos demais é o operador, nunca a sessão: quem responde pelo ticket é o humano ao teclado.

Leia o spec só o suficiente para saber referenciá-lo. **Nos prompts de dispatch, passe caminhos e referências** — o conteúdo do spec e dos tickets fica de fora. Tudo que você cola num prompt fica residente no seu contexto até o fim da fila; um caminho custa uma linha.

## 2. Ledger

Antes do primeiro dispatch, crie `.scratch/ticket-run/<slug-da-feature>.md` com uma linha por ticket: referência, status, SHA (quando houver), **início, fim e duração**, observação de uma linha. Atualize **após cada ticket**, não em lote.

Carimbe o horário no dispatch e na volta do `DONE` — um `date` de uma linha, não estimativa de memória. Duração por ticket é a primeira coisa que se pergunta de uma fila autônoma ("por que demorou tanto?") e a única que não dá para reconstruir depois: as durações que os subagents reportam misturam trabalho e espera de formas que não reconciliam entre si, e o `git log` só sabe a hora do commit, nunca a do dispatch.

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

Antes do primeiro dispatch, resolva **você** as **quatro** convenções do repo que o brief carrega preenchidas:

1. **Onde nasce teste novo** — qual camada, com o comando dela. Repo que migrou de camada mantém o runner antigo instalado e verde por um bom tempo, e subagent que só recebe "rode os testes" continua escrevendo na camada que está sendo aposentada: cada ticket vira dívida nova, escrita no lugar errado por instrução sua. Sem declaração no repo, olhe os scripts do `package.json` (ou equivalente) **e a data** dos testes commitados — o que é recente manda, não o que é numeroso.
2. **A cadência de teste** (`docs/agents/testing.md` ou seção do `CLAUDE.md`; sem declaração, a default é suíte completa uma vez ao fim do ticket). Camadas diferentes têm cadências diferentes — a barata roda sempre, a cara roda por raio de alcance —, então o brief costuma precisar de **dois** comandos, não de um.
3. **A convenção de done do tracker** (`docs/agents/issue-tracker.md` e o mapeamento de labels/estados, se o repo tiver um).
4. **Onde mora a quarentena da demanda** — o contêiner que o `references/achados.md` da `ticket:checkpoint` define (pasta da feature ou issue-mãe). É para lá que vai o excedente que o implementador encontrar, e o brief precisa do endereço concreto.

O subagent recebe a instrução **concreta** — comandos e alvos nomeados, o estado exato em que a issue termina, o caminho da quarentena —, nunca o documento pra interpretar: interpretação delegada é onde a cadência declarada vira suíte rodada à toa e o fechamento sai no estado errado.

Para cada ticket da frontier, despache **um** subagent com o brief abaixo, preenchido — prosa inline, sem mandar ler arquivo nenhum de skill:

<brief-de-dispatch>

> Implemente o ticket `<referência>`, em `<caminho ou nº>`. Spec em `<caminho>`. Leia ambos antes de qualquer coisa, e também `CONTEXT.md` e os ADRs de `docs/adr/` que tocarem a área.
>
> Escopo restrito ao ticket. Excedente que você encontrar **não vira código e não vira ticket**: vai para a quarentena da demanda, em `<contêiner que você resolveu no passo 3>`, nascendo `needs-triage`. Abrir issue na hora enche board, relatório e métrica com trabalho que ninguém decidiu que existe — e o achado que você abriria já pode estar lá, registrado por outra sessão que também passou por perto. Quem promove quarentena a ticket é humano, em triagem.
>
> Use a skill `mattpocock-skills:tdd` nas costuras nomeadas no spec. **Teste novo nasce em `<camada + comando que você resolveu no passo 3>`** — não na camada que o repo está aposentando, mesmo que ela tenha mais testes e mais exemplos para copiar. Enquanto trabalha, rode só typecheck e os testes do arquivo. Ao fim: `<instrução-de-teste que você resolveu da cadência do repo — comandos e alvos nomeados, ex.: "rode `npm run test:unit` sempre e `cypress/e2e/foo.cy.js` só se o diff tocar X; a suíte completa fica com o orquestrador">`.
>
> **Rode todo comando em primeiro plano.** Nada de `run_in_background` nem de monitor, e não deixe shell de espera pendurado: teste é a etapa em que mais se espera, e é despachando espera em segundo plano que um agente encerra a vez e não volta. Aceite o tempo de parede.
>
> Anote o SHA do `HEAD` **antes** de commitar — é o ponto fixo da revisão — e commite. **Um ticket = um commit.**
>
> **Não revise, e não marque o ticket como feito ainda.** A revisão é despachada por quem te chamou; ela volta pra você e você a aplica. Encerre aqui devolvendo `REVIEW_PENDING`.
>
> **Critério de aceite que você não atendeu é obrigatório declarar** — inclusive, e principalmente, quando você julga que não dava para atender. Não vale omitir porque a justificativa parece boa: `REVIEW_PENDING` é status de sucesso, e AC omitido fecha o ticket com ele em aberto e ninguém sabendo. Declarar não é pedir permissão nem parar a sua vez: você segue normalmente, e quem decide se a lacuna é aceitável é quem te chamou.
>
> Spec conflitando com o código: erro **factual** (nome, assinatura, caminho — só existe um jeito certo) corrija no spec e siga; erro **de design**, registre no ticket o que o spec diz, o que o código mostra e por que conflitam, devolva `SPEC_DESIGN` e não implemente por cima. Na dúvida, é design.
>
> Devolva **apenas**: `STATUS` (`REVIEW_PENDING` | `SPEC_DESIGN` | `BLOCKED`) · SHA do ponto fixo e SHA do commit · testes em uma linha · **critérios de aceite não atendidos, ou `nenhum`** · até três linhas de observação.

</brief-de-dispatch>

### 3.1 A revisão, e a volta ao mesmo subagent

`REVIEW_PENDING` significa que existe commit e falta revisá-lo. Três movimentos, nesta ordem.

**Sempre dois revisores**, um por eixo, numa mensagem só (duas chamadas do Agent tool), subagent `general-purpose`. Eles rodam em paralelo, então dois custam o mesmo relógio que um — dimensionar a revisão pelo tamanho do diff economiza quase nada e erra com frequência: numa fila real, um diff de 134 linhas revisado por um agente só devolveu 8 achados, contra 6 de um diff de 199 linhas com revisão dupla. Passe a cada um: o comando de diff (`git diff <ponto-fixo>...HEAD`, três pontos), a lista de commits, o **caminho** de `references/revisao.md` desta skill dizendo qual seção cobrir (`## Eixo Standards` ou `## Eixo Spec`), e — para quem cobre Spec — os caminhos do spec e do ticket. Mande cada um **escrever o relatório** em `.scratch/ticket-run/review-<referência>-<eixo>.md` e devolver **uma linha**: `<n> achados · <caminho>`.

Se o retorno do ticket declarou **critério de aceite não atendido** com justificativa de viabilidade ("não há suíte pra estender", "exigiria infra nova"), peça ao revisor do eixo Spec um **parecer explícito e concreto** sobre isso, além do resto: é viável e proporcional, e se for, o que precisaria ser feito. Justificativa de inviabilidade costuma confundir *não existe exemplo desta tela* com *não existe padrão para escrever um* — numa fila real, o revisor derrubou uma dessas apontando um precedente literal no mesmo repo, e a cobertura saiu no amend.

Você não lê `references/revisao.md` nem os relatórios. Passa caminhos, recebe duas linhas. É o mesmo princípio do passo 1: o que você cola no seu contexto fica lá até o fim da fila, e uma fila longa não sobrevive a dois relatórios por ticket.

Antes de despachar, confirme que o ponto fixo resolve (`git rev-parse`) e que o diff não é vazio — ref errada tem que falhar aqui, não dentro de dois revisores.

**Devolva os relatórios ao subagent do ticket**, com `SendMessage`, endereçando o mesmo agent que devolveu `REVIEW_PENDING`. Ele ainda tem o contexto do que implementou e por quê — que é justamente o que os revisores não têm e o que você não deve carregar. Peça: *leia o(s) relatório(s) em `<caminho(s)>`, aplique o que couber via `--amend` sobre `<sha>`, mantendo um ticket = um commit; em seguida `<instrução-de-done que você resolveu da convenção do repo — o estado exato em que a issue termina: fechada ou aberta, com quais labels>`; devolva `DONE` · SHA final · o que aplicou e o que descartou, com o porquê, em até três linhas.*

Achado que o subagent descartar é informação, não fracasso — registre a justificativa no ledger junto com o resto.

**Se o subagent do ticket não responder** ao `SendMessage` (morreu, ou o retorno vem fora do contrato), não reimplemente e não aplique você mesmo: despache um subagent fresco dizendo que o commit `<sha>` já entrega o ticket, que a revisão está no(s) caminho(s), e que a tarefa dele é só aplicar e fechar. É a mesma retomada do passo 2, com os relatórios já prontos.

### 3.2 Status possíveis

Um ticket passa por dois retornos: o do dispatch e o da volta da revisão. Os status abaixo valem para os dois.

- **`REVIEW_PENDING`** — caminho normal do primeiro retorno. Registre o SHA no ledger **antes** de despachar a revisão: o commit já existe, e se esta sessão cair no meio do passo 3.1 é essa linha que evita reimplementá-lo. Siga para 3.1.
  - **Se o retorno declarar critério de aceite não atendido**, a decisão é **sua**, e não do implementador: ou você manda atender (no `SendMessage` do 3.1, junto com os relatórios, dizendo explicitamente que é decisão do orquestrador), ou você aceita a lacuna — e aí ela vai para o ledger **e** para o comentário de fechamento da issue, com o porquê. O que não pode acontecer é o ticket fechar com AC em aberto sem ninguém ter decidido isso. Registre também quando a decisão for aceitar: é ela que o usuário precisa achar depois, se discordar.
- **`DONE`** — só chega depois da revisão aplicada. Registre no ledger, com o SHA final e o que foi descartado, e siga para o próximo da frontier. Não pause para aprovação entre tickets: este é o modo autônomo; quem quer acompanhar de perto roda o `/implement` do `mattpocock-skills` à mão, um ticket por sessão.
- **`SPEC_DESIGN`** — o subagent encontrou erro de spec de design, registrou o conflito no ticket e parou. A decisão pertence a uma sessão de effort alto apontada para esse registro — **essa sessão é esta**. Pare o loop, apresente o registro ao usuário e espere a decisão dele. Decidido, o ticket volta à frontier.
- **`BLOCKED`** — dono alheio, dependência externa, ou o subagent travou sem progresso. **Escale:** bloqueio é informação, e a fila espera a resposta na ordem em que está.
- **Qualquer outra coisa** — retorno fora do contrato, subagent que morreu, erro não classificado. Trate como `BLOCKED`: registre no ledger o que voltou **literalmente**, sem interpretar, e **escale**. Um retorno que você não reconhece é a situação em que menos se sabe o que aconteceu com o repositório, e portanto a pior hora para adivinhar um status e seguir. Reexecutar o ticket também é decisão do usuário: o subagent pode ter commitado antes de morrer.

Todo desfecho — inclusive os ruins — vira linha no ledger. Descarte silencioso é proibido: um ticket que "sumiu" da fila é um bug seu.

### 3.3 Quando o checkpoint vence

**Quem conta é você, pelo ledger.** Cinco tickets fechados desde a última linha de checkpoint (ou desde o início da fila) fecham um ciclo, e o próximo dispatch só sai depois dele.

Vencido, **invoque a skill `ticket:checkpoint`** — aqui no orquestrador, nunca num subagent. O checkpoint é seu pela invariante do topo deste arquivo, e porque as duas entradas que a skill precisa só você tem — o intervalo (o SHA da última linha de checkpoint do ledger) e o lote (referência + SHA das linhas do ciclo).

Se o repo declarar (passo 3) que a suíte completa fica reservada pro checkpoint em vez de rodar por ticket, é aqui — no orquestrador, antes de invocar a skill — que ela roda; a `ticket:checkpoint` é estritamente leitura e não executa teste nenhum.

Registre o resultado em linha própria no ledger e siga. Achados novos vão para o contêiner de checkpoint da demanda, fora da fila, e nascem `needs-triage`: **nunca** entram nesta frontier. A frontier é a foto do início da fila; quem a amplia é o usuário, via triagem, nunca o checkpoint.

## 4. Encerramento

Frontier vazia = fila encerrada. Acumulado de **3+ tickets** desde a última linha de checkpoint: invoque a `ticket:checkpoint` uma última vez antes do resumo — fila encerrada com um lote desse tamanho não revisado é trabalho pela metade. Com 1–2 tickets, o ciclo inteiro custa mais do que o lote vale: registre no ledger uma linha **`Pendente de checkpoint`** com referência e SHA de cada ticket, e siga pro resumo — a contagem do passo 3.3 parte da última linha de checkpoint, então uma fila futura da mesma demanda absorve esses tickets no primeiro ciclo dela por construção, e o marcador de commit do §1 da `ticket:checkpoint` garante o intervalo mesmo se o ledger se perder. Se a cadência declarada pelo repo (passo 3) reserva teste pro checkpoint, ele acompanha o checkpoint: roda quando ele roda.

Monte o resumo final **a partir do ledger**, não de memória: tickets concluídos com SHAs, observações acumuladas, achados registrados pelos checkpoints, e o que ficou bloqueado ou aguardando decisão. Se sobraram tickets inalcançáveis (bloqueador nunca resolvido, ciclo de dependência), aponte-os explicitamente — são a primeira coisa que o usuário precisa destravar.
