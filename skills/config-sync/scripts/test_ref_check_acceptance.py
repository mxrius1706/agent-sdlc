"""Abnahmetest c1: ref-check.py prueft Pfade in Backticks auf Existenz.

Angenommener Vertrag (Block b3):
  ref-check.py <file.md> ... [--root <dir>]   Exit 1 bei fehlenden Pfaden, sonst 0,
                                              unlesbare Datei: ein Satz, Exit 2
  check_file(path, root) -> Liste von (zeile, token) fuer fehlende Pfade
    Token = Inline-Code zwischen einzelnen Backticks, der wie ein relativer Pfad aussieht
    (enthaelt "/" oder endet auf .md .py .json .sh .ts .js .yml .yaml .toml; beginnt nicht
    mit http, /, ~, $, -; enthaelt keines von < > * ? { } | ( ) Leerzeichen).
    Aufgeloest gegen root und gegen das Verzeichnis der Datei; eines von beiden genuegt.
  Ausgabe je fehlendem Pfad: "MISSING <datei>:<zeile> <token>"
"""
import importlib.util
import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "ref-check.py")


def load():
    spec = importlib.util.spec_from_file_location("ref_check", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def write(path, text=""):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


class RefCheckTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = self._tmp.name
        write(os.path.join(self.root, "docs", "vorhanden.md"), "x\n")
        write(os.path.join(self.root, "tools", "lauf.py"), "x\n")

    def doc(self, text, sub="anweisung.md"):
        path = os.path.join(self.root, sub)
        write(path, text)
        return path

    def test_existing_path_is_ok(self):
        mod = load()
        p = self.doc("Siehe `docs/vorhanden.md` und `tools/lauf.py`.\n")
        self.assertEqual(mod.check_file(p, self.root), [])

    def test_missing_path_reported_with_line(self):
        mod = load()
        p = self.doc("Erste Zeile.\nSiehe `docs/fehlt.md` hier.\n\nUnd `tools/nein.py`.\n")
        self.assertEqual(mod.check_file(p, self.root),
                         [(2, "docs/fehlt.md"), (4, "tools/nein.py")])

    def test_url_and_placeholders_skipped(self):
        mod = load()
        p = self.doc("`https://example.invalid/a/b.md` `<projekt>/x.md` `docs/*.md` "
                     "`~/a/b.md` `/abs/pfad.md` `$HOME/a.md` `--flag/x` `a b/c.md` "
                     "`docs/{a,b}.md` `x|y/z.md` `f(x)/g.md` `kein-pfad` `wort`\n")
        self.assertEqual(mod.check_file(p, self.root), [])

    def test_extension_without_slash_is_skipped(self):
        # t8: ein Dateiname ohne Ordner ist kein Pfad, den die Datei selbst aufloesen muss
        mod = load()
        p = self.doc("`fehlt.json` und `vorhanden.md`\n")
        self.assertEqual(mod.check_file(p, self.root), [])

    def test_resolves_against_file_directory_too(self):
        mod = load()
        write(os.path.join(self.root, "sub", "nah.md"), "x\n")
        p = self.doc("`nah.md` und `docs/vorhanden.md`\n", sub=os.path.join("sub", "a.md"))
        self.assertEqual(mod.check_file(p, self.root), [])

    def test_main_exit_codes_and_output(self):
        mod = load()
        ok = self.doc("`docs/vorhanden.md`\n")
        bad = self.doc("x\n`docs/fehlt.md`\n", sub="schlecht.md")
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(mod.main([ok, "--root", self.root]), 0)
            self.assertEqual(mod.main([bad, "--root", self.root]), 1)
        self.assertIn(f"MISSING {bad}:2 docs/fehlt.md", out.getvalue())

    def test_unreadable_file_exit_2(self):
        mod = load()
        err = io.StringIO()
        with redirect_stderr(err), redirect_stdout(io.StringIO()):
            code = mod.main([os.path.join(self.root, "gibtsnicht.md")])
        self.assertEqual(code, 2)
        self.assertNotIn("Traceback", err.getvalue())


if __name__ == "__main__":
    unittest.main()
