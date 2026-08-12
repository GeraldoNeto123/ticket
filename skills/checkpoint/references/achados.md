# O que fazer com os achados do checkpoint

Você chega aqui pelo §4 da `/ticket:checkpoint`, com as listas 2, 3 e 4 do
relatório em mãos. Nenhuma delas entra na fila da feature.

## Defeitos reais → achado fora da fila

Achado fica em **quarentena** até um humano promovê-lo, e a fila converge para o
escopo original. Sem isso ela cresce mais rápido do que é consumida, e o "done"
vira alvo móvel.

Tudo que o checkpoint produz vive **na demanda de onde veio**, num contêiner
separado da fila. Os dois modos têm a mesma forma — pasta da feature ↔ issue pai,
arquivo ↔ comentário:

- **Modo arquivo:** `.scratch/<feature>/checkpoint/`, irmã de `issues/` e não
  dentro dela. Um arquivo por achado, `<slug-da-âncora>.md`, sem número da
  sequência da feature: numeração é da fila, e achado não é fila.
- **Modo tracker:** um **comentário na issue pai** da demanda, com os rótulos
  `checkpoint` + `needs-triage` aplicados **ao pai**. É por eles que a busca do
  dedup acha os contêineres. Achado não abre issue: ela nasce na **promoção**,
  quando um humano decidiu. Abri-la na detecção enche board, relatório e métrica
  de sprint com trabalho que ninguém decidiu que existe.

Nos dois modos o status de nascença é **sempre** `needs-triage`, nunca
`ready-for-agent`. Promover achado a item de fila é decisão humana, via triagem.

**O mesmo contêiner recebe o excedente que a sessão de implementação encontra.** A
régua é uma só: achado nasce em quarentena, independentemente de quem tropeçou
nele. A assimetria alternativa — checkpoint em quarentena, implementador abrindo
issue direto — foi testada e sai cara nos dois sentidos. Numa fila real, oito
issues nasceram assim em uma noite, sem dedup entre si; e o checkpoint seguinte
gastou a rodada inteira para achar três defeitos e descobrir que os três já eram
issues abertas horas antes pelos próprios implementadores. Capacidade de revisão
transversal gasta redescobrindo o que já estava registrado é o custo exato que a
quarentena única evita.

**Se a demanda não tem issue pai, escale.** O `/to-tickets` trata o `## Parent`
como opcional, então o caso é real. A criação do pai é do usuário: inventar
estrutura no tracker de alguém é surpresa, e como a demanda se organiza é decisão
dele. Reporte os achados no encerramento para não perdê-los enquanto ele decide.

### Critério de promoção

A quarentena só serve se a saída dela tiver régua. Sem régua, promover vira
decisão de gosto tomada com a fila à vista — e a fila cresce: numa etapa real, 49
tickets viraram 88, com 37 nascendo **depois** do veredito de fechamento, e
apenas 4 dos 88 morreram `wontfix`, num desenho cujo pressuposto é que a maioria
morre ali.

Um achado sai da quarentena e vira ticket numerado **só** se:

1. **produz dado errado para o cliente** — um caminho alcançável que grava, apaga
   ou exibe valor incorreto. O teste é "alguém sofre o efeito", não "poderia ser
   melhor"; **ou**
2. **já recorreu** — a mesma âncora aparece no registro de **dois checkpoints
   diferentes**.

Todo o resto morre `wontfix` **no ato da triagem**, e a entrada permanece onde
está. Não há terceira porta: propor promoção fora do critério reabre exatamente o
buraco que ele fecha.

O teste (2) é o que separa estrutura de gosto, e é por ele que a âncora precisa
ser exata. Recorrência é contagem, não impressão.

É a mesma **âncora** que o spec e os tickets escrevem no lugar de `arquivo:linha`
— identidade que sobrevive ao código se mexer. Lá ela serve para reencontrar o
alvo; aqui, para tornar recorrência contável. Um conceito, dois usos.

### A busca de duplicata é sua

O revisor reporta a âncora e para aí. Faça a busca antes de criar, sempre sobre
**todos** os contêineres, nunca só o da demanda da vez:

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
comentários funciona igual nas duas plataformas.

