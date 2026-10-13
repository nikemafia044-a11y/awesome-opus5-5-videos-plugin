import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import build  # noqa: E402


def item(slug, **extra):
    base = {"slug": slug, "category": "motion", "tech_tags": ["canvas"], "prompt": "make a video",
            "prompt_partial": False, "added": "2026-10-12", "has_remake": False}
    base.update(extra)
    return base


def fake_upstream(root, items, files):
    (root / "data").mkdir(parents=True)
    (root / "prompts").mkdir()
    (root / "data" / "videos.json").write_text(json.dumps(items), encoding="utf-8")
    for slug in files:
        (root / "prompts" / f"{slug}.md").write_bytes(f"# {slug}\r\n\r\nprompt\r\n".encode())


class TreeHashTest(unittest.TestCase):
    def test_ordena_pelo_texto_do_caminho_em_qualquer_so(self):
        # 'references/INDEX.md' fica entre 'ibm' e 'intercom' no sort de Path do Windows,
        # mas antes de todos no Linux; o hash tem de seguir a ordem do texto nos dois.
        files = {
            "SKILL.md": b"skill",
            "references/INDEX.md": b"index",
            "references/interactive.md": b"interactive",
            "references/prompts/ibm-1.md": b"ibm",
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for rel, data in files.items():
                (root / rel).parent.mkdir(parents=True, exist_ok=True)
                (root / rel).write_bytes(data)
            expected = hashlib.sha256()
            for rel in sorted(files):
                expected.update(rel.encode() + b"\0" + files[rel] + b"\0")
            self.assertEqual(build.tree_hash(root), expected.hexdigest())


class NextVersionTest(unittest.TestCase):
    def test_mesmo_dia_sobe_o_patch(self):
        self.assertEqual(build.next_version("1.20261012.2", "20261012"), "1.20261012.3")

    def test_dia_novo_zera_o_patch(self):
        self.assertEqual(build.next_version("1.20261012.2", "20261013"), "1.20261013.0")

    def test_versao_inicial(self):
        self.assertEqual(build.next_version("1.0.0", "20261012"), "1.20261012.0")


class OneLineTest(unittest.TestCase):
    def test_junta_linhas_e_corta_na_palavra(self):
        out = build.one_line("uma frase\ncom   quebras e palavras " * 10, 40)
        self.assertEqual(out, "uma frase com quebras e palavras uma…")

    def test_texto_sem_espacos_corta_no_caractere(self):
        self.assertEqual(build.one_line("動" * 50, 10), "動" * 10 + "…")

    def test_texto_curto_fica_igual(self):
        self.assertEqual(build.one_line("  curto  ", 40), "curto")


class EntryLineTest(unittest.TestCase):
    def test_com_titulo_e_marcas(self):
        line = build.entry_line(item("a-1", title="Crayon Piano", tech_tags=["canvas", "audio"],
                                     has_remake=True, prompt_partial=True))
        self.assertEqual(line, "- **Crayon Piano** (`a-1`) · canvas, audio · 2026-10-12 · remake · parcial")

    def test_sem_titulo_usa_o_comeco_do_prompt(self):
        line = build.entry_line(item("b-2", tech_tags=[], prompt="make a\ndynamic showreel"))
        self.assertEqual(line, '- "make a dynamic showreel" (`b-2`) · 2026-10-12')


class GenerateTest(unittest.TestCase):
    def test_gera_indices_e_ignora_slugs_invalidos(self):
        items = [
            item("old-1", added="2026-09-26"),
            item("new-2"),
            item("cube-3", category="3d", tech_tags=["threejs"]),
            item("../evil"),            # slug que escaparia da pasta
            item("missing-4"),          # sem arquivo no upstream
            item("new-2"),              # duplicado
            item("odd-5", category="index"),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            up, out = Path(tmp) / "up", Path(tmp) / "out"
            fake_upstream(up, items, ["old-1", "new-2", "cube-3", "odd-5"])
            with mock.patch.object(build, "MIN_PROMPTS", 1):
                count, skipped = build.generate(up, out)
            self.assertEqual(count, 4)
            self.assertEqual(skipped, ["../evil", "missing-4", "new-2"])
            refs = out / "references"
            self.assertEqual(sorted(p.name for p in refs.iterdir()),
                             ["3d.md", "INDEX.md", "motion.md", "outros.md", "prompts"])
            motion = (refs / "motion.md").read_text(encoding="utf-8")
            self.assertLess(motion.index("`new-2`"), motion.index("`old-1`"))  # mais recente primeiro
            self.assertNotIn("\r", (refs / "prompts" / "new-2.md").read_text(encoding="utf-8"))
            skill = (out / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn("Biblioteca de 4 prompts", skill)
            self.assertNotIn("__", skill)

    def test_upstream_quebrado_nao_gera_nada(self):
        with tempfile.TemporaryDirectory() as tmp:
            up, out = Path(tmp) / "up", Path(tmp) / "out"
            fake_upstream(up, [item("a-1")], ["a-1"])
            with self.assertRaises(SystemExit):
                build.generate(up, out)
            self.assertFalse(out.exists())


if __name__ == "__main__":
    unittest.main()
