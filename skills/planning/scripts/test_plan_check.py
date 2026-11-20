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


def blocks_table(rows):
    """rows: Liste (Block, Dateien, Exklusiv)."""
    head = "| Block | Tasks | Files | Wave | Exclusive |\n|---|---|---|---|---|\n"
    return head + "".join(
        f"| {b} | {b}1, {b}2 | {files} | {n + 1} | {ex} |\n" for n, (b, files, ex) in enumerate(rows))


def n_files(n, prefix="src/"):
    return ", ".join(f"{prefix}f{i}.py" for i in range(n))


def stage_of(files, blocks=1, exclusive=False, depth=None, limits=None, schema=None, security=None):
    rows = [(f"b{i}", files if i == 0 else f"other{i}/x.py", "no") for i in range(blocks)]
    if exclusive:
        rows[-1] = (rows[-1][0], rows[-1][1], "yes")
    text = make_plan(Blocks=blocks_table(rows))
    return pc.stage_plan(
        text, depth, pc.parse_limits(limits),
        pc.compile_re(schema or pc.DEFAULT_SCHEMA, "x"), pc.compile_re(security or pc.DEFAULT_SECURITY, "x"))


class StageTest(unittest.TestCase):
    def test_s_at_five_files(self):
        self.assertEqual(stage_of(n_files(5))[0], "S")

    def test_m_at_six_files(self):
        self.assertEqual(stage_of(n_files(6))[0], "M")

    def test_m_two_blocks_few_files(self):
        self.assertEqual(stage_of(n_files(2), blocks=2)[0], "M")

    def test_m_at_25_files(self):
        self.assertEqual(stage_of(n_files(25))[0], "M")

    def test_l_at_26_files(self):
        self.assertEqual(stage_of(n_files(26))[0], "L")

    def test_files_counted_across_blocks(self):
        self.assertEqual(stage_of(n_files(23), blocks=3)[0], "M")
        self.assertEqual(stage_of(n_files(23), blocks=4)[0], "L")

    def test_l_exclusive_block(self):
        stage, reasons = stage_of(n_files(1), blocks=2, exclusive=True)
        self.assertEqual(stage, "L")
        self.assertTrue(any("b1" in r for r in reasons))

    def test_l_schema_path(self):
        self.assertEqual(stage_of("db/migrations/001.py, a.py")[0], "L")
        self.assertEqual(stage_of("db/init.sql")[0], "L")

    def test_l_security_path(self):
        self.assertEqual(stage_of("src/auth/login.py")[0], "L")

    def test_custom_path_patterns(self):
        self.assertEqual(stage_of("src/billing/x.py", security=r"billing")[0], "L")
        self.assertEqual(stage_of("db/migrations/001.py", schema=r"^nomatch$")[0], "S")

    def test_depth_is_lower_bound(self):
        self.assertEqual(stage_of(n_files(1), depth="mini")[0], "S")
        self.assertEqual(stage_of(n_files(1), depth="standard")[0], "M")
        self.assertEqual(stage_of(n_files(1), depth="voll")[0], "L")
        self.assertEqual(stage_of(n_files(30), depth="mini")[0], "L")
        self.assertEqual(stage_of(n_files(10), depth="standard")[0], "M")

    def test_limits_override(self):
        self.assertEqual(stage_of(n_files(6), limits="stage_s_files=6")[0], "S")
        self.assertEqual(stage_of(n_files(5), limits="stage_s_files=4")[0], "M")
        self.assertEqual(stage_of(n_files(26), limits="stage_l_files=30")[0], "M")
        self.assertEqual(stage_of(n_files(10), limits="stage_l_files=9")[0], "L")

    def test_reasons_not_empty(self):
        self.assertTrue(stage_of(n_files(3))[1])


class CliStageTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def plan(self, text, name="p.md"):
        p = os.path.join(self.tmp.name, name)
        write(p, text)
        return p

    def test_first_line_one_word_exit_0(self):
        text = make_plan(Blocks=blocks_table([("b1", n_files(3), "no")]))
        r = run("stage", self.plan(text))
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.splitlines()[0], "S")
        self.assertGreater(len(r.stdout.splitlines()), 1)

    def test_deterministic(self):
        p = self.plan(make_plan())
        self.assertEqual(run("stage", p, "--depth", "voll").stdout, run("stage", p, "--depth", "voll").stdout)
        self.assertEqual(run("stage", p, "--depth", "voll").stdout.splitlines()[0], "L")

    def test_input_errors_exit_2(self):
        for args in (["stage", os.path.join(self.tmp.name, "nix.md")],
                     ["stage", self.plan("# Plan\n\nfrei\n", "frei.md")],
                     ["stage", self.plan(make_plan()), "--limits", "files"],
                     ["stage", self.plan(make_plan()), "--limits", "nope=1"],
                     ["stage", self.plan(make_plan()), "--schema-paths", "("],
                     ["stage", self.plan(make_plan()), "--depth", "riesig"]):
            r = run(*args)
            self.assertEqual(r.returncode, 2, args)
            self.assertNotIn("Traceback", r.stderr)
            self.assertEqual(len(r.stderr.strip().splitlines()), 1, args)


