---
name: split
description: "Fatia o spec em tickets: roda o portão de modelagem de domínio (campo → escritores por fluxo, conflito vira ADR) e só então segue o /to-tickets do mattpocock-skills, com o ADR como entrada."
disable-model-invocation: true
---

# /ticket:split

**Argumento desta sessão:** $ARGUMENTS

O argumento aponta o spec da etapa. Esta skill **não reimplementa** o `/to-tickets` — ela roda o portão que precisa vir antes e então o segue, com o resultado do portão como entrada.

O modo (arquivo ou tracker) vem do `docs/agents/issue-tracker.md`, como em toda skill deste plugin.

## 1. Ler o `to-tickets`

O diretório-base desta skill aparece no cabeçalho quando ela é invocada:

```bash
<diretório-base>/../../scripts/upstream-skill.py to-tickets
```

Ele imprime o caminho absoluto do `SKILL.md` que de fato roda. Se falhar, a mensagem dele diz o que fazer — pare e siga-a; não improvise um fatiamento próprio.

**Leia o arquivo agora, mas execute-o só no passo 3.** Ler antes é o que te permite conferir, no passo 2, se o portão ainda encaixa no que ele espera receber.

Leia o arquivo; **não** invoque a skill — ela é `disable-model-invocation`, e o Skill tool recusaria.

Confirme que o arquivo lido ainda tem o que os passos seguintes pressupõem: **arestas de bloqueio** por ticket (`Blocked by` / link nativo), um **template** de ticket e a noção de **frontier**. Se algo mudou de forma, pare e diga o que mudou — seguir a forma nova com adendos escritos para a antiga produz tickets que se contradizem, e o erro só aparece na implementação.

## 2. O portão de modelagem

O `/to-spec` fatia por comportamento visível ao usuário, que é a fatia certa para entregar valor. Falta a passada **ortogonal**: olhar o estado que os comportamentos compartilham. Sem ela, dois tickets consomem premissas opostas sobre o mesmo campo, cada um passa na própria revisão e nos próprios testes, e o defeito só aparece no checkpoint — caro, e com chance de escapar. Numa etapa real de 64 tickets, sete tinham exatamente essa forma, todos sobre um punhado de colunas da mesma tabela.

**Critério de entrada, antes de qualquer trabalho:** esta etapa vai escrever em estado compartilhado por **mais de um fluxo** (síncrono da requisição, webhook, varredura agendada, migration)? Se não — etapa só de leitura, de UI, ou que escreve num lugar só —, diga isso explicitamente ao usuário e vá para o passo 3. Portão que roda quando não há o que decidir é cerimônia, e cerimônia é o que faz o comando parar de ser usado.

Se sim, rode a passada. **Invoque a skill `mattpocock-skills:domain-modeling`** — ela é invocável por modelo, então aqui é invocação de verdade, não leitura — enquadrando o trabalho assim:

1. **Liste o estado compartilhado que a etapa toca.** Tabelas e colunas, não telas nem rotas.
2. **Para cada campo, nomeie os escritores.** Um `grep` pelo nome do campo dá a lista; o trabalho é classificar cada escritor **por fluxo**. Escritores em fluxos diferentes são o sinal de alerta.
3. **Onde houver mais de um escritor, decida agora** e registre em ADR (`docs/adr/`, salvo se o projeto documentar outro lugar): quem ganha quando discordam, e o que cada um faz **quando não sabe o valor**. "Não sabe" é o caso que mais erra, e o padrão silencioso (`?? valor`) é quase sempre a resposta errada.

O `domain-modeling` traz de graça o confronto com o glossário e a atualização do `CONTEXT.md` — que é justamente o que falta quando dois tickets inventam dois nomes para o mesmo fato. Deixe-o fazer isso; o que é seu aqui é a disciplina acima: o que mapear, o que vira ADR, e quando parar.

**Termo condenado tem que sair do código, ou não devia ter sido condenado.** O formato do glossário manda escolher um vencedor e listar os perdedores em `_Avoid_`, e não pergunta se o perdedor é como o código chama a coisa hoje. Antes de fechar a passada, procure no `src/` cada termo que você acabou de pôr em `_Avoid_`: se ele nomeia símbolo público vivo, o vocabulário não está resolvido — está dividido. Duas saídas, e nenhuma delas é o silêncio: ou o código migra, e a renomeação vira ticket desta fatia com o cuidado de raio de alcance que o `to-tickets` descreve para refatoração ampla; ou o `_Avoid_` estava errado, e quem ganha é o nome que o código já usa. Deixar como está custa duas vezes: o glossário passa a mentir, e o `checkpoint-reviewer`, que lê o glossário, reporta como divergência de naming um conflito que o documento criou.

**Pare no ADR.** O portão decide e registra; ele não implementa nem abre ticket.

## 3. Fatiar

Agora sim, siga o `to-tickets` que você leu, com dois acréscimos:

**O ADR é entrada.** Cada ticket que toca um campo mapeado cita o ADR pelo número. O brief não reenumera escritores — o documento faz isso e sobrevive ao `/clear`, que o brief não faz.

**Referência a código é âncora: símbolo ou trecho, nunca `arquivo:linha`.** O ticket é lido semanas depois, com todo ticket anterior já tendo empurrado as linhas do arquivo: escreva `ContratacaoService.assinar`, não `contratacao.service.ts:537`. O hook `referencias-de-linha.py` acusa na hora — troque ali mesmo.

**Em modo tracker, a demanda precisa de issue pai.** O upstream trata o `## Parent` como opcional; aqui ele não é. Os achados do checkpoint vivem como comentários na issue pai, e sem pai o checkpoint para e pergunta — no meio de uma fila em andamento, que é a pior hora. Se não houver pai, pergunte ao usuário **agora**, antes de publicar os tickets: criar estrutura no tracker de alguém por conta própria é surpresa, mas perguntar aqui custa uma frase.

## 4. Depois

A fila publicada é consumida pela `/ticket:implement`, um ticket por sessão, ou pela `/ticket:run`, que orquestra a frontier inteira. Diga ao usuário qual dos dois cabe: `run` é o modo autônomo; `implement` é para quem quer acompanhar de perto.
