# Erro de spec: onde registrar, por modo

Você chega aqui pelo passo 3 da `SKILL.md`, quando o spec conflita com o código.
Este arquivo cobre o registro do conflito e a métrica do passo 7, que só existe
quando o passo 3 disparou — por isso os dois estão fora do caminho quente.

A classificação (factual ou design) é da `SKILL.md`. Aqui é só o destino.

## Registrar o conflito

**Factual** — corrigir o spec:

- **Arquivo:** edite o doc e commite um `docs:` separado.
- **Tracker:** o spec é uma issue, publicada lá pelo `/to-spec`. Edite o corpo
  dela; não há commit.

**De design** — registrar no ticket o que o spec diz, o que o código mostra e por
que conflitam:

- **Arquivo:** edite o `.md` do ticket.
- **Tracker:** um comentário na issue (`gh issue comment`, `glab issue note`).

## A métrica do passo 7

Uma linha: data, ticket, tipo (factual | design), resumo de uma linha.

O arquivo é sempre versionado. A métrica mede a qualidade do spec ao longo do
tempo, então precisa sobreviver ao ticket.

- **Tickets como arquivo:** `spec-errors.md` ao lado deles — por exemplo,
  `.scratch/<feature>/issues/spec-errors.md`.
- **Tickets num tracker:** `docs/spec-errors.md` no repo, com o número da issue
  na linha. A métrica não vive só como comentário na issue: comentário espalhado
  não se soma.

O commit da linha acompanha o desfecho. No caso **factual**, ela entra no mesmo
`docs:` da correção do spec. No caso **design**, é um `docs:` próprio, commitado
**antes** de parar o ticket — parar sem commitar a métrica é perdê-la.
