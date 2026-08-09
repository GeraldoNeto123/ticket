# O commit de exceção do passo 5

Você chega aqui pelo passo 5.3 da `SKILL.md`, quando `git log @{u}..HEAD` veio
vazio: o commit deste ticket já está no upstream, e amendar reescreveria
histórico publicado. Os achados da revisão vão num commit novo.

Está fora do caminho quente porque o push da branch é manual e fora da skill —
na maioria dos tickets o amend é seguro e este arquivo nunca é lido.

O assunto leva **`achados de <sha-curto>`**, com o sha do commit revisado:

```
refactor(escopo): achados de 9d281b74 — <resumo>
```

O marcador não é enfeite. O contador do passo 8 conta commits, não tickets: sem
ele, este commit passaria por um segundo ticket e fecharia o ciclo cedo. É o
mesmo papel da palavra `checkpoint` no commit do checkpoint, e ainda diz *qual*
commit foi revisado.

Registre no ticket que este ciclo abriu exceção à regra de um commit por ticket,
com os dois shas.
