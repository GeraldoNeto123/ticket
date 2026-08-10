---
name: checkpoint
description: "Checkpoint de consistência do acumulado de tickets: dispara o agent checkpoint-reviewer sobre um intervalo de commits, aplica correções pequenas e roteia achados para fora da fila. Invocada pelo orquestrador da /ticket:run a cada 5 tickets fechados, ou pelo usuário para revisar o acumulado de sessões manuais."
---

# /ticket:checkpoint

**Argumento desta sessão:** $ARGUMENTS

Tickets são implementados um por sessão, e cada sessão enxerga só o próprio
ticket. O checkpoint é a passada transversal: um agent revisa o **acumulado**
procurando o que nenhuma sessão isolada podia ver. Cadência: a cada **cinco**
tickets fechados. Numa fila `/ticket:run`, quem conta é o orquestrador, pelo
ledger; fora dela, quem invoca é o usuário.

O modo (arquivo ou tracker) vem do `docs/agents/issue-tracker.md`.

## 1. Intervalo e lote

O ciclo é delimitado pelos commits que o próprio checkpoint deixa no histórico —
assunto `refactor: checkpoint ...` ou `docs(checkpoint): ...`. Ao contrário de um
marcador local (tag, arquivo de estado), eles viajam com o clone e não dependem
de hook instalado.

- **Intervalo**: do último commit com um desses assuntos até o `HEAD`:

  ```bash
  git log -1 --format='%H' -E \
    --grep='^refactor(\([^)]*\))?: *checkpoint' \
    --grep='^docs\(checkpoint\)'
  ```

  Numa fila, a última linha de checkpoint do ledger nomeia o mesmo SHA — as duas
  fontes devem concordar; divergindo, o ledger manda, e anote a divergência.
  Nunca houve checkpoint: numa fila, o intervalo começa no commit **anterior** ao
  primeiro SHA do ledger; fora dela, pergunte ao usuário de onde revisar.

- **Lote**: a referência de cada ticket fechado no intervalo, com o SHA do commit
  que o entregou. Numa fila, o ledger já tem as duas colunas por linha. Fora
  dela, `git log --oneline <intervalo>` dá a lista — em tracker, o trailer
  `Closes #<n>` nomeia a issue de cada commit.

O lote é o que o revisor não reconstrói tão bem quanto você. Sem ele, sabe *que*
código mudou, não *a mando de qual ticket*. É a diferença entre um achado que
atravessa três tickets do lote e um que não atravessa nenhum — código que o
intervalo passou perto sem tocar, que ele marca `fora do lote`. Débito antigo
entra por aí, e é o usuário quem decide o que fazer com ele.

## 2. Disparar a revisão

Dispare o agent `checkpoint-reviewer` passando o **intervalo**, **onde vivem os
tickets e o spec** (o diretório, em modo arquivo; o repo/projeto e o CLI de
leitura, em modo tracker) e o **lote**. Ele devolve um relatório em quatro
listas e não altera nada.

## 3. Correções pequenas

A lista 1 vira **um único** commit:

```
refactor: checkpoint <sha..sha> — <resumo>
```

O assunto não é enfeite: é por ele que o **próximo** checkpoint encontra o fim
deste ciclo (§1) e subtrai este commit do que vai revisar. Sem ele, o ciclo
seguinte revisa a saída deste e reporta como achado novo o que você já
classificou.

## 4. O resto do relatório

As listas 2, 3 e 4 têm destino próprio, e nenhuma delas entra na fila da
feature. **O procedimento está em [`references/achados.md`](references/achados.md)** —
onde o achado mora, o critério de promoção, a busca de duplicata, o registro das
inconsistências e o commit que fecha os dois.

Se o relatório inteiro veio vazio e a lista 1 não produziu commit, crie mesmo
assim o registro do intervalo com "sem achados": é o commit `docs(checkpoint):`
dele que marca o fim do ciclo — sem nenhum marcador, o próximo checkpoint
revisaria estes tickets de novo.

## Critério de conclusão

- [ ] Intervalo e lote determinados antes do disparo — numa fila, conferidos
      contra o ledger
- [ ] Lista 1 aplicada num único `refactor: checkpoint <intervalo> — <resumo>`,
      ou vazia
- [ ] Listas 2–4 roteadas pelo `achados.md`
- [ ] O ciclo tem marcador no histórico (`refactor: checkpoint` ou
      `docs(checkpoint):`) — em modo tracker, onde não há commit de achados, a
      lista 1 vazia dispensa o marcador e o intervalo do próximo ciclo sai do
      ledger ou do usuário
- [ ] Numa fila: linha própria de checkpoint no ledger, com o SHA final do ciclo
