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


class FalseAlarmFilterTest(unittest.TestCase):
    """t8: Fallgruppen, die frueher falsch gemeldet wurden, ergeben keine Meldung."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = self._tmp.name

    def doc(self, text, name="a.md"):
        path = os.path.join(self.root, name)
        write(path, text)
        return path

    def test_knowledge_base_paths_give_no_report(self):
        mod = load()
        p = self.doc("Entscheidungen in `specs/decisions/`, Index `specs/_index.md`.\n")
        self.assertEqual(mod.check_file(p, self.root), [])

    def test_bare_file_names_give_no_report(self):
        mod = load()
        p = self.doc("`GLOSSARY.md`, `CLAUDE.md`, `settings.json`, `werkzeug.py`\n")
        self.assertEqual(mod.check_file(p, self.root), [])

    def test_data_and_package_names_give_no_report(self):
        mod = load()
        p = self.doc("`+/-` `application/json` `phase-3/beispiel-b2-teil` "
                     "`refs/heads/phase-7a/beispiel` `@bereich/paket`\n")
        self.assertEqual(mod.check_file(p, self.root), [])

    def test_real_missing_path_stays_between_filtered_cases(self):
        mod = load()
        p = self.doc("`GLOSSARY.md` `specs/decisions/` `docs/fehlt.md` `+/-`\n")
        self.assertEqual(mod.check_file(p, self.root), [(1, "docs/fehlt.md")])

    def test_cli_exit_0_for_false_alarm_groups_only(self):
        p = self.doc("`specs/decisions/` `GLOSSARY.md` `application/json`\n")
        r = subprocess.run([sys.executable, "-I", SCRIPT, p, "--root", self.root],
                           capture_output=True, text=True)
        self.assertEqual(r.stdout, "")
        self.assertEqual(r.returncode, 0)


class GateOrderCopyTest(unittest.TestCase):
    """t7: eine Kopie der Gate-Reihenfolge in einem Fahrplan wird gefunden."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = self._tmp.name

    def run_cli(self, text):
        path = os.path.join(self.root, "fahrplan.md")
        write(path, text)
        r = subprocess.run([sys.executable, "-I", SCRIPT, path, "--root", self.root],
                           capture_output=True, text=True)
        return path, r

    def test_copy_of_gate_order_is_reported_with_line(self):
        path, r = self.run_cli(
            "# Fahrplan\n\nPhasen-Gate:\n"
            "Fest sind zwei Gates: `review-changes`, dann `thermo-nuclear-code-quality-review`.\n")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("%s:4" % path, r.stdout)

    def test_copy_as_numbered_list_is_reported(self):
        path, r = self.run_cli(
            "# Fahrplan\n\n1. review-changes ueber den Phasen-Diff\n"
            "2. thermo als festes Gate danach\n")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn(path, r.stdout)

    def test_reference_to_the_ritual_is_no_report(self):
        _, r = self.run_cli(
            "# Fahrplan\n\nDas Gate-Ritual steht in `plan-build`; hier steht nur der Verweis.\n"
            "Ein Review mit `review-changes` laeuft nach Bedarf.\n")
        self.assertEqual(r.stdout, "")
        self.assertEqual(r.returncode, 0)
