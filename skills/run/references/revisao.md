# Briefs de revisão — despachados pelo orquestrador

Este arquivo existe para o orquestrador **não** carregar seu conteúdo. Ele passa o caminho
deste arquivo aos revisores e nomeia qual seção cada um lê; quem lê é o revisor, na janela dele.

Os dois eixos são deliberadamente separados e **não se fundem**: um diff pode seguir todos os
padrões implementando a coisa errada, ou entregar exatamente o que a issue pediu quebrando as
convenções do repo. Fundir os achados faz um eixo mascarar o outro.

Cada revisor **escreve seu relatório em arquivo** e devolve **uma linha só** ao orquestrador —
`<n> achados · <caminho>`. O relatório inteiro no retorno encheria o contexto do orquestrador a
cada ticket, que é justamente o que este desenho evita.

Formato do relatório, em ambos os eixos: um achado por bloco, com arquivo e linha, o que está
errado, e a citação (do padrão ou da linha do spec) que sustenta o achado. Marque cada um como
**hard** (violação objetiva) ou **judgement** (leitura discutível). Sem preâmbulo, sem resumo
executivo, sem repetir o diff.

---

## Eixo Standards

Leia os padrões documentados do repo — `CLAUDE.md` da raiz e os `CLAUDE.md` por diretório que o
diff tocar, mais `docs/` onde houver convenção escrita. Rode o diff contra eles.

Sobre isso, aplique a baseline de smells abaixo (Fowler, _Refactoring_, cap. 3), que vale mesmo
onde o repo não documenta nada. Duas regras a prendem:

- **O repo manda.** Padrão documentado do repo sempre vence; onde ele endossa algo que a baseline
  marcaria, a baseline cala.
- **Sempre juízo.** Cada smell é heurística rotulada ("possível Feature Envy"), nunca violação
  dura — e, como qualquer padrão aqui, pule o que a ferramenta já garante (Prettier, ESLint, tsc).

- **Mysterious Name** — função, variável ou tipo cujo nome não revela o que faz ou guarda. → renomeie; se não sai nome honesto, o design está turvo.
- **Duplicated Code** — a mesma forma de lógica aparece em mais de um hunk ou arquivo do diff. → extraia a forma comum, chame dos dois lados.
- **Feature Envy** — método que mexe mais nos dados de outro objeto que nos próprios. → mova o método para junto dos dados que ele inveja.
- **Data Clumps** — os mesmos poucos campos ou parâmetros andam sempre juntos (um tipo querendo nascer). → junte num tipo só, passe ele.
- **Primitive Obsession** — primitivo ou string no lugar de um conceito de domínio que merece tipo próprio. → dê ao conceito seu tipinho.
- **Repeated Switches** — o mesmo `switch`/cascata de `if` sobre o mesmo tipo se repete no diff. → troque por polimorfismo, ou por um mapa que os dois pontos compartilham.
- **Shotgun Surgery** — uma mudança lógica obriga edições espalhadas por muitos arquivos do diff. → junte o que muda junto num módulo.
- **Divergent Change** — um arquivo ou módulo editado por vários motivos sem relação entre si. → separe, para cada módulo mudar por um motivo só.
- **Speculative Generality** — abstração, parâmetro ou gancho criados para necessidade que o spec não tem. → apague; inline de volta até uma necessidade real aparecer.
- **Message Chains** — navegação longa `a.b().c().d()` da qual o chamador não deveria depender. → esconda a caminhada atrás de um método no primeiro objeto.
- **Middle Man** — classe ou função que quase só delega adiante. → corte, chame o alvo real direto.
- **Refused Bequest** — subclasse ou implementador que ignora ou sobrescreve quase tudo que herda. → largue a herança, use composição.

Reporte, por arquivo/hunk onde couber: (a) todo ponto em que o diff viola padrão documentado —
cite o padrão (arquivo + a regra); (b) todo smell da baseline que enxergar — nomeie e cite o
hunk. Até 400 palavras no arquivo de relatório.

---

## Eixo Spec

Leia o spec e o ticket nos caminhos que o orquestrador passou. Rode o diff contra eles.

Reporte: (a) requisitos que o spec pediu e estão faltando ou pela metade; (b) comportamento no
diff que ninguém pediu (scope creep); (c) requisitos que parecem implementados mas cuja
implementação está errada. **Cite a linha do spec** em cada achado. Até 400 palavras no arquivo
de relatório.

Se não houver spec alcançável, escreva exatamente `sem spec disponível` no relatório e devolva
`0 achados · <caminho>` — não invente critério para preencher o eixo.
