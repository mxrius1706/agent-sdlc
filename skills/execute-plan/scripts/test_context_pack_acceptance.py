"""Abnahmetests fuer context-pack.py (Block b1, Aufgaben p1 bis p3). Rot, bis das Skript existiert.

Angenommener Vertrag (aus dem Regelbuendel, Abschnitt b1):

    context-pack.py <plan.md> --block <id> --root <dir> [--specs <datei-oder-ordner> ...]
                    [--global-claude <datei>] [--trailer <zeile>] [--out <datei>] [--max-chars N]

    block_scope(plan_path, block_id) -> Tupel (files, req_ids, task_rows)
        files: Liste der Pfade aus der Spalte Files des Blocks
        req_ids: Liste der Anforderungskennungen der Aufgaben des Blocks
        task_rows: Liste der Aufgabenzeilen des Blocks (je Aufgabe ein Eintrag)
        unbekannter Block: ValueError
    collect(scope, root, specs, global_claude) -> Tupel (included, excluded)
        beide Listen von Abschnitt-IDs (Strings) oder Dicts mit Schluessel "id";
        ID-Schema wie chunk_markdown in context-usage.py: <relativer Pfad>#<Ueberschriftenpfad>
        included in Bundle-Reihenfolge (Bereichs-CLAUDE.md: naechste zuerst)
    main(argv) -> Exit-Code; Buendel nach stdout, mit --out in die Datei plus <out>.manifest.json
        Manifest-Schluessel: block, hash (sha256 der Buendel-Bytes), included, excluded, notes
        Exit 2: fehlender Plan oder unbekannter Block (ein Satz auf stderr)
        Exit 3: Buendel groesser als --max-chars (ein Satz mit Blockname auf stderr, keine Ausgabedatei)
"""
import contextlib
import hashlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "context-pack.py")


