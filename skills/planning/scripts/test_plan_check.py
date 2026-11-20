"""Tests fuer plan-check.py (synthetische Plaene im Temp-Ordner, nur Standardbibliothek)."""
import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "plan-check.py")


def load():
    spec = importlib.util.spec_from_file_location("plan_check", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


pc = load()

BLOCKS = """| Block | Tasks | Files | Wave | Exclusive |
|---|---|---|---|---|
| b1 | a1, a2 | skills/x/, tests/x/ | 1 | no |
| b2 | a3, a4 | skills/y/ | 1 | no |
"""

TASKS = """| Id | Block | Task | Test target (seam) | Requirements |
|---|---|---|---|---|
| a1 | b1 | Parser | `parse()`: leer | REQ-001 |
| a2 | b1 | Writer | `write()`: Fehler | REQ-002 |
| a3 | b2 | Text | n/a: text | AC-001 |
| a4 | b2 | Lader | `load()`: fehlt | REQ-001, SEC-001 |
"""

DECISIONS = """| Question | Answer | Reason |
|---|---|---|
| Format | Tabellen | maschinenlesbar |
"""

SECTIONS = {
    "Context": "Hintergrund.",
    "Goal": "Ziel des Plans.",
    "Decisions": DECISIONS,
    "Critical files": "- skills/x/a.py",
    "Order": "b1 und b2 parallel.",
    "Blocks": BLOCKS,
    "Waves": "Welle 1: b1, b2.",
    "Tasks": TASKS,
    "Tests": "Je Anforderung ein Fall.",
    "Verification": "`python3 -I -m unittest discover`",
    "Out of scope": "Parallele Gates.",
}


def make_plan(**over):
    """Sauberer Plan; over[Name mit _ statt Leerzeichen] ersetzt den Inhalt, None entfernt den Abschnitt."""
    parts = ["# Plan: Probe\n"]
    keys = {k.replace(" ", "_"): k for k in SECTIONS}
    for key, body in SECTIONS.items():
        name = key.replace(" ", "_")
        if name in over:
            body = over[name]
        if body is None:
            continue
        parts.append(f"## {key}\n\n{body}\n")
    assert set(over) <= set(keys), "unbekannter Abschnitt"
    return "\n".join(parts)


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def rules(findings):
    return sorted({f[0] for f in findings})


def lint(text, depth="standard", ids=None, limits=None):
    return pc.lint_plan(text, depth, ids, limits or pc.parse_limits(None))


class CleanPlanTest(unittest.TestCase):
    def test_clean_standard(self):
        self.assertEqual(lint(make_plan()), [])

    def test_clean_mini_needs_fewer_sections(self):
        text = make_plan(Decisions=None, Critical_files=None, Order=None, Waves=None)
        self.assertEqual(lint(text, "mini"), [])
        self.assertEqual(rules(lint(text, "standard")), ["L1"])

    def test_aliases_and_combined_heading(self):
        text = (
            "## Kontext und Ziel\n\nx\n\n## Blocks and waves\n\n" + BLOCKS +
            "\n### Tasks\n\n" + TASKS + "\n## TESTS\n\nx\n\n## Verifikation\n\n`pytest`\n\n"
            "## Out of scope\n\nNichts Weiteres, ausser Specs.\n\n## Entscheidungen\n\n" + DECISIONS +
            "\n## Kritische Dateien\n\nx\n\n## Reihenfolge\n\nx\n"
        )
        self.assertEqual(lint(text), [])

    def test_table_columns_any_order_case_and_extra(self):
        blocks = ("| files | EXCLUSIVE | Wave | Notes | tasks | BLOCK |\n|---|---|---|---|---|---|\n"
                  "| skills/x/ | no | 1 | n | a1, a2 | b1 |\n| skills/y/ | no | 1 | n | a3, a4 | b2 |\n")
        tasks = ("| Requirements | Id | Test Target | Task | Block |\n|---|---|---|---|---|\n"
                 "| REQ-001 | a1 | `f()` | t | b1 |\n")
        self.assertEqual(lint(make_plan(Blocks=blocks, Tasks=tasks)), [])


class RuleTest(unittest.TestCase):
    def test_l1_missing_section(self):
        found = lint(make_plan(Tests=None))
        self.assertEqual(rules(found), ["L1"])
        self.assertIn("Tests", found[0][1])

    def test_l2_empty_and_placeholder(self):
        for body in ("", "none", "- TBD", "n/a", "keine", "<todo>"):
            self.assertEqual(rules(lint(make_plan(Out_of_scope=body))), ["L2"], body)

    def test_l3_block_without_files(self):
        blocks = BLOCKS.replace("skills/y/", "")
        found = lint(make_plan(Blocks=blocks))
        self.assertEqual(rules(found), ["L3"])
        self.assertEqual(found[0][1], "b2")

    def test_l3_block_without_tasks(self):
        blocks = BLOCKS.replace("a3, a4", "")
        self.assertEqual(rules(lint(make_plan(Blocks=blocks))), ["L3"])

    def test_l3_single_task_only_if_exclusive(self):
        blocks = BLOCKS.replace("a3, a4", "a3")
        self.assertEqual(rules(lint(make_plan(Blocks=blocks))), ["L3"])
        lines = blocks.splitlines()
        lines[-1] = "| b2 | a3 | skills/y/ | 2 | yes |"
        self.assertEqual(lint(make_plan(Blocks="\n".join(lines) + "\n")), [])

    def test_l3_too_many_tasks(self):
        seven = ", ".join(f"a{i}" for i in range(1, 8))
        six = ", ".join(f"a{i}" for i in range(1, 7))
        self.assertEqual(rules(lint(make_plan(Blocks=BLOCKS.replace("a1, a2", seven)))), ["L3"])
        self.assertEqual(lint(make_plan(Blocks=BLOCKS.replace("a1, a2", six))), [])

    def test_l4_overlap_same_path(self):
        blocks = BLOCKS.replace("skills/y/", "skills/x/")
        self.assertEqual(rules(lint(make_plan(Blocks=blocks))), ["L4"])

    def test_l4_overlap_parent_child(self):
        blocks = BLOCKS.replace("skills/y/", "skills/x/sub/file.py")
        self.assertEqual(rules(lint(make_plan(Blocks=blocks))), ["L4"])

    def test_l4_prefix_name_is_not_overlap(self):
        blocks = BLOCKS.replace("skills/y/", "skills/xy/")
        self.assertEqual(lint(make_plan(Blocks=blocks)), [])

    def test_l4_disjoint_in_different_waves_may_share_nothing(self):
        blocks = BLOCKS.replace("skills/y/", "skills/x/").replace("| b2 | a3, a4 | skills/x/ | 1 |", "| b2 | a3, a4 | skills/x/ | 2 |")
        self.assertEqual(lint(make_plan(Blocks=blocks)), [])

    def test_l4_exclusive_shares_wave(self):
        blocks = BLOCKS.replace("skills/y/ | 1 | no", "skills/y/ | 1 | yes")
        self.assertEqual(rules(lint(make_plan(Blocks=blocks))), ["L4"])

    def test_l4_fourth_block_in_wave(self):
        rows = "".join(f"| b{i} | a{i}, c{i} | d{i}/ | 1 | no |\n" for i in range(1, 5))
        blocks = "| Block | Tasks | Files | Wave | Exclusive |\n|---|---|---|---|---|\n" + rows
        self.assertEqual(rules(lint(make_plan(Blocks=blocks))), ["L4"])
        three = "| Block | Tasks | Files | Wave | Exclusive |\n|---|---|---|---|---|\n" + "".join(
            f"| b{i} | a{i}, c{i} | d{i}/ | 1 | no |\n" for i in range(1, 4))
        self.assertEqual(lint(make_plan(Blocks=three)), [])

    def test_l4_block_without_wave(self):
        blocks = BLOCKS.replace("skills/y/ | 1 |", "skills/y/ |  |")
        found = lint(make_plan(Blocks=blocks))
        self.assertEqual(rules(found), ["L4"])
        self.assertEqual(found[0][1], "b2")

    def test_l5_missing_target(self):
        tasks = TASKS.replace("`parse()`: leer", "")
        found = lint(make_plan(Tasks=tasks))
        self.assertEqual(rules(found), ["L5"])
        self.assertEqual(found[0][1], "a1")

    def test_l5_target_without_seam(self):
        tasks = TASKS.replace("`parse()`: leer", "Parser testen")
        self.assertEqual(rules(lint(make_plan(Tasks=tasks))), ["L5"])

    def test_l6_requirement_coverage(self):
        with tempfile.TemporaryDirectory() as tmp:
            write(os.path.join(tmp, "spec", "a.md"), "REQ-001 eins\nREQ-002 zwei\n")
            write(os.path.join(tmp, "spec", "sub", "b.md"), "AC-009 drei\nREQ-001 nochmal\n")
            ids = pc.collect_req_ids([os.path.join(tmp, "spec")], pc.DEFAULT_REQ)
        self.assertEqual(ids, ["AC-009", "REQ-001", "REQ-002"])
        found = lint(make_plan(), ids=ids)
        self.assertEqual([(f[0], f[1]) for f in found], [("L6", "AC-009")])
        covered = lint(make_plan(Out_of_scope="AC-009 bleibt draussen."), ids=ids)
        self.assertEqual(covered, [])

    def test_l6_custom_pattern(self):
        with tempfile.TemporaryDirectory() as tmp:
            write(os.path.join(tmp, "s.md"), "REQ-001 und R7 und R8\n")
            ids = pc.collect_req_ids([os.path.join(tmp, "s.md")], r"\bR\d+\b")
        self.assertEqual(ids, ["R7", "R8"])

    def test_l7_no_command(self):
        self.assertEqual(rules(lint(make_plan(Verification="Alles pruefen."))), ["L7"])

    def test_l7_fenced_block_counts(self):
        self.assertEqual(lint(make_plan(Verification="```\npytest\n```")), [])

    def test_l8_empty_reason(self):
        dec = "| Question | Answer | Reason |\n|---|---|---|\n| Format | Tabellen |  |\n"
        self.assertEqual(rules(lint(make_plan(Decisions=dec))), ["L8"])

    def test_l8_not_checked_in_mini(self):
        dec = "| Question | Answer | Reason |\n|---|---|---|\n| Format | Tabellen |  |\n"
        self.assertEqual(lint(make_plan(Decisions=dec), "mini"), [])

    def test_headings_in_fence_ignored(self):
        text = make_plan(Tests="```\n## Verification\n```")
        self.assertEqual(lint(text), [])


class SixFaultsTest(unittest.TestCase):
    def test_six_faults_all_found(self):
        dec = "| Question | Answer | Reason |\n|---|---|---|\n| Format | Tabellen |  |\n"
        blocks = BLOCKS.replace("skills/y/", "")
        tasks = TASKS.replace("`load()`: fehlt", "")
        text = make_plan(
            Critical_files=None,        # L1
            Out_of_scope="none",        # L2
            Blocks=blocks,              # L3
            Tasks=tasks,                # L5
            Verification="Pruefen.",    # L7
            Decisions=dec,              # L8
        )
        self.assertEqual(rules(lint(text)), ["L1", "L2", "L3", "L5", "L7", "L8"])


def run(*args):
    return subprocess.run([sys.executable, "-I", SCRIPT, *args], capture_output=True, text=True)


class CliLintTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def path(self, name, text):
        p = os.path.join(self.tmp.name, name)
        write(p, text)
        return p

    def test_clean_exit_0(self):
        r = run("lint", self.path("p.md", make_plan()))
        self.assertEqual((r.returncode, r.stdout), (0, ""))

    def test_findings_exit_1_with_shape(self):
        r = run("lint", self.path("p.md", make_plan(Verification="x")))
        self.assertEqual(r.returncode, 1)
        line = r.stdout.splitlines()[0]
        self.assertRegex(line, r"^L7 \S.*: .+")

    def test_deterministic(self):
        p = self.path("p.md", make_plan(Verification="x", Out_of_scope="none"))
        self.assertEqual(run("lint", p).stdout, run("lint", p).stdout)

    def test_missing_file_exit_2(self):
        r = run("lint", os.path.join(self.tmp.name, "gibt-es-nicht.md"))
        self.assertEqual(r.returncode, 2)
        self.assertNotIn("Traceback", r.stderr)
        self.assertEqual(len(r.stderr.strip().splitlines()), 1)

    def test_free_form_plan_exit_2(self):
        r = run("lint", self.path("p.md", "# Plan\n\n## Blocks\n\n- b1: x\n"))
        self.assertEqual(r.returncode, 2)
        self.assertNotIn("Traceback", r.stderr)

    def test_binary_file_exit_2(self):
        p = os.path.join(self.tmp.name, "b.md")
        with open(p, "wb") as fh:
            fh.write(b"\xff\xfe\x00\x80")
        r = run("lint", p)
        self.assertEqual(r.returncode, 2)
        self.assertNotIn("Traceback", r.stderr)

    def test_specs_option(self):
        spec = self.path("spec/a.md", "REQ-001 REQ-077\n")
        r = run("lint", self.path("p.md", make_plan()), "--specs", os.path.dirname(spec))
        self.assertEqual(r.returncode, 1)
        self.assertIn("L6 REQ-077", r.stdout)

    def test_bad_spec_path_and_pattern_exit_2(self):
        p = self.path("p.md", make_plan())
        self.assertEqual(run("lint", p, "--specs", os.path.join(self.tmp.name, "nix")).returncode, 2)
        s = self.path("s.md", "REQ-001")
        self.assertEqual(run("lint", p, "--specs", s, "--req-pattern", "(").returncode, 2)

    def test_depth_option(self):
        p = self.path("p.md", make_plan(Decisions=None, Critical_files=None, Order=None, Waves=None))
        self.assertEqual(run("lint", p, "--depth", "mini").returncode, 0)
        self.assertEqual(run("lint", p).returncode, 1)


if __name__ == "__main__":
    unittest.main()
