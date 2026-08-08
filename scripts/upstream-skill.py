#!/usr/bin/env python3
"""Imprime o caminho absoluto do `SKILL.md` de uma skill de outro plugin.

As skills `/ticket:spec` e `/ticket:split` envolvem o `to-spec` e o `to-tickets`
do `mattpocock-skills`: elas **leem** aquele arquivo e o seguem, porque os dois
são `disable-model-invocation` e o Skill tool recusa invocação vinda de modelo —
o mesmo motivo pelo qual a `/ticket:run` lê a `implement` em vez de invocá-la.

Envolver, e não forkar, é deliberado: o upstream continua se atualizando sem
merge nenhum. O preço é este script, porque o caminho carrega a versão instalada
(`.../mattpocock-skills/1.2.2/...`) e não pode ser fixado.

Uso:
    upstream-skill.py to-tickets
    upstream-skill.py to-spec mattpocock-skills@mattpocock

Sai com código 1 e uma mensagem acionável quando não encontra — nunca chuta.
Chutar aqui significa seguir instruções de uma versão que não é a que roda.
"""

import glob
import json
import os
import re
import subprocess
import sys

PLUGIN_PADRAO = "mattpocock-skills@mattpocock"
BUCKET = os.path.join("skills", "engineering")


def config_dir():
    return os.path.expanduser(os.environ.get("CLAUDE_CONFIG_DIR", "~/.claude"))


def por_manifesto(plugin):
    """Rota 1: o manifesto de instalação diz exatamente qual cópia roda."""
    caminho = os.path.join(config_dir(), "plugins", "installed_plugins.json")
    try:
        with open(caminho, encoding="utf-8") as f:
            dados = json.load(f)
        return dados["plugins"][plugin][0]["installPath"]
    except (OSError, ValueError, KeyError, IndexError, TypeError):
        return None


def por_versao(plugin):
    """Rota 2: a CLI dá a versão instalada; o glob acha a pasta dela.

    Existe porque o formato do manifesto é observado, não documentado — se ele
    mudar, a resolução cai aqui em vez de falhar.
    """
    nome = plugin.split("@")[0]
    try:
        r = subprocess.run(
            ["claude", "plugin", "details", plugin],
            capture_output=True, text=True, timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if r.returncode != 0:
        return None
    m = re.search(r"^\S+\s+(\d+\.\d+\.\d+\S*)", r.stdout.strip())
    if not m:
        return None
    achados = glob.glob(
        os.path.join(config_dir(), "plugins", "cache", "*", nome, m.group(1))
    )
    return achados[0] if len(achados) == 1 else None


def main():
    if not 2 <= len(sys.argv) <= 3:
        print(__doc__, file=sys.stderr)
        return 2

    skill = sys.argv[1]
    plugin = sys.argv[2] if len(sys.argv) == 3 else PLUGIN_PADRAO

    for rota in (por_manifesto, por_versao):
        raiz = rota(plugin)
        if not raiz:
            continue
        caminho = os.path.join(raiz, BUCKET, skill, "SKILL.md")
        if os.path.isfile(caminho):
            print(os.path.abspath(caminho))
            return 0

    print(
        f"Não encontrei a skill `{skill}` do plugin `{plugin}`.\n"
        f"Sem ela esta skill não tem o que seguir — e improvisar um substituto "
        f"produziria um documento com a forma errada para o resto do fluxo.\n"
        f"Instale ou atualize o plugin e rode de novo:\n"
        f"    /plugin marketplace add mattpocock/skills\n"
        f"    /plugin install {plugin}",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
