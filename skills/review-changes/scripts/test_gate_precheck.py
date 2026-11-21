"""Unit-Tests fuer gate-precheck.py (Block b2). Synthetische Daten, kein Netz."""
import importlib.util
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "gate-precheck.py")


def load():
    spec = importlib.util.spec_from_file_location("gate_precheck", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class RunChecksUnitTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)

    def test_detail_keeps_only_last_lines(self):
        gp = load()
        code = "import sys\nfor i in range(50): print('zeile-%d' % i)\nsys.exit(1)"
        script = os.path.join(self._tmp.name, "laut.py")
        with open(script, "w", encoding="utf-8") as fh:
            fh.write(code + "\n")
        res = gp.run_checks([sys.executable + " " + script], self._tmp.name)
        self.assertEqual(res[0][0], "FAIL")
        self.assertIn("zeile-49", res[0][2])
        self.assertNotIn("zeile-0\n", res[0][2] + "\n")

    def test_unparsable_command_is_fail(self):
        gp = load()
        res = gp.run_checks(["echo 'offen"], self._tmp.name)
        self.assertEqual(res[0][0], "FAIL")

    def test_empty_command_list_gives_one_pass_note(self):
        gp = load()
        res = gp.run_checks([], self._tmp.name)
        self.assertEqual([r[0] for r in res], ["PASS"])

    def test_check_name_is_stable(self):
        gp = load()
        res = gp.run_checks([sys.executable + " -c pass"], self._tmp.name)
        self.assertTrue(res[0][1].startswith("cmd"))


class LineCountUnitTest(unittest.TestCase):
    def test_count_lines(self):
        gp = load()
        self.assertEqual(gp.count_lines(b""), 0)
        self.assertEqual(gp.count_lines(b"a\nb\n"), 2)
        self.assertEqual(gp.count_lines(b"a\nb"), 2)

    def test_binary_is_not_counted(self):
        gp = load()
        self.assertIsNone(gp.count_lines(b"ab\x00cd\n" * 10))


class LinkExtractUnitTest(unittest.TestCase):
    def test_links_with_line_numbers_skip_fences_and_urls(self):
        gp = load()
        text = ("[a](x.md)\n```\n[b](y.md)\n```\n"
                "[c](https://example.invalid)\n[d](#anker)\n[e](z.md#t)\n")
        self.assertEqual(gp.extract_links(text), [(1, "x.md"), (7, "z.md")])


class ReportUnitTest(unittest.TestCase):
    def test_format_line_keeps_first_detail_line_on_one_row(self):
        gp = load()
        rows = gp.format_lines([("FAIL", "cmd `x`", "Exit 1\nzeile a\nzeile b")])
        self.assertEqual(rows[0], "FAIL cmd `x`: Exit 1")
        self.assertEqual(rows[1:], ["    zeile a", "    zeile b"])

    def test_thermo_line(self):
        gp = load()
        self.assertEqual(gp.thermo_line([("PASS", "groesse", "ok")]), "thermo: no")
        yes = gp.thermo_line([("FAIL", "groesse", "a.py hat 9 Zeilen")])
        self.assertTrue(yes.startswith("thermo: yes (") and yes.endswith(")"))

    def test_exit_code(self):
        gp = load()
        self.assertEqual(gp.exit_code([("PASS", "a", "b")]), 0)
        self.assertEqual(gp.exit_code([("PASS", "a", "b"), ("FAIL", "c", "d")]), 1)


if __name__ == "__main__":
    unittest.main()


class PipeExitCodeTest(unittest.TestCase):
    """t9: Exit 1 eines Befehls der Projektzeile `verification` bleibt Exit 1, auch in einer Pipe."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = self._tmp.name
        # endet mit 1, wenn er ohne Zusatzargumente laeuft (echte Pipe), sonst 0
        self.script = os.path.join(self.root, "validate.py")
        with open(self.script, "w", encoding="utf-8") as fh:
            fh.write("import sys\nprint('validate-marker')\nsys.exit(0 if len(sys.argv) > 1 else 1)\n")

    def test_plain_exit_1_stays_fail(self):
        gp = load()
        res = gp.run_checks([sys.executable + " " + self.script], self.root)
        self.assertEqual(res[0][0], "FAIL")
        self.assertIn("Exit 1", res[0][2])

    def test_exit_1_in_front_of_a_pipe_stays_fail(self):
        gp = load()
        res = gp.run_checks([sys.executable + " " + self.script + " | cat"], self.root)
        self.assertEqual(res[0][0], "FAIL")
        self.assertIn("validate-marker", res[0][2])

    def test_main_exit_1_with_piped_command(self):
        import contextlib
        import io
        import subprocess
        gp = load()
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid",
                        "-c", "commit.gpgsign=false", "commit", "-q", "--allow-empty", "-m", "i"],
                       cwd=self.root, check=True)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = gp.main(["--base", "HEAD", "--root", self.root,
                            "--cmd", sys.executable + " " + self.script + " | cat"])
        self.assertEqual(code, 1, out.getvalue())
