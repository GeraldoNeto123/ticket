---
name: run
description: "Executa a fila de tickets de uma feature em sequência: um subagent fresco por ticket rodando /ticket:implement, ledger de progresso, checkpoint no orquestrador e escalada explícita — nada é descartado em silêncio."
disable-model-invocation: true
---

# /ticket:run

**Argumento desta sessão:** $ARGUMENTS

O argumento aponta o spec/preâmbulo da feature e onde vivem os tickets dela (diretório, rótulo ou issue-mãe). Você é o **orquestrador**: despacha um subagent fresco por ticket, sequencialmente, e nunca implementa nada você mesmo. Cada ticket foi dimensionado pelo `/to-tickets` para caber numa janela limpa — é o subagent que ganha essa janela; se a implementação acontecesse aqui, o terceiro ticket já rodaria sobre o contexto acumulado dos dois primeiros, exatamente o que o fluxo existe para evitar.

Paralelismo é proibido nesta versão, por design: tickets são fatias verticais e colidem nos arquivos de junção (rotas, schema, registro de DI). Um de cada vez, sempre.

## 1. Montar a fila

Leia `docs/agents/issue-tracker.md` para saber o modo (arquivo ou tracker) e o CLI. Liste os tickets da feature com o campo **Blocked by** de cada um e monte a **frontier**: os tickets cujos bloqueadores estão todos done. Trabalhe sempre a frontier; quando um ticket termina, recalcule.

Leia o spec só o suficiente para saber referenciá-lo. **Não cole conteúdo de spec nem de tickets nos prompts de dispatch** — passe caminhos e referências. Tudo que você cola num prompt fica residente no seu contexto até o fim da fila; caminhos custam uma linha.

## 2. Ledger

Antes do primeiro dispatch, crie `.scratch/ticket-run/<slug-da-feature>.md` com uma linha por ticket: referência, status, SHA (quando houver), observação de uma linha. Atualize **após cada ticket**, não em lote.

O ledger é seu mapa de recuperação: os SHAs que ele nomeia existem no git mesmo quando seu contexto já não lembra deles. Se esta sessão for compactada no meio da fila, o ledger é o que permite retomar sem reexecutar nada.

## 3. O loop

Primeiro, resolva o caminho da skill `implement`: ela mora ao lado desta, em `<diretório-base desta skill>/../implement/SKILL.md` (o diretório-base aparece no cabeçalho quando esta skill é invocada). Resolva para caminho absoluto uma vez e reuse em todos os dispatches.

O subagent **lê esse arquivo, não invoca a skill**: `implement` é porta de entrada humana (`disable-model-invocation`) e o Skill tool recusa invocação vinda de modelo — inclusive de subagents. Ler o arquivo entrega as mesmas instruções pelo caminho que a política permite, no padrão task-brief: "leia isto primeiro; são seus requisitos".

Para cada ticket da frontier, despache **um** subagent com um prompt mínimo:

- Leia `<caminho absoluto da implement/SKILL.md>` primeiro e siga-o como suas instruções de trabalho. Onde o arquivo diz `$ARGUMENTS`, vale: ticket `<referência>`, spec em `<caminho do spec>`.
- Execute o fluxo até o fim do passo 7. **Não execute o passo 8 (checkpoint)** — se o aviso do hook chegar no commit, termine o passo 5 normalmente e inclua `CHECKPOINT_DUE` no retorno.
- Retorne **apenas** este contrato: `STATUS` (uma das opções abaixo) · SHA do commit (se houver) · resumo dos testes em uma linha · observações em até três linhas. Sem diff, sem histórico, sem narrativa.

Status possíveis e o que fazer com cada um:

- **`DONE`** — registre no ledger e siga para o próximo da frontier. Não pause para aprovação entre tickets: este é o modo autônomo; quem quer acompanhar de perto roda `/ticket:implement` à mão.
- **`DONE` + `CHECKPOINT_DUE`** — antes do próximo ticket, **você** roda o passo 8 da `/ticket:implement` aqui no orquestrador: dispare o agent `checkpoint-reviewer` com o intervalo e o local dos tickets, aplique correções pequenas num `refactor: checkpoint ...`, abra tickets para achados grandes (com as regras de dedup e rótulo de lá) e mova/publique a tag. O checkpoint é seu por dois motivos: subagent não despacha agent, e o acumulado é responsabilidade de quem enxerga a fila inteira. Registre o resultado no ledger e siga — achados novos nascem `needs-triage`, então **não** entram nesta frontier.
- **`SPEC_DESIGN`** — o subagent encontrou erro de spec de design, registrou o conflito no ticket e parou (passo 3 da implement). A skill de lá manda escalar para "uma sessão de effort alto apontada para esse registro" — **essa sessão é esta**. Pare o loop, apresente o registro ao usuário e espere a decisão dele. Decidido, o ticket volta à frontier.
- **`BLOCKED`** — dono alheio, dependência externa, ou o subagent travou sem progresso. Pare e pergunte ao usuário. Nunca reordene a fila em silêncio para "contornar": bloqueio é informação, não obstáculo a esconder.

Todo desfecho — inclusive os ruins — vira linha no ledger. Descarte silencioso é proibido: um ticket que "sumiu" da fila é um bug seu.

## 4. Encerramento

Frontier vazia = fila encerrada. Se o último lote não fechou um ciclo de checkpoint, rode o passo 8 uma última vez antes do resumo — fila encerrada com acumulado não revisado é trabalho pela metade.

Monte o resumo final **a partir do ledger**, não de memória: tickets concluídos com SHAs, observações acumuladas, tickets novos abertos pelos checkpoints, e o que ficou bloqueado ou aguardando decisão. Se sobraram tickets inalcançáveis (bloqueador nunca resolvido, ciclo de dependência), aponte-os explicitamente — são a primeira coisa que o usuário precisa destravar.
