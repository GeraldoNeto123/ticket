# Procedimento do checkpoint de consistência

Leia este arquivo quando o passo 8 da `/ticket:implement` vencer — o hook avisou,
ou a conferência manual acusou o acumulado. Ele não vive no `SKILL.md` porque o
checkpoint roda uma vez a cada cinco tickets: nas outras quatro seria peso morto
no contexto.

Antes de qualquer coisa, confirme que o passo 5 terminou. O aviso chega no commit
do passo 5.1, ainda antes da revisão e do amend, e o checkpoint revisa o
acumulado — que só está completo quando o commit deste ticket está.

## 1. Disparar a revisão

Dispare o agent `checkpoint-reviewer` passando três coisas:

- o intervalo, exatamente como o aviso o nomeou (tipicamente
  `runbook-checkpoint-<slug>..HEAD`);
- **onde vivem os tickets e o spec** — o diretório, em modo arquivo; o
  repo/projeto e o CLI de leitura, em modo tracker;
- **o lote** — a referência de cada ticket fechado no intervalo com o SHA do
  commit que o entregou. Num `/ticket:run`, o ledger já tem as duas colunas por
  linha; numa sessão manual, `git log --oneline <intervalo>` dá a lista, e em
  tracker o trailer `Closes #<n>` nomeia a issue de cada commit.

O lote é o que o revisor não consegue reconstruir tão bem quanto você: sem ele
sabe *que* código mudou, não *a mando de qual ticket*. É a diferença entre um
achado que atravessa três tickets do lote e um que não atravessa nenhum — código
que o intervalo passou perto sem tocar, que ele marca `fora do lote` no
relatório. Débito antigo entra por aí, e é você quem decide o que fazer com ele.

Ele devolve um relatório em quatro listas e não altera nada. O que fazer com cada
lista é o resto deste arquivo.

## 2. Correções pequenas

Viram **um único** commit `refactor:` seu, com a palavra `checkpoint` na
mensagem:

```
refactor: checkpoint <sha..sha> — <resumo>
```

A palavra importa, e por dois motivos: é por ela que o hook detecta um checkpoint
que rodou sem a tag ter sido movida, e é por ela que o **próximo** checkpoint
subtrai este commit do que vai revisar. Sem a palavra, o ciclo seguinte revisa a
saída deste e reporta como achado novo o que você já classificou. O mesmo vale
para o `docs(checkpoint):` do passo 4. Esse commit e os `docs:` do passo 3 são as
exceções à regra de um commit por ticket.

## 3. Defeitos reais → achado **fora da fila**

O resto do relatório **nunca entra na fila da feature**. A regra existe por
experiência: quando todo achado virava ticket na mesma pasta numerada, a fila
crescia mais rápido do que era consumida (13 tickets viraram 39) e o "done" virou
alvo móvel. A fila converge para o escopo original; achado fica em quarentena até
um humano promovê-lo.

Tudo que o checkpoint produz vive **na demanda de onde veio**, num contêiner
separado da fila. Os dois modos têm a mesma forma — pasta da feature ↔ issue pai,
arquivo ↔ comentário:

- **Modo arquivo:** `.scratch/<feature>/checkpoint/` — irmã de `issues/`, não
  dentro dela. Um arquivo por achado, `<slug-da-âncora>.md`, sem número da
  sequência da feature: numeração é da fila, e achado não é fila.
- **Modo tracker:** um **comentário na issue pai** da demanda, com os rótulos
  `checkpoint` + `needs-triage` aplicados **ao pai** (é por eles que a busca do
  dedup acha os contêineres). Achado não abre issue: nasce `needs-triage` e boa
  parte morre em `wontfix`, então abrir issue na detecção enche board, relatório
  e métrica de sprint com trabalho que ninguém decidiu que existe. A issue nasce
  na **promoção**, quando um humano decidiu.

Escopar por demanda é o que permite mais de um dev no mesmo repo: features
diferentes escrevem em pastas diferentes e cada um tria o que é seu. Um contêiner
único no projeto colocaria todo mundo no mesmo arquivo — e o ciclo do checkpoint
já é escopado por operador, então o contêiner global desfaria uma partição que o
resto do fluxo mantém.

**Onde o achado mora e onde o dedup procura são coisas diferentes** — não confunda
uma com a outra. O achado mora na demanda; a busca do passo seguinte varre
**todas** as demandas. É essa separação que dá escopo sem perder memória: um
intervalo de commits atravessa duas features com frequência, e o dedup que
enxergasse só a feature da vez reabriria o mesmo achado a cada lote.

