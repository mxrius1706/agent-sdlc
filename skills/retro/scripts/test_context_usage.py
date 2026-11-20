"""Tests fuer context-usage.py (synthetische Daten, nur Standardbibliothek)."""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "context-usage.py")


def load():
    spec = importlib.util.spec_from_file_location("context_usage", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


cu = load()


def lines(prefix, n):
    """n verschiedene Zeilen mit mindestens 25 Zeichen."""
    return "\n".join(f"{prefix} Zeile Nummer {i} mit genug Text" for i in range(n))


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


class ChunkMarkdownTest(unittest.TestCase):
    def test_heading_path(self):
        text = "# Titel\n" + lines("a", 3) + "\n## Unter\n" + lines("b", 3) + "\n"
        ids = [s["id"] for s in cu.chunk_markdown("docs/a.md", text)]
        self.assertEqual(ids, ["docs/a.md#Titel", "docs/a.md#Titel > Unter"])

    def test_sibling_resets_path(self):
        text = "# T\n## A\n" + lines("a", 3) + "\n## B\n" + lines("b", 3) + "\n"
        ids = [s["id"] for s in cu.chunk_markdown("x.md", text)]
        self.assertEqual(ids, ["x.md#T > A", "x.md#T > B"])

    def test_duplicate_gets_suffix(self):
        text = "# T\n" + lines("a", 3) + "\n# T\n" + lines("b", 3) + "\n"
        ids = [s["id"] for s in cu.chunk_markdown("x.md", text)]
        self.assertEqual(ids, ["x.md#T", "x.md#T~2"])

    def test_requirement_alias(self):
        text = "## R12 Sitzungen laden\n" + lines("a", 3) + "\n## Ohne Nummer\n" + lines("b", 3)
        secs = cu.chunk_markdown("x.md", text)
        self.assertEqual(secs[0]["alias"], "x.md#R12")
        self.assertEqual(secs[1]["alias"], None)

    def test_short_sections_dropped(self):
        text = "# Kurz\nzu kurz\nauch kurz\n# Lang\n" + lines("a", 3) + "\n"
        ids = [s["id"] for s in cu.chunk_markdown("x.md", text)]
        self.assertEqual(ids, ["x.md#Lang"])

    def test_duplicate_lines_count_once(self):
        text = "# T\n" + ("immer dieselbe lange Zeile hier\n" * 5)
        self.assertEqual(cu.chunk_markdown("x.md", text), [])

    def test_code_fence_hash_is_no_heading(self):
        text = "# T\n```\n# kein Titel hier drin im Codeblock\n```\n" + lines("a", 3) + "\n"
        ids = [s["id"] for s in cu.chunk_markdown("x.md", text)]
        self.assertEqual(ids, ["x.md#T"])


class LoadDocsTest(unittest.TestCase):
    def test_default_docs(self):
        with tempfile.TemporaryDirectory() as tmp:
            proj = os.path.join(tmp, "projekt-a")
            vault = os.path.join(tmp, "vault")
            os.makedirs(os.path.join(vault, ".obsidian"))
            write(os.path.join(vault, "Notiz.md"), "# N\n" + lines("n", 3))
            write(os.path.join(vault, "Sub", "Roadmap.md"), "# R\n" + lines("r", 3))
            write(os.path.join(proj, "CLAUDE.md"), "# C\n" + lines("c", 3))
            write(os.path.join(proj, ".claude", "rules", "r1.md"), "# R1\n" + lines("x", 3))
            write(os.path.join(proj, ".claude", "roadmap-path"), os.path.join(vault, "Sub", "Roadmap.md") + "\n")
            got = sorted(n for n, _ in cu.load_docs(proj))
            self.assertEqual(got, sorted(["CLAUDE.md", ".claude/rules/r1.md",
                                          "vault/Notiz.md", "vault/Sub/Roadmap.md"]))

    def test_explicit_docs(self):
        with tempfile.TemporaryDirectory() as tmp:
            write(os.path.join(tmp, "a.md"), "# A\n")
            write(os.path.join(tmp, "d", "b.md"), "# B\n")
            got = sorted(n for n, _ in cu.load_docs(tmp, [os.path.join(tmp, "a.md"), os.path.join(tmp, "d")]))
            self.assertEqual(got, ["a.md", "d/b.md"])


_n = [0]


def rec(o):
    _n[0] += 1
    o.setdefault("uuid", f"u{_n[0]}")
    o.setdefault("timestamp", "2026-11-10T10:00:00Z")
    return o


def rec_result(text):
    return rec({"type": "user", "message": {"role": "user", "content": [
        {"type": "tool_result", "tool_use_id": "t", "content": text}]}})


def rec_attach(text):
    return rec({"type": "attachment", "attachment": {"type": "nested_memory", "content": text}})


def rec_tool(name, inp):
    return rec({"type": "assistant", "message": {"id": f"m{_n[0]}", "role": "assistant", "content": [
        {"type": "tool_use", "id": "t", "name": name, "input": inp}]}})


def rec_usage(inp, cw, cr):
    return rec({"type": "assistant", "message": {"id": f"m{_n[0]}", "role": "assistant", "content": [],
                "usage": {"input_tokens": inp, "cache_creation_input_tokens": cw,
                          "cache_read_input_tokens": cr, "output_tokens": 5}}})


def write_jsonl(path, records):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        for r in records:
            fh.write(json.dumps(r) + "\n")


SEC_LINES = [f"Abschnitt Zeile Nummer {i} mit genug Text" for i in range(5)]
SEC_TEXT = "# Doku\n" + "\n".join(SEC_LINES) + "\nBezeichner SPEZIAL_KENNUNG_77 steht hier drin\n"


def one_section():
    return cu.chunk_markdown("docs/a.md", SEC_TEXT)


class ScanTranscriptTest(unittest.TestCase):
    def scan(self, records, sections=None):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "s.jsonl")
            write_jsonl(path, records)
            return cu.scan_transcript(path, sections or one_section())

    SID = "docs/a.md#Doku"

    def test_gelesen(self):
        r = self.scan([rec_result("\n".join(SEC_LINES))])
        self.assertEqual(r[self.SID]["gelesen"]["full"], 1)
        self.assertEqual(r[self.SID]["injiziert"]["full"], 0)

    def test_gelesen_content_list_and_line_numbers(self):
        numbered = "\n".join(f"   {i + 1}\u2192{ln}" for i, ln in enumerate(SEC_LINES))
        rr = rec_result([{"type": "text", "text": numbered}])
        r = self.scan([rr])
        self.assertEqual(r[self.SID]["gelesen"]["full"], 1)

    def test_injiziert(self):
        r = self.scan([rec_attach("\n".join(SEC_LINES))])
        self.assertEqual(r[self.SID]["injiziert"]["full"], 1)
        self.assertEqual(r[self.SID]["gelesen"]["full"], 0)

    def test_kopiert_agent_and_sendmessage(self):
        r = self.scan([rec_tool("Agent", {"prompt": "\n".join(SEC_LINES)}),
                       rec_tool("SendMessage", {"message": "\n".join(SEC_LINES)})])
        self.assertEqual(r[self.SID]["kopiert"]["full"], 2)

    def test_other_tool_input_is_no_load(self):
        r = self.scan([rec_tool("Bash", {"command": "\n".join(SEC_LINES)})])
        self.assertEqual(r, {})

    def test_partial_and_thresholds(self):
        body = SEC_LINES + ["Bezeichner SPEZIAL_KENNUNG_77 steht hier drin"]  # 6 Zeilen
        # 2 von 6 = 33 %: Teil; 1 von 6 = 17 %: nichts; 5 von 6 = 83 %: voll
        r = self.scan([rec_result("\n".join(body[:2]))])
        self.assertEqual(r[self.SID]["gelesen"], {"full": 0, "partial": 1})
        self.assertEqual(self.scan([rec_result(body[0])]), {})
        r = self.scan([rec_result("\n".join(body[:5]))])
        self.assertEqual(r[self.SID]["gelesen"], {"full": 1, "partial": 0})

    def test_same_line_ten_times_changes_nothing(self):
        one = self.scan([rec_result(SEC_LINES[0])])
        ten = self.scan([rec_result("\n".join([SEC_LINES[0]] * 10))])
        self.assertEqual(one, ten)
        self.assertEqual(ten, {})
        # drei verschiedene Zeilen, je zehnmal: 3 von 6 bleibt Teilladung, wird nicht voll
        r = self.scan([rec_result("\n".join(SEC_LINES[:3] * 10))])
        self.assertEqual(r[self.SID]["gelesen"], {"full": 0, "partial": 1})

    def test_same_record_ten_times_counts_once(self):
        r1 = rec_result("\n".join(SEC_LINES))
        r = self.scan([r1] * 10)
        self.assertEqual(r[self.SID]["gelesen"]["full"], 1)

    def test_short_lines_ignored(self):
        self.assertEqual(self.scan([rec_result("kurz\nauch kurz\n---")]), {})

    def test_ident_later(self):
        r = self.scan([rec_result("\n".join(SEC_LINES)),
                       rec_tool("Bash", {"command": "grep SPEZIAL_KENNUNG_77 src"})])
        self.assertTrue(r[self.SID]["ident_later"])

    def test_ident_before_load_does_not_count(self):
        r = self.scan([rec_tool("Bash", {"command": "grep SPEZIAL_KENNUNG_77 src"}),
                       rec_result("\n".join(SEC_LINES))])
        self.assertFalse(r[self.SID]["ident_later"])

    def test_ident_in_two_sections_is_not_unique(self):
        other = cu.chunk_markdown("docs/b.md", SEC_TEXT)
        secs = one_section() + other
        r = self.scan([rec_result("\n".join(SEC_LINES)),
                       rec_tool("Bash", {"command": "grep SPEZIAL_KENNUNG_77 src"})], secs)
        self.assertFalse(r[self.SID]["ident_later"])


