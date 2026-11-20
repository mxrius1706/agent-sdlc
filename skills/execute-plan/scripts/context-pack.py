#!/usr/bin/env python3
"""Baut das Kontextpaket fuer einen Block eines Plans. Nur Standardbibliothek.

    python3 -I context-pack.py <plan.md> --block <id> --root <dir> [--specs <datei-oder-ordner> ...]
                               [--global-claude <datei>] [--trailer <zeile>] [--out <datei>]
                               [--max-chars N]

Das Buendel geht nach stdout, mit --out in die Datei plus <out>.manifest.json.
Exit 2: Plan fehlt oder Block unbekannt (ein Satz auf stderr). Exit 3: Buendel groesser als
--max-chars (ein Satz auf stderr, keine Ausgabedatei). Gleiche Eingabe gibt gleiche Bytes.
Dieses Skript importiert kein anderes Skript; chunk_markdown ist eine Kopie aus context-usage.py.
"""
import re

MIN_LINE = 25  # Zeichen: kuerzere Zeilen zaehlen nicht (Trenner, Zufallstreffer)
MIN_LINES = 3  # Abschnitte mit weniger verschiedenen Zeilen entfallen

HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
REQ_NO = re.compile(r"^([A-Za-z]{1,4}-?\d+[a-z]?|\d+(?:\.\d+)+)(?=$|[\s:.)\]-])")
REQ_ID = re.compile(r"\b[A-Z]{2,6}-\d+[a-z]?\b")


def split_raw(text):
    """Markdown -> Liste (Ueberschriftenpfad, Ueberschrift, Ebene, Zeilen). Der Vorspann hat Ebene 0."""
    raw = []
    stack = []
    cur = ("", "", 0, [])
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
            cur = (" > ".join(t for t in stack if t), title, level, [line])
        else:
            cur[3].append(line)
    raw.append(cur)
    return raw


def chunk_markdown(relpath, text):
    """Markdown -> Liste {id, alias, heading, chars, lines, level, text}. Wie in context-usage.py.

    Die Schluessel level und text sind Zusatz; id, alias, heading, chars und lines sind gleich.
    """
    out = []
    seen = {}
    for path, title, level, lines in split_raw(text):
        body = lines[1:] if level else lines  # die Ueberschriftenzeile gehoert nicht zum Inhalt
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
                    "lines": distinct, "level": level, "text": "\n".join(lines) + "\n"})
    return out


# ---- Plan lesen ----

def plan_sections(text):
    """Plan -> {kleingeschriebener Abschnittsname: Zeilen}."""
    out = {}
    name = None
    for line in text.splitlines():
        m = re.match(r"^##\s+(.*?)\s*$", line)
        if m:
            name = m.group(1).lower()
            out.setdefault(name, [])
        elif name is not None:
            out[name].append(line)
    return out


def split_row(line):
    cells = line.strip().strip("|").split("|")
    return [c.strip() for c in cells]


def read_table(lines):
    """Erste Tabelle in Zeilen -> Liste von Dicts (Spaltenname kleingeschrieben). Leer, wenn keine."""
    rows = [ln for ln in lines if ln.strip().startswith("|")]
    if len(rows) < 2:
        return []
    head = [h.lower() for h in split_row(rows[0])]
    out = []
    for ln in rows[1:]:
        cells = split_row(ln)
        if all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c) and any(cells):
            continue
        out.append({h: (cells[i] if i < len(cells) else "") for i, h in enumerate(head)})
    return out


def column(row, prefix):
    for key, val in row.items():
        if key.startswith(prefix):
            return val
    return ""


def split_list(cell):
    return [p.strip().strip("`").strip() for p in cell.split(",") if p.strip().strip("`").strip()]


def read_plan(plan_path):
    with open(plan_path, encoding="utf-8") as fh:
        return plan_sections(fh.read())


def block_scope(plan_path, block_id):
    """Plan, Block -> (Dateien, Anforderungskennungen, Aufgabenzeilen). Unbekannter Block: ValueError."""
    secs = read_plan(plan_path)
    blocks = read_table(secs.get("blocks", []))
    tasks = read_table(secs.get("tasks", []))
    if not blocks:
        raise ValueError("Der Plan hat keine Blocks-Tabelle.")
    row = next((b for b in blocks if column(b, "block") == block_id), None)
    if row is None:
        raise ValueError(f"Block {block_id} steht nicht im Plan.")
    files = split_list(column(row, "files"))
    rows = [t for t in tasks if column(t, "block") == block_id]
    reqs = []
    for t in rows:
        for rid in REQ_ID.findall(column(t, "requirements")):
            if rid not in reqs:
                reqs.append(rid)
    return files, reqs, rows
