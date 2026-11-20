"""Tests fuer session-cost.py: Rollen und Limit-Luecken, mit synthetischen Transkripten."""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "session-cost.py")
_spec = importlib.util.spec_from_file_location("session_cost", SCRIPT)
sc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sc)


def line(ts, text="hallo", mid=None, typ="assistant", out=10):
    o = {"type": typ, "timestamp": ts, "uuid": mid or ts,
         "message": {"id": mid or ts, "model": "m-x", "content": [{"type": "text", "text": text}],
                     "usage": {"output_tokens": out}}}
    return json.dumps(o)


def write(path, lines):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


class RoleTest(unittest.TestCase):
    def test_block_review(self):
        self.assertEqual(sc.classify_role("Review Block b2"), "block-review")

    def test_block_fix(self):
        self.assertEqual(sc.classify_role("Fix findings b3"), "block-fix")

    def test_gate_review(self):
        self.assertEqual(sc.classify_role("Gate review plan"), "gate-review")
        self.assertEqual(sc.classify_role("Phase review"), "gate-review")
        self.assertEqual(sc.classify_role("Thermo review"), "gate-review")

    def test_gate_fix(self):
        self.assertEqual(sc.classify_role("Fix gate findings"), "gate-fix")
        self.assertEqual(sc.classify_role("Fix Umbau"), "gate-fix")

    def test_build(self):
        self.assertEqual(sc.classify_role("Build block b1"), "build")
        self.assertEqual(sc.classify_role("Bau der Skripte"), "build")

    def test_research(self):
        self.assertEqual(sc.classify_role("Fetch docs"), "research")
        self.assertEqual(sc.classify_role("Lese Dateien"), "research")

    def test_other(self):
        self.assertEqual(sc.classify_role("Kaffee kochen"), "other")
        self.assertEqual(sc.classify_role(""), "other")

    def test_ordering_specific_first(self):
        # Gate-Review mit "block" im Text ist kein Block-Review
        self.assertEqual(sc.classify_role("Gate review after block"), "gate-review")
        # Gate-Fix mit Block-Id ist kein Block-Fix
        self.assertEqual(sc.classify_role("Fix gate finding b3"), "gate-fix")
        # Fix mit Block-Id vor build
        self.assertEqual(sc.classify_role("Fix build b3"), "block-fix")
        # build vor research
        self.assertEqual(sc.classify_role("Read and build"), "build")


def make_projects(tmp, agents, main_lines=None):
    proj = os.path.join(tmp, "projekt-a")
    write(os.path.join(proj, "s1.jsonl"), main_lines or [line("2026-11-01T10:00:00Z"), line("2026-11-01T10:01:00Z")])
    for i, (desc, out) in enumerate(agents):
        base = os.path.join(proj, "s1", "subagents", f"agent-{i}")
        write(base + ".jsonl", [line("2026-11-01T10:00:00Z", mid=f"a{i}", out=out),
                                line("2026-11-01T10:02:00Z", mid=f"b{i}", out=out)])
        with open(base + ".meta.json", "w", encoding="utf-8") as fh:
            json.dump({"description": desc, "agentType": "x"}, fh)
    return tmp


def run(*args):
    return subprocess.run([sys.executable, "-I", SCRIPT, *args], capture_output=True, text=True)


class RolesCliTest(unittest.TestCase):
    def test_roles_table(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_projects(tmp, [("Build block b1", 5), ("Build block b2", 7), ("Review Block b1", 3)])
            r = run("--root", tmp, "--roles")
            self.assertEqual(r.returncode, 0, r.stderr)
            rows = {l.split()[0]: l.split() for l in r.stdout.splitlines() if l.split()}
            self.assertEqual(rows["build"][1:], ["2", "4.0", "24"])
            self.assertEqual(rows["block-review"][1:], ["1", "2.0", "6"])


if __name__ == "__main__":
    unittest.main()
