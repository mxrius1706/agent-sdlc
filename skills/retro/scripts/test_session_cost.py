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


class AgentTypeTest(unittest.TestCase):
    """Der Agententyp der Rollen gewinnt vor den Stichworten der Beschreibung."""

    def test_type_wins(self):
        cases = {"gate-reviewer": "gate-review", "block-reviewer": "block-review", "block-fixer": "block-fix",
                 "block-implementer": "build", "acceptance-writer": "build"}
        for typ, role in cases.items():
            self.assertEqual(sc.classify_role("Cluster B portal server", typ), role, typ)

    def test_unknown_type_falls_back_to_words(self):
        self.assertEqual(sc.classify_role("Review Block b2", "general-purpose"), "block-review")
        self.assertEqual(sc.classify_role("Review Block b2", "?"), "block-review")
        self.assertEqual(sc.classify_role("Review Block b2", None), "block-review")


class HandlaufRoleTest(unittest.TestCase):
    """Agents des Handlaufs bekommen eine eigene Rolle statt `other`."""

    def test_description_of_general_purpose_agent(self):
        self.assertEqual(sc.classify_role("Handlauf Phase 2", "general-purpose"), "handlauf")
        self.assertEqual(sc.classify_role("Handlauf: Plan gegen Code pruefen", "general-purpose"), "handlauf")

    def test_description_wins_over_review_words(self):
        self.assertEqual(sc.classify_role("Handlauf Review Phase 3", "general-purpose"), "handlauf")

    def test_type_handlauf(self):
        self.assertEqual(sc.classify_role("Durchlauf", "handlauf"), "handlauf")

    def test_role_table_has_row(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_projects(tmp, [("Handlauf Phase 2", 1), ("Build block b1", 1)])
            rows = {r["role"]: r for r in sc.role_table(sc.collect([tmp], None, None, None))}
            self.assertEqual(rows["handlauf"]["agents"], 1)
            self.assertEqual(rows["other"]["agents"], 0)

    def test_cli_prints_role(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_projects(tmp, [("Handlauf Phase 2", 1)])
            self.assertIn("handlauf", run("--root", tmp, "--roles").stdout)


def bash_line(ts, command):
    o = {"type": "assistant", "timestamp": ts, "uuid": ts,
         "message": {"id": ts, "model": "m-x", "usage": {"output_tokens": 5},
                     "content": [{"type": "tool_use", "id": "t" + ts, "name": "Bash", "input": {"command": command}}]}}
    return json.dumps(o)


class FixQuoteWithoutBuildAgentsTest(unittest.TestCase):
    """Ohne build-Agents ist die Fix-Quote nie ein stummes `-`: Zahl aus den Commits der Hauptsitzung oder benannter Grund."""

    def fix_line(self, out):
        return [l for l in out.splitlines() if l.startswith("Fix-Quote")][0]

    def test_quote_from_main_session_commits(self):
        main = [bash_line("2026-11-01T10:00:00Z", 'git commit -m "feat(a): erster Teil"'),
                bash_line("2026-11-01T10:01:00Z", 'git commit -m "feat(b): zweiter Teil"'),
                bash_line("2026-11-01T10:02:00Z", 'git commit -m "feat(c): dritter Teil"'),
                bash_line("2026-11-01T10:03:00Z", 'git commit -m "fix(a): Befund behoben"')]
        with tempfile.TemporaryDirectory() as tmp:
            make_projects(tmp, [("Review Block b1", 1)], main_lines=main)
            self.assertEqual(self.fix_line(run("--root", tmp, "--roles").stdout), "Fix-Quote 0.33")  # 1 Fix / 3 Bau

    def test_gap_is_named_when_not_derivable(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_projects(tmp, [("Review Block b1", 1)])  # weder build-Agents noch Commits
            text = self.fix_line(run("--root", tmp, "--roles").stdout)
            self.assertNotEqual(text.strip(), "Fix-Quote -")
            self.assertGreater(len(text.removeprefix("Fix-Quote -").strip()), 5, text)  # Grund steht dabei


class GenericTermsTest(unittest.TestCase):
    CASES = {
        "gate-review": ["Phase review plan", "Thermo review Datei", "Gate-Review nach Phase 2", "Phase 3 nachpruefen"],
        "gate-fix": ["Fix Phase findings", "Gate-Fix Runde"],
        "spec": ["Konsistenz Specs pruefen", "Spec-Rueckfluss", "Backflow der Hinweise", "ADR schreiben", "Review Konsistenz"],
        "block-review": ["Review der Aenderung", "Re-Review", "Fix-Review", "Nachpruefung Diff", "Folge-Review", "Fix-Diff pruefen",
                         "Sammelbefunde pruefen"],
        "block-fix": ["Fixer b2", "Fix-Block 3", "Fixes einarbeiten", "Fix-Runde", "Findings abarbeiten"],
        "build": ["Implement Parser", "Implementieren der Ausgabe", "Refactor Modul", "Write Skript", "Umbau Ausgabe"],
        "research": ["Suche nach Aufrufern", "Search usages", "Fehlersuche Ausgabe", "Erkunde Ordner"],
        "other": ["Kaffee kochen", "Inspect something", "Plan schreiben"],
    }

    def test_table(self):
        for role, labels in self.CASES.items():
            for lab in labels:
                self.assertEqual(sc.classify_role(lab), role, lab)

    def test_other_share_low(self):
        labels = [l for ls in self.CASES.values() for l in ls if l not in ("Kaffee kochen", "Inspect something", "Plan schreiben")]
        other = [l for l in labels if sc.classify_role(l) == "other"]
        self.assertEqual(other, [])

    def test_spec_not_matching_inside_words(self):
        self.assertNotEqual(sc.classify_role("Inspect specific thing"), "spec")


class FixQuoteTest(unittest.TestCase):
    def test_fix_quote_value_and_rounding(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_projects(tmp, [("Build block b1", 1), ("Build block b2", 1), ("Build block b3", 1),
                                ("Fix findings b1", 1), ("Fix gate findings", 1)])
            data = sc.collect([tmp], None, None, None)
            self.assertEqual(sc.fix_quote(sc.role_table(data)), 0.67)  # 4 Min / 6 Min

    def test_fix_quote_without_build(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_projects(tmp, [("Fix findings b1", 1)])
            data = sc.collect([tmp], None, None, None)
            self.assertIsNone(sc.fix_quote(sc.role_table(data)))

    def test_cli_row_and_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_projects(tmp, [("Build block b1", 1), ("Fix findings b1", 1)])
            r = run("--root", tmp, "--roles")
            self.assertIn("Fix-Quote 1.00", r.stdout)
            d = json.loads(run("--root", tmp, "--roles", "--json").stdout)
            self.assertEqual(d["fix_quote"], 1.0)

    def test_cli_row_without_build(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_projects(tmp, [("Fix findings b1", 1)])
            self.assertIn("Fix-Quote -", run("--root", tmp, "--roles").stdout)
            d = json.loads(run("--root", tmp, "--roles", "--json").stdout)
            self.assertIsNone(d["fix_quote"])


class PeriodTest(unittest.TestCase):
    def two_sessions(self, tmp):
        make_projects(tmp, [("Build block b1", 1)])
        proj = os.path.join(tmp, "projekt-a")
        write(os.path.join(proj, "s2.jsonl"), [line("2026-11-10T10:00:00Z"), line("2026-11-10T10:01:00Z")])

    def sessions(self, *args):
        d = json.loads(run("--root", self.tmp, "--json", *args).stdout)
        return sorted(x["session"] for x in d)

    def test_since_until(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.tmp = tmp
            self.two_sessions(tmp)
            self.assertEqual(self.sessions(), ["s1", "s2"])
            self.assertEqual(self.sessions("--until", "2026-11-05"), ["s1"])
            self.assertEqual(self.sessions("--since", "2026-11-05"), ["s2"])
            self.assertEqual(self.sessions("--until", "2026-11-10"), ["s1", "s2"])  # Endtag eingeschlossen
            self.assertEqual(self.sessions("--since", "2026-11-02", "--until", "2026-11-09"), [])


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


class RoleTableTest(unittest.TestCase):
    def test_role_table_names_and_values(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_projects(tmp, [("Build block b1", 5), ("Review Block b1", 3)])
            data = sc.collect([tmp], None, None, None)
            rows = {r["role"]: r for r in sc.role_table(data)}
            self.assertEqual(rows["build"], {"role": "build", "agents": 1, "minutes": 2.0, "out": 10})
            self.assertEqual(rows["other"]["agents"], 0)
            self.assertEqual(len(rows), len(sc.ROLES))

    def test_transcript_stamps_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_projects(tmp, [])
            t = sc.read_transcript(os.path.join(tmp, "projekt-a", "s1.jsonl"))
            self.assertEqual(len(t["stamps"]), 2)
            self.assertNotIn("ts", t)


class JsonModesTest(unittest.TestCase):
    def test_json_with_roles(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_projects(tmp, [("Build block b1", 5)])
            r = run("--root", tmp, "--roles", "--json")
            self.assertEqual(r.returncode, 0, r.stderr)
            d = json.loads(r.stdout)
            rows = {x["role"]: x for x in d["roles"]}
            self.assertEqual(rows["build"]["agents"], 1)
            self.assertEqual(rows["build"]["out"], 10)

    def test_json_with_gaps(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_projects(tmp, [], [line("2026-11-01T10:00:00Z", "limit resets 12:00"),
                                    line("2026-11-01T11:00:00Z")])
            r = run("--root", tmp, "--gaps", "--json")
            self.assertEqual(r.returncode, 0, r.stderr)
            d = json.loads(r.stdout)
            g = d["gaps"][0]
            self.assertEqual(g["session"], "s1")
            self.assertEqual(g["gaps"][0]["minutes"], 60)
            self.assertTrue(g["gaps"][0]["limit"])

    def test_json_plain_still_list(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_projects(tmp, [])
            d = json.loads(run("--root", tmp, "--json").stdout)
            self.assertIsInstance(d, list)


class GapTest(unittest.TestCase):
    def gaps(self, lines, **kw):
        with tempfile.TemporaryDirectory() as tmp:
            p = os.path.join(tmp, "t.jsonl")
            write(p, lines)
            return sc.limit_gaps(p, **kw)

    def test_limit_gap_normal_gap_and_short_pause(self):
        g = self.gaps([
            line("2026-11-01T10:00:00Z", "Arbeit"),
            line("2026-11-01T10:02:00Z", "Usage LIMIT reached, it Resets at 14:00"),
            line("2026-11-01T12:02:00Z", "weiter"),       # 120 Min nach Limit
            line("2026-11-01T12:03:00Z", "fertig"),
            line("2026-11-01T12:33:00Z", "noch was"),     # 30 Min nach normaler Nachricht
            line("2026-11-01T12:38:00Z", "kurz"),         # 5 Min: keine Luecke
        ])
        self.assertEqual(len(g), 2)
        self.assertEqual(g[0]["minutes"], 120)
        self.assertTrue(g[0]["limit"])
        self.assertTrue(g[0]["start"].startswith("2026-11-01T10:02:00"))
        self.assertEqual(g[1]["minutes"], 30)
        self.assertFalse(g[1]["limit"])

    def test_limit_needs_both_words(self):
        g = self.gaps([line("2026-11-01T10:00:00Z", "limit only"), line("2026-11-01T11:00:00Z")])
        self.assertFalse(g[0]["limit"])

    def test_user_line_between_limit_and_gap(self):
        # Eine Nutzerzeile nach der Limit-Meldung aendert nichts: die Luecke bleibt eine Limit-Luecke
        g = self.gaps([
            line("2026-11-01T10:00:00Z", "limit reached, resets 14:00"),
            line("2026-11-01T10:01:00Z", "weiter bitte", typ="user"),
            line("2026-11-01T12:00:00Z", "ok"),
        ])
        self.assertEqual(len(g), 1)
        self.assertEqual(g[0]["minutes"], 119)
        self.assertTrue(g[0]["limit"])
        self.assertTrue(g[0]["start"].startswith("2026-11-01T10:01:00"))

    def test_gap_min(self):
        lines = [line("2026-11-01T10:00:00Z"), line("2026-11-01T10:10:00Z")]
        self.assertEqual(self.gaps(lines), [])
        self.assertEqual(len(self.gaps(lines, gap_min=5)), 1)

    def test_gaps_cli(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_projects(tmp, [], [line("2026-11-01T10:00:00Z", "limit resets 12:00"),
                                    line("2026-11-01T11:00:00Z")])
            r = run("--root", tmp, "--gaps")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("LIMIT", r.stdout)
            self.assertIn("60", r.stdout)
            r = run("--root", tmp, "--gaps", "--gap-min", "90")
            self.assertNotIn("LIMIT", r.stdout)


if __name__ == "__main__":
    unittest.main()