**Se a demanda não tem issue pai, pare e pergunte.** O `/to-tickets` trata o
`## Parent` como opcional, então o caso é real. Não crie o pai por conta própria:
inventar estrutura no tracker de alguém é surpresa, e a decisão de como a demanda
se organiza é do usuário, não do checkpoint. Reporte os achados no encerramento
para não perdê-los enquanto ele decide.

Nos dois modos o status de nascença é **sempre** `needs-triage` — nunca
`ready-for-agent`: promover achado a item de fila é decisão humana, via triagem,
não sua.

### Critério de promoção

A quarentena só serve se a saída dela tiver régua. Sem régua, promover vira
decisão de gosto tomada com a fila à vista — e a fila cresce: numa etapa real,
49 tickets viraram 88, com 37 nascendo **depois** do veredito de fechamento, e
apenas 4 dos 88 morreram `wontfix`, num desenho cujo pressuposto é que a maioria
morre ali.

Um achado sai da quarentena e vira ticket numerado **só** se:

1. **produz dado errado para o cliente** — um caminho alcançável que grava,
   apaga ou exibe valor incorreto. O teste é "alguém sofre o efeito", não
   "poderia ser melhor"; **ou**
2. **já recorreu** — a mesma âncora aparece no registro de **dois checkpoints
   diferentes**.

Todo o resto morre `wontfix` **no ato da triagem**, e a entrada permanece onde
está.

O teste (2) é o que separa estrutura de gosto, e é por ele que a âncora precisa
ser exata: recorrência é contagem, não impressão. Na etapa 6 ele teria promovido
"decide pela cópia pré-lock" (4 recorrências) e "escritor apaga campo que não
conhece" (2, em colunas diferentes) — as duas famílias que motivaram um ADR — sem
promover "quatro estilos de classificação de erro do SDK", que apareceu uma vez e
nunca produziu dado errado.

Quando for você a triar, é esta a régua e não há terceira porta: achado que não
passa em (1) nem em (2) você marca `wontfix` e deixa onde está. Propor promoção
fora do critério reabre exatamente o buraco que ele fecha.

Antes de criar, confirme a duplicata você mesmo — sempre sobre **todos** os
contêineres, nunca só o da demanda da vez:

```bash
# arquivo — o glob atravessa as features; sem ele, o dedup cega
grep -ril "<âncora>" .scratch/*/checkpoint/

# tracker — os pais rotulados são os contêineres; leia os comentários de cada um
gh issue list   --label checkpoint --state all --json number --jq '.[].number'
glab issue list --label checkpoint --all
# depois, por pai:
gh issue view <n> --comments | grep -i "<âncora>"
glab issue view <n> --comments | grep -i "<âncora>"
```

Duas etapas em vez de uma busca só porque **nenhum dos dois CLIs procura dentro de
comentário**: o `--search` do `glab` cobre apenas título e descrição, e o do `gh`
depende de qualificador de busca que nem sempre alcança. Listar os pais pelo
rótulo e ler os comentários é determinístico e funciona igual nas duas
plataformas.

