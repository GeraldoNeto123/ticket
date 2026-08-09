---
name: run
description: "Executa a fila de tickets de uma feature em sequência: um subagent fresco por ticket rodando /ticket:implement, ledger de progresso, checkpoint no orquestrador e escalada explícita — nada é descartado em silêncio."
disable-model-invocation: true
---

# /ticket:run

**Argumento desta sessão:** $ARGUMENTS

O argumento aponta o spec/preâmbulo da feature e onde vivem os tickets dela (diretório, rótulo ou issue-mãe). Você é o **orquestrador**: despacha um subagent fresco por ticket, sequencialmente, e nunca implementa nada você mesmo. Cada ticket foi dimensionado pelo `/to-tickets` para caber numa janela limpa — é o subagent que ganha essa janela; se a implementação acontecesse aqui, o terceiro ticket já rodaria sobre o contexto acumulado dos dois primeiros, exatamente o que o fluxo existe para evitar.

Paralelismo é proibido nesta versão, por design: tickets são fatias verticais e colidem nos arquivos de junção (rotas, schema, registro de DI). Um de cada vez, sempre.

## 1. Montar a fila

Leia `docs/agents/issue-tracker.md` para saber o modo (arquivo ou tracker) e o CLI. Liste os tickets da feature com o campo **Blocked by** de cada um e monte a **frontier**: os tickets cujos bloqueadores estão todos done. Trabalhe sempre a frontier; quando um ticket termina, recalcule.

Leia o spec só o suficiente para saber referenciá-lo. **Nos prompts de dispatch, passe caminhos e referências** — o conteúdo do spec e dos tickets fica de fora. Tudo que você cola num prompt fica residente no seu contexto até o fim da fila; um caminho custa uma linha.

## 2. Ledger

Antes do primeiro dispatch, crie `.scratch/ticket-run/<slug-da-feature>.md` com uma linha por ticket: referência, status, SHA (quando houver), observação de uma linha. Atualize **após cada ticket**, não em lote.

Todo checkpoint que rodar ganha **linha própria** no ledger. É ela que separa um ciclo do seguinte, e é dela que sai a contagem do passo 3.

O ledger é seu mapa de recuperação: os SHAs que ele nomeia existem no git mesmo quando seu contexto já não lembra deles. Se esta sessão for compactada no meio da fila, o ledger é o que permite retomar sem reexecutar nada.

**Se o ledger já existe, esta fila está sendo retomada — e retomar não é recomeçar.** Uma sessão que morre no meio de um ticket deixa um estado que nenhum retorno de subagent descreveu: o commit pode existir sem o ticket estar `done`, o `Assignee` pode ter sido escrito e não commitado. Antes do primeiro dispatch, cruze três fontes para cada ticket da frontier — a linha do ledger, o `git log` do intervalo e o `Status:` do próprio ticket. Quatro desfechos:

- **Sem commit e sem `done`** — execução normal, dispatch como sempre.
- **Com commit e sem `done`** — **retomada**. O trabalho existe; reimplementá-lo produz um segundo commit do mesmo ticket e joga fora o primeiro. O dispatch precisa dizer isso na primeira linha: *não reimplemente; o commit `<sha>` já entrega este ticket; confira-o, retome do passo em que parou e use `<sha>^` como ponto fixo da revisão do passo 5*. Sem o ponto fixo explícito, a revisão do subagent diffa contra o lugar errado e passa em branco.
- **`done`** — sai da frontier, não vira dispatch.
- **Ambíguo** — o commit toca mais do que o ticket, há mais de um commit para ele, ou não existe ledger porque a sessão morreu antes de criá-lo: **pare e pergunte.** Aqui é onde menos se sabe o que aconteceu com o repositório, e portanto a pior hora para adivinhar. Marcar como `done` um ticket cuja revisão nunca rodou custa tanto quanto reimplementar por cima.

Reconciliado, registre no ledger o que você concluiu de cada um antes de despachar — a reconciliação também é trabalho que se perde se a sessão cair de novo.

Ele é memória de **execução**, não conhecimento do projeto — os fatos duráveis já vivem no git e nos tickets — portanto **não é versionado**. Garanta isso antes de criá-lo: se `git check-ignore .scratch/ticket-run` falhar, acrescente `.scratch/ticket-run/` ao `.git/info/exclude` (ignore local do clone; não use `.gitignore`, que geraria um commit de ruído no repo).

## 3. O loop

Primeiro, resolva o caminho da skill `implement`. Ela mora ao lado desta, em `<diretório-base desta skill>/../implement/SKILL.md`; o diretório-base aparece no cabeçalho quando esta skill é invocada. Resolva para caminho absoluto uma vez e reuse em todos os dispatches — **conferindo antes de cada um que o arquivo ainda existe** (`test -f`).

O caminho carrega a versão do plugin (`.../ticket/<versão>/skills/...`). Um `plugin update` no meio da fila poda o diretório da versão antiga: o caminho que você resolveu no primeiro ticket morre sem aviso, e os dispatches seguintes mandam o subagent ler um arquivo que não está mais lá. Já aconteceu.

Se sumiu, **não tente re-resolver pelo diretório-base que veio no cabeçalho** — ele aponta para a mesma pasta podada e está tão morto quanto. Ache a versão nova por fora do plugin:

```bash
# rota primária: o manifesto diz exatamente qual versão está instalada
python3 -c "import json,os;d=json.load(open(os.path.expanduser('~/.claude/plugins/installed_plugins.json')));print(d['plugins']['ticket@ticket'][0]['installPath']+'/skills/implement/SKILL.md')"

# se o manifesto não abrir, o cache desempata — com `sort -V`, nunca `tail -1` puro
ls -d ~/.claude/plugins/cache/ticket/ticket/*/skills/implement/SKILL.md | sort -V | tail -1
```

