# Ticket que acrescenta um escritor a campo governado por ADR

Você chega aqui pelo passo 2 da `SKILL.md`, quando o código que este ticket vai
escrever toca um campo que um ADR mapeia. Está fora do caminho quente porque só
alguns tickets criam escritor; os outros pagariam o contexto à toa.

**Ler o ADR não basta.** Leitura não produz a linha que o próximo ticket precisa
encontrar, e o próximo ticket é uma sessão limpa que só tem o documento.

O caso cai nos dois do passo 3, sem protocolo novo:

- O escritor **obedece** à regra já decidida — quem ganha no conflito, o que cada
  um faz quando não sabe o valor. Acrescentá-lo à lista do ADR é correção
  **factual**: entra no mesmo commit `docs:`, e o ticket segue.
- O escritor **não cabe** na regra — pede outro critério de desempate, ou o caso
  "não sabe" não estava previsto. Isso é **design**: registre no ticket e
  **escale**.

## Duas ressalvas

O roteamento para o passo 3 traz junto regras que **não** valem aqui:

- **ADR sempre commita, inclusive em tracker.** Editar o corpo da issue vale para
  o spec, que o `/to-spec` publica lá. O ADR mora em `docs/adr/` nos dois modos,
  então a correção é sempre um `docs:`.
- **Só o caso de design entra na métrica do passo 7.** Escritor que obedece à
  regra é evolução normal do código e não diz nada sobre a qualidade do spec;
  contá-lo infla o `spec-errors.md` com trabalho saudável. Escritor que exige
  critério novo é o portão de modelagem tendo saído incompleto — que é exatamente
  o que a métrica mede.

O portão do `/ticket:split` enumerou os escritores antes de a fila existir.
Ticket que cria escritor sem devolver a informação ao ADR desfaz o portão um
passo adiante, e o defeito reaparece no checkpoint, caro.