Se já existe: acrescente ao registro existente o que o novo checkpoint adiciona e
**não crie outro**. Corpo mínimo de cada achado:

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
Origem: checkpoint-reviewer · intervalo `<sha..sha>` · atravessa <tickets do lote, ou `fora do lote`>
```

## 4. Inconsistências sem defeito → registro

Uma linha cada, no mesmo contêiner da demanda e **agrupadas por intervalo**. Vale aqui a mesma regra de endereço do achado: símbolo ou trecho, nunca `arquivo:linha` — o registro é o artefato de vida mais longa do fluxo, porque só sai quando alguém o promove, e portanto é onde a linha tem mais tempo para deixar de corresponder.

- **Modo arquivo:** `.scratch/<feature>/checkpoint/registro/<sha-curto>..<sha-curto>.md`
  — um arquivo por checkpoint, nomeado pelo intervalo revisado.
- **Modo tracker:** um comentário na issue pai, um por checkpoint, com o intervalo
  no cabeçalho.

Sem inconsistência nenhuma, não crie nada. Não abrem arquivo de achado nem issue —
são memória para a triagem humana e para o dedup do próximo checkpoint, que já as
alcança pelas buscas acima.

Em modo arquivo, o que os §3 e §4 escreveram entra num commit de assunto
`docs(checkpoint): <resumo>` — **um só**, cobrindo achados e registro. O prefixo
é o que faz o próximo ciclo subtrair este commit do conjunto que revisa, pelo
mesmo motivo que a palavra `checkpoint` cumpre no commit do passo 2. Em modo
tracker não há commit: achado e registro são comentários na issue pai.

Uma entrada dessas sai por **um único motivo: ter virado ticket pelo critério de
promoção do §3** — e quem a remove é o humano que a promoveu na triagem, nunca
você e nunca o checkpoint seguinte. Não há expiração por idade, por volume nem
por "parecer obsoleta": entrada antiga que ninguém resolveu é precisamente o que
o registro existe para manter à vista, e é ela que torna o teste (2) do critério
contável — expurgar por idade apagaria a evidência de recorrência antes de a
segunda ocorrência chegar. Encontrar entradas repetidas de checkpoints anteriores é o
funcionamento esperado, não sujeira a limpar. O rastro sobrevive do outro lado —
o ticket promovido carrega a origem do achado.

## 5. Propostas de processo → ao usuário, textualmente

Reporte no encerramento. Mudam a skill ou o agent, nunca viram ticket do
projeto — achado meta que vira ticket é o fluxo gerando trabalho sobre a própria
burocracia.

## 6. Respeite o que é issue e o que não é

Se o `issue-tracker.md` do projeto separa issue (unidade de trabalho) de
spec/plano/ADR (documento), um achado que é documento vai para `docs/`, não para o
tracker.

## 7. Fechar o ciclo: mover a tag

**Depois dos commits que este checkpoint produziu** — o `refactor: checkpoint` do
§2 e o `docs(checkpoint):` do §4. A ordem das seções acima é a ordem de execução,
e a tag é o último passo por uma razão que se observa: movida antes, os commits
do próprio ciclo caem no intervalo seguinte, e o hook, que detecta ciclo pela
metade procurando um `refactor: checkpoint` **depois** da tag, passa a acusar
"a tag não foi movida" em todo ciclo — um aviso falso sobre um ciclo que fechou
certo. Aviso que mente é pior do que aviso ausente: ele treina o operador a
ignorar a única coisa que avisa quando o ciclo de fato ficou pela metade.

Local, sempre. **Nunca publique:**

```bash
git tag -f "runbook-checkpoint-<slug>"
```

A tag é um marcador de progresso pessoal, escopado ao seu e-mail. Ela não
descreve nada do projeto e nenhum outro desenvolvedor tem uso para ela.
Publicá-la — e reescrevê-la com `push -f` a cada ciclo — faz o `git fetch` dos
outros recusar com *"would clobber existing tag"*. Custo real para o time,
benefício zero.

A contrapartida, aceita de propósito: clone novo ou outra máquina começa o
ciclo do zero, porque não há remoto de onde recuperar a tag. Quando isso
acontecer, o hook avisa e pergunta em vez de descartar o acumulado em silêncio.

Dois casos em que o push não acontece, e nenhum deles é motivo para insistir:

- **Repo sem remoto** (comum em modo arquivo) — só mova a tag; não há para onde
  publicar.
- **Push recusado** (tag protegida, sem permissão) — a tag local já se moveu, e é
  ela que o hook lê, então o ciclo fechou *para você*. Não tente contornar com
  outro nome de tag nem desista da movimentação: informe o usuário de que os
  outros clones não vão enxergar este checkpoint e siga.

## 8. Se a tag do ciclo não existir

**Não a crie em silêncio quando o repo já usou o fluxo** — tag ausente ali
significa clone novo, outra máquina ou tag apagada, e nunca "o acumulado foi
revisado". Tente `git fetch origin --tags` primeiro; se ela não estiver no remoto,
pergunte ao usuário se deve revisar o acumulado ou recomeçar do HEAD.

Num repo que está adotando o fluxo agora, o caso é outro e o hook já instrui:
criar a tag no HEAD abre o primeiro ciclo, e o que veio antes fica de fora
deliberadamente.

Caso especial: repo que usava o fluxo antes do escopo por operador tem a tag
legada `runbook-checkpoint` sem sufixo. O hook segue contando por ela e instrui a
migração, que preserva o intervalo em vez de descartá-lo:

```bash
git tag runbook-checkpoint-<slug> runbook-checkpoint
```