class EvidenceTierTest(unittest.TestCase):
    def test_b_on_partial(self):
        self.assertEqual(cu.evidence_tier(1, False), "B")

    def test_b_on_later_ident(self):
        self.assertEqual(cu.evidence_tier(0, True), "B")

    def test_c_otherwise(self):
        self.assertEqual(cu.evidence_tier(0, False), "C")


def scan_entry(channel, full=0, partial=0, ident=False):
    e = {c: {"full": 0, "partial": 0} for c in ("gelesen", "injiziert", "kopiert")}
    e[channel] = {"full": full, "partial": partial}
    e["ident_later"] = ident
    return e


class AggregateTest(unittest.TestCase):
    def test_sums_and_ballast(self):
        secs = one_section()
        sid = secs[0]["id"]
        rows = cu.aggregate(secs, [{sid: scan_entry("gelesen", full=2)},
                                   {sid: scan_entry("injiziert", full=1)}])
        row = rows[0]
        self.assertEqual((row["id"], row["loads"], row["partial"]), (sid, 3, 0))
        self.assertEqual(row["channels"], {"gelesen": 2, "injiziert": 1, "kopiert": 0})
        self.assertEqual(row["tier"], "C")
        self.assertEqual(row["ballast"], secs[0]["chars"] * 2)  # injiziert zaehlt nicht

    def test_injected_split_by_recipient(self):
        secs = one_section()
        sid = secs[0]["id"]
        rows = cu.aggregate(secs, [("main", {sid: scan_entry("injiziert", full=1)}),
                                   ("general-purpose", {sid: scan_entry("injiziert", full=1)}),
                                   ("web-fetch", {sid: scan_entry("injiziert", full=1)})])
        row = rows[0]
        self.assertEqual((row["inj_main"], row["inj_sub"]), (1, 2))
        self.assertEqual(row["ballast"], 0)
        self.assertEqual(row["sub_chars"], secs[0]["chars"] * 2)  # Zeichen, die Subagenten tragen

    def test_plain_scans_still_accepted(self):
        secs = one_section()
        sid = secs[0]["id"]
        rows = cu.aggregate(secs, [{sid: scan_entry("injiziert", full=1)}])
        self.assertEqual((rows[0]["inj_main"], rows[0]["inj_sub"]), (0, 1))

    def test_tier_b_has_no_ballast(self):
        secs = one_section()
        sid = secs[0]["id"]
        rows = cu.aggregate(secs, [{sid: scan_entry("gelesen", full=1, ident=True)}])
        self.assertEqual((rows[0]["tier"], rows[0]["ballast"]), ("B", 0))

    def test_partial_makes_tier_b(self):
        secs = one_section()
        sid = secs[0]["id"]
        rows = cu.aggregate(secs, [{sid: scan_entry("kopiert", partial=1)}])
        self.assertEqual((rows[0]["tier"], rows[0]["partial"], rows[0]["loads"]), ("B", 1, 0))

    def test_unloaded_sections_listed_last_without_tier(self):
        secs = one_section() + cu.chunk_markdown("docs/b.md", SEC_TEXT)
        rows = cu.aggregate(secs, [{secs[0]["id"]: scan_entry("gelesen", full=1)}])
        self.assertEqual([r["id"] for r in rows], [secs[0]["id"], secs[1]["id"]])
        self.assertIsNone(rows[1]["tier"])