def depth_of(areas=1, specs=1, gates=3, files=5, flags=(), limits=None):
    return pc.depth_for(areas, specs, gates, files, list(flags), pc.parse_limits(limits))


class DepthTest(unittest.TestCase):
    def test_mini_at_thresholds(self):
        self.assertEqual(depth_of()[0], "mini")
        self.assertEqual(depth_of(areas=0, specs=0, gates=0, files=0)[0], "mini")

    def test_just_over_each_mini_threshold_is_standard(self):
        for kw in ({"areas": 2}, {"specs": 2}, {"gates": 4}, {"files": 6}):
            self.assertEqual(depth_of(**kw)[0], "standard", kw)

    def test_standard_at_three_areas_voll_at_four(self):
        self.assertEqual(depth_of(areas=3, specs=5, gates=9, files=50)[0], "standard")
        self.assertEqual(depth_of(areas=4)[0], "voll")

    def test_schema_and_security_flags_are_voll(self):
        self.assertEqual(depth_of(flags=["schema"])[0], "voll")
        self.assertEqual(depth_of(flags=["security"])[0], "voll")

    def test_other_flags_raise_to_standard(self):
        for flag in ("exclusive", "dependency", "nopattern"):
            self.assertEqual(depth_of(flags=[flag])[0], "standard", flag)
        self.assertEqual(depth_of(areas=4, flags=["dependency"])[0], "voll")

    def test_limits_override(self):
        self.assertEqual(depth_of(areas=2, limits="areas=2")[0], "mini")
        self.assertEqual(depth_of(files=9, limits="files=9")[0], "mini")
        self.assertEqual(depth_of(gates=5, limits="gate_points=5")[0], "mini")
        self.assertEqual(depth_of(specs=3, limits="spec_sources=3")[0], "mini")
        self.assertEqual(depth_of(areas=4, limits="standard_areas=4")[0], "standard")
        self.assertEqual(depth_of(files=5, limits="files=4")[0], "standard")

    def test_limits_ignores_other_limits(self):
        self.assertEqual(depth_of(limits="wave_blocks=9,block_tasks=9")[0], "mini")

    def test_reasons_not_empty(self):
        self.assertTrue(depth_of(areas=4)[1])


class CliDepthTest(unittest.TestCase):
    BASE = ["depth", "--areas", "1", "--spec-sources", "1", "--gate-points", "3", "--files", "5"]

    def test_output_shape(self):
        r = run(*self.BASE)
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.splitlines()[0], "mini")
        self.assertGreater(len(r.stdout.splitlines()), 1)

    def test_flags_repeated_and_listed(self):
        a = run(*self.BASE, "--flag", "schema", "--flag", "exclusive")
        b = run(*self.BASE, "--flag", "schema", "exclusive")
        self.assertEqual(a.stdout.splitlines()[0], "voll")
        self.assertEqual(a.stdout, b.stdout)

    def test_limits_and_determinism(self):
        args = [*self.BASE[:2], "2", *self.BASE[3:], "--limits", "areas=2"]
        r = run(*args)
        self.assertEqual(r.stdout.splitlines()[0], "mini")
        self.assertEqual(r.stdout, run(*args).stdout)

    def test_input_errors_exit_2(self):
        for extra in (["--flag", "bogus"], ["--limits", "areas=x"], ["--limits", "zzz=1"]):
            r = run(*self.BASE, *extra)
            self.assertEqual(r.returncode, 2, extra)
            self.assertNotIn("Traceback", r.stderr)
        r = run("depth", "--areas", "1")
        self.assertEqual(r.returncode, 2)
        self.assertEqual(len(r.stderr.strip().splitlines()), 1)
        self.assertEqual(run("depth", "--areas", "x").returncode, 2)


if __name__ == "__main__":
    unittest.main()
