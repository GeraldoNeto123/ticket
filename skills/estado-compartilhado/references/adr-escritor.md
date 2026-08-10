# Ticket que acrescenta um escritor a campo governado por ADR

Leia este arquivo quando o código de um ticket for escrever num campo que um ADR
mapeia. O portão do `/ticket:estado-compartilhado` enumerou os escritores antes
de a fila existir; ticket que cria escritor sem devolver a informação ao ADR
desfaz o portão um passo adiante, e o defeito reaparece no checkpoint, caro.

**Ler o ADR não basta.** Leitura não produz a linha que o próximo ticket precisa
encontrar, e o próximo ticket é uma sessão limpa que só tem o documento.

Dois casos:

- O escritor **obedece** à regra já decidida — quem ganha no conflito, o que cada
  um faz quando não sabe o valor. Acrescentá-lo à lista do ADR é correção
  **factual**: um commit `docs:` próprio, e o ticket segue.
- O escritor **não cabe** na regra — pede outro critério de desempate, ou o caso
  "não sabe" não estava previsto. Isso é erro de spec **de design**: registre no
  ticket o que o spec pede, o que o ADR decide e por que conflitam, e **escale**
  (numa fila, devolva `SPEC_DESIGN`). Implementar por cima reabre a decisão sem
  quem a tomou.

Uma ressalva: **ADR sempre commita, inclusive em modo tracker.** Editar o corpo
da issue vale para o spec, que vive lá. O ADR mora em `docs/adr/` nos dois modos,
então a correção é sempre um `docs:`.
