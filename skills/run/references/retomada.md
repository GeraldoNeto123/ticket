# Retomada de fila — reconciliação antes do primeiro dispatch

Você chega aqui pelo passo 2 da `/ticket:run`, porque o ledger da feature já
existe (ou há commit de ticket da fila sem ledger): esta fila está sendo
retomada, e retomar não é recomeçar.

Uma sessão que morre no meio de um ticket deixa um estado que nenhum retorno de
subagent descreveu: o commit pode existir sem o ticket estar `done`, o
`Assignee` pode ter sido escrito e não commitado. Antes do primeiro dispatch,
cruze três fontes para cada ticket da frontier — a linha do ledger, o `git log`
do intervalo e o `Status:` do próprio ticket. Quatro desfechos:

- **Sem commit e sem `done`** — execução normal, dispatch como sempre.
- **Com commit e sem `done`** — **retomada**. O trabalho existe; reimplementá-lo
  produz um segundo commit do mesmo ticket e joga fora o primeiro. O dispatch
  precisa dizer isso na primeira linha: *não reimplemente; o commit `<sha>` já
  entrega este ticket; confira-o, retome do ponto em que parou e use `<sha>^`
  como ponto fixo da revisão*. Sem o ponto fixo explícito, a revisão do subagent
  diffa contra o lugar errado e passa em branco.
- **`done`** — sai da frontier, não vira dispatch.
- **Ambíguo** — o commit toca mais do que o ticket, há mais de um commit para
  ele, ou não existe ledger porque a sessão morreu antes de criá-lo: **escale.**
  Aqui é onde menos se sabe o que aconteceu com o repositório, e portanto a pior
  hora para adivinhar. Marcar como `done` um ticket cuja revisão nunca rodou
  custa tanto quanto reimplementar por cima.

Reconciliado, registre no ledger o que você concluiu de cada um antes de
despachar — a reconciliação também é trabalho que se perde se a sessão cair de
novo.
