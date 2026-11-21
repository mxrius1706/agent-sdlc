#!/usr/bin/env python3
"""Prueft, ob Pfade in Inline-Code (einzelne Backticks) einer Markdown-Datei existieren.

    python3 -I ref-check.py <datei.md> ... [--root <ordner>]

Ein Token gilt als Pfad, wenn es "/" enthaelt (ein Dateiname ohne Ordner ist keiner), nicht mit
http, /, ~, $, -, + oder @ beginnt und keines von < > * ? { } | ( ) Leerzeichen enthaelt. Keine
Pfade sind ausserdem Wissensbasis-Pfade (specs/), Medientypen (application/json), Branch-Namen
(phase-3/..., refs/heads/...). Aufgeloest
wird gegen --root (Standard: Ordner der Datei) und gegen den Ordner der Datei.
Ausgabe je fehlendem Pfad: MISSING <datei>:<zeile> <token>. Zusaetzlich GATE-ORDER <datei>:<zeile>,
wenn eine Zeile `review-changes` und darauf (gleiche oder naechste Zeile) `thermo` nennt: das ist
eine Kopie der Gate-Reihenfolge, die nur im Ritual von plan-build stehen soll. Exit 1 bei
Meldungen, 2 bei unlesbarer Datei, sonst 0.
"""
import argparse
import os
import re
import sys

BAD_START = ("http", "/", "~", "$", "-", "+", "@", "specs/", "refs/")
MEDIA_TYPES = ("application/", "text/", "image/", "audio/", "video/", "multipart/", "font/")
BRANCH = re.compile(r"phase-\w+/")
BAD_CHARS = set("<>*?{}|() \t")
TOKEN = re.compile(r"(?<!`)`([^`\n]+)`(?!`)")


def looks_like_path(tok):
    """Sieht das Token wie ein relativer Pfad aus?"""
    if tok.startswith(BAD_START) or BAD_CHARS & set(tok):
        return False
    if tok.startswith(MEDIA_TYPES) or BRANCH.match(tok):
        return False
    return "/" in tok


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


ORDER_WORD = re.compile(r"\b(then|followed|before|after|dann|danach|vor|gefolgt)\b|->|\u2192")
ITEM = re.compile(r"\s*\d+[.)]\s")


def gate_order_copies(path):
    """Datei -> Zeilennummern mit einer Kopie der Gate-Reihenfolge.

    Gemeldet wird nur, wenn zwischen `review-changes` und `thermo` ein Reihenfolgewort steht, oder wenn beide in
    aufeinanderfolgenden Punkten einer nummerierten Liste stehen und ein Punkt das Wort Gate nennt.
    Aufzaehlungen mit and/und/Komma und Tabellenzeilen untereinander melden nichts."""
    with open(path, encoding="utf-8", errors="replace") as fh:
        lines = fh.read().splitlines()
    hits = []
    fence = False
    prev = None  # (Zeile, Text) des vorigen Listenpunkts mit review-changes
    for no, line in enumerate(lines, 1):
        if line.lstrip().startswith(("```", "~~~")):
            fence = not fence
            continue
        if fence:
            continue
        low = line.lower()
        first = low.find("review-changes")
        if first >= 0 and ORDER_WORD.search(low[first:low.find("thermo", first)] if "thermo" in low[first:] else ""):
            hits.append(no)
        if ITEM.match(line):
            if prev is not None and "thermo" in low and "gate" in (prev[1] + low):
                hits.append(prev[0])
            prev = (no, low) if first >= 0 else None
        elif line.strip():
            prev = None
    return hits


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
        for no in gate_order_copies(f):
            print(f"GATE-ORDER {f}:{no} Kopie der Gate-Reihenfolge, Verweis aufs Ritual in plan-build genuegt")
            found = True
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
