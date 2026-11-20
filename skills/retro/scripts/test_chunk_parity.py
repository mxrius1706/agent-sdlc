"""Abnahmetest r2: chunk_markdown in context-usage.py und context-pack.py ist gleich.

Vertrag: beide Skripte haben chunk_markdown(relpath, text) und liefern fuer denselben
Text dieselben Abschnitt-IDs (und Aliase). Ohne context-pack.py (Block b1 noch nicht
gemergt) wird der Test uebersprungen.
"""
import importlib.util
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
USAGE = os.path.join(HERE, "context-usage.py")
PACK = os.path.normpath(os.path.join(HERE, "..", "..", "execute-plan", "scripts", "context-pack.py"))


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def body(prefix, n=4):
    return "\n".join(f"{prefix} Zeile Nummer {i} mit genug Text" for i in range(n))


TEXTS = {
    "einfach": "# Titel\n" + body("a") + "\n## Unter\n" + body("b") + "\n",
    "doppelt": "# Titel\n" + body("a") + "\n# Titel\n" + body("b") + "\n",
    "sprung": "# Titel\n" + body("a") + "\n### Tief\n" + body("b") + "\n",
    "zaehler": "## 1.2 Regel\n" + body("a") + "\n## R-3 Regel\n" + body("b") + "\n",
    "zaun": "# Titel\n```\n# kein Titel\n```\n" + body("a") + "\n",
    "kurz": "# Titel\nkurz\n## Lang\n" + body("c") + "\n",
    "vorspann": body("v") + "\n# Titel\n" + body("a") + "\n",
}


class ChunkParityTest(unittest.TestCase):
    def test_same_ids_for_same_text(self):
        if not os.path.exists(PACK):
            self.skipTest("context-pack.py fehlt noch (Block b1 nicht gemergt)")
        usage = load("context_usage", USAGE)
        pack = load("context_pack", PACK)
        for name, text in TEXTS.items():
            with self.subTest(text=name):
                a = [(s["id"], s.get("alias")) for s in usage.chunk_markdown("docs/x.md", text)]
                b = [(s["id"], s.get("alias")) for s in pack.chunk_markdown("docs/x.md", text)]
                self.assertTrue(a, "Testtext ergibt keine Abschnitte")
                self.assertEqual(a, b)


if __name__ == "__main__":
    unittest.main()
