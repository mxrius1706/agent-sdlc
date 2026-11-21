"""Tests fuer auslauf.py: Funktionen und Unterprozess, synthetische Projekte."""

import importlib.util
import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "auslauf.py")
spec = importlib.util.spec_from_file_location("auslauf", SCRIPT)
auslauf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(auslauf)

TABLE = (
    "Phasen-Branch: phase/x\nPlan: p.md\nRegelbuendel: r.md\n\n"
    "| Block | Status | Statuscode | Fix-Runden | Worktree |\n"
    "|---|---|---|---|---|\n"
    "| b1 | laufend | - | 0 | w1 |\n"
    "| b2 | review | - | 0 | w2 |\n"
    "| b3 | fix | - | 1 | w3 |\n"
    "| b4 | gemerged | DONE | 0 | w4 |\n"
    "| b5 | offen | - | 0 | - |\n"
)


def write_transcript(path, lines):
    with open(path, "w", encoding="utf-8") as handle:
        for entry in lines:
            handle.write(json.dumps(entry) + "\n")


def assistant(msg_id, inp, cc=0, cr=0):
    return {"type": "assistant", "message": {"id": msg_id, "usage": {
        "input_tokens": inp, "cache_creation_input_tokens": cc,
        "cache_read_input_tokens": cr}}}


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.project = os.path.join(self.tmp.name, "projekt-a")
        self.run_dir = os.path.join(self.project, ".claude", "run")
        os.makedirs(self.run_dir)
        self.transcript = os.path.join(self.tmp.name, "t.jsonl")

    def state(self, text=TABLE):
        with open(os.path.join(self.run_dir, "phase-2.md"), "w") as handle:
            handle.write(text)

    def set_fill(self, tokens):
        write_transcript(self.transcript, [assistant("m1", tokens)])

    def call(self, event, **extra):
        data = {"session_id": "s1", "transcript_path": self.transcript,
                "cwd": self.project, "hook_event_name": event}
        data.update(extra)
        env = dict(os.environ, CLAUDE_PROJECT_DIR=self.project)
        proc = subprocess.run([sys.executable, "-I", SCRIPT],
                              input=json.dumps(data), capture_output=True,
                              text=True, env=env)
        return proc

    def mark(self):
        return os.path.join(self.run_dir, "auslauf-s1")


class TestFill(Base):
    def test_sum_of_three_fields(self):
        write_transcript(self.transcript, [assistant("m1", 100000, 200000, 300000)])
        self.assertAlmostEqual(auslauf.fill(self.transcript, 1000000), 0.6)

    def test_same_id_last_wins(self):
        write_transcript(self.transcript, [
            assistant("m1", 100000), assistant("m1", 500000),
            {"type": "user", "message": {"content": "x"}}])
        self.assertAlmostEqual(auslauf.fill(self.transcript, 1000000), 0.5)

    def test_empty_or_missing(self):
        open(self.transcript, "w").close()
        self.assertEqual(auslauf.fill(self.transcript, 1000000), 0)
        self.assertEqual(auslauf.fill(self.transcript + "x", 1000000), 0)


class TestConfig(Base):
    def test_defaults(self):
        self.assertEqual(auslauf.read_config(self.project),
                         {"fenster": 1000000, "kontext": 0.6, "notbremse": 0.8})

    def test_override_and_broken(self):
        path = os.path.join(self.project, ".claude", "auslauf.json")
        with open(path, "w") as handle:
            handle.write('{"kontext": 0.5}')
        self.assertEqual(auslauf.read_config(self.project)["kontext"], 0.5)
        with open(path, "w") as handle:
            handle.write("{kaputt")
        self.assertEqual(auslauf.read_config(self.project)["kontext"], 0.6)


class TestRunning(Base):
    def test_running_blocks(self):
        self.state()
        self.assertEqual(sorted(auslauf.running_blocks(self.run_dir)),
                         ["b1", "b2", "b3"])

    def test_no_state(self):
        self.assertEqual(auslauf.running_blocks(self.run_dir), [])


