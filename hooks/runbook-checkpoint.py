#!/usr/bin/env python3
"""Mantém honesto o ciclo de checkpoint do fluxo /ticket:implement.

Roda como hook PostToolUse depois de todo `git commit`. Faz o que o passo 8 da
skill `/ticket:implement` pedia, só que fora do alcance do esquecimento do modelo:

  - conta os commits de ticket **do operador** desde a tag escopada dele
    (`runbook-checkpoint/<slug do e-mail do git>`) — cada operador tem ciclo
    próprio, para que dois não sobrescrevam a tag um do outro;
  - ao atingir o limite, injeta a ordem de rodar o `checkpoint-reviewer`;
  - se a tag sumiu num repo que já usou o fluxo, avisa alto em vez de deixar
    o acumulado ser descartado em silêncio;
  - se só existe a tag legada sem escopo, instrui a migração que preserva
    o intervalo;
  - detecta o caso de um checkpoint que rodou sem a tag ter sido movida.

Silencioso em qualquer repo que não use o fluxo.
"""

import json
import os
import re
import subprocess
import sys

TAG_BASE = "runbook-checkpoint"
LIMITE = 3
REGISTRO = os.path.expanduser("~/.claude/state/runbook-checkpoint-repos")

# Prefixos que o próprio fluxo gera e que não contam como ticket.
NAO_CONTA = re.compile(r"^[0-9a-f]+\s+(docs|chore|refactor|ci|style|test)[(:]", re.I)
CHECKPOINT = re.compile(r"checkpoint", re.I)


def git(*args, cwd):
    """Roda git e devolve stdout limpo, ou None se o comando falhar."""
    try:
        r = subprocess.run(
            ("git",) + args, cwd=cwd, capture_output=True, text=True, timeout=15
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return r.stdout.strip() if r.returncode == 0 else None


def avisar(texto):
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
    tag = f"{TAG_BASE}/{slug}"

    def tem(ref):
        return git("rev-parse", "-q", "--verify", f"refs/tags/{ref}", cwd=raiz) is not None

    if not tem(tag):
        if tem(TAG_BASE):
            avisar(
                f"Este repo tem a tag legada `{TAG_BASE}` (sem escopo de operador), "
                f"mas não a sua `{tag}`. Migre preservando o intervalo acumulado:\n"
                f"    git tag {tag} {TAG_BASE} && git push origin {tag}\n"
                f"A legada pode ser apagada quando todos os operadores migrarem."
            )
        if raiz not in registrados():
            return  # repo que não usa o fluxo — silêncio
        avisar(
            f"A tag `{tag}` não existe neste repo, mas ele já usou o fluxo /ticket:implement "
            f"antes. Isso normalmente significa clone novo, outra máquina ou tag "
            f"apagada — e NÃO que o acumulado foi revisado.\n\n"
            f"Não recrie a tag em silêncio. Primeiro tente recuperá-la do remoto "
            f"(`git fetch origin --tags`). Se ela não existir lá, pare e pergunte "
            f"ao usuário se deve rodar o `checkpoint-reviewer` sobre o acumulado "
            f"ou recomeçar do HEAD."
        )

    registrar(raiz)

    argumentos = ["log", "--oneline", "--no-merges"]
    if email:
        argumentos.append(f"--author={email}")
    log = git(*argumentos, f"{tag}..HEAD", cwd=raiz)
    if log is None:
        return
    linhas = [l for l in log.splitlines() if l.strip()]

    tickets = [l for l in linhas if not NAO_CONTA.search(l)]
    n = len(tickets)

    orfao = any(CHECKPOINT.search(l) for l in linhas)
    if orfao:
        avisar(
            f"Existe um commit de checkpoint no intervalo `{tag}..HEAD`, mas a tag "
            f"não foi movida — o ciclo do passo 8 ficou pela metade. Confirme com "
            f"`git log --oneline {tag}..HEAD` e, se o checkpoint de fato já rodou, "
            f"feche o ciclo agora:\n"
            f"    git tag -f {tag} && git push -f origin {tag}"
        )

    if n >= LIMITE:
        avisar(
            f"{n} commits de ticket acumulados desde `{tag}` (limite: {LIMITE}). "
            f"Rode o passo 8 da /ticket:implement agora, antes de seguir:\n\n"
            f"1. Dispare o agent `checkpoint-reviewer` com o intervalo "
            f"`{tag}..HEAD` e o diretório dos tickets.\n"
            f"2. Correções pequenas viram um único commit `refactor:`; achados "
            f"grandes viram tickets novos.\n"
            f"3. Mova e publique a tag: `git tag -f {tag} && git push -f origin {tag}`"
        )


if __name__ == "__main__":
    main()
