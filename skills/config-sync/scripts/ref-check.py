#!/usr/bin/env python3
"""Prueft, ob Pfade in Inline-Code (einzelne Backticks) einer Markdown-Datei existieren.

    python3 -I ref-check.py <datei.md> ... [--root <ordner>]

Ein Token gilt als Pfad, wenn es "/" enthaelt oder auf eine bekannte Endung endet, nicht mit
http, /, ~, $ oder - beginnt und keines von < > * ? { } | ( ) Leerzeichen enthaelt. Aufgeloest
wird gegen --root (Standard: Ordner der Datei) und gegen den Ordner der Datei.
Ausgabe je fehlendem Pfad: MISSING <datei>:<zeile> <token>. Exit 1 bei Fehlenden, 2 bei
unlesbarer Datei, sonst 0.
"""
import argparse
import os
import re
import sys

EXTS = (".md", ".py", ".json", ".sh", ".ts", ".js", ".yml", ".yaml", ".toml")
BAD_START = ("http", "/", "~", "$", "-")
BAD_CHARS = set("<>*?{}|() \t")
TOKEN = re.compile(r"(?<!`)`([^`\n]+)`(?!`)")


def looks_like_path(tok):
    """Sieht das Token wie ein relativer Pfad aus?"""
    if tok.startswith(BAD_START) or BAD_CHARS & set(tok):
        return False
    return "/" in tok or tok.endswith(EXTS)


def check_file(path, root):
    """Datei -> Liste (Zeile, Token) fuer Pfade, die weder gegen root noch gegen den Dateiordner existieren."""
    with open(path, encoding="utf-8", errors="replace") as fh:
        text = fh.read()
    here = os.path.dirname(os.path.abspath(path))
    bases = [os.path.abspath(root) if root else here]
    if here not in bases:
        bases.append(here)
    missing = []
    fence = False
    for no, line in enumerate(text.splitlines(), 1):
        if line.lstrip().startswith(("```", "~~~")):
            fence = not fence
            continue
        if fence:
            continue
        for tok in TOKEN.findall(line):
            if looks_like_path(tok) and not any(os.path.exists(os.path.join(b, tok)) for b in bases):
                missing.append((no, tok))
    return missing


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+", help="Markdown-Dateien")
    ap.add_argument("--root", help="Ordner, gegen den Pfade aufgeloest werden (Standard: Ordner der Datei)")
    a = ap.parse_args(argv)
    found = False
    for f in a.files:
        try:
            missing = check_file(f, a.root)
        except OSError:
            print(f"Die Datei {f} ist nicht lesbar.", file=sys.stderr)
            return 2
        for no, tok in missing:
            print(f"MISSING {f}:{no} {tok}")
            found = True
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
