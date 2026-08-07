#!/usr/bin/env python3
"""Acusa documento do fluxo que nasce com âncora `arquivo:linha`.

Roda como hook PostToolUse depois de todo `Write`/`Edit` em `.md`. A regra que
ele checa já está escrita em cinco lugares — passo 2 da `/ticket:implement`,
`references/checkpoint.md`, o agent `checkpoint-reviewer` e as duas skills que
produzem spec e tickets — e vazou assim mesmo: numa feature real, três
checkpoints seguidos gastaram correções pequenas com âncoras deslocadas, e o
documento que mais doeu (um contrato lido por outro time) foi escrito por uma
sessão que não rodava skill nenhuma. Instrução não alcança quem não a lê;
checagem alcança — e é por isso que este hook existe em vez de uma sexta
instrução.

Ele **não bloqueia**: quando roda, o arquivo já foi escrito. O aviso pede a
troca por símbolo ou trecho antes de seguir, que é uma edição barata agora e um
achado repetido de checkpoint depois.

Silencioso em qualquer repo que não use o fluxo.
"""

import json
import os
import re
import subprocess
import sys

# Marcador de que o repo adotou o fluxo — o mesmo que o `runbook-checkpoint.py`
# usa. Sem esta guarda o hook opinaria sobre o markdown de qualquer projeto.
MARCADOR = os.path.join("docs", "agents", "issue-tracker.md")

# A extensão é o que separa âncora de código de tudo o mais que tem dois-pontos
# seguido de número: `localhost:3000`, `18:30`, `v1.2:beta`. Sem ela o hook
# viraria ruído e seria desligado — que é o destino de todo aviso que erra.
EXTENSOES = (
    "ts|tsx|js|jsx|mjs|cjs|py|go|rb|java|kt|php|cs|rs|swift|sql|vue|svelte"
    "|css|scss|html|json|ya?ml|toml|sh|prisma|graphql|proto"
)
ANCORA = re.compile(rf"[\w./@-]+\.(?:{EXTENSOES}):\d+", re.I)

# Cerca de bloco de código. Trecho colado que cita faixa de linha descreve o
# próprio trecho — não navega até ele — e essa é a exceção legítima à regra.
CERCA = re.compile(r"^\s{0,3}(```|~~~)")

LIMITE_AMOSTRA = 5


def git(*args, cwd):
    """Roda git e devolve stdout limpo, ou None se o comando falhar."""
    try:
        r = subprocess.run(
            ("git",) + args, cwd=cwd, capture_output=True, text=True, timeout=10
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return r.stdout.strip() if r.returncode == 0 else None


def texto_escrito(entrada):
    """O que esta chamada acabou de gravar — não o arquivo inteiro.

    Em `Edit`, olhar só o `new_string` é deliberado: reclamar de âncora que já
    estava no arquivo transformaria toda edição vizinha num aviso, e o aviso que
    culpa quem não escreveu é o primeiro a ser ignorado.
    """
    tool_input = entrada.get("tool_input") or {}
    partes = [tool_input.get("content"), tool_input.get("new_string")]
    for edicao in tool_input.get("edits") or []:
        if isinstance(edicao, dict):
            partes.append(edicao.get("new_string"))
    return "\n".join(p for p in partes if isinstance(p, str))


def ancoras_fora_de_cerca(texto):
    """Âncoras encontradas, ignorando o que está dentro de bloco cercado."""
    achadas, dentro = [], False
    for linha in texto.splitlines():
        if CERCA.match(linha):
            dentro = not dentro
            continue
        if not dentro:
            achadas.extend(ANCORA.findall(linha))
    unicas = []
    for a in achadas:
        if a not in unicas:
            unicas.append(a)
    return unicas


def main():
    try:
        entrada = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return

    caminho = (entrada.get("tool_input") or {}).get("file_path") or ""
    if not caminho.lower().endswith(".md"):
        return  # antes de qualquer git: este hook roda em toda escrita

    ancoras = ancoras_fora_de_cerca(texto_escrito(entrada))
    if not ancoras:
        return

    diretorio = os.path.dirname(os.path.abspath(caminho)) or os.getcwd()
    if not os.path.isdir(diretorio):
        return
    raiz = git("rev-parse", "--show-toplevel", cwd=diretorio)
    if not raiz or not os.path.isfile(os.path.join(raiz, MARCADOR)):
        return  # repo que não usa o fluxo — silêncio

    amostra = ", ".join(f"`{a}`" for a in ancoras[:LIMITE_AMOSTRA])
    if len(ancoras) > LIMITE_AMOSTRA:
        amostra += f" (e mais {len(ancoras) - LIMITE_AMOSTRA})"

    try:
        relativo = os.path.relpath(os.path.abspath(caminho), raiz)
    except ValueError:
        relativo = caminho

    json.dump(
        {
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": (
                    f"`{relativo}` acabou de receber referência de linha: {amostra}.\n\n"
                    f"Documento do fluxo aponta código pelo **símbolo** ou pelo trecho "
                    f"citado, nunca pelo número da linha: a numeração se move a cada "
                    f"ticket implementado, e quem ler depois edita a linha errada com um "
                    f"diff de aparência plausível — o modo de falha é silencioso, não "
                    f"barulhento. Troque agora, enquanto o contexto para localizar o "
                    f"símbolo ainda está aberto.\n\n"
                    f"Se a citação descreve um trecho colado (faixa de linha de um "
                    f"exemplo, saída de ferramenta) em vez de navegar até ele, cerque-a "
                    f"em bloco de código: é a exceção legítima, e a cerca é o que a "
                    f"distingue de uma âncora."
                ),
            }
        },
        sys.stdout,
    )


if __name__ == "__main__":
    main()
