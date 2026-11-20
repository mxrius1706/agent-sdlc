"""Tests fuer context-usage.py (synthetische Daten, nur Standardbibliothek)."""
import importlib.util
import os
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "context-usage.py")


def load():
    spec = importlib.util.spec_from_file_location("context_usage", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


cu = load()


def lines(prefix, n):
    """n verschiedene Zeilen mit mindestens 25 Zeichen."""
    return "\n".join(f"{prefix} Zeile Nummer {i} mit genug Text" for i in range(n))


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


class ChunkMarkdownTest(unittest.TestCase):
    def test_heading_path(self):
        text = "# Titel\n" + lines("a", 3) + "\n## Unter\n" + lines("b", 3) + "\n"
        ids = [s["id"] for s in cu.chunk_markdown("docs/a.md", text)]
        self.assertEqual(ids, ["docs/a.md#Titel", "docs/a.md#Titel > Unter"])

    def test_sibling_resets_path(self):
        text = "# T\n## A\n" + lines("a", 3) + "\n## B\n" + lines("b", 3) + "\n"
        ids = [s["id"] for s in cu.chunk_markdown("x.md", text)]
        self.assertEqual(ids, ["x.md#T > A", "x.md#T > B"])

    def test_duplicate_gets_suffix(self):
        text = "# T\n" + lines("a", 3) + "\n# T\n" + lines("b", 3) + "\n"
        ids = [s["id"] for s in cu.chunk_markdown("x.md", text)]
        self.assertEqual(ids, ["x.md#T", "x.md#T~2"])

    def test_requirement_alias(self):
        text = "## R12 Sitzungen laden\n" + lines("a", 3) + "\n## Ohne Nummer\n" + lines("b", 3)
        secs = cu.chunk_markdown("x.md", text)
        self.assertEqual(secs[0]["alias"], "x.md#R12")
        self.assertEqual(secs[1]["alias"], None)

    def test_short_sections_dropped(self):
        text = "# Kurz\nzu kurz\nauch kurz\n# Lang\n" + lines("a", 3) + "\n"
        ids = [s["id"] for s in cu.chunk_markdown("x.md", text)]
        self.assertEqual(ids, ["x.md#Lang"])

    def test_duplicate_lines_count_once(self):
        text = "# T\n" + ("immer dieselbe lange Zeile hier\n" * 5)
        self.assertEqual(cu.chunk_markdown("x.md", text), [])

    def test_code_fence_hash_is_no_heading(self):
        text = "# T\n```\n# kein Titel hier drin im Codeblock\n```\n" + lines("a", 3) + "\n"
        ids = [s["id"] for s in cu.chunk_markdown("x.md", text)]
        self.assertEqual(ids, ["x.md#T"])


class LoadDocsTest(unittest.TestCase):
    def test_default_docs(self):
        with tempfile.TemporaryDirectory() as tmp:
            proj = os.path.join(tmp, "projekt-a")
            vault = os.path.join(tmp, "vault")
            os.makedirs(os.path.join(vault, ".obsidian"))
            write(os.path.join(vault, "Notiz.md"), "# N\n" + lines("n", 3))
            write(os.path.join(vault, "Sub", "Roadmap.md"), "# R\n" + lines("r", 3))
            write(os.path.join(proj, "CLAUDE.md"), "# C\n" + lines("c", 3))
            write(os.path.join(proj, ".claude", "rules", "r1.md"), "# R1\n" + lines("x", 3))
            write(os.path.join(proj, ".claude", "roadmap-path"), os.path.join(vault, "Sub", "Roadmap.md") + "\n")
            got = sorted(n for n, _ in cu.load_docs(proj))
            self.assertEqual(got, sorted(["CLAUDE.md", ".claude/rules/r1.md",
                                          "vault/Notiz.md", "vault/Sub/Roadmap.md"]))

    def test_explicit_docs(self):
        with tempfile.TemporaryDirectory() as tmp:
            write(os.path.join(tmp, "a.md"), "# A\n")
            write(os.path.join(tmp, "d", "b.md"), "# B\n")
            got = sorted(n for n, _ in cu.load_docs(tmp, [os.path.join(tmp, "a.md"), os.path.join(tmp, "d")]))
            self.assertEqual(got, ["a.md", "d/b.md"])


if __name__ == "__main__":
    unittest.main()
