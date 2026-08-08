#!/usr/bin/env python3
"""Mantém honesto o ciclo de checkpoint do fluxo /ticket:implement.

Roda como hook PostToolUse depois de todo `git commit`. Faz o que o passo 8 da
skill `/ticket:implement` pedia, só que fora do alcance do esquecimento do modelo:

  - conta os commits de ticket **do operador** desde a tag escopada dele
    (`runbook-checkpoint-<slug do e-mail do git>`) — cada operador tem ciclo
    próprio, para que dois não sobrescrevam a tag um do outro;
  - ao atingir o limite, injeta a ordem de rodar o `checkpoint-reviewer`;
  - abre o primeiro ciclo num repo que adotou o fluxo e ainda não tem tag —
    sem isso o ciclo nunca começava, porque a tag só nascia dentro do passo 8
    e o passo 8 só era acionado por este aviso;
  - se a tag sumiu num repo que já usou o fluxo, avisa alto em vez de deixar
    o acumulado ser descartado em silêncio;
  - se só existe a tag legada sem escopo, instrui a migração **e segue
    contando por ela**, para que a falta de migração atrase o checkpoint em
    vez de cancelá-lo;
  - detecta o caso de um checkpoint que rodou sem a tag ter sido movida.

Silencioso em qualquer repo que não use o fluxo, e em qualquer sessão que não
tenha invocado `/ticket:implement` ou `/ticket:run`.

A tag é **local, nunca publicada**. Ela é um marcador de progresso pessoal —
escopado ao operador — e não descreve nada do projeto, então ninguém mais tem
uso para ela. Publicá-la, e ainda por cima reescrevê-la com `push -f` a cada
ciclo, fazia o `git fetch` dos outros desenvolvedores recusar com "would
clobber existing tag": custo real para o time, benefício zero.
"""

import json
import os
import re
import subprocess
import sys

TAG_BASE = "runbook-checkpoint"
LIMITE = 5
REGISTRO = os.path.expanduser("~/.claude/state/runbook-checkpoint-repos")

# Só a sessão que de fato entrou no fluxo recebe o aviso. Antes o hook avisava
# toda sessão que commitasse e delegava ao modelo a decisão de ignorar, o que
# transformava o checkpoint em ruído de fundo em sessão de triagem, de review,
# de correção avulsa — e ruído recorrente é ruído que se aprende a ignorar.
#
# O discriminador é a **invocação**, não a menção: uma sessão que conversa
# sobre o fluxo não é o fluxo.
#
# Por isso a checagem é estrutural, e não textual. Procurar a string
# `"skill":"ticket:implement"` no transcript cru parece bastar e não basta: a
# própria sessão que mantém este hook escreve esses literais na conversa e
# passa a se declarar sessão do fluxo. Foi o que aconteceu no primeiro teste
# desta função. Só contam, então:
#   - bloco `tool_use` da ferramenta Skill cujo `input.skill` é do fluxo;
#   - `<command-name>` dentro de mensagem do **usuário** — texto que o assistente
#     escreve não conta, e é lá que a menção mora.
FLUXO = {"ticket:implement", "ticket:run"}
COMANDO_DE_BARRA = re.compile(r"<command-name>/?ticket:(implement|run)</command-name>")

# Marcador de que o repo adotou o fluxo, independente de já existir tag. É o
# arquivo que a skill lê antes de tudo para saber onde vivem os tickets; sem
# um sinal assim, "usa o fluxo" só podia ser deduzido da tag — e a tag era
# justamente o que ainda não existia no primeiro ciclo.
MARCADOR = os.path.join("docs", "agents", "issue-tracker.md")

# Reconhece `git commit` dentro do comando que o Bash acabou de rodar. A
# filtragem mora aqui, e não no campo `if` do hooks.json, porque aquele campo
# usa a sintaxe de regra de permissão — que não enxerga dentro de comando
# composto (`git add -A && git commit -m ...`) nem de substituição `$(...)`,
# que são justamente as duas formas em que o commit costuma chegar.
#
# O `git` precisa estar em posição de comando (início, ou logo depois de um
# separador de shell), senão `echo "vou git commit depois"` dispara o hook. Os
# tokens opcionais no meio cobrem `git -C <caminho> commit`; recusar aspas ali
# impede que a regra atravesse uma string.
COMMIT = re.compile(
    r"""(?:^|[\n;&|(]|\bthen\b|\bdo\b|\belse\b)\s*git\s+(?:[^\s'"]+\s+){0,3}commit\b"""
)