class StartLoadTest(unittest.TestCase):
    def test_attachments_and_tokens_of_first_call(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "a.jsonl")
            write_jsonl(path, [rec_attach("x"), rec_attach("y"), rec_usage(10, 200, 30),
                               rec_attach("spaeter"), rec_usage(1, 1, 1)])
            self.assertEqual(cu.start_load(path), {"attachments": 2, "tokens": 240})

    def test_by_agent_type(self):
        rows = cu.startlast_by_type([("worker", {"attachments": 2, "tokens": 100}),
                                     ("worker", {"attachments": 4, "tokens": 300}),
                                     ("prueffer", {"attachments": 0, "tokens": 50})])
        self.assertEqual(rows["worker"], {"n": 2, "attachments": 3.0, "tokens": 200.0})
        self.assertEqual(rows["prueffer"]["n"], 1)


class CliTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        t = self.tmp.name
        self.proj = os.path.join(t, "projekt-a")
        write(os.path.join(self.proj, "CLAUDE.md"), SEC_TEXT)
        self.root = os.path.join(t, "acc", "projects")
        folder = os.path.join(self.root, "-work-projekt-a")
        write_jsonl(os.path.join(folder, "s1.jsonl"), [
            rec_result("\n".join(SEC_LINES)),
            rec_tool("Agent", {"prompt": "\n".join(SEC_LINES[:2])}),
            rec_tool("Bash", {"command": "grep SPEZIAL_KENNUNG_77"})])
        sub = os.path.join(folder, "s1", "subagents")
        write_jsonl(os.path.join(sub, "agent-1.jsonl"), [rec_attach("z"), rec_usage(5, 50, 5)])
        write(os.path.join(sub, "agent-1.meta.json"), json.dumps({"agentType": "worker", "description": "d"}))
        old = [rec_result("\n".join(SEC_LINES))]
        for r in old:
            r["timestamp"] = "2026-01-01T00:00:00Z"
        write_jsonl(os.path.join(folder, "s0.jsonl"), old)
        self.out = os.path.join(t, "out", "cu.json")

    def tearDown(self):
        self.tmp.cleanup()

    def run_cli(self, *extra):
        cmd = [sys.executable, "-I", SCRIPT, "--root", self.root, "--project", "projekt-a",
               "--project-dir", self.proj, "--json-out", self.out] + list(extra)
        return subprocess.run(cmd, capture_output=True, text=True, cwd=self.tmp.name)

    def test_end_to_end(self):
        p = self.run_cli()
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("CLAUDE.md#Doku", p.stdout)
        with open(self.out, encoding="utf-8") as fh:
            data = json.load(fh)
        self.assertEqual(sorted(data), ["meta", "sections", "startlast"])
        row = data["sections"][0]
        for k in ("id", "loads", "partial", "channels", "chars", "tier", "ballast"):
            self.assertIn(k, row)
        self.assertEqual(row["loads"], 2)  # s0 und s1 jeweils einmal gelesen
        self.assertEqual(row["partial"], 1)  # Agent-Prompt mit 2 von 6 Zeilen
        self.assertEqual(row["tier"], "B")
        self.assertEqual(data["startlast"]["worker"]["tokens"], 60.0)
        self.assertEqual(data["meta"]["sessions"], 2)

    def test_since_filters_old_session(self):
        p = self.run_cli("--since", "2026-06-01")
        self.assertEqual(p.returncode, 0, p.stderr)
        with open(self.out, encoding="utf-8") as fh:
            data = json.load(fh)
        self.assertEqual(data["sections"][0]["loads"], 1)
        self.assertEqual(data["meta"]["sessions"], 1)

    def test_symlinked_root_counted_once(self):
        link = os.path.join(self.tmp.name, "acc2")
        os.symlink(os.path.join(self.tmp.name, "acc"), link)
        p = self.run_cli("--root", os.path.join(link, "projects"))
        self.assertEqual(p.returncode, 0, p.stderr)
        with open(self.out, encoding="utf-8") as fh:
            data = json.load(fh)
        self.assertEqual(data["sections"][0]["loads"], 2)

    def test_top_limits_console_rows(self):
        write(os.path.join(self.proj, "CLAUDE.md"), SEC_TEXT + "\n## Zwei\n" + lines("z", 4) + "\n")
        p = self.run_cli("--top", "1")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertNotIn("Zwei", p.stdout)

    def test_docs_option(self):
        other = os.path.join(self.tmp.name, "extra.md")
        write(other, "# Extra\n" + lines("e", 4) + "\n")
        p = self.run_cli("--docs", other)
        self.assertEqual(p.returncode, 0, p.stderr)
        with open(self.out, encoding="utf-8") as fh:
            data = json.load(fh)
        self.assertEqual([r["id"] for r in data["sections"]], [os.path.relpath(other, self.proj) + "#Extra"])

    def test_help(self):
        p = subprocess.run([sys.executable, "-I", SCRIPT, "--help"], capture_output=True, text=True)
        self.assertEqual(p.returncode, 0)


