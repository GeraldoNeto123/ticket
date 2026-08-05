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

Em modo arquivo, tudo que o checkpoint produz vive num `checkpoint/` único na
**raiz da árvore de tickets** — a pasta que contém as pastas de feature, não a da
feature da vez (tickets em `.scratch/<feature>/issues/` → `.scratch/checkpoint/`).
Um intervalo de commits atravessa duas features com frequência, e ancorar o
registro na feature do HEAD fragmenta a memória e cega o dedup, que passaria a
enxergar só a feature atual. Em modo tracker não há pasta: o equivalente é o
rótulo `checkpoint`, que já é global no projeto.

Cada defeito real vira um registro: em modo arquivo, um arquivo por achado em
`<raiz-dos-tickets>/checkpoint/<slug-da-âncora>.md` — sem número da sequência da
feature; em modo tracker, uma issue com os rótulos `checkpoint` + `needs-triage`.

Nos dois modos o status de nascença é **sempre** `needs-triage` — nunca
`ready-for-agent`: promover achado a item de fila é decisão humana, via triagem,
não sua.

Antes de criar, confirme a duplicata você mesmo:

```bash
grep -ril "<âncora>" <raiz-dos-tickets>/checkpoint/         # arquivo
gh issue list --search "<âncora>" --state all --limit 20    # GitHub
glab issue list --search "<âncora>" --all                   # GitLab
```

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

Uma linha cada em
`<raiz-dos-tickets>/checkpoint/registro/<sha-curto>..<sha-curto>.md`: **um arquivo
por checkpoint**, nomeado pelo intervalo revisado (sem inconsistência nenhuma, não
crie o arquivo). Não abrem arquivo de achado nem issue — são memória para a
triagem humana e para o dedup do próximo checkpoint, que já as alcança pelo
`grep -r` acima.

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