**Varra também os tickets já fechados, não só os contêineres de checkpoint:**

```bash
grep -ril "<âncora>" .scratch/*/issues/
```

Um ticket `done` cuja âncora bate pode ser exatamente este achado, já decidido —
risco aceito com justificativa, comportamento provado por teste e mantido. Leia o
ticket antes de criar qualquer coisa: achado que reabre decisão registrada não é
achado, é a decisão sendo esquecida. Numa etapa real, o dedup contra os tickets
matou um "defeito" que era risco residual aceito, documentado e testado num
ticket fechado da mesma área.

O achado mora na demanda, mas a busca varre todas. É essa separação que dá escopo
sem perder memória: um intervalo de commits atravessa duas features com
frequência, e o dedup que enxergasse só a feature da vez reabriria o mesmo achado
a cada lote.

Se já existe, acrescente ao registro existente o que o novo checkpoint adiciona.
**Não crie outro.**

<template-achado>

```markdown
## Achado
<uma frase: o defeito, do ponto de vista de quem sofre o efeito>

## Onde
<arquivo por ocorrência, apontando símbolo ou trecho — a âncora, nunca a linha>

## Por que nenhum ticket isolado viu
<a justificativa de ter vindo do checkpoint>

## Âncora de busca
`<termo exato: código de erro, símbolo, constraint>`

**Status:** needs-triage

---
Origem: checkpoint-reviewer · intervalo `<sha..sha>` · atravessa <tickets do lote, ou `fora do lote`>
```

</template-achado>

## Inconsistências sem defeito → registro

Uma linha cada, no mesmo contêiner da demanda e **agrupadas por intervalo**. Vale
aqui a mesma **âncora** do achado. O registro é o artefato de vida mais longa do
fluxo, porque só sai quando alguém o promove — é onde uma referência frágil tem
mais tempo para deixar de corresponder.

- **Modo arquivo:** `.scratch/<feature>/checkpoint/registro/<sha-curto>..<sha-curto>.md`,
  um arquivo por checkpoint, nomeado pelo intervalo revisado.
- **Modo tracker:** um comentário na issue pai, um por checkpoint, com o
  intervalo no cabeçalho.

Sem inconsistência nenhuma, só crie o registro se ele for o único marcador do
ciclo — o caso "sem achados" do §4 da `/ticket:checkpoint`. Inconsistências não
abrem arquivo de achado nem issue: são memória para a triagem humana e para o
dedup do próximo checkpoint.

Uma entrada dessas sai por **um único motivo: ter virado ticket pelo critério de
promoção**, e quem a remove é o humano que a promoveu. Entrada antiga que ninguém
resolveu é precisamente o que o registro existe para manter à vista — é ela que
torna o teste (2) contável. Expurgá-la por idade apagaria a evidência de
recorrência antes de a segunda ocorrência chegar. Entradas repetidas de
checkpoints anteriores são o funcionamento esperado.

## O commit dos dois

Em modo arquivo, achados e registro entram num commit só, de assunto
`docs(checkpoint): <resumo>`. O prefixo é o que faz o próximo ciclo subtrair este
commit do conjunto que revisa — e é um dos dois marcadores pelos quais o §1
encontra onde o ciclo anterior terminou.

Antes de commitar, confirme que o caminho é versionável:

```bash
git check-ignore .scratch/<feature>/checkpoint
```

Projeto que ignora `.scratch/` inteiro faz o `git add` não adicionar nada, e o
commit sai vazio ou sem os arquivos — os achados somem sem erro nenhum. Se
estiver ignorado, avise o usuário e reporte os achados no encerramento em vez de
perdê-los.

Em modo tracker não há commit: achado e registro são comentários na issue pai.

## Propostas de processo → ao usuário, textualmente

Reporte no encerramento. Elas mudam a skill ou o agent, e nunca viram ticket do
projeto — achado meta que vira ticket é o fluxo gerando trabalho sobre a própria
burocracia.

## Respeite o que é issue e o que não é

Se o `issue-tracker.md` do projeto separa issue (unidade de trabalho) de
spec/plano/ADR (documento), um achado que é documento vai para `docs/`, não para
o tracker.
