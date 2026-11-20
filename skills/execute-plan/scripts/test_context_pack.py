"""Eigene Unit-Tests fuer context-pack.py (synthetische Daten im Temp-Ordner)."""
import importlib.util
import os
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "context-pack.py")
USAGE = os.path.join(HERE, "..", "..", "retro", "scripts", "context-usage.py")


def load(path=SCRIPT, name="context_pack"):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def body(marker):
    return "".join(f"{marker} Zeile {n} mit ausreichend Text\n" for n in "abc")


PLAN = """# Plan

## Blocks

| Files | Block | Wave | Tasks | Exclusive |
|---|---|---|---|---|
| `src/x.py`, docs/ | b1 | 1 | t1 | no |
| src/y.py | b2 | 1 | t2, t3 | no |

## Tasks

| Id | Block | Task | Test target (seam) | Requirements |
|---|---|---|---|---|
| t1 | b1 | Eins | `f()`: leer | REQ-001, SEC-2 |
| t2 | b2 | Zwei | n/a: text | - |
| t3 | b2 | Drei | n/a: text | REQ-001 |
"""


class ChunkMarkdown(unittest.TestCase):
    TEXT = ("## Eins\n" + body("a") + "### Unter\n" + body("b") + "## Eins\n" + body("c") +
            "```\n## kein Kopf\n```\n## Kurz\nnur eine\n")

    def test_ids_wie_beim_zerleger_im_retro_skript(self):
        got = [c["id"] for c in load().chunk_markdown("d/x.md", self.TEXT)]
        self.assertEqual(["d/x.md#Eins", "d/x.md#Eins > Unter", "d/x.md#Eins~2"], got)

    def test_paritaet_mit_context_usage_wenn_vorhanden(self):
        if not os.path.exists(USAGE):
            self.skipTest("context-usage.py fehlt")
        other = load(USAGE, "context_usage")
        for text in (self.TEXT, "# A\n" + body("x"), body("y"), ""):
            a = [(c["id"], c["alias"], c["chars"]) for c in load().chunk_markdown("p.md", text)]
            b = [(c["id"], c["alias"], c["chars"]) for c in other.chunk_markdown("p.md", text)]
            self.assertEqual(b, a)


class BlockScope(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.plan = os.path.join(self.tmp.name, "plan.md")
        with open(self.plan, "w", encoding="utf-8") as fh:
            fh.write(PLAN)

    def test_spaltenreihenfolge_egal_und_backticks_entfernt(self):
        files, reqs, rows = load().block_scope(self.plan, "b1")
        self.assertEqual(["src/x.py", "docs/"], files)
        self.assertEqual(["REQ-001", "SEC-2"], reqs)
        self.assertEqual(["t1"], [r["id"] for r in rows])

    def test_strich_ist_keine_kennung_und_doppelte_entfallen(self):
        files, reqs, rows = load().block_scope(self.plan, "b2")
        self.assertEqual(["REQ-001"], reqs)
        self.assertEqual(2, len(rows))

    def test_plan_ohne_tabelle_gibt_valueerror(self):
        with open(self.plan, "w", encoding="utf-8") as fh:
            fh.write("# Plan\n\n## Context\ntext\n")
        with self.assertRaises(ValueError):
            load().block_scope(self.plan, "b1")


if __name__ == "__main__":
    unittest.main()
