# ticket

Plugin do Claude Code com o fluxo **`/ticket:implement`**: implementação disciplinada de um ticket por sessão — reivindicação, escopo sagrado, TDD, protocolo de erro de spec, commit → review → amend e um checkpoint de consistência automático a cada 3 tickets.

## O que vem no pacote

| Componente | O que faz |
|---|---|
| Skill `implement` | O fluxo em 8 passos, invocado com `/ticket:implement <ticket>` |
| Agent `checkpoint-reviewer` | Revisão de consistência **entre** tickets acumulados (Opus, effort high) — o olhar que nenhuma sessão isolada tem |
| Hook `runbook-checkpoint.py` | PostToolUse em todo `git commit`: conta os commits de ticket do operador e avisa quando o checkpoint vence. Registrado automaticamente na instalação do plugin |

## Pré-requisitos

1. **Plugin `mattpocock-skills`** — o `/tdd` e o `code-review` do fluxo vêm dele:

   ```
   /plugin marketplace add mattpocock/skills
   /plugin install mattpocock-skills@mattpocock
   ```

2. **Setup por projeto** — no repo em que o fluxo vai rodar, rode uma vez:

   ```
   /setup-matt-pocock-skills
   ```

   Isso cria `docs/agents/issue-tracker.md` (onde os tickets vivem: arquivos `.md`, GitHub, GitLab...) e o vocabulário de rótulos que a skill consulta.

## Instalação

```
/plugin marketplace add GeraldoNeto123/ticket
/plugin install ticket@ticket
```

Reinicie a sessão (ou `/reload-plugins`) e invoque:

```
/ticket:implement <número da issue ou caminho do ticket>
```

## O fluxo, em uma linha por passo

1. **Reivindicar** — bloqueadores primeiro (frontier), depois dono; ticket de outra pessoa para o fluxo.
2. **Implementar** — escopo restrito ao ticket, `/tdd` nas costuras que o spec registrou.
3. **Erro de spec** — factual corrige na hora; design registra, para o ticket e escala. Na dúvida, é design.
4. **Verificar** — evidência antes de alegação.
5. **Commit → review → amend** — a revisão só enxerga trabalho commitado; 1 ticket = 1 commit. Push é manual, fora do fluxo.
6. **Encerrar** — *feito* ≠ *fechado*: quem fecha issue é o merge, não o push.
7. **Métrica** — cada erro de spec vira uma linha versionada em `spec-errors.md`.
8. **Checkpoint** — a cada 3 tickets, o agent revisa o acumulado; correções pequenas viram um `refactor:`, achados grandes viram tickets novos.

## Multi-operador

A tag de checkpoint é escopada por operador (`runbook-checkpoint/<slug do e-mail do git>`), e o hook conta apenas commits do próprio autor — mais de uma pessoa pode rodar o fluxo no mesmo repo sem sobrescrever o ciclo alheio. Repos que usavam a tag legada sem escopo recebem instrução de migração automaticamente.

## Licença

[MIT](./LICENSE)