def load():
    spec = importlib.util.spec_from_file_location("context_pack", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def body(marker):
    """Drei verschiedene lange Zeilen, damit der Zerleger den Abschnitt behaelt."""
    return (f"{marker} erste Zeile mit ausreichend Text\n"
            f"{marker} zweite Zeile mit ausreichend Text\n"
            f"{marker} dritte Zeile mit ausreichend Text\n")


PLAN = """# Plan: Testprojekt

## Blocks

| Block | Tasks | Files | Wave | Exclusive |
|---|---|---|---|---|
| b1 | a1, a2 | src/a/mod.py | 1 | no |
| b2 | a3 | docs/ | 1 | no |

## Tasks

| Id | Block | Task | Test target (seam) | Requirements |
|---|---|---|---|---|
| a1 | b1 | Bestellung pruefen | `pruefe()`: leer | REQ-001 |
| a2 | b1 | Ausgabe schreiben | `schreibe()`: Fehler | REQ-003 |
| a3 | b2 | Text | n/a: text | REQ-002 |

## Decisions

| Question | Answer | Reason |
|---|---|---|
| Format | MARKER-DECISION-FORMAT | maschinenlesbar |

## Verification

- `python3 -I -m unittest discover -s tests -p 'test_*.py'`
"""

TRAILER = "Co-Authored-By: Test Agent <test@example.invalid>"


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def make_project(tmp, glossary=True):
    """Synthetisches Projekt: je Fach ein Treffer und ein Nichttreffer."""
    root = os.path.join(tmp, "projekt-a")
    write(os.path.join(root, "CLAUDE.md"),
          "## Für Subagenten\n" + body("MARKER-SUB-ROOT") +
          "\n## Anderes\n" + body("MARKER-ROOT-OTHER"))
    write(os.path.join(root, "src", "CLAUDE.md"), "## Bereich Quelle\n" + body("MARKER-AREA-SRC"))
    write(os.path.join(root, "src", "a", "CLAUDE.md"), "## Bereich A\n" + body("MARKER-AREA-A"))
    write(os.path.join(root, "other", "CLAUDE.md"), "## Bereich Fremd\n" + body("MARKER-AREA-OTHER"))
    write(os.path.join(root, ".claude", "rules", "py.md"),
          '---\npaths:\n  - "src/a/*.py"\n---\n## Python-Regel\n' + body("MARKER-RULE-PY"))
    write(os.path.join(root, ".claude", "rules", "docs.md"),
          '---\npaths:\n  - "docs/*.md"\n---\n## Doku-Regel\n' + body("MARKER-RULE-DOCS"))
    write(os.path.join(root, "specs", "spec.md"),
          "## Anforderung eins\nREQ-001 gilt fuer die Pruefung.\n" + body("MARKER-SPEC-HIT") +
          "\n## Anforderung zwei\nREQ-099 gilt nirgends hier.\n" + body("MARKER-SPEC-MISS"))
    if glossary:
        write(os.path.join(root, "GLOSSARY.md"),
              "## Bestellung\nEine Anfrage eines Kunden an das Lager.\n"
              "_Avoid_: Auftragszettel\n" + body("MARKER-GLOSS-HIT") +
              "\n## Rechnung\nEin Beleg ueber den offenen Betrag.\n"
              "_Avoid_: Zahlzettel\n" + body("MARKER-GLOSS-MISS"))
    plan = os.path.join(tmp, "plan.md")
    write(plan, PLAN)
    glob_claude = os.path.join(tmp, "global", "CLAUDE.md")
    write(glob_claude, "## Für Subagenten\n" + body("MARKER-SUB-GLOBAL"))
    return root, plan, glob_claude


def ids(items):
    return [i["id"] if isinstance(i, dict) else i for i in items]


def has_prefix(items, prefix):
    return any(i.startswith(prefix) for i in ids(items))


def run_main(argv, cwd=None):
    mod = load()
    out, err = io.StringIO(), io.StringIO()
    old = os.getcwd()
    try:
        if cwd:
            os.chdir(cwd)
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = mod.main(argv)
    finally:
        os.chdir(old)
    return code, out.getvalue(), err.getvalue()


class P1BlockScope(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.plan = os.path.join(self.tmp.name, "plan.md")
        write(self.plan, PLAN)

    def test_p1_bekannter_block_gibt_dateien_und_kennungen(self):
        files, reqs, rows = load().block_scope(self.plan, "b1")
        self.assertIn("src/a/mod.py", list(files))
        self.assertEqual({"REQ-001", "REQ-003"}, set(reqs))
        self.assertEqual(2, len(rows))
        self.assertNotIn("REQ-002", set(reqs))

    def test_p1_unbekannter_block_gibt_valueerror(self):
        with self.assertRaises(ValueError):
            load().block_scope(self.plan, "b9")


class P2Collect(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root, self.plan, self.glob = make_project(self.tmp.name)
        self.mod = load()
        scope = self.mod.block_scope(self.plan, "b1")
        specs = [os.path.join(self.root, "specs")]
        self.inc, self.exc = self.mod.collect(scope, self.root, specs, self.glob)
        self.inc, self.exc = ids(self.inc), ids(self.exc)

    def test_p2_subagenten_abschnitt_des_projekts(self):
        self.assertIn("CLAUDE.md#Für Subagenten", self.inc)
        self.assertNotIn("CLAUDE.md#Anderes", self.inc)

    def test_p2_bereichs_claude_naechste_zuerst_ohne_wurzel_und_fremde(self):
        a, src = "src/a/CLAUDE.md#Bereich A", "src/CLAUDE.md#Bereich Quelle"
        self.assertIn(a, self.inc)
        self.assertIn(src, self.inc)
        self.assertLess(self.inc.index(a), self.inc.index(src))
        self.assertFalse(has_prefix(self.inc, "other/CLAUDE.md#"))

    def test_p2_pfadregel_mit_passendem_glob_ohne_treffer_im_manifest(self):
        self.assertTrue(has_prefix(self.inc, ".claude/rules/py.md#"))
        self.assertFalse(has_prefix(self.inc, ".claude/rules/docs.md#"))
        self.assertTrue(has_prefix(self.exc, ".claude/rules/docs.md#"))

    def test_p2_spec_abschnitt_nach_anforderungskennung(self):
        self.assertIn("specs/spec.md#Anforderung eins", self.inc)
        self.assertNotIn("specs/spec.md#Anforderung zwei", self.inc)
        self.assertIn("specs/spec.md#Anforderung zwei", self.exc)

    def test_p2_glossarbegriff_per_textvergleich(self):
        self.assertIn("GLOSSARY.md#Bestellung", self.inc)
        self.assertNotIn("GLOSSARY.md#Rechnung", self.inc)
        self.assertIn("GLOSSARY.md#Rechnung", self.exc)

    def test_p2_treffer_stehen_nicht_in_excluded(self):
        for sid in ("CLAUDE.md#Für Subagenten", "specs/spec.md#Anforderung eins",
                    "GLOSSARY.md#Bestellung"):
            self.assertNotIn(sid, self.exc)


class P3Main(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root, self.plan, self.glob = make_project(self.tmp.name)
        self.out = os.path.join(self.tmp.name, "pack.md")

    def argv(self, *extra, out=True, trailer=True):
        a = [self.plan, "--block", "b1", "--root", self.root,
             "--specs", os.path.join(self.root, "specs"), "--global-claude", self.glob]
        if trailer:
            a += ["--trailer", TRAILER]
        if out:
            a += ["--out", self.out]
        return a + list(extra)

    def read(self, path):
        with open(path, "rb") as fh:
            return fh.read()

    def test_p3_gleiche_eingabe_gleiche_bytes_und_hash(self):
        self.assertEqual(0, run_main(self.argv())[0])
        first = self.read(self.out)
        m1 = json.loads(self.read(self.out + ".manifest.json"))
        os.remove(self.out)
        self.assertEqual(0, run_main(self.argv())[0])
        self.assertEqual(first, self.read(self.out))
        m2 = json.loads(self.read(self.out + ".manifest.json"))
        self.assertEqual(m1["hash"], m2["hash"])
        self.assertEqual(hashlib.sha256(first).hexdigest(), m1["hash"])

    def test_p3_manifest_schluessel_und_fehlender_glossarbegriff(self):
        self.assertEqual(0, run_main(self.argv())[0])
        m = json.loads(self.read(self.out + ".manifest.json"))
        self.assertEqual({"block", "hash", "included", "excluded", "notes"}, set(m))
        self.assertEqual("b1", m["block"])
        self.assertIn("GLOSSARY.md#Bestellung", ids(m["included"]))
        self.assertIn("GLOSSARY.md#Rechnung", ids(m["excluded"]))
        self.assertNotIn("GLOSSARY.md#Rechnung", ids(m["included"]))

    def test_p3_buendel_inhalt_und_reihenfolge(self):
        self.assertEqual(0, run_main(self.argv())[0])
        text = self.read(self.out).decode("utf-8")
        order = ["MARKER-SUB-ROOT", "MARKER-SUB-GLOBAL", "MARKER-AREA-A", "MARKER-AREA-SRC",
                 "MARKER-RULE-PY", "MARKER-SPEC-HIT", "MARKER-GLOSS-HIT", "Auftragszettel",
                 "MARKER-DECISION-FORMAT", "unittest discover", TRAILER]
        pos = []
        for needle in order:
            self.assertIn(needle, text)
            pos.append(text.index(needle))
        self.assertEqual(sorted(pos), pos)
        for needle in ("MARKER-ROOT-OTHER", "MARKER-AREA-OTHER", "MARKER-RULE-DOCS",
                       "MARKER-SPEC-MISS", "MARKER-GLOSS-MISS"):
            self.assertNotIn(needle, text)

    def test_p3_ohne_out_geht_das_buendel_nach_stdout(self):
        code, out, _ = run_main(self.argv(out=False))
        self.assertEqual(0, code)
        self.assertIn("MARKER-SUB-ROOT", out)
        self.assertFalse(os.path.exists(self.out))

    def test_p3_ohne_glossar_steht_ein_hinweis_im_manifest(self):
        root, plan, glob = make_project(os.path.join(self.tmp.name, "zwei"), glossary=False)
        out = os.path.join(self.tmp.name, "zwei", "pack.md")
        code, _, _ = run_main([plan, "--block", "b1", "--root", root, "--global-claude", glob,
                               "--trailer", TRAILER, "--out", out])
        self.assertEqual(0, code)
        m = json.loads(self.read(out + ".manifest.json"))
        self.assertTrue(any("no glossary found" in n for n in m["notes"]), m["notes"])

    def test_p3_ohne_trailer_und_ohne_git_hinweis(self):
        code, _, _ = run_main(self.argv(trailer=False), cwd=self.root)
        self.assertEqual(0, code)
        m = json.loads(self.read(self.out + ".manifest.json"))
        self.assertTrue(any("no trailer found" in n for n in m["notes"]), m["notes"])

    def test_p3_trailer_aus_dem_neuesten_commit(self):
        def git(*a):
            subprocess.run(["git", "-c", "user.name=test", "-c", "user.email=test@example.invalid", *a],
                           cwd=self.root, check=True, capture_output=True)
        git("init", "-q")
        git("add", "CLAUDE.md")
        git("commit", "-q", "-m", "feat: x\n\n" + TRAILER)
        code, _, _ = run_main(self.argv(trailer=False), cwd=self.root)
        self.assertEqual(0, code)
        self.assertIn(TRAILER, self.read(self.out).decode("utf-8"))

    def test_p3_zu_grosses_paket_exit_3_ohne_datei(self):
        code, _, err = run_main(self.argv("--max-chars", "200"))
        self.assertEqual(3, code)
        self.assertIn("b1", err)
        self.assertFalse(os.path.exists(self.out))
        self.assertFalse(os.path.exists(self.out + ".manifest.json"))

    def test_p3_fehlender_plan_exit_2(self):
        code, _, err = run_main([os.path.join(self.tmp.name, "gibtsnicht.md"), "--block", "b1",
                                 "--root", self.root])
        self.assertEqual(2, code)
        self.assertTrue(err.strip())
        self.assertNotIn("Traceback", err)

    def test_p3_unbekannter_block_exit_2(self):
        code, _, err = run_main([self.plan, "--block", "b9", "--root", self.root])
        self.assertEqual(2, code)
        self.assertTrue(err.strip())
        self.assertNotIn("Traceback", err)

    def test_p3_unterprozess_unter_isolated_mode(self):
        p = subprocess.run([sys.executable, "-I", SCRIPT] + self.argv(), capture_output=True, text=True)
        self.assertEqual(0, p.returncode, p.stderr)
        self.assertTrue(os.path.exists(self.out + ".manifest.json"))


if __name__ == "__main__":
    unittest.main()
