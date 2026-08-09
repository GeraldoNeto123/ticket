# Procedimento do checkpoint de consistência

Leia este arquivo quando o passo 8 da `/ticket:implement` vencer — o hook avisou,
ou a conferência manual acusou o acumulado. Ele não vive no `SKILL.md` porque o
checkpoint roda uma vez a cada cinco tickets: nas outras quatro seria peso morto
no contexto.

Antes de qualquer coisa, confirme que o passo 5 terminou. O aviso chega no commit
do passo 5.1, ainda antes da revisão e do amend, e o checkpoint revisa o
acumulado — que só está completo quando o commit deste ticket está.

## O ciclo, e conferir que o hook existe

A tag do ciclo é **escopada por operador**: `runbook-checkpoint-<slug>`, com o
slug derivado da parte local do `git config user.email` (minúsculas, sequências
não alfanuméricas viram um `-`). Cada operador tem ciclo próprio e o hook conta
só os commits dele — é o que permite mais de uma pessoa rodar o fluxo no mesmo
repo sem uma sobrescrever a tag da outra. Na dúvida sobre o nome,
`git tag -l 'runbook-checkpoint*'` lista as existentes.

O hook é infraestrutura da **máquina**, não do repo, e ausente ele falha em
silêncio: o checkpoint simplesmente nunca é pedido. Numa sessão manual, se você
chegou ao fim de um passo 5 e nenhum aviso apareceu, confira por conta própria:

```bash
git log --oneline --no-merges --author="$(git config user.email)" \
  -E --invert-grep \
  --grep='^(docs|chore|ci|style|test)[(:]' \
  --grep='^refactor(\([^)]*\))?: *checkpoint' \
  --grep='achados de [0-9a-f]{7,40}' \
  "runbook-checkpoint-<slug>..HEAD"
```

O filtro e o limiar acompanham os do hook de propósito — conferência que conta
diferente do contador acusa problema onde não há. **5 linhas ou mais sem nenhum
aviso ter chegado** = hook não instalado nesta máquina: rode o checkpoint agora
e avise o usuário para reinstalar o plugin `ticket`, que é de onde o hook vem.
Se o comando falhar dizendo que a revisão não existe, é a tag que falta — o
ciclo nunca foi aberto, e o §8 trata.

Num `/ticket:run` a contagem é do orquestrador, pelo ledger, e não depende deste
comando nem do aviso.

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

O resto do relatório **nunca entra na fila da feature**. Achado fica em
quarentena até um humano promovê-lo, e a fila converge para o escopo original —
sem isso ela cresce mais rápido do que é consumida e o "done" vira alvo móvel.

Tudo que o checkpoint produz vive **na demanda de onde veio**, num contêiner
separado da fila. Os dois modos têm a mesma forma — pasta da feature ↔ issue pai,
arquivo ↔ comentário:

- **Modo arquivo:** `.scratch/<feature>/checkpoint/` — irmã de `issues/`, não
  dentro dela. Um arquivo por achado, `<slug-da-âncora>.md`, sem número da
  sequência da feature: numeração é da fila, e achado não é fila.
- **Modo tracker:** um **comentário na issue pai** da demanda, com os rótulos
  `checkpoint` + `needs-triage` aplicados **ao pai** (é por eles que a busca do
  dedup acha os contêineres). Achado não abre issue — ela nasce na **promoção**,
  quando um humano decidiu; abri-la na detecção enche board, relatório e métrica
  de sprint com trabalho que ninguém decidiu que existe.

**Onde o achado mora e onde o dedup procura são coisas diferentes.** O achado mora
na demanda — é o que permite mais de um dev no mesmo repo, cada um triando o que é
seu, na mesma partição por operador que o ciclo já usa. A busca do passo seguinte
varre **todas** as demandas: um intervalo de commits atravessa duas features com
frequência, e o dedup que enxergasse só a feature da vez reabriria o mesmo achado
a cada lote.

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
ser exata: recorrência é contagem, não impressão. Não há terceira porta — achado
que não passa em (1) nem em (2) você marca `wontfix` e deixa onde está; propor
promoção fora do critério reabre exatamente o buraco que ele fecha.

**A busca de duplicata é sua**, não do revisor — ele reporta a âncora e para aí.
Faça-a antes de criar, sempre sobre **todos** os contêineres, nunca só o da
demanda da vez:

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

São duas etapas porque **nenhum dos dois CLIs procura dentro de comentário** — o
`--search` cobre título e descrição, e só. Listar os pais pelo rótulo e ler os
comentários é determinístico e funciona igual nas duas plataformas.

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

Uma linha cada, no mesmo contêiner da demanda e **agrupadas por intervalo**. Vale
aqui a mesma **âncora** do achado — o registro é o artefato de vida mais longa do
fluxo, porque só sai quando alguém o promove, então é onde uma referência frágil
tem mais tempo para deixar de corresponder.

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

Antes de commitar, confirme que o caminho é versionável
(`git check-ignore .scratch/<feature>/checkpoint`). Projeto que ignora `.scratch/`
inteiro faz o `git add` não adicionar nada e o commit sair vazio ou sem os
arquivos — os achados somem sem erro nenhum. Se estiver ignorado, avise o usuário
e reporte os achados no encerramento em vez de perdê-los.

Uma entrada dessas sai por **um único motivo: ter virado ticket pelo critério de
promoção do §3**, e quem a remove é o humano que a promoveu. Entrada antiga que
ninguém resolveu é precisamente o que o registro existe para manter à vista: é
ela que torna o teste (2) contável, e expurgá-la por idade apagaria a evidência
de recorrência antes de a segunda ocorrência chegar. Entradas repetidas de
checkpoints anteriores são o funcionamento esperado.

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
e a tag é o último passo: movida antes, os commits do próprio ciclo caem no
intervalo seguinte, e o hook — que detecta ciclo pela metade procurando um
`refactor: checkpoint` **depois** da tag — passa a acusar "a tag não foi movida"
em todo ciclo. Aviso que mente treina o operador a ignorar a única coisa que
avisa quando o ciclo de fato ficou pela metade.

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
