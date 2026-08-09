---
name: spec
description: "Escreve o spec da etapa envolvendo o /to-spec do mattpocock-skills."
disable-model-invocation: true
---

# /ticket:spec

**Argumento desta sessão:** $ARGUMENTS

Esta skill **não reimplementa** o `/to-spec` — ela o segue e acrescenta o que o resto do fluxo consome depois. Envolver em vez de duplicar é deliberado: o upstream continua evoluindo sem que nada aqui precise ser mesclado.

O modo (arquivo ou tracker) vem do `docs/agents/issue-tracker.md`, como em toda skill deste plugin.

## 1. Seguir o `to-spec`

**O procedimento está em [`../../references/envolver-upstream.md`](../../references/envolver-upstream.md)** — resolver o caminho da versão instalada, ler em vez de invocar, e conferir a forma antes dos adendos. Rode-o com `to-spec`.

Os pressupostos a conferir no passo 3 de lá, que os adendos abaixo exigem:

- um **template de spec** com seção de decisões de implementação e de teste;
- um passo de **costuras de teste** acordadas com o usuário.

## 2. Os adendos

Aplique estes ao documento que o `to-spec` manda escrever. Eles não substituem nada de lá; cobrem o que o upstream não tem como saber, porque dizem respeito a quem lê o spec **depois**.

**Referência a código é âncora: símbolo ou trecho citado, nunca `arquivo:linha`.** Escreva `ContratacaoService.assinar`, não `contratacao.service.ts:537`. O upstream já pede para evitar caminho e snippet, mas não nomeia número de linha nem diz o que pôr no lugar. O hook `referencias-de-linha.py` acusa na hora — troque ali mesmo, enquanto o contexto para achar o símbolo ainda está aberto.

**As costuras precisam sobreviver no documento, não só no acordo.** O upstream faz você desenhá-las e conferi-las com o usuário; o que este fluxo consome é o **registro** delas. A `/ticket:implement` manda usar `/tdd` "nas costuras pré-acordadas, que vêm do spec", e trata spec sem costura nomeada como lacuna — o ticket para e escala. Cada sessão de implementação começa limpa e não esteve na conversa em que vocês concordaram: nomeie a costura de um jeito que uma sessão nova ache, pelo módulo e pelo símbolo.

## 3. Depois

O spec publicado é a entrada do `/ticket:split`, que roda o portão de modelagem e só então fatia. Diga isso ao usuário no encerramento — fatiar direto pelo `/to-tickets` pula o portão, e é exatamente o que este fluxo aprendeu a não fazer.
