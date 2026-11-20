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


class Globs(unittest.TestCase):
    def test_stern_und_doppelstern(self):
        m = load().glob_match
        self.assertTrue(m("src/*.py", "src/a.py"))
        self.assertFalse(m("src/*.py", "src/a/b.py"))
        self.assertTrue(m("src/**/*.py", "src/a/b.py"))
        self.assertTrue(m("**/*.md", "README.md"))
        self.assertTrue(m("docs/?.md", "docs/a.md"))
        self.assertFalse(m("docs/?.md", "docs/ab.md"))


class Frontmatter(unittest.TestCase):
    def test_liste_inline_und_skalar(self):
        f = load().rule_paths
        self.assertEqual(["a/*.py", "b/*.md"], f('---\npaths:\n  - "a/*.py"\n  - b/*.md\n---\nText\n')[0])
        self.assertEqual(["x/*.py", "y"], f('---\npaths: ["x/*.py", \'y\']\n---\n')[0])
        self.assertEqual(["z/**"], f("---\npaths: z/**\n---\n")[0])

    def test_ohne_frontmatter_keine_pfade_und_text_bleibt(self):
        paths, rest = load().rule_paths("## Kopf\nText\n")
        self.assertEqual([], paths)
        self.assertEqual("## Kopf\nText\n", rest)

    def test_rest_ist_der_text_nach_dem_frontmatter(self):
        self.assertEqual("## K\n", load().rule_paths("---\npaths:\n  - a\n---\n## K\n")[1])


def make(tmp, rel, text):
    path = os.path.join(tmp, *rel.split("/"))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    return path


class Collect(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = os.path.join(self.tmp.name, "projekt-a")
        self.mod = load()

    def run_collect(self, files, reqs=(), tasks=(), specs=(), glob=None):
        scope = (list(files), list(reqs), [{"task": t} for t in tasks])
        inc, exc = self.mod.collect(scope, self.root, list(specs), glob)
        return [i["id"] for i in inc], [e["id"] for e in exc], inc

    def test_unterabschnitte_gehoeren_zum_subagenten_abschnitt(self):
        make(self.root, "CLAUDE.md", "## Für Subagenten\n" + body("o") + "### Tief\n" + body("t") +
             "## Danach\n" + body("d"))
        inc, exc, items = self.run_collect([])
        self.assertEqual(["CLAUDE.md#Für Subagenten"], inc)
        self.assertIn("CLAUDE.md#Danach", exc)
        self.assertIn("### Tief", items[0]["text"])
        self.assertNotIn("d Zeile", items[0]["text"])

    def test_gleicher_bereich_wird_nur_einmal_aufgenommen(self):
        make(self.root, "src/CLAUDE.md", "## Bereich\n" + body("s"))
        inc, _, _ = self.run_collect(["src/a.py", "src/b.py"])
        self.assertEqual(["src/CLAUDE.md#Bereich"], inc)

    def test_glossar_unter_specs_und_kein_doppelter_treffer(self):
        make(self.root, "specs/GLOSSARY.md", "## Lager\nEin Ort fuer Ware im Haus.\n" + body("g"))
        specs = [os.path.join(self.root, "specs")]
        inc, exc, _ = self.run_collect([], tasks=["Lager aufraeumen"], specs=specs)
        self.assertEqual(["specs/GLOSSARY.md#Lager"], inc)
        self.assertEqual([], exc)

    def test_avoid_zeilen_stehen_hinter_der_beschreibung(self):
        make(self.root, "GLOSSARY.md", "## Lager\n_Avoid_: Halle\nBeschreibung Zeile mit genug Text\n" + body("g"))
        _, _, items = self.run_collect(["src/lager.py"])
        self.assertTrue(items[0]["text"].rstrip().endswith("_Avoid_: Halle"))

    def test_glossarbegriff_aus_dateinamen(self):
        make(self.root, "GLOSSARY.md", "## Lager\n" + body("g"))
        inc, _, _ = self.run_collect(["src/lager.py"])
        self.assertEqual(["GLOSSARY.md#Lager"], inc)

    def test_ohne_kennungen_kein_spec_abschnitt(self):
        make(self.root, "specs/s.md", "## A\nREQ-001 hier.\n" + body("s"))
        inc, exc, _ = self.run_collect([], reqs=[], specs=[os.path.join(self.root, "specs")])
        self.assertEqual([], inc)
        self.assertEqual(["specs/s.md#A"], exc)

    def test_kennung_ist_kein_teilwort(self):
        make(self.root, "specs/s.md", "## A\nREQ-0011 hier.\n" + body("s"))
        inc, _, _ = self.run_collect([], reqs=["REQ-001"], specs=[os.path.join(self.root, "specs")])
        self.assertEqual([], inc)

    def test_regel_ohne_paths_trifft_nie(self):
        make(self.root, ".claude/rules/r.md", "## R\n" + body("r"))
        inc, exc, _ = self.run_collect(["src/a.py"])
        self.assertEqual([], inc)
        self.assertEqual([".claude/rules/r.md#R"], exc)


class Main(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = os.path.join(self.tmp.name, "projekt-a")
        os.makedirs(self.root)
        self.plan = make(self.tmp.name, "plan.md", PLAN + "\n## Decisions\n\n| Question | Answer | Reason |\n"
                         "|---|---|---|\n| Q | A-ANTWORT | R |\n\n## Verification\n\n- `pytest -q`\n")
        self.mod = load()

    def call(self, argv):
        import contextlib
        import io
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = self.mod.main(argv)
        return code, out.getvalue(), err.getvalue()

    def test_letzte_coauthored_zeile_der_nachricht(self):
        msg = "feat: x\n\nCo-Authored-By: A <a@example.invalid>\nco-authored-by: B <b@example.invalid>\n"
        self.assertEqual("co-authored-by: B <b@example.invalid>", self.mod.last_trailer(msg))
        self.assertIsNone(self.mod.last_trailer("feat: x\n"))

    def test_buendel_enthaelt_kopf_entscheidungen_und_verifikation(self):
        code, out, _ = self.call([self.plan, "--block", "b1", "--root", self.root, "--trailer", "T: 1"])
        self.assertEqual(0, code)
        for needle in ("b1", "src/x.py", "A-ANTWORT", "pytest -q", "T: 1"):
            self.assertIn(needle, out)

    def test_zu_gross_schreibt_nichts_nach_stdout(self):
        code, out, err = self.call([self.plan, "--block", "b1", "--root", self.root, "--max-chars", "10"])
        self.assertEqual((3, ""), (code, out))
        self.assertIn("10", err)

    def test_max_chars_genau_an_der_grenze_ist_erlaubt(self):
        _, out, _ = self.call([self.plan, "--block", "b1", "--root", self.root, "--trailer", "T: 1"])
        code, _, _ = self.call([self.plan, "--block", "b1", "--root", self.root, "--trailer", "T: 1",
                                "--max-chars", str(len(out))])
        self.assertEqual(0, code)

    def test_ungueltige_option_gibt_exit_2_ohne_traceback(self):
        code, _, err = self.call([self.plan, "--block", "b1", "--root", self.root, "--max-chars", "x"])
        self.assertEqual(2, code)
        self.assertNotIn("Traceback", err)

    def test_fehlendes_wurzelverzeichnis_exit_2(self):
        code, _, err = self.call([self.plan, "--block", "b1", "--root", os.path.join(self.tmp.name, "nein")])
        self.assertEqual(2, code)
        self.assertTrue(err.strip())


if __name__ == "__main__":
    unittest.main()