# Prefixos que o próprio fluxo gera e que não contam como ticket.
NAO_CONTA = re.compile(r"^[0-9a-f]+\s+(docs|chore|refactor|ci|style|test)[(:]", re.I)
# Só o formato canônico do passo 8 (`refactor: checkpoint <sha..sha> — ...`)
# é um checkpoint. Commits que apenas mencionam a palavra — triagem de
# achados, docs sobre o fluxo — não fecham ciclo nenhum.
CHECKPOINT = re.compile(r"^[0-9a-f]+\s+refactor(\([^)]*\))?:\s*checkpoint\b", re.I)

# Rodapé repetido em todo aviso. O caso "sessão que não é do fluxo" saiu daqui
# porque o hook agora filtra por invocação e essa sessão nem chega a ver o
# aviso. Sobra o subagent: ele roda dentro do fluxo, então casa o filtro, mas o
# checkpoint pertence ao orquestrador.
FORA_DO_FLUXO = (
    "Se você é um subagent despachado por uma fila /ticket:run, o checkpoint "
    "não é seu: devolva `CHECKPOINT_DUE` ao orquestrador e siga."
)


def sessao_do_fluxo(entrada):
    """A sessão que commitou invocou /ticket:implement ou /ticket:run?

    Na dúvida devolve False: avisar quem não pediu é o defeito que este filtro
    existe para corrigir. Um falso negativo custa um ciclo de atraso — o aviso
    volta no próximo commit da sessão certa.
    """
    caminho = entrada.get("transcript_path")
    if not caminho:
        return False
    try:
        with open(caminho, encoding="utf-8", errors="replace") as f:
            for linha in f:
                try:
                    registro = json.loads(linha)
                except (json.JSONDecodeError, ValueError):
                    continue
                mensagem = registro.get("message")
                if not isinstance(mensagem, dict):
                    continue
                papel = mensagem.get("role")
                conteudo = mensagem.get("content")

                # Mensagem do usuário vem como string quando é um comando de
                # barra — que é justamente o caso que interessa aqui.
                if papel == "user" and isinstance(conteudo, str):
                    if COMANDO_DE_BARRA.search(conteudo):
                        return True
                    continue

                if not isinstance(conteudo, list):
                    continue
                for bloco in conteudo:
                    if not isinstance(bloco, dict):
                        continue
                    if papel == "assistant" and bloco.get("name") == "Skill":
                        entrada_skill = bloco.get("input")
                        if (
                            isinstance(entrada_skill, dict)
                            and entrada_skill.get("skill") in FLUXO
                        ):
                            return True
                    elif papel == "user" and bloco.get("type") == "text":
                        if COMANDO_DE_BARRA.search(bloco.get("text") or ""):
                            return True
    except OSError:
        return False
    return False


def git(*args, cwd):
    """Roda git e devolve stdout limpo, ou None se o comando falhar."""
    try:
        r = subprocess.run(
            ("git",) + args, cwd=cwd, capture_output=True, text=True, timeout=15
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return r.stdout.strip() if r.returncode == 0 else None


def avisar(*textos):
    """Emite os avisos acumulados como contexto para o modelo e encerra."""
    texto = "\n\n".join(t for t in textos if t)
    if not texto:
        sys.exit(0)
    json.dump(
        {
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": texto,
            }
        },
        sys.stdout,
    )
    sys.exit(0)


def registrados():
    try:
        with open(REGISTRO, encoding="utf-8") as f:
            return {linha.strip() for linha in f if linha.strip()}
    except OSError:
        return set()


def registrar(raiz):
    if raiz in registrados():
        return
    try:
        os.makedirs(os.path.dirname(REGISTRO), exist_ok=True)
        with open(REGISTRO, "a", encoding="utf-8") as f:
            f.write(raiz + "\n")
    except OSError:
        pass


