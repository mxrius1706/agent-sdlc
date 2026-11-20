"""Abnahmetest r1: context-usage.py --pack (Nachladen und Ueberversorgung).

Angenommener Vertrag (Block b3):
  reload_report(manifest, rows) -> dict
    manifest: dict mit Schluessel "included" (Liste von Abschnitt-IDs)
    rows:     Zeilen aus aggregate(sections, scans) (Subagent-Scans)
    Rueckgabe: {"reloaded": [IDs], "unused_in_pack": [IDs], "quote": str}
      reloaded       = Abschnitte mit voller "gelesen"-Ladung im Subagent, nicht in included
      unused_in_pack = Abschnitte in included, im Subagent nur mit Stufe C oder gar nicht geladen
      quote          = reloaded / alle vom Subagent gelesenen Abschnitte, zwei Nachkommastellen,
                       "-" wenn kein Abschnitt gelesen wurde
Listen werden sortiert verglichen (Reihenfolge nicht festgelegt).
"""
import importlib.util
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "context-usage.py")


def load():
    spec = importlib.util.spec_from_file_location("context_usage", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def entry(gelesen=0, ident_later=False):
    ch = {c: {"full": 0, "partial": 0} for c in ("gelesen", "injiziert", "kopiert")}
    ch["gelesen"]["full"] = gelesen
    ch["ident_later"] = ident_later
    return ch


def sec(sid):
    return {"id": sid, "alias": None, "chars": 100, "heading": sid, "lines": set()}


def build(mod, ids, sub_scan):
    return mod.aggregate([sec(i) for i in ids], [("sub", sub_scan)])


A, B, C, D = "docs/a.md#A", "docs/b.md#B", "docs/c.md#C", "docs/d.md#D"


class ReloadReportTest(unittest.TestCase):
    def test_reload_and_unused(self):
        mod = load()
        # A: im Paket, gelesen, Stufe C. B: im Paket, nie geladen.
        # C: nicht im Paket, gelesen, Stufe B. D: im Paket, gelesen, Stufe B.
        scan = {A: entry(1), C: entry(1, True), D: entry(1, True)}
        rows = build(mod, [A, B, C, D], scan)
        rep = mod.reload_report({"included": [A, B, D]}, rows)
        self.assertEqual(sorted(rep["reloaded"]), [C])
        self.assertEqual(sorted(rep["unused_in_pack"]), [A, B])
        self.assertEqual(rep["quote"], "0.33")

    def test_all_in_pack_has_zero_quote(self):
        mod = load()
        rows = build(mod, [A, D], {A: entry(1, True), D: entry(2, True)})
        rep = mod.reload_report({"included": [A, D]}, rows)
        self.assertEqual(rep["reloaded"], [])
        self.assertEqual(rep["unused_in_pack"], [])
        self.assertEqual(rep["quote"], "0.00")

    def test_no_subagent_reads_gives_dash(self):
        mod = load()
        rows = build(mod, [A, B], {})
        rep = mod.reload_report({"included": [A]}, rows)
        self.assertEqual(rep["reloaded"], [])
        self.assertEqual(rep["quote"], "-")
        self.assertEqual(sorted(rep["unused_in_pack"]), [A])


if __name__ == "__main__":
    unittest.main()
