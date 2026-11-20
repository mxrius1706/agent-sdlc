"""Abnahmetests fuer gate-precheck.py (Block b2, Aufgaben g1 bis g3).

Angenommene Schnittstelle (aus dem Regelbuendel, Interface contracts / b2):

  gate-precheck.py --base <ref> [--head <ref>] [--root <dir>]
                   [--cmd "<command>" ...] [--trailer "<line>"] [--size-limit N]

  Vorgaben: --head HEAD, --root ., --size-limit 1000. --cmd wiederholbar, mit shlex
  zerlegt, ohne Shell in --root ausgefuehrt; Exit 0 ist PASS, sonst oder fehlende
  Datei ist FAIL mit den letzten Ausgabezeilen.
  Funktionen, je Rueckgabe eine Liste von Tupeln (status, check, detail),
  status ist "PASS" oder "FAIL":
    run_checks(cmds, root)
    check_trailer(base, head, trailer, root)  jeder Commit in base..head (ohne Merges)
                                              enthaelt die Zeile woertlich; ohne
                                              Trailer (None) ein PASS mit Hinweis
    check_sizes(base, head, limit, root)      Datei ueber der Grenze bei head und bei
                                              base darunter/gleich/fehlend: FAIL mit
                                              Dateiname und Zeilenzahlen; schon bei base
                                              ueber der Grenze und gewachsen: nur Hinweis
    check_links(base, head, root)             relative Markdown-Links in geaenderten
                                              .md-Dateien muessen existieren (Anker
                                              ignoriert, URL und mailto uebersprungen);
                                              FAIL mit Datei und Zeile
  main(argv) -> Exitcode, gibt die Zeilen auf stdout aus:
    "PASS <check>: <detail>" oder "FAIL <check>: <detail>", letzte Zeile genau
    "thermo: yes (<grund>)" bei Groessen-Ueberschreitung, sonst "thermo: no".
    Exit 1 bei mindestens einem FAIL, sonst 0; falsche Eingabe (unbekannte Ref,
    fehlendes Root): ein Satz auf stderr, Exit 2.
"""
import contextlib
import importlib.util
import io
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "gate-precheck.py")
TRAILER = "Co-Authored-By: Test Agent <test@example.invalid>"


