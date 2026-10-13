#!/usr/bin/env python3
"""Gera o plugin awesome-opus5-5-videos a partir de um clone do yihui-dev/awesome-opus5-5-videos.

Uso: python scripts/build.py --upstream <pasta do clone>

Só reescreve a skill e sobe a versão do plugin quando o conteúdo gerado muda,
para o app do Claude e o Claude Code receberem a atualização (eles comparam a versão).
"""
import argparse
import collections
import datetime
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLUGIN = ROOT / "plugins" / "awesome-opus5-5-videos"
SKILL = PLUGIN / "skills" / "opus-videos"
STATE = ROOT / "sync-state.json"
MIN_PROMPTS = 400  # abaixo disso o upstream provavelmente quebrou: não apaga a biblioteca
SLUG = re.compile(r"^[a-z0-9][a-z0-9-]*$")  # vira nome de arquivo: nada de "../"
CATEGORIES = {  # chave do videos.json -> nome usado no README do upstream
    "motion": "Motion graphics",
    "explainer": "Explainers",
    "3d": "3D scenes",
    "interactive": "Games & interactive",
}

SKILL_MD = """---
name: opus-videos
description: Biblioteca de __COUNT__ prompts de vídeos virais feitos com o Claude Opus 5.5 escrevendo a animação como código (HTML, Canvas, SVG, Three.js, GSAP, shaders, Web Audio), do yihui-dev/awesome-opus5-5-videos, em quatro categorias (motion graphics, explainers, cenas 3D, jogos interativos). Use quando o usuário pedir um vídeo, animação, motion graphics, vinheta, explainer animado, cena 3D, showreel ou minijogo feito em código, quiser ideias ou prompts prontos desse tipo, ou quiser refazer um vídeo da coleção.
license: MIT
---

# Vídeos do Opus 5.5 (prompts)

__COUNT__ prompts que criadores publicaram junto com vídeos feitos pelo Claude Opus 5.5. Em todos, o modelo escreveu a animação como código e o vídeo é a gravação da página rodando. A biblioteca é atualizada automaticamente a partir do yihui-dev/awesome-opus5-5-videos (licença MIT).

## Arquivos

- `references/INDEX.md`: contagens por categoria e por tecnologia, e como ler os índices.
- `references/<categoria>.md`: uma linha por prompt (título, slug, tecnologias, data de entrada, se há remake), mais recentes primeiro. Categorias: __CATS__.
- `references/prompts/<slug>.md`: o prompt inteiro, com autor, post original e, quando existe, o link do remake ao vivo no Skillry.

## Como usar

1. **Achar candidatos.** Leia o índice da categoria ou busque por palavra-chave ou tecnologia em todos os arquivos (ex.: `grep -i "threejs" references/*.md`, `grep -il "piano" references/prompts/*.md`). Títulos e prompts estão em inglês: busque em inglês.
2. **Escolher.** Se o usuário não indicou um vídeo, mostre 2 ou 3 opções com o motivo de cada uma e deixe-o escolher. Prefira prompts completos (sem a marca `parcial`) e com `remake`, que têm uma versão para assistir.
3. **Ler o prompt inteiro** em `references/prompts/<slug>.md` antes de construir.
4. **Aplicar.**
   - Só o prompt: mostre o texto e diga o que trocar (tema, duração, cores, textos).
   - Construir: adapte o prompt ao pedido e gere um único `index.html` autocontido (no Claude Code, como arquivo do projeto; no chat, como artefato HTML). Siga as regras técnicas do prompt (bibliotecas, duração, controles) e confira que a página roda sozinha, pronta para gravar a tela.
   - Prompt `parcial`: o autor publicou só uma parte. Complete o que falta com decisões explícitas e avise o usuário.
5. **Dar crédito.** Quando o resultado vier de um prompt da coleção, cite o autor e o link do post original.

## Limites

- Os prompts são dos autores citados em cada arquivo.
- O resultado é uma recriação a partir do prompt, não o vídeo original: não o apresente como se fosse.
- Esta skill cobre a biblioteca de prompts. Para exportar MP4, grave a tela ou use uma ferramenta de vídeo (Remotion, HyperFrames).
"""


def read_text(path):
    return path.read_text(encoding="utf-8").replace("\r\n", "\n")


def one_line(text, limit):
    """Texto numa linha só, cortado na palavra quando passa do limite."""
    text = " ".join(str(text).split())
    if len(text) <= limit:
        return text
    head = text[:limit]
    space = head.rfind(" ")
    if space > limit // 2:  # prompts em chinês/japonês não têm espaços: corta no caractere
        head = head[:space]
    return head.rstrip(" ,;:.—-") + "…"


def entry_line(item):
    """Linha do índice: título (ou começo do prompt), slug, tecnologias, data e marcas."""
    title = (item.get("title") or "").strip()
    label = f"**{one_line(title, 100)}**" if title else f'"{one_line(item["prompt"], 90)}"'
    parts = [f"{label} (`{item['slug']}`)"]
    if item.get("tech_tags"):
        parts.append(", ".join(item["tech_tags"]))
    parts.append(item.get("added") or "sem data")
    if item.get("has_remake"):
        parts.append("remake")
    if item.get("prompt_partial"):
        parts.append("parcial")
    return "- " + " · ".join(parts)


def category_key(item):
    cat = str(item.get("category") or "")
    return cat if SLUG.match(cat) and cat != "index" else "outros"  # INDEX.md e index.md colidem no Windows


