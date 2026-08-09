# Envolver uma skill do `mattpocock-skills`

A `/ticket:spec` e a `/ticket:split` **envolvem** um upstream em vez de duplicá-lo:
seguem o `to-spec` e o `to-tickets` e acrescentam o que só quem conhece o resto
deste fluxo sabe. Este arquivo é o procedimento comum às duas.

Ele vive fora das duas skills porque nenhuma pode invocar a outra: as duas são
`disable-model-invocation`, então não têm description alcançável por modelo.
Referência compartilhada por skills user-invoked mora em arquivo simples.

## 1. Resolver o caminho

O diretório-base da skill aparece no cabeçalho quando ela é invocada:

```bash
<diretório-base>/../../scripts/upstream-skill.py <nome-da-skill>
```

Ele imprime o caminho absoluto do `SKILL.md` que **de fato roda**. A versão
instalada vive no caminho, então nada aqui pode fixá-la.

Se o script falhar, a mensagem dele diz o que fazer: **escale** — pare e siga a
instrução, em vez de improvisar o documento por conta própria. Documento com a
forma errada quebra os comandos seguintes deste fluxo, e quebra em silêncio.

## 2. Ler, nunca invocar

**Leia o arquivo.** O upstream é `disable-model-invocation` e o Skill tool
recusaria a invocação — ler entrega as mesmas instruções pelo caminho que a
política permite.

## 3. Conferir a forma antes de aplicar os adendos

Ler o upstream te dá atualização sem merge; o preço simétrico é mudança
silenciosa. Antes de aplicar qualquer adendo, confirme que o arquivo lido ainda
tem o que eles pressupõem — **a lista de pressupostos é de cada skill**, e está
no `SKILL.md` que te trouxe aqui.

Se algum sumiu ou mudou de forma, **escale**: diga exatamente o que mudou. Seguir
uma forma nova com adendos escritos para a antiga produz um documento que
contradiz a si mesmo, e o erro só aparece um ou dois comandos depois.