def load():
    """Laedt das Skript erst im Test, damit jeder Test einzeln rot wird."""
    spec = importlib.util.spec_from_file_location("gate_precheck", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def git(root, *args):
    res = subprocess.run(
        ["git", "-c", "user.name=test", "-c", "user.email=test@example.invalid",
         "-c", "commit.gpgsign=false", *args],
        cwd=root, capture_output=True, text=True, check=True)
    return res.stdout.strip()


def write(root, rel, text):
    path = os.path.join(root, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def commit(root, msg, trailer=True):
    git(root, "add", "-A")
    full = msg + ("\n\n" + TRAILER if trailer else "")
    git(root, "commit", "-m", full)
    return git(root, "rev-parse", "HEAD")


def lines(n):
    return "".join("zeile %d\n" % i for i in range(n))


class RepoCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = os.path.realpath(self._tmp.name)
        git(self.root, "init", "-q")
        write(self.root, "README.md", "# projekt-a\n")
        self.base = commit(self.root, "init")

    def statuses(self, results):
        return [r[0] for r in results]


class RunChecksTest(RepoCase):
    """g1: run_checks(cmds, root)"""

    def test_green_command_is_pass(self):
        gp = load()
        res = gp.run_checks([sys.executable + " -c pass"], self.root)
        self.assertEqual(self.statuses(res), ["PASS"])

    def test_red_command_is_fail_with_output_tail(self):
        gp = load()
        cmd = "%s -c \"import sys; print('boom-marker'); sys.exit(3)\"" % sys.executable
        res = gp.run_checks([cmd], self.root)
        self.assertEqual(self.statuses(res), ["FAIL"])
        self.assertIn("boom-marker", res[0][2])

    def test_missing_executable_is_fail_not_crash(self):
        gp = load()
        res = gp.run_checks(["gibt-es-nicht-xyz --version"], self.root)
        self.assertEqual(self.statuses(res), ["FAIL"])

    def test_one_result_per_command_and_runs_in_root(self):
        gp = load()
        probe = "%s -c \"import os,sys; sys.exit(0 if os.path.exists('README.md') else 1)\"" % sys.executable
        res = gp.run_checks([probe, sys.executable + " -c pass"], self.root)
        self.assertEqual(self.statuses(res), ["PASS", "PASS"])

    def test_no_shell_is_used(self):
        gp = load()
        res = gp.run_checks(["echo a && exit 1"], self.root)
        # ohne Shell ist "&&" ein gewoehnliches Argument, der Befehl endet mit 0
        self.assertEqual(self.statuses(res), ["PASS"])


class TrailerTest(RepoCase):
    """g2: check_trailer"""

    def test_all_commits_with_trailer_pass(self):
        gp = load()
        write(self.root, "a.txt", "a\n")
        commit(self.root, "feat: a")
        write(self.root, "b.txt", "b\n")
        head = commit(self.root, "feat: b")
        res = gp.check_trailer(self.base, head, TRAILER, self.root)
        self.assertNotIn("FAIL", self.statuses(res))

    def test_commit_without_trailer_fails(self):
        gp = load()
        write(self.root, "a.txt", "a\n")
        commit(self.root, "feat: a")
        write(self.root, "b.txt", "b\n")
        head = commit(self.root, "feat: b", trailer=False)
        res = gp.check_trailer(self.base, head, TRAILER, self.root)
        self.assertIn("FAIL", self.statuses(res))

    def test_merge_commit_is_excluded(self):
        gp = load()
        main_branch = git(self.root, "rev-parse", "--abbrev-ref", "HEAD")
        git(self.root, "checkout", "-q", "-b", "seite")
        write(self.root, "s.txt", "s\n")
        commit(self.root, "feat: seite")
        git(self.root, "checkout", "-q", main_branch)
        write(self.root, "m.txt", "m\n")
        commit(self.root, "feat: main")
        git(self.root, "merge", "--no-ff", "-q", "-m", "merge seite", "seite")
        head = git(self.root, "rev-parse", "HEAD")
        res = gp.check_trailer(self.base, head, TRAILER, self.root)
        self.assertNotIn("FAIL", self.statuses(res))

    def test_without_trailer_option_is_pass_note(self):
        gp = load()
        write(self.root, "a.txt", "a\n")
        head = commit(self.root, "feat: a", trailer=False)
        res = gp.check_trailer(self.base, head, None, self.root)
        self.assertEqual(self.statuses(res), ["PASS"])


class SizesTest(RepoCase):
    """g2: check_sizes (Grenze 5 Zeilen: darunter, genau darauf, darueber)"""

    def run_size(self, n, limit=5):
        gp = load()
        write(self.root, "gross.py", lines(n))
        head = commit(self.root, "feat: gross")
        return gp.check_sizes(self.base, head, limit, self.root)

    def test_just_below_limit_passes(self):
        self.assertNotIn("FAIL", self.statuses(self.run_size(4)))

    def test_exactly_at_limit_passes(self):
        self.assertNotIn("FAIL", self.statuses(self.run_size(5)))

    def test_just_above_limit_fails_naming_file_and_counts(self):
        res = self.run_size(6)
        fails = [r for r in res if r[0] == "FAIL"]
        self.assertEqual(len(fails), 1)
        self.assertIn("gross.py", fails[0][2])
        self.assertIn("6", fails[0][2])

    def test_crossing_from_below_fails(self):
        gp = load()
        write(self.root, "wachs.py", lines(4))
        base = commit(self.root, "feat: klein")
        write(self.root, "wachs.py", lines(9))
        head = commit(self.root, "feat: gewachsen")
        res = gp.check_sizes(base, head, 5, self.root)
        self.assertIn("FAIL", self.statuses(res))

    def test_already_over_at_base_and_grown_is_note_not_fail(self):
        gp = load()
        write(self.root, "alt.py", lines(8))
        base = commit(self.root, "feat: schon gross")
        write(self.root, "alt.py", lines(12))
        head = commit(self.root, "feat: noch groesser")
        res = gp.check_sizes(base, head, 5, self.root)
        self.assertNotIn("FAIL", self.statuses(res))
        self.assertTrue(any("alt.py" in r[2] for r in res))

    def test_unchanged_big_file_is_ignored(self):
        gp = load()
        write(self.root, "alt.py", lines(8))
        base = commit(self.root, "feat: schon gross")
        write(self.root, "neu.txt", "x\n")
        head = commit(self.root, "feat: andere datei")
        res = gp.check_sizes(base, head, 5, self.root)
        self.assertNotIn("FAIL", self.statuses(res))


class LinksTest(RepoCase):
    """g2: check_links"""

    def test_existing_targets_pass(self):
        gp = load()
        write(self.root, "docs/ziel.md", "# ziel\n")
        write(self.root, "docs/a.md",
              "[ok](ziel.md)\n[anker](ziel.md#abschnitt)\n"
              "[web](https://example.invalid/x)\n[mail](mailto:a@example.invalid)\n")
        head = commit(self.root, "docs: a")
        res = gp.check_links(self.base, head, self.root)
        self.assertNotIn("FAIL", self.statuses(res))

    def test_missing_target_fails_with_file_and_line(self):
        gp = load()
        write(self.root, "docs/a.md", "# a\n\n[kaputt](fehlt.md)\n")
        head = commit(self.root, "docs: a")
        res = gp.check_links(self.base, head, self.root)
        fails = [r for r in res if r[0] == "FAIL"]
        self.assertEqual(len(fails), 1)
        self.assertIn("a.md", fails[0][2])
        self.assertIn("3", fails[0][2])

    def test_unchanged_md_is_not_checked(self):
        gp = load()
        write(self.root, "alt.md", "[kaputt](fehlt.md)\n")
        base = commit(self.root, "docs: alt")
        write(self.root, "neu.txt", "x\n")
        head = commit(self.root, "feat: neu")
        res = gp.check_links(base, head, self.root)
        self.assertNotIn("FAIL", self.statuses(res))


class MainTest(RepoCase):
    """g3: main(argv), Berichtzeilen und Exit-Codes"""

    def run_main(self, argv):
        gp = load()
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = gp.main(argv)
        return code, out.getvalue().splitlines(), err.getvalue()

    def test_all_green_exit_0_and_thermo_no(self):
        write(self.root, "a.txt", "a\n")
        commit(self.root, "feat: a")
        code, out, _ = self.run_main([
            "--base", self.base, "--root", self.root, "--trailer", TRAILER,
            "--cmd", sys.executable + " -c pass"])
        self.assertEqual(code, 0)
        self.assertEqual(out[-1], "thermo: no")
        self.assertTrue(any(l.startswith("PASS ") for l in out))
        self.assertFalse(any(l.startswith("FAIL ") for l in out))

    def test_one_defect_exit_1(self):
        write(self.root, "a.txt", "a\n")
        commit(self.root, "feat: a", trailer=False)
        code, out, _ = self.run_main([
            "--base", self.base, "--root", self.root, "--trailer", TRAILER])
        self.assertEqual(code, 1)
        self.assertTrue(any(l.startswith("FAIL ") for l in out))
        self.assertEqual(out[-1], "thermo: no")

    def test_failing_cmd_exit_1(self):
        write(self.root, "a.txt", "a\n")
        commit(self.root, "feat: a")
        code, out, _ = self.run_main([
            "--base", self.base, "--root", self.root,
            "--cmd", sys.executable + " -c \"import sys; sys.exit(1)\""])
        self.assertEqual(code, 1)

    def test_file_over_limit_says_thermo_yes(self):
        write(self.root, "gross.py", lines(7))
        commit(self.root, "feat: gross")
        code, out, _ = self.run_main([
            "--base", self.base, "--root", self.root, "--size-limit", "5"])
        self.assertEqual(code, 1)
        self.assertTrue(out[-1].startswith("thermo: yes ("), out[-1])
        self.assertTrue(out[-1].endswith(")"))

    def test_file_at_limit_says_thermo_no(self):
        write(self.root, "gross.py", lines(5))
        commit(self.root, "feat: genau")
        code, out, _ = self.run_main([
            "--base", self.base, "--root", self.root, "--size-limit", "5"])
        self.assertEqual(code, 0)
        self.assertEqual(out[-1], "thermo: no")

    def test_default_head_and_size_limit(self):
        write(self.root, "mittel.py", lines(999))
        commit(self.root, "feat: mittel")
        code, out, _ = self.run_main(["--base", self.base, "--root", self.root])
        self.assertEqual(code, 0)
        self.assertEqual(out[-1], "thermo: no")

    def test_line_format_is_status_check_colon_detail(self):
        write(self.root, "a.txt", "a\n")
        commit(self.root, "feat: a")
        _, out, _ = self.run_main(["--base", self.base, "--root", self.root])
        for l in out[:-1]:
            head, sep, _detail = l.partition(": ")
            self.assertEqual(sep, ": ", l)
            self.assertIn(head.split(" ")[0], ("PASS", "FAIL"), l)

    def test_unknown_ref_exit_2_one_sentence(self):
        code, out, err = self.run_main([
            "--base", "gibt-es-nicht", "--root", self.root])
        self.assertEqual(code, 2)
        self.assertNotIn("Traceback", err)
        self.assertEqual(len(err.strip().splitlines()), 1)

    def test_missing_root_exit_2(self):
        code, out, err = self.run_main([
            "--base", self.base, "--root", os.path.join(self.root, "nicht-da")])
        self.assertEqual(code, 2)
        self.assertNotIn("Traceback", err)

    def test_runs_as_subprocess_under_isolated_mode(self):
        write(self.root, "a.txt", "a\n")
        commit(self.root, "feat: a")
        res = subprocess.run(
            [sys.executable, "-I", SCRIPT, "--base", self.base, "--root", self.root],
            capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertEqual(res.stdout.splitlines()[-1], "thermo: no")


if __name__ == "__main__":
    unittest.main()
