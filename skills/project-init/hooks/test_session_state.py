"""Tests fuer session-state.py: bestehendes Verhalten und Laufzustand-Kurzfassung."""

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "session-state.py")
spec = importlib.util.spec_from_file_location("session_state", SCRIPT)
session_state = importlib.util.module_from_spec(spec)
spec.loader.exec_module(session_state)

RUN_STATE = (
    "Phasen-Branch: phase/x\nPlan: p.md\nRegelbuendel: r.md\n\n"
    "| Block | Status | Statuscode | Fix-Runden | Worktree |\n"
    "|---|---|---|---|---|\n"
    "| b1 | laufend | - | 0 | w1 |\n"
    "| b2 | gemerged | DONE | 0 | w2 |\n"
)


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.project = os.path.join(self.tmp.name, "projekt-a")
        os.makedirs(os.path.join(self.project, ".claude"))

    def write(self, rel, text):
        path = os.path.join(self.project, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(text)

    def run_hook(self):
        env = {k: v for k, v in os.environ.items()
               if k not in ("PROJECT_ROADMAP", "PROJECT_STATE")}
        env["CLAUDE_PROJECT_DIR"] = self.project
        proc = subprocess.run([sys.executable, "-I", SCRIPT], input="{}",
                              capture_output=True, text=True, env=env)
        self.assertEqual(proc.returncode, 0)
        return proc.stdout

    def context(self):
        out = self.run_hook()
        return json.loads(out)["hookSpecificOutput"]["additionalContext"] if out else ""


class TestExisting(Base):
    def test_nothing_gives_empty_output(self):
        self.assertEqual(self.run_hook(), "")

    def test_handoff_only(self):
        self.write(".claude/state.md", "Uebergabe-Text")
        ctx = self.context()
        self.assertTrue(ctx.startswith("LETZTE SITZUNG (aus .claude/state.md)\nUebergabe-Text"))
        self.assertIn("Kein Fahrplan gefunden.", ctx)

    def test_roadmap_and_handoff(self):
        self.write("roadmap.md", "# Fahrplan\nPosition")
        self.write(".claude/state.md", "Uebergabe-Text")
        ctx = self.context()
        self.assertTrue(ctx.startswith("FAHRPLAN (wo steht das Projekt, was kommt als Naechstes)\n# Fahrplan"))
        self.assertIn("LETZTE SITZUNG", ctx)
        self.assertIn("Beginne die Sitzung damit", ctx)

    def test_event_name(self):
        self.write(".claude/state.md", "x")
        out = json.loads(self.run_hook())
        self.assertEqual(out["hookSpecificOutput"]["hookEventName"], "SessionStart")


class TestRunSummary(Base):
    def test_function_none_without_state(self):
        self.assertIsNone(session_state.run_summary(self.project))

    def test_function_content(self):
        self.write(".claude/run/phase-2.md", RUN_STATE)
        text = session_state.run_summary(self.project)
        self.assertIn("phase/x", text)
        self.assertIn("b1: laufend", text)
        self.assertIn("b2: gemerged", text)
        self.assertIn("Weitermachen mit execute-plan Schritt 0", text)

    def test_appended_to_context(self):
        self.write(".claude/state.md", "Uebergabe-Text")
        before = self.run_hook()
        self.write(".claude/run/phase-2.md", RUN_STATE)
        ctx = self.context()
        base = json.loads(before)["hookSpecificOutput"]["additionalContext"]
        self.assertTrue(ctx.startswith(base))
        self.assertIn("Weitermachen mit execute-plan Schritt 0", ctx[len(base):])

    def test_unchanged_without_state(self):
        self.write(".claude/state.md", "Uebergabe-Text")
        os.makedirs(os.path.join(self.project, ".claude", "run"))
        self.write(".claude/run/auslauf-s1", "kontext")
        self.assertNotIn("execute-plan", self.context())

    def test_newest_state_wins(self):
        self.write(".claude/run/alt.md", RUN_STATE.replace("phase/x", "phase/alt"))
        os.utime(os.path.join(self.project, ".claude/run/alt.md"), (1, 1))
        self.write(".claude/run/neu.md", RUN_STATE.replace("phase/x", "phase/neu"))
        text = session_state.run_summary(self.project)
        self.assertIn("phase/neu", text)
        self.assertNotIn("phase/alt", text)


class TestNewerReports(Base):
    """t1: Berichte in .claude/plans/, die neuer sind als der Laufzustand."""

    def setUp(self):
        super().setUp()
        self.write(".claude/run/phase-2.md", RUN_STATE)
        self.state_file = os.path.join(self.project, ".claude/run/phase-2.md")
        os.utime(self.state_file, (1000, 1000))

    def report(self, name, mtime):
        self.write(".claude/plans/" + name, "# Bericht\n")
        os.utime(os.path.join(self.project, ".claude/plans", name), (mtime, mtime))

    def test_newer_report_is_named(self):
        self.report("phase-2-bericht.md", 2000)
        ctx = self.context()
        self.assertIn("phase-2-bericht.md", ctx)
        self.assertIn("Weitermachen mit execute-plan Schritt 0", ctx)

    def test_no_report_no_mention(self):
        self.write(".claude/plans/phase-2.md", "# Plan\n")
        os.utime(os.path.join(self.project, ".claude/plans/phase-2.md"), (2000, 2000))
        self.assertNotIn("plans/", self.context())

    def test_older_report_not_named(self):
        self.report("phase-1-bericht.md", 500)
        self.assertNotIn("phase-1-bericht.md", self.context())

    def test_only_newer_of_two_reports(self):
        self.report("phase-1-bericht.md", 500)
        self.report("phase-2-bericht.md", 2000)
        ctx = self.context()
        self.assertIn("phase-2-bericht.md", ctx)
        self.assertNotIn("phase-1-bericht.md", ctx)

    def test_without_run_state_nothing_to_compare(self):
        os.remove(self.state_file)
        self.report("phase-2-bericht.md", 2000)
        self.assertNotIn("phase-2-bericht.md", self.context())


if __name__ == "__main__":
    unittest.main()
