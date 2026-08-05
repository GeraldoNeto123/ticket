# Procedimento do checkpoint de consistência

Leia este arquivo quando o passo 8 da `/ticket:implement` vencer — o hook avisou,
ou a conferência manual acusou o acumulado. Ele não vive no `SKILL.md` porque o
checkpoint roda uma vez a cada cinco tickets: nas outras quatro seria peso morto
no contexto.

Antes de qualquer coisa, confirme que o passo 5 terminou. O aviso chega no commit
do passo 5.1, ainda antes da revisão e do amend, e o checkpoint revisa o
acumulado — que só está completo quando o commit deste ticket está.

## 1. Disparar a revisão

Dispare o agent `checkpoint-reviewer` passando duas coisas:

- o intervalo, exatamente como o aviso o nomeou (tipicamente
  `runbook-checkpoint-<slug>..HEAD`);
- **onde vivem os tickets e o spec** — o diretório, em modo arquivo; o
  repo/projeto e o CLI de leitura, em modo tracker.

Ele devolve um relatório em quatro listas e não altera nada. O que fazer com cada
lista é o resto deste arquivo.

## 2. Correções pequenas

Viram **um único** commit `refactor:` seu, com a palavra `checkpoint` na
mensagem:

```
refactor: checkpoint <sha..sha> — <resumo>
```

A palavra importa: é por ela que o hook detecta um checkpoint que rodou sem a tag
ter sido movida. Esse commit e os `docs:` do passo 3 são as exceções à regra de um
commit por ticket.

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
Origem: checkpoint-reviewer · intervalo `<sha..sha>`
```

## 4. Inconsistências sem defeito → registro

Uma linha cada, no mesmo contêiner da demanda e **agrupadas por intervalo**:

- **Modo arquivo:** `.scratch/<feature>/checkpoint/registro/<sha-curto>..<sha-curto>.md`
  — um arquivo por checkpoint, nomeado pelo intervalo revisado.
- **Modo tracker:** um comentário na issue pai, um por checkpoint, com o intervalo
  no cabeçalho.

Sem inconsistência nenhuma, não crie nada. Não abrem arquivo de achado nem issue —
são memória para a triagem humana e para o dedup do próximo checkpoint, que já as
alcança pelas buscas acima.

Uma entrada dessas sai por **um único motivo: ter virado ticket** — e quem a
remove é o humano que a promoveu na triagem, nunca você e nunca o checkpoint
seguinte. Não há expiração por idade, por volume nem por "parecer obsoleta":
entrada antiga que ninguém resolveu é precisamente o que o registro existe para
manter à vista. Encontrar entradas repetidas de checkpoints anteriores é o
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

## 7. Fechar o ciclo: mover e publicar a tag

As duas coisas, sempre:

```bash
git tag -f "runbook-checkpoint-<slug>" && git push -f origin "runbook-checkpoint-<slug>"
```

O `push -f` aqui só alcança a **sua** tag — as dos outros operadores ficam
intactas.

Sem o push a tag fica só na máquina: um clone novo não a encontra e o acumulado
inteiro passa por revisado sem nunca ter sido revisado.

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
git tag runbook-checkpoint-<slug> runbook-checkpoint && git push origin runbook-checkpoint-<slug>
```
