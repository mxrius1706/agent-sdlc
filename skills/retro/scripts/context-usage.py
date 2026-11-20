#!/usr/bin/env python3
"""Welche Abschnitte des Projektwissens werden in Sitzungen geladen, und ueber welchen Kanal.

Liest nur lokale Dateien (Projektdokumente, Transkripte unter ~/.claude*/projects).

    python3 -I context-usage.py --project agent-sdlc --since 2026-11-01 --top 20
    python3 -I context-usage.py --json-out .claude/context-usage.json

Abschnitts-ID: <relativer Pfad>#<Ueberschriftenpfad>, doppelte mit ~2. Beginnt eine
Ueberschrift mit einer Anforderungsnummer (z. B. R12), gilt <Pfad>#R12 als Alias.
"""
import glob
import os
import re

MIN_LINE = 25  # Zeichen: kuerzere Zeilen zaehlen nicht (Trenner, Zufallstreffer)
MIN_LINES = 3  # Abschnitte mit weniger verschiedenen Zeilen entfallen
SKIP_DIRS = {".git", "node_modules", ".worktrees", ".obsidian", "__pycache__", ".venv"}

HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
REQ_NO = re.compile(r"^([A-Za-z]{1,4}-?\d+[a-z]?|\d+(?:\.\d+)+)(?=$|[\s:.)\]-])")


def chunk_markdown(relpath, text):
    """Markdown -> Liste {id, alias, heading, chars, lines}. Lines = verschiedene Zeilen ab MIN_LINE."""
    raw = []  # (Ueberschriftenpfad, Ueberschrift, Zeilen)
    stack = []
    cur = ("", "", [])
    fence = False
    for line in text.splitlines():
        if line.lstrip().startswith("```") or line.lstrip().startswith("~~~"):
            fence = not fence
        m = None if fence else HEADING.match(line)
        if m:
            raw.append(cur)
            level, title = len(m.group(1)), m.group(2)
            stack = stack[:level - 1]
            while len(stack) < level - 1:
                stack.append("")
            stack.append(title)
            cur = (" > ".join(t for t in stack if t), title, [])
        else:
            cur[2].append(line)
    raw.append(cur)
    out = []
    seen = {}
    for path, title, body in raw:
        distinct = {ln.strip() for ln in body if len(ln.strip()) >= MIN_LINE}
        if len(distinct) < MIN_LINES:
            continue
        sid = f"{relpath}#{path}"
        seen[sid] = seen.get(sid, 0) + 1
        if seen[sid] > 1:
            sid += f"~{seen[sid]}"
        m = REQ_NO.match(title)
        out.append({"id": sid, "alias": f"{relpath}#{m.group(1)}" if m else None,
                    "heading": title, "chars": sum(len(b) + 1 for b in body),
                    "lines": distinct})
    return out


def read_text(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError:
        return None


def walk_md(root, name=None):
    """Alle .md-Dateien unter root (oder nur Dateien mit genau diesem Namen), ohne SKIP_DIRS."""
    found = []
    for base, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
        for f in sorted(files):
            if (name and f == name) or (not name and f.endswith(".md")):
                found.append(os.path.join(base, f))
    return found


def find_vault(project_dir):
    """Vault-Wurzel: .claude/roadmap-path nach oben bis zu einem Ordner mit .obsidian."""
    rp = read_text(os.path.join(project_dir, ".claude", "roadmap-path"))
    if not rp or not rp.strip():
        return None
    cur = os.path.expanduser(rp.strip())
    if not os.path.isabs(cur):
        cur = os.path.join(project_dir, cur)
    cur = os.path.dirname(os.path.realpath(cur)) if not os.path.isdir(cur) else os.path.realpath(cur)
    while True:
        if os.path.isdir(os.path.join(cur, ".obsidian")):
            return cur
        parent = os.path.dirname(cur)
        if parent == cur:
            return None
        cur = parent


def load_docs(project_dir, docs=None):
    """Liste (relativer Name, Text). Standard: CLAUDE.md, .claude/rules/*.md, Vault.

    Vault-Dateien heissen vault/<Pfad im Vault>. Mit docs (Dateien oder Ordner) nur diese.
    """
    project_dir = os.path.abspath(project_dir)
    files = []
    if docs:
        for d in docs:
            d = os.path.abspath(os.path.expanduser(d))
            files += walk_md(d) if os.path.isdir(d) else [d]
        names = [(os.path.relpath(f, project_dir), f) for f in files]
    else:
        names = [(os.path.relpath(f, project_dir), f) for f in walk_md(project_dir, "CLAUDE.md")]
        names += [(os.path.relpath(f, project_dir), f)
                  for f in sorted(glob.glob(os.path.join(project_dir, ".claude", "rules", "*.md")))]
        vault = find_vault(project_dir)
        if vault:
            names += [("vault/" + os.path.relpath(f, vault), f) for f in walk_md(vault)]
    out = []
    seen = set()
    for name, f in names:
        real = os.path.realpath(f)
        text = read_text(f)
        if text is None or real in seen:
            continue
        seen.add(real)
        out.append((name, text))
    return out
