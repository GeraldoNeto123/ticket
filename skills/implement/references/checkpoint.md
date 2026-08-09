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
não alfanuméricas viram um `-`). Cada operador tem ciclo próprio, e o hook conta
só os commits dele. É o que permite mais de uma pessoa rodar o fluxo no mesmo
repo sem uma sobrescrever a tag da outra. Na dúvida sobre o nome,
`git tag -l 'runbook-checkpoint*'` lista as existentes.

O hook é infraestrutura da **máquina**, não do repo. Ausente, ele falha em
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

O filtro e o limiar acompanham os do hook de propósito: conferência que conta
diferente do contador acusa problema onde não há. **5 linhas ou mais sem nenhum
aviso ter chegado** = hook não instalado nesta máquina. Rode o checkpoint agora e
avise o usuário para reinstalar o plugin `ticket`, que é de onde o hook vem. Se o
comando falhar dizendo que a revisão não existe, é a tag que falta — o ciclo
nunca foi aberto, e o §5 trata.

Num `/ticket:run` a contagem é do orquestrador, pelo ledger. Não depende deste
comando nem do aviso.

## 1. Disparar a revisão

Dispare o agent `checkpoint-reviewer` passando três coisas:

- o **intervalo**, exatamente como o aviso o nomeou — tipicamente
  `runbook-checkpoint-<slug>..HEAD`;
- **onde vivem os tickets e o spec** — o diretório, em modo arquivo; o
  repo/projeto e o CLI de leitura, em modo tracker;
- **o lote** — a referência de cada ticket fechado no intervalo, com o SHA do
  commit que o entregou. Num `/ticket:run`, o ledger já tem as duas colunas por
  linha. Numa sessão manual, `git log --oneline <intervalo>` dá a lista, e em
  tracker o trailer `Closes #<n>` nomeia a issue de cada commit.

O lote é o que o revisor não reconstrói tão bem quanto você. Sem ele, sabe *que*
código mudou, não *a mando de qual ticket*. É a diferença entre um achado que
atravessa três tickets do lote e um que não atravessa nenhum — código que o
intervalo passou perto sem tocar, que ele marca `fora do lote`. Débito antigo
entra por aí, e é você quem decide o que fazer com ele.

Ele devolve um relatório em quatro listas e não altera nada.

## 2. Correções pequenas

A lista 1 vira **um único** commit `refactor:` seu, com a palavra `checkpoint` na
mensagem:

```
refactor: checkpoint <sha..sha> — <resumo>
```

A palavra importa por dois motivos. É por ela que o hook detecta um checkpoint
que rodou sem a tag ter sido movida, e é por ela que o **próximo** checkpoint
subtrai este commit do que vai revisar. Sem a palavra, o ciclo seguinte revisa a
saída deste e reporta como achado novo o que você já classificou.

## 3. O resto do relatório

As listas 2, 3 e 4 têm destino próprio, e nenhuma delas entra na fila da feature.
**O procedimento está em [`achados.md`](achados.md), ao lado deste arquivo.** Ele
cobre onde o achado mora, o critério de promoção, a busca de duplicata, o
registro das inconsistências e o commit que fecha os dois.

Volte para cá depois: a tag só se move no fim.

## 4. Fechar o ciclo: mover a tag

**Depois dos commits que este checkpoint produziu** — o `refactor: checkpoint` do
§2 e o `docs(checkpoint):` do `achados.md`. A ordem das seções é a ordem de
execução, e a tag é o último passo. Movida antes, os commits do próprio ciclo
caem no intervalo seguinte; o hook, que detecta ciclo pela metade procurando um
`refactor: checkpoint` **depois** da tag, passa a acusar "a tag não foi movida"
em todo ciclo. Aviso que mente treina o operador a ignorar a única coisa que
avisa quando o ciclo de fato ficou pela metade.

A tag é local e se move no lugar:

```bash
git tag -f "runbook-checkpoint-<slug>"
```

**Mantenha-a local.** Ela é um marcador de progresso pessoal, escopado ao seu
e-mail: não descreve nada do projeto, e nenhum outro desenvolvedor tem uso para
ela. Publicada — e reescrita com `push -f` a cada ciclo — faz o `git fetch` dos
outros recusar com *"would clobber existing tag"*. Custo real para o time,
benefício zero.

A contrapartida, aceita de propósito: clone novo ou outra máquina começa o ciclo
do zero, porque não há remoto de onde recuperar a tag. Quando isso acontecer, o
hook avisa e pergunta em vez de descartar o acumulado em silêncio.

## 5. Se a tag do ciclo não existir

**Repo que já usou o fluxo e está sem a tag: escale.** Tag ausente ali significa
clone novo, outra máquina ou tag apagada, e nunca "o acumulado foi revisado".
Tente `git fetch origin --tags` primeiro; se ela não estiver no remoto, pergunte
ao usuário se deve revisar o acumulado ou recomeçar do HEAD.

Num repo que está adotando o fluxo agora, o caso é outro e o hook já instrui:
criar a tag no HEAD abre o primeiro ciclo, e o que veio antes fica de fora
deliberadamente.

Caso especial: repo que usava o fluxo antes do escopo por operador tem a tag
legada `runbook-checkpoint`, sem sufixo. O hook segue contando por ela e instrui
a migração, que preserva o intervalo em vez de descartá-lo:

```bash
git tag runbook-checkpoint-<slug> runbook-checkpoint
```
