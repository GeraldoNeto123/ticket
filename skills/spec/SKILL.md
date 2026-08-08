---
name: spec
description: "Escreve o spec da etapa: segue o /to-spec do mattpocock-skills e acrescenta o que o resto deste fluxo consome depois — costuras que sobrevivem ao /clear e referência de código por símbolo, nunca por linha."
disable-model-invocation: true
---

# /ticket:spec

**Argumento desta sessão:** $ARGUMENTS

Esta skill **não reimplementa** o `/to-spec` — ela o segue e acrescenta o que o resto do fluxo consome depois. Envolver em vez de duplicar é deliberado: o upstream continua evoluindo sem que nada aqui precise ser mesclado, e você não mantém uma segunda cópia da mesma disciplina.

O modo (arquivo ou tracker) vem do `docs/agents/issue-tracker.md`, como em toda skill deste plugin.

## 1. Ler o `to-spec` e segui-lo

O diretório-base desta skill aparece no cabeçalho quando ela é invocada. Resolva o caminho do upstream a partir dele:

```bash
<diretório-base>/../../scripts/upstream-skill.py to-spec
```

Ele imprime o caminho absoluto do `SKILL.md` que **de fato roda** — a versão instalada vive no caminho, então nada aqui pode fixá-la. Se o script falhar, ele já diz o que fazer: pare e siga a instrução dele, não improvise um spec por conta própria. Um documento com a forma errada quebra o `/ticket:split` e a `/ticket:implement` mais adiante, e quebra em silêncio.

**Leia o arquivo e siga-o.** Não tente invocar a skill: ela é `disable-model-invocation`, e o Skill tool recusa invocação vinda de modelo — é o mesmo motivo pelo qual a `/ticket:run` lê a `implement` em vez de invocá-la.

## 2. Confirmar o que você espera dele

Ler o upstream te dá atualização sem merge; o preço simétrico é mudança silenciosa. Antes de aplicar os adendos do passo 3, confirme que o arquivo lido ainda tem as duas coisas que eles pressupõem:

- um **template de spec** com seção de decisões de implementação e de teste;
- um passo de **costuras de teste** acordadas com o usuário.

Se alguma sumiu ou mudou de forma, **pare e diga o que mudou**. Seguir uma forma nova com adendos escritos para a antiga produz um documento que contradiz a si mesmo — e o erro só aparece dois comandos depois, quando um ticket for implementado.

## 3. Os adendos

Aplique estes ao documento que o `to-spec` manda escrever. Eles não substituem nada de lá; cobrem o que o upstream não tem como saber, porque dizem respeito a quem lê o spec **depois**.

**Referência a código é símbolo ou trecho citado, nunca `arquivo:linha`.** O upstream já pede para evitar caminho e snippet, mas não nomeia número de linha nem diz o que escrever no lugar — e é aí que a âncora entra. A numeração se move a cada ticket implementado; quem ler depois edita a linha errada com um diff de aparência plausível, que é o modo de falha silencioso. Escreva `ContratacaoService.assinar`, não `contratacao.service.ts:537`. Num repo que usa este fluxo, o hook `referencias-de-linha.py` acusa a âncora na hora em que ela é escrita — se o aviso aparecer, troque ali mesmo, enquanto o contexto para achar o símbolo ainda está aberto.

**As costuras precisam sobreviver no documento, não só no acordo.** O upstream faz você desenhá-las e conferi-las com o usuário; o que este fluxo consome é o **registro** delas. A `/ticket:implement` manda usar `/tdd` "nas costuras pré-acordadas, que vêm do spec", e trata spec sem costura nomeada como lacuna — o ticket para e escala. Cada sessão de implementação começa limpa e não esteve na conversa em que vocês concordaram: nomeie a costura de um jeito que uma sessão nova ache, pelo módulo e pelo símbolo.

## 4. Depois

O spec publicado é a entrada do `/ticket:split`, que roda o portão de modelagem e só então fatia. Diga isso ao usuário no encerramento — fatiar direto pelo `/to-tickets` pula o portão, e é exatamente o que este fluxo aprendeu a não fazer.