class PackCliTest(unittest.TestCase):
    """--pack: zweiter Bericht nur aus den Subagenten-Transkripten."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        t = self.tmp.name
        self.proj = os.path.join(t, "projekt-a")
        write(os.path.join(self.proj, "CLAUDE.md"), SEC_TEXT)
        self.root = os.path.join(t, "acc", "projects")
        folder = os.path.join(self.root, "-work-projekt-a")
        # Hauptsitzung liest den Abschnitt, der Subagent ebenfalls
        write_jsonl(os.path.join(folder, "s1.jsonl"), [rec_result("\n".join(SEC_LINES))])
        sub = os.path.join(folder, "s1", "subagents")
        write_jsonl(os.path.join(sub, "agent-1.jsonl"), [rec_result("\n".join(SEC_LINES))])
        write(os.path.join(sub, "agent-1.meta.json"), json.dumps({"agentType": "worker"}))
        self.out = os.path.join(t, "out", "cu.json")

    def manifest(self, included):
        path = os.path.join(self.tmp.name, "m.json")
        write(path, json.dumps({"block": "b1", "included": included}))
        return path

    def run_cli(self, *extra):
        cmd = [sys.executable, "-I", SCRIPT, "--root", self.root, "--project", "projekt-a",
               "--project-dir", self.proj, "--json-out", self.out] + list(extra)
        return subprocess.run(cmd, capture_output=True, text=True, cwd=self.tmp.name)

    def test_reload_when_not_in_pack(self):
        p = self.run_cli("--pack", self.manifest([]))
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("Nachladen und Ueberversorgung", p.stdout)
        self.assertIn("Nachlade-Quote: 1.00", p.stdout)
        with open(self.out, encoding="utf-8") as fh:
            data = json.load(fh)
        self.assertEqual(data["pack"]["reloaded"], ["CLAUDE.md#Doku"])
        self.assertEqual(data["pack"]["quote"], "1.00")

    def test_unused_when_in_pack(self):
        p = self.run_cli("--pack", self.manifest(["CLAUDE.md#Doku"]))
        self.assertEqual(p.returncode, 0, p.stderr)
        with open(self.out, encoding="utf-8") as fh:
            data = json.load(fh)
        self.assertEqual(data["pack"]["reloaded"], [])
        self.assertEqual(data["pack"]["unused_in_pack"], ["CLAUDE.md#Doku"])

    def test_without_pack_no_key(self):
        p = self.run_cli()
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertNotIn("Nachladen", p.stdout)
        with open(self.out, encoding="utf-8") as fh:
            self.assertNotIn("pack", json.load(fh))

    def test_bad_manifest_exit_2(self):
        p = self.run_cli("--pack", os.path.join(self.tmp.name, "fehlt.json"))
        self.assertEqual(p.returncode, 2)
        self.assertNotIn("Traceback", p.stderr)


if __name__ == "__main__":
    unittest.main()