def main():
    try:
        entrada = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return

    comando = (entrada.get("tool_input") or {}).get("command") or ""
    if not COMMIT.search(comando):
        return

    if not sessao_do_fluxo(entrada):
        return

    cwd = entrada.get("cwd") or os.getcwd()
    raiz = git("rev-parse", "--show-toplevel", cwd=cwd)
    if not raiz:
        return  # não é repo git

    # Worktree vinculada: o ciclo de checkpoint pertence à árvore principal.
    # Sem esta guarda, um subagent implementando num worktree receberia a
    # ordem de checkpoint no meio do trabalho — as tags são compartilhadas.
    git_dir = git("rev-parse", "--absolute-git-dir", cwd=raiz)
    comum = git("rev-parse", "--git-common-dir", cwd=raiz)
    if git_dir and comum and os.path.realpath(git_dir) != os.path.realpath(
        os.path.join(raiz, comum) if not os.path.isabs(comum) else comum
    ):
        return

    email = git("config", "user.email", cwd=raiz) or ""
    slug = (
        re.sub(r"[^a-z0-9]+", "-", email.split("@")[0].lower()).strip("-") or "anon"
    )
    tag = f"{TAG_BASE}-{slug}"
    tag_separador_antigo = f"{TAG_BASE}/{slug}"

    def tem(ref):
        return git("rev-parse", "-q", "--verify", f"refs/tags/{ref}", cwd=raiz) is not None

    ja_registrado = raiz in registrados()
    usa_fluxo = ja_registrado or os.path.isfile(os.path.join(raiz, MARCADOR))

    avisos = []

    # Qual referência ancora o ciclo. A tag escopada é a certa; a legada serve
    # de base provisória para que um repo não-migrado siga sendo contado.
    if tem(tag):
        base = tag
    elif tem(TAG_BASE):
        base = TAG_BASE
        avisos.append(
            f"Este repo ainda usa a tag legada `{TAG_BASE}` (sem escopo de operador). "
            f"Migre preservando o intervalo acumulado:\n"
            f"    git tag {tag} {TAG_BASE}\n"
            f"A legada pode ser apagada quando todos os operadores migrarem. "
            f"Até lá a contagem abaixo usa `{TAG_BASE}` como base."
        )
    else:
        base = None

    if base is None:
        if not usa_fluxo:
            return  # repo que não usa o fluxo — silêncio
        if ja_registrado:
            avisar(
                f"A tag `{tag}` não existe neste repo, mas ele já usou o fluxo "
                f"/ticket:implement antes. Isso normalmente significa clone novo, outra "
                f"máquina ou tag apagada — e NÃO que o acumulado foi revisado.\n\n"
                f"Não recrie a tag em silêncio: pare e pergunte ao usuário se deve "
                f"rodar o `checkpoint-reviewer` sobre o acumulado ou recomeçar do "
                f"HEAD. A tag é local e nunca é publicada, então não há remoto de "
                f"onde recuperá-la — clone novo começa ciclo do zero por desenho.",
                FORA_DO_FLUXO,
            )
        avisar(
            f"Este repo tem `{MARCADOR}` (adotou o fluxo /ticket:implement) mas ainda "
            f"não tem a tag de checkpoint `{tag}` — então nenhum ciclo está aberto e "
            f"o checkpoint nunca vai vencer. Abra o primeiro ciclo agora:\n"
            f"    git tag {tag}\n"
            f"A tag ancora no HEAD: o ciclo passa a contar deste commit em diante, e "
            f"o que veio antes fica de fora. Se houver trabalho anterior que nunca "
            f"passou por checkpoint, pergunte ao usuário se a âncora deve recuar. "
            f"A tag é local: não a publique.",
            FORA_DO_FLUXO,
        )

    registrar(raiz)

    if tem(tag_separador_antigo):
        avisos.append(
            f"Sobrou a tag `{tag_separador_antigo}`, do separador antigo (`/`) usado "
            f"antes da v1.1.1. Ela não é mais lida por nada e confunde "
            f"`git tag -l '{TAG_BASE}*'`. Apague quando for conveniente:\n"
            f"    git tag -d {tag_separador_antigo} && git push origin :{tag_separador_antigo}"
        )

    argumentos = ["log", "--oneline", "--no-merges"]
    if email:
        argumentos.append(f"--author={email}")
    log = git(*argumentos, f"{base}..HEAD", cwd=raiz)
    if log is None:
        avisar(*avisos)  # a contagem falhou, mas o que já se sabe não se perde
    linhas = [l for l in log.splitlines() if l.strip()]

    tickets = [l for l in linhas if not NAO_CONTA.search(l)]
    n = len(tickets)

    if any(CHECKPOINT.search(l) for l in linhas):
        avisos.append(
            f"Existe um commit de checkpoint no intervalo `{base}..HEAD`, mas a tag "
            f"não foi movida — o ciclo do passo 8 ficou pela metade. Confirme com "
            f"`git log --oneline {base}..HEAD` e, se o checkpoint de fato já rodou, "
            f"feche o ciclo agora:\n"
            f"    git tag -f {tag}"
        )

    if n >= LIMITE:
        avisos.append(
            f"{n} commits de ticket acumulados desde `{base}` (limite: {LIMITE}). "
            f"Rode o passo 8 da /ticket:implement agora, antes de seguir:\n\n"
            f"1. Dispare o agent `checkpoint-reviewer` com o intervalo "
            f"`{base}..HEAD` e o diretório dos tickets.\n"
            f"2. Correções pequenas viram um único commit `refactor:`; defeitos "
            f"reais viram achados em quarentena, fora da fila.\n"
            f"3. Mova a tag (local, não publique): `git tag -f {tag}`"
        )

    if avisos:
        avisar(*avisos, FORA_DO_FLUXO)


if __name__ == "__main__":
    main()
