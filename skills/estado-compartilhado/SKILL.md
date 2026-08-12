---
name: estado-compartilhado
description: "Portão de modelagem entre o /to-spec e o /to-tickets: mapeia o estado que as fatias vão dividir e resolve conflito de escritor em ADR."
disable-model-invocation: true
---

# /ticket:estado-compartilhado

**Argumento desta sessão:** $ARGUMENTS

O argumento aponta o spec da etapa. Esta skill roda **entre** o `/to-spec` e o `/to-tickets`.

O `/to-tickets` fatia por comportamento visível ao usuário — fatias verticais, que são a fatia certa para entregar valor. Falta a passada **ortogonal**: olhar o estado que os comportamentos compartilham. Sem ela, dois tickets consomem premissas opostas sobre o mesmo campo, cada um passa na própria revisão e nos próprios testes, e o defeito só aparece no checkpoint — caro, e com chance de escapar. Numa etapa real de 64 tickets, sete tinham exatamente essa forma, todos sobre um punhado de colunas da mesma tabela.

O modo (arquivo ou tracker) vem do `docs/agents/issue-tracker.md`.

## 1. Critério de entrada

Antes de qualquer trabalho: esta etapa vai escrever em estado compartilhado por **mais de um fluxo** (síncrono da requisição, webhook, varredura agendada, migration)? Se não — etapa só de leitura, de UI, ou que escreve num lugar só —, diga isso explicitamente ao usuário e encerre: siga direto para o `/to-tickets`. Portão que roda quando não há o que decidir é cerimônia, e cerimônia é o que faz o comando parar de ser usado.

## 2. A passada

**Invoque a skill `mattpocock-skills:domain-modeling`**, enquadrando o trabalho assim:

1. **Liste o estado compartilhado que a etapa toca.** Tabelas e colunas, não telas nem rotas.
2. **Para cada campo, nomeie os escritores.** Um `grep` pelo nome do campo dá a lista; o trabalho é classificar cada escritor **por fluxo**. Escritores em fluxos diferentes são o sinal de alerta.
3. **Onde houver mais de um escritor, decida agora** e registre em ADR (`docs/adr/`, salvo se o projeto documentar outro lugar): quem ganha quando discordam, e o que cada um faz **quando não sabe o valor**. "Não sabe" é o caso que mais erra, e o padrão silencioso (`?? valor`) é quase sempre a resposta errada.

O ADR **enumera os escritores** — é essa lista que a verificação de invariante e o checkpoint usam depois. Ticket futuro que acrescentar escritor atualiza o ADR; o procedimento está em [`references/adr-escritor.md`](references/adr-escritor.md), e o ADR deve dizer que a lista é mantida assim.

O `domain-modeling` traz de graça o confronto com o glossário e a atualização do `CONTEXT.md` — que é justamente o que falta quando dois tickets inventam dois nomes para o mesmo fato. Deixe-o fazer isso; o que é seu aqui é a disciplina acima: o que mapear, o que vira ADR, e quando parar.

**Termo condenado tem que sair do código, ou não devia ter sido condenado.** O formato do glossário manda escolher um vencedor e listar os perdedores em `_Avoid_`, e não pergunta se o perdedor é como o código chama a coisa hoje. Antes de fechar a passada, procure no `src/` cada termo que você acabou de pôr em `_Avoid_`: se ele nomeia símbolo público vivo, o vocabulário não está resolvido — está dividido. Duas saídas, e nenhuma delas é o silêncio: ou o código migra, e a renomeação vira ticket desta fatia com o cuidado de raio de alcance que o `/to-tickets` descreve para refatoração ampla; ou o `_Avoid_` estava errado, e quem ganha é o nome que o código já usa. Deixar como está custa duas vezes: o glossário passa a mentir, e o `checkpoint-reviewer`, que lê o glossário, reporta como divergência de naming um conflito que o documento criou.

**Pare no ADR.** O portão decide e registra; ele não implementa nem abre ticket.

## 3. Depois

Siga para o `/to-tickets`, com três cuidados que vêm daqui:

- **O ADR é entrada.** Cada ticket que toca um campo mapeado cita o ADR pelo número. O brief não reenumera escritores — o documento faz isso e sobrevive ao `/clear`, que o brief não faz.
- **Referência a código é âncora: símbolo ou trecho, nunca `arquivo:linha`.** Escreva `ContratacaoService.assinar`, não `contratacao.service.ts:537` — o ticket é lido semanas depois, com todo ticket anterior já tendo empurrado as linhas do arquivo. O hook `referencias-de-linha.py` acusa na hora — troque ali mesmo.
- **Em modo tracker, a demanda precisa de issue pai.** Os achados do checkpoint vivem como comentários na issue pai, e sem pai o checkpoint para e pergunta — no meio de uma fila em andamento, que é a pior hora. Se não houver pai, **escale agora**, antes de publicar os tickets: criar estrutura no tracker de alguém por conta própria é surpresa, mas perguntar aqui custa uma frase.
