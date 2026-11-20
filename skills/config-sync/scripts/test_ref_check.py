"""Eigene Tests fuer ref-check.py (synthetische Daten, nur Standardbibliothek)."""
import importlib.util
import io
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

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


class RefCheckExtraTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = self._tmp.name
        write(os.path.join(self.root, "docs", "da.md"), "x\n")

    def doc(self, text, name="a.md"):
        path = os.path.join(self.root, name)
        write(path, text)
        return path

    def test_default_root_is_file_directory(self):
        mod = load()
        p = self.doc("`docs/da.md` `docs/weg.md`\n")
        self.assertEqual(mod.check_file(p, None), [(1, "docs/weg.md")])

    def test_fenced_block_and_double_backticks_ignored(self):
        mod = load()
        p = self.doc("```\n`docs/weg.md`\n```\n``docs/weg2.md``\n")
        self.assertEqual(mod.check_file(p, self.root), [])

    def test_two_missing_tokens_in_one_line(self):
        mod = load()
        p = self.doc("`a/x.md` und `b/y.py`\n")
        self.assertEqual(mod.check_file(p, self.root), [(1, "a/x.md"), (1, "b/y.py")])

    def test_cli_exit_codes(self):
        p = self.doc("`docs/weg.md`\n")
        r = subprocess.run([sys.executable, "-I", SCRIPT, p, "--root", self.root],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 1)
        self.assertIn(f"MISSING {p}:1 docs/weg.md", r.stdout)
        r = subprocess.run([sys.executable, "-I", SCRIPT, self.root], capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)
        self.assertNotIn("Traceback", r.stderr)

    def test_multiple_files(self):
        mod = load()
        a = self.doc("`docs/da.md`\n", "a.md")
        b = self.doc("`nein/x.md`\n", "b.md")
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(mod.main([a, b, "--root", self.root]), 1)
        self.assertEqual(out.getvalue().strip(), f"MISSING {b}:1 nein/x.md")


if __name__ == "__main__":
    unittest.main()