O `sort -V` não é preciosismo: em ordem alfabética `1.10.1` vem **antes** de `1.9.0`, então `ls | tail -1` devolve a versão velha com cara de resposta certa — e o resto da fila roda contra instruções desatualizadas sem nada acusar.

Achou: siga com o caminho novo e anote no ledger que a versão trocou no meio da fila. Não achou: pare e pergunte, em vez de despachar sem instruções.

O subagent **lê esse arquivo, não invoca a skill**: `implement` é porta de entrada humana (`disable-model-invocation`) e o Skill tool recusa invocação vinda de modelo — inclusive de subagents. Ler o arquivo entrega as mesmas instruções pelo caminho que a política permite, no padrão task-brief: "leia isto primeiro; são seus requisitos".

Para cada ticket da frontier, despache **um** subagent com um prompt mínimo:

- Leia `<caminho absoluto da implement/SKILL.md>` primeiro e siga-o como suas instruções de trabalho. Onde o arquivo diz `$ARGUMENTS`, vale: ticket `<referência>`, spec em `<caminho do spec>`. **Se o arquivo não existir, devolva `BLOCKED` dizendo exatamente isso e não implemente nada** — sem ele você não tem os requisitos, e um ticket implementado de memória é pior do que um ticket não implementado.
- Execute o fluxo e **pare no fim do passo 7** — o passo 8 (checkpoint) é do orquestrador. Se o aviso do hook chegar no commit, termine o passo 5 normalmente e inclua `CHECKPOINT_DUE` no retorno.
- Retorne **apenas** o contrato abaixo. Sem diff, sem histórico, sem narrativa.

<contrato-de-retorno>

- [ ] `STATUS` — uma das opções da lista abaixo, escrita literalmente
- [ ] SHA do commit, se houver
- [ ] Resumo dos testes em **uma** linha
- [ ] Observações em até **três** linhas

</contrato-de-retorno>

Status possíveis e o que fazer com cada um:

- **`DONE`** — registre no ledger e siga para o próximo da frontier. Não pause para aprovação entre tickets: este é o modo autônomo; quem quer acompanhar de perto roda `/ticket:implement` à mão.
- **`SPEC_DESIGN`** — o subagent encontrou erro de spec de design, registrou o conflito no ticket e parou (passo 3 da implement). A skill de lá manda escalar para "uma sessão de effort alto apontada para esse registro" — **essa sessão é esta**. Pare o loop, apresente o registro ao usuário e espere a decisão dele. Decidido, o ticket volta à frontier.
- **`BLOCKED`** — dono alheio, dependência externa, ou o subagent travou sem progresso. Pare e pergunte ao usuário: bloqueio é informação, e a fila espera a resposta na ordem em que está.

- **Qualquer outra coisa** — retorno fora do contrato, subagent que morreu, erro não classificado. Trate como `BLOCKED`: registre no ledger o que voltou **literalmente**, sem interpretar, e pare para perguntar. Um retorno que você não reconhece é a situação em que menos se sabe o que aconteceu com o repositório, e portanto a pior hora para adivinhar um status e seguir. Reexecutar o ticket também não é decisão sua: o subagent pode ter commitado antes de morrer.

Todo desfecho — inclusive os ruins — vira linha no ledger. Descarte silencioso é proibido: um ticket que "sumiu" da fila é um bug seu.

### Quando o checkpoint vence

**Quem conta é você, pelo ledger.** Cinco tickets fechados desde a última linha de checkpoint (ou desde o início da fila) fecham um ciclo, e o próximo dispatch só sai depois dele.

Um `CHECKPOINT_DUE` que volte de um subagent **confirma** a contagem; a ausência dele não diz nada. O aviso vem do hook `runbook-checkpoint.py`, que só fala com a sessão que de fato entrou no fluxo — e o subagent chega à `implement` **lendo o arquivo**, não invocando a skill, então pode não casar esse filtro. O hook também é infraestrutura da máquina: numa máquina sem ele, aviso nenhum chega, nunca. Contar no ledger é o que faz o ciclo vencer nos dois casos.

Vencido, **você** roda o passo 8 aqui no orquestrador, seguindo o `references/checkpoint.md` do diretório da skill `implement` (ao lado do `SKILL.md` que você já resolveu para dispatch): dispare o agent `checkpoint-reviewer` com o intervalo, o local dos tickets e o **lote** — as linhas de ledger (referência + SHA) dos tickets fechados neste ciclo, que só você tem —, aplique correções pequenas num `refactor: checkpoint ...`, registre os achados fora da fila e mova a tag. O checkpoint é seu por dois motivos: subagent não despacha agent, e o acumulado é responsabilidade de quem enxerga a fila inteira.

Registre o resultado no ledger e siga. Achados novos vão para o contêiner de checkpoint da demanda (pasta `checkpoint/` irmã de `issues/` em modo arquivo; comentário na issue pai em modo tracker), fora da fila, e nascem `needs-triage`: **nunca** entram nesta frontier. A frontier é a foto do início da fila; quem a amplia é o usuário, via triagem, nunca o checkpoint.

## 4. Encerramento

Frontier vazia = fila encerrada. Se o último lote não fechou um ciclo de checkpoint, rode o passo 8 uma última vez antes do resumo — fila encerrada com acumulado não revisado é trabalho pela metade.

Monte o resumo final **a partir do ledger**, não de memória: tickets concluídos com SHAs, observações acumuladas, tickets novos abertos pelos checkpoints, e o que ficou bloqueado ou aguardando decisão. Se sobraram tickets inalcançáveis (bloqueador nunca resolvido, ciclo de dependência), aponte-os explicitamente — são a primeira coisa que o usuário precisa destravar.
