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


if __name__ == "__main__":
    unittest.main()