class TestThresholds(Base):
    def run_prompt(self, tokens):
        self.set_fill(tokens)
        return self.call("UserPromptSubmit", prompt="hallo")

    def test_below(self):
        proc = self.run_prompt(599999)
        self.assertEqual((proc.returncode, proc.stdout), (0, ""))
        self.assertFalse(os.path.exists(self.mark()))

    def test_on_threshold(self):
        proc = self.run_prompt(600000)
        self.assertEqual(proc.returncode, 0)
        self.assertIn("session-recap", proc.stdout)
        self.assertTrue(os.path.exists(self.mark()))

    def test_above(self):
        self.assertIn("session-recap", self.run_prompt(600001).stdout)

    def test_printed_once(self):
        self.assertNotEqual(self.run_prompt(650000).stdout, "")
        self.assertEqual(self.run_prompt(650000).stdout, "")

    def test_notbremse_levels(self):
        self.run_prompt(650000)
        self.set_fill(799999)
        self.assertEqual(self.call("UserPromptSubmit", prompt="x").stdout, "")
        self.set_fill(800000)
        out = self.call("UserPromptSubmit", prompt="x").stdout
        self.assertIn("NOTBREMSE", out)
        self.assertEqual(self.call("UserPromptSubmit", prompt="x").stdout, "")

    def test_notbremse_directly(self):
        self.assertIn("NOTBREMSE", self.run_prompt(800001).stdout)

    def test_posttooluse_json(self):
        self.set_fill(650000)
        out = json.loads(self.call("PostToolUse", tool_name="Bash").stdout)
        spec_out = out["hookSpecificOutput"]
        self.assertEqual(spec_out["hookEventName"], "PostToolUse")
        self.assertIn("session-recap", spec_out["additionalContext"])

    def test_subagent_ignored(self):
        self.set_fill(900000)
        proc = self.call("UserPromptSubmit", prompt="x", agent_id="a1")
        self.assertEqual((proc.returncode, proc.stdout), (0, ""))
        self.assertFalse(os.path.exists(self.mark()))


class TestGoalClear(Base):
    """t5: bei gesetzter Auslauf-Marke nennt die Ausgabe `/goal clear`."""

    def run_prompt(self, tokens):
        self.set_fill(tokens)
        return self.call("UserPromptSubmit", prompt="hallo")

    def test_instruction_names_goal_clear(self):
        self.assertIn("/goal clear", self.run_prompt(650000).stdout)

    def test_emergency_names_goal_clear(self):
        self.assertIn("/goal clear", self.run_prompt(850000).stdout)

    def test_posttooluse_names_goal_clear(self):
        self.set_fill(650000)
        out = json.loads(self.call("PostToolUse", tool_name="Bash").stdout)
        self.assertIn("/goal clear", out["hookSpecificOutput"]["additionalContext"])

    def test_below_threshold_no_hint(self):
        self.assertNotIn("/goal clear", self.run_prompt(100000).stdout)


class TestPreToolUse(Base):
    def agent(self, prompt, **extra):
        return self.call("PreToolUse", tool_name="Agent",
                         tool_input={"prompt": prompt}, **extra)

    def denied(self, proc):
        if not proc.stdout:
            return False
        out = json.loads(proc.stdout)["hookSpecificOutput"]
        self.assertEqual(out["hookEventName"], "PreToolUse")
        return out["permissionDecision"] == "deny"

    def setUp(self):
        super().setUp()
        self.state()
        open(self.mark(), "w").close()

    def test_no_id_denied(self):
        self.assertTrue(self.denied(self.agent("baue etwas")))

    def test_running_ids_allowed(self):
        for block in ("b1", "b2", "b3"):
            self.assertFalse(self.denied(self.agent("Block " + block + " weiter")))

    def test_merged_denied(self):
        self.assertTrue(self.denied(self.agent("Block b4 nochmal")))

    def test_id_is_whole_word(self):
        self.assertTrue(self.denied(self.agent("Block b10 neu")))

    def test_without_mark_allowed(self):
        os.remove(self.mark())
        self.assertFalse(self.denied(self.agent("baue etwas")))

    def test_subagent_ignored(self):
        self.assertFalse(self.denied(self.agent("baue etwas", agent_id="a1")))

    def test_other_tool_ignored(self):
        proc = self.call("PreToolUse", tool_name="Bash", tool_input={"command": "ls"})
        self.assertEqual(proc.stdout, "")

    def test_no_run_state_allowed(self):
        os.remove(os.path.join(self.run_dir, "phase-2.md"))
        proc = self.agent("baue etwas")
        self.assertEqual((proc.returncode, proc.stdout), (0, ""))


class TestRobust(Base):
    def test_garbage_stdin(self):
        proc = subprocess.run([sys.executable, "-I", SCRIPT], input="kein json",
                              capture_output=True, text=True)
        self.assertEqual((proc.returncode, proc.stdout), (0, ""))

    def test_broken_config_still_works(self):
        with open(os.path.join(self.project, ".claude", "auslauf.json"), "w") as h:
            h.write("{kaputt")
        self.set_fill(650000)
        proc = self.call("UserPromptSubmit", prompt="x")
        self.assertEqual(proc.returncode, 0)
        self.assertIn("session-recap", proc.stdout)

    def test_unwritable_run_dir(self):
        self.set_fill(650000)
        os.chmod(self.run_dir, stat.S_IRUSR | stat.S_IXUSR)
        self.addCleanup(os.chmod, self.run_dir, stat.S_IRWXU)
        proc = self.call("UserPromptSubmit", prompt="x")
        self.assertEqual((proc.returncode, proc.stdout), (0, ""))


if __name__ == "__main__":
    unittest.main()