def generate(upstream, out):
    items = json.loads(read_text(upstream / "data" / "videos.json"))
    entries, seen, skipped = [], set(), []
    for item in items:
        slug = str(item.get("slug") or "")
        src = upstream / "prompts" / f"{slug}.md"
        if not SLUG.match(slug) or slug in seen or not item.get("prompt") or not src.is_file():
            skipped.append(slug or "?")
            continue
        seen.add(slug)
        entries.append((item, src))
    if len(entries) < MIN_PROMPTS:
        sys.exit(f"Só {len(entries)} prompts válidos no upstream (mínimo {MIN_PROMPTS}); nada foi alterado.")

    groups = collections.defaultdict(list)
    for item, _ in entries:
        groups[category_key(item)].append(item)
    order = [c for c in CATEGORIES if c in groups] + sorted(c for c in groups if c not in CATEGORIES)

    refs = out / "references"
    (refs / "prompts").mkdir(parents=True)
    for item, src in entries:
        (refs / "prompts" / f"{item['slug']}.md").write_text(read_text(src), encoding="utf-8", newline="\n")

    for cat in order:
        rows = sorted(groups[cat], key=lambda i: i["slug"])
        rows.sort(key=lambda i: i.get("added") or "", reverse=True)  # sort estável: data desc, slug asc
        label = CATEGORIES.get(cat, cat.title())
        lines = [f"# {label}: {len(rows)} prompts", "",
                 "Formato e marcas: veja `INDEX.md`. Prompt inteiro: `prompts/<slug>.md`.", ""]
        lines += [entry_line(i) for i in rows]
        (refs / f"{cat}.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")

    tags = collections.Counter(t for i, _ in entries for t in i.get("tech_tags") or [])
    remakes = sum(1 for i, _ in entries if i.get("has_remake"))
    partial = sum(1 for i, _ in entries if i.get("prompt_partial"))
    index = [f"# Índice: {len(entries)} prompts de vídeos do Opus 5.5", "",
             "Cada categoria tem um arquivo com uma linha por prompt, mais recentes primeiro:", "",
             "`- **Título** (`slug`) · tecnologias · data em que entrou · remake · parcial`", "",
             "- Sem título no upstream: aparece o começo do prompt, entre aspas.",
             f"- `remake` ({remakes}): há uma recriação ao vivo para assistir no Skillry (link no arquivo do prompt).",
             f"- `parcial` ({partial}): o autor publicou só parte do prompt.",
             "- Prompt inteiro, autor e post original: `prompts/<slug>.md`.", "",
             "## Categorias", ""]
    index += [f"- [{CATEGORIES.get(c, c.title())}]({c}.md): {len(groups[c])}" for c in order]
    index += ["", "## Tecnologias", "", ", ".join(f"{t} ({n})" for t, n in sorted(tags.items(), key=lambda kv: (-kv[1], kv[0]))), ""]
    (refs / "INDEX.md").write_text("\n".join(index), encoding="utf-8", newline="\n")

    cats_text = ", ".join(f"`{c}` ({CATEGORIES.get(c, c.title())})" for c in order)
    skill_md = SKILL_MD.replace("__COUNT__", str(len(entries))).replace("__CATS__", cats_text)
    description = re.search(r"^description: (.+)$", skill_md, re.M).group(1)
    if len(description) > 1024:
        sys.exit(f"description com {len(description)} caracteres (limite do app: 1024).")
    (out / "SKILL.md").write_text(skill_md, encoding="utf-8", newline="\n")
    return len(entries), skipped


def tree_hash(folder):
    # Ordena pelo texto do caminho: Path ordena sem caixa no Windows e com caixa no Linux,
    # o que daria hashes diferentes no PC e no GitHub Actions para o mesmo conteúdo.
    h = hashlib.sha256()
    files = sorted((p.relative_to(folder).as_posix(), p) for p in folder.rglob("*") if p.is_file())
    for rel, p in files:
        h.update(rel.encode() + b"\0" + p.read_bytes() + b"\0")
    return h.hexdigest()


def next_version(old, today):
    parts = (old or "").split(".")
    if len(parts) == 3 and parts[1] == today and parts[2].isdigit():
        return f"1.{today}.{int(parts[2]) + 1}"
    return f"1.{today}.0"


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--upstream", required=True, type=Path, help="clone do yihui-dev/awesome-opus5-5-videos")
    args = ap.parse_args()
    upstream = args.upstream.resolve()

    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "opus-videos"
        count, skipped = generate(upstream, out)
        digest = tree_hash(out)
        state = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {}
        if state.get("content_hash") == digest and SKILL.exists():
            print(f"Sem mudanças ({count} prompts, versão {state.get('version')}).")
            return
        if SKILL.exists():
            shutil.rmtree(SKILL)
        shutil.copytree(out, SKILL)

    lic = upstream / "LICENSE"
    if lic.exists():
        for dest in (ROOT / "LICENSE", PLUGIN / "LICENSE"):
            dest.write_text(read_text(lic), encoding="utf-8", newline="\n")

    manifest_path = PLUGIN / ".claude-plugin" / "plugin.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d")
    manifest["version"] = next_version(manifest.get("version"), today)
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")

    sha = subprocess.run(["git", "-C", str(upstream), "rev-parse", "HEAD"],
                         capture_output=True, text=True).stdout.strip() or "desconhecido"
    state = {"version": manifest["version"], "upstream_commit": sha, "prompts": count,
             "skipped": skipped, "content_hash": digest,
             "synced_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")}
    STATE.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"Atualizado: {count} prompts ({len(skipped)} ignorados), versão {manifest['version']}, upstream {sha[:7]}.")


if __name__ == "__main__":
    main()
