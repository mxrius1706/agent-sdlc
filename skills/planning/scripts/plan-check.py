#!/usr/bin/env python3
"""Prueft, stuft und bemisst Plaene deterministisch. Nur Standardbibliothek.

    python3 -I plan-check.py lint  <plan.md> [--depth mini|standard|voll] [--specs <Pfad> ...]
                                   [--req-pattern <regex>] [--limits k=v,...]
    python3 -I plan-check.py stage <plan.md> [--depth ...] [--limits k=v,...]
                                   [--schema-paths <regex>] [--security-paths <regex>]
    python3 -I plan-check.py depth --areas N --spec-sources N --gate-points N --files N
                                   [--flag schema|exclusive|security|dependency|nopattern ...]
                                   [--limits k=v,...]

lint:  Zeilen "<Regel-ID> <Ort>: <Satz>", Exit 1 bei Verstoessen, sonst 0.
stage/depth: erste Zeile ein Wort (S|M|L bzw. mini|standard|voll), danach die Gruende.
Fehler in der Eingabe (Datei oder Tabelle fehlt, ungueltige Option): ein Satz auf stderr, Exit 2.

Plantabellen: Spaltennamen ohne Beachtung der Gross- und Kleinschreibung, beliebige Reihenfolge,
Zusatzspalten erlaubt. Pfade kommagetrennt, ein Verzeichnis gilt fuer alles darunter.
"""
import argparse
import os
import re
import sys

DEFAULT_REQ = r"\b(?:REQ|SEC|CON|GUD|PAT|AC)-\d+\b"
DEFAULT_SCHEMA = r"(^|/)(migrations?|schema|prisma)(/|\.|$)|\.sql$"
DEFAULT_SECURITY = r"(^|/)(auth|security|secrets?|crypto)(/|\.|$)"

# Schwellen (Startwerte), per --limits k=v ueberschreibbar
DEFAULT_LIMITS = {
    "areas": 1,           # mini: hoechstens so viele Bereiche
    "standard_areas": 3,  # standard: hoechstens so viele Bereiche
    "spec_sources": 1,
    "gate_points": 3,
    "files": 5,           # mini: hoechstens so viele Dateien
    "stage_s_files": 5,
    "stage_l_files": 25,
    "wave_blocks": 3,
    "block_tasks": 6,
}

DEPTHS = ("mini", "standard", "voll")
FLAGS = ("schema", "exclusive", "security", "dependency", "nopattern")

# Abschnittsname -> Aliase (kleingeschrieben)
SECTIONS = {
    "Context": ("context", "kontext"),
    "Goal": ("goal", "ziel"),
    "Out of scope": ("out of scope",),
    "Decisions": ("decisions", "entscheidungen"),
    "Critical files": ("critical files", "kritische dateien"),
    "Order": ("order", "reihenfolge"),
    "Blocks": ("blocks",),
    "Waves": ("waves",),
    "Tasks": ("tasks",),
    "Tests": ("tests",),
    "Verification": ("verification", "verifikation"),
}
REQUIRED_MINI = ("Context", "Goal", "Blocks", "Tasks", "Tests", "Verification", "Out of scope")
REQUIRED_MORE = ("Decisions", "Critical files", "Order", "Waves")

PLACEHOLDERS = {"none", "n/a", "na", "tbd", "tba", "todo", "keine", "nichts", "-", "..."}
REASON_COLUMNS = ("reason", "rationale", "why", "grund", "begruendung", "begründung")

HEADING = re.compile(r"^(#{1,4})\s+(.*?)\s*#*\s*$")
FENCE = re.compile(r"^\s*(```|~~~)")


class InputError(Exception):
    """Fehler in der Eingabe: ein Satz, Exit 2."""


# ---------------------------------------------------------------- Lesen

def read_text(path):
    """Datei als Text lesen, jeder Fehler wird ein Satz."""
    try:
        with open(path, encoding="utf-8") as fh:
            return fh.read()
    except FileNotFoundError:
        raise InputError(f"Datei nicht gefunden: {path}")
    except (OSError, UnicodeDecodeError):
        raise InputError(f"Datei nicht lesbar als Text: {path}")


def parse_limits(spec):
    """'k=v,k=v' -> Schwellen mit Startwerten. Unbekannter Name oder Nicht-Zahl ist ein Fehler."""
    limits = dict(DEFAULT_LIMITS)
    if not spec:
        return limits
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        name, _, value = part.partition("=")
        name = name.strip()
        if name not in limits:
            raise InputError(f"Unbekannte Schwelle in --limits: {name}")
        try:
            limits[name] = int(value.strip())
        except ValueError:
            raise InputError(f"Schwelle {name} braucht eine ganze Zahl")
    return limits


def compile_re(pattern, what):
    try:
        return re.compile(pattern)
    except re.error:
        raise InputError(f"Ungueltiger regulaerer Ausdruck fuer {what}")


def parse_sections(lines):
    """Ueberschriften # bis ####, Codebloecke ausgenommen -> Liste {level, title, body}."""
    heads = []
    fence = False
    for i, line in enumerate(lines):
        if FENCE.match(line):
            fence = not fence
            continue
        m = None if fence else HEADING.match(line)
        if m:
            heads.append((i, len(m.group(1)), m.group(2)))
    out = []
    for n, (i, level, title) in enumerate(heads):
        end = len(lines)
        for j, lv, _ in heads[n + 1:]:
            if lv <= level:
                end = j
                break
        out.append({"level": level, "title": title, "body": lines[i + 1:end]})
    return out


def find_section(sections, name):
    """Erster Abschnitt, dessen Ueberschrift den Namen (oder Alias) als ganzes Wort enthaelt."""
    for sec in sections:
        title = sec["title"].lower()
        for alias in SECTIONS[name]:
            if re.search(r"(?<!\w)" + re.escape(alias) + r"(?!\w)", title):
                return sec
    return None


def split_cells(line):
    """Tabellenzeile -> Zellen. Ein | in Backticks oder mit Backslash trennt nicht."""
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    cells, cur, tick = [], [], False
    i = 0
    while i < len(line):
        ch = line[i]
        if ch == "\\" and line[i + 1:i + 2] == "|":
            cur.append("|")
            i += 2
            continue
        if ch == "`":
            tick = not tick
        if ch == "|" and not tick:
            cells.append("".join(cur).strip())
            cur = []
        else:
            cur.append(ch)
        i += 1
    rest = "".join(cur).strip()
    if rest or not line.endswith("|"):
        cells.append(rest)
    return cells


def is_separator(line):
    s = line.strip()
    return "|" in s and "-" in s and set(s) <= set("|-: ")


def parse_tables(lines):
    """Alle Markdown-Tabellen (ausserhalb von Codebloecken) -> Liste {header, rows}."""
    tables = []
    fence = False
    i = 0
    while i < len(lines):
        line = lines[i]
        if FENCE.match(line):
            fence = not fence
        if not fence and line.strip().startswith("|") and i + 1 < len(lines) and is_separator(lines[i + 1]):
            header = [c.lower() for c in split_cells(line)]
            rows = []
            i += 2
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = split_cells(lines[i])
                cells += [""] * (len(header) - len(cells))
                rows.append(dict(zip(header, cells)))
                i += 1
            tables.append({"header": header, "rows": rows})
            continue
        i += 1
    return tables


def has_columns(header, exact, prefix=()):
    return all(c in header for c in exact) and all(any(h.startswith(p) for h in header) for p in prefix)


def find_blocks_table(tables):
    for t in tables:
        if has_columns(t["header"], ("block", "tasks", "files")):
            return t
    raise InputError("Blocks-Tabelle (Spalten Block, Tasks, Files) fehlt im Plan")


def find_tasks_table(tables):
    for t in tables:
        if has_columns(t["header"], ("id", "block", "task", "requirements"), ("test target",)):
            return t
    raise InputError("Tasks-Tabelle (Spalten Id, Block, Task, Test target, Requirements) fehlt im Plan")


def column(row, name):
    """Zelle nach Spaltenname, auch als Praefix (Test target (seam))."""
    if name in row:
        return row[name]
    for key, value in row.items():
        if key.startswith(name):
            return value
    return ""


def split_list(text):
    return [p.strip() for p in text.split(",") if p.strip()]


def norm_path(path):
    path = path.strip().strip("`")
    while path.startswith("./"):
        path = path[2:]
    return path.rstrip("/")


def overlaps(a, b):
    return a == b or a.startswith(b + "/") or b.startswith(a + "/")


def is_yes(text):
    return text.strip().strip("`").lower() in ("yes", "ja", "true")


def block_list(table):
    """Blocks-Tabelle -> Liste {id, tasks, files, wave, exclusive}."""
    out = []
    for row in table["rows"]:
        out.append({
            "id": column(row, "block"),
            "tasks": split_list(column(row, "tasks")),
            "files": [norm_path(p) for p in split_list(column(row, "files")) if norm_path(p)],
            "wave": column(row, "wave").strip(),
            "exclusive": is_yes(column(row, "exclusive")),
        })
    return out


# ---------------------------------------------------------------- Anforderungen

def collect_req_ids(paths, pattern):
    """Anforderungskennungen aus Dateien oder Ordnern (.md, .txt), sortiert und eindeutig."""
    rx = compile_re(pattern, "--req-pattern")
    files = []
    for path in paths:
        if os.path.isdir(path):
            for root, dirs, names in os.walk(path):
                dirs[:] = sorted(d for d in dirs if not d.startswith("."))
                files += [os.path.join(root, n) for n in sorted(names) if n.endswith((".md", ".txt"))]
        elif os.path.isfile(path):
            files.append(path)
        else:
            raise InputError(f"Spec-Pfad nicht gefunden: {path}")
    ids = set()
    for path in files:
        ids.update(m.group(0) for m in rx.finditer(read_text(path)))
    return sorted(ids)


# ---------------------------------------------------------------- lint

def is_placeholder(body):
    """Leer oder nur Platzhalter (none, tbd, <...>, ...)."""
    items = []
    for line in body:
        s = re.sub(r"^\s*[-*+>]\s*", "", line).strip().strip(".:;!").strip().lower()
        if s:
            items.append(s)
    if not items:
        return True
    return all(s in PLACEHOLDERS or re.fullmatch(r"<[^>]*>", s) for s in items)


def has_command(body):
    """Ein Befehl in Backticks oder ein Codeblock mit Inhalt."""
    fence = False
    for line in body:
        if FENCE.match(line):
            fence = not fence
        elif fence and line.strip():
            return True
        elif not fence and re.search(r"`[^`\n]*[^`\s][^`\n]*`", line):
            return True
    return False


def lint_plan(text, depth, spec_ids, limits):
    """Liste (Regel, Ort, Satz) in fester Reihenfolge."""
    lines = text.splitlines()
    sections = parse_sections(lines)
    tables = parse_tables(lines)
    blocks = block_list(find_blocks_table(tables))
    tasks = find_tasks_table(tables)["rows"]
    out = []

    required = REQUIRED_MINI + (REQUIRED_MORE if depth != "mini" else ())
    for name in required:
        if find_section(sections, name) is None:
            out.append(("L1", name, "Pflichtabschnitt fehlt."))

    scope = find_section(sections, "Out of scope")
    if scope is not None and is_placeholder(scope["body"]):
        out.append(("L2", "Out of scope", "Abschnitt ist leer oder nur ein Platzhalter."))

    for b in blocks:
        if not b["tasks"]:
            out.append(("L3", b["id"], "Block ohne Aufgaben."))
        elif len(b["tasks"]) == 1 and not b["exclusive"]:
            out.append(("L3", b["id"], "Block mit einer Aufgabe ist nur mit Exclusive = yes erlaubt."))
        elif len(b["tasks"]) > limits["block_tasks"]:
            out.append(("L3", b["id"], f"Block mit mehr als {limits['block_tasks']} Aufgaben."))
        if not b["files"]:
            out.append(("L3", b["id"], "Block ohne Dateien."))

    out += lint_waves(blocks, depth, limits)

    for row in tasks:
        tid = column(row, "id")
        target = column(row, "test target").strip()
        if not target:
            out.append(("L5", tid, "Aufgabe ohne Test target."))
        elif "`" not in target and not target.lower().startswith("n/a: text"):
            out.append(("L5", tid, "Test target ohne Schnittstelle in Backticks."))

    if spec_ids:
        used = " ".join(column(r, "requirements") for r in tasks)
        used += " " + (" ".join(scope["body"]) if scope else "")
        for rid in spec_ids:
            if not re.search(r"(?<![\w-])" + re.escape(rid) + r"(?![\w-])", used):
                out.append(("L6", rid, "Anforderung steht weder in einer Aufgabe noch in Out of scope."))

    ver = find_section(sections, "Verification")
    if ver is not None and not has_command(ver["body"]):
        out.append(("L7", "Verification", "Kein Befehl in Backticks."))

    if depth != "mini":
        dec = find_section(sections, "Decisions")
        out += lint_decisions(dec) if dec is not None else []
    return out


def lint_waves(blocks, depth, limits):
    out = []
    if depth == "mini" and not any(b["wave"] for b in blocks):
        return out
    waves = {}
    for b in blocks:
        if not b["wave"]:
            out.append(("L4", b["id"], "Block steht in keiner Welle."))
        else:
            waves.setdefault(b["wave"], []).append(b)
    for wave in sorted(waves):
        group = waves[wave]
        if len(group) > limits["wave_blocks"]:
            out.append(("L4", f"Welle {wave}", f"Mehr als {limits['wave_blocks']} Bloecke in einer Welle."))
        if len(group) > 1:
            for b in group:
                if b["exclusive"]:
                    out.append(("L4", b["id"], f"Exklusiver Block teilt Welle {wave} mit anderen."))
        for n, a in enumerate(group):
            for b in group[n + 1:]:
                hit = [(x, y) for x in a["files"] for y in b["files"] if overlaps(x, y)]
                if hit:
                    out.append(("L4", f"{a['id']}/{b['id']}",
                                f"Ueberlappende Dateien in Welle {wave}: {hit[0][0]} und {hit[0][1]}."))
    return out


def lint_decisions(section):
    tables = parse_tables(section["body"])
    if not tables:
        return []
    table = tables[0]
    names = [h for h in table["header"] if h in REASON_COLUMNS]
    col = names[0] if names else table["header"][-1]
    out = []
    for n, row in enumerate(table["rows"], 1):
        if not row.get(col, "").strip():
            first = next(iter(row.values()), "") or f"Zeile {n}"
            out.append(("L8", first, "Entscheidung ohne Begruendung."))
    return out


# ---------------------------------------------------------------- Kommandozeile

class Parser(argparse.ArgumentParser):
    def error(self, message):
        print(f"Ungueltige Eingabe: {message.splitlines()[0]}", file=sys.stderr)
        sys.exit(2)


def build_parser():
    p = Parser(description="Plan pruefen, Stufe und Tiefe bestimmen.")
    sub = p.add_subparsers(dest="cmd", parser_class=Parser)
    sub.required = True

    lint = sub.add_parser("lint", help="Plan gegen die Regeln L1 bis L8 pruefen")
    lint.add_argument("plan")
    lint.add_argument("--depth", choices=DEPTHS, default="standard")
    lint.add_argument("--specs", nargs="+", action="extend", default=[])
    lint.add_argument("--req-pattern", default=DEFAULT_REQ)
    lint.add_argument("--limits")

    stage = sub.add_parser("stage", help="Prozessstufe S, M oder L aus dem Plan")
    stage.add_argument("plan")
    stage.add_argument("--depth", choices=DEPTHS)
    stage.add_argument("--limits")
    stage.add_argument("--schema-paths", default=DEFAULT_SCHEMA)
    stage.add_argument("--security-paths", default=DEFAULT_SECURITY)

    depth = sub.add_parser("depth", help="Planungstiefe aus Kennzahlen")
    for name in ("areas", "spec-sources", "gate-points", "files"):
        depth.add_argument("--" + name, type=int, required=True)
    depth.add_argument("--flag", nargs="+", action="extend", choices=FLAGS, default=[])
    depth.add_argument("--limits")
    return p


def cmd_lint(args):
    limits = parse_limits(args.limits)
    compile_re(args.req_pattern, "--req-pattern")
    ids = collect_req_ids(args.specs, args.req_pattern) if args.specs else None
    found = lint_plan(read_text(args.plan), args.depth, ids, limits)
    for rule, place, sentence in found:
        print(f"{rule} {place}: {sentence}")
    return 1 if found else 0


def stage_plan(text, depth, limits, schema_rx, security_rx):
    """Stufe aus dem Plan -> (S|M|L, Gruende)."""
    lines = text.splitlines()
    blocks = block_list(find_blocks_table(parse_tables(lines)))
    files = sorted({f for b in blocks for f in b["files"]})
    reasons = [f"Bloecke: {len(blocks)}, Dateien: {len(files)}"]
    big = False
    for b in blocks:
        if b["exclusive"]:
            big = True
            reasons.append(f"Exklusiver Block: {b['id']}")
    for f in files:
        if schema_rx.search(f):
            big = True
            reasons.append(f"Datei im Schema-Muster: {f}")
        if security_rx.search(f):
            big = True
            reasons.append(f"Datei im Sicherheitsmuster: {f}")
    if len(files) > limits["stage_l_files"]:
        big = True
        reasons.append(f"Mehr als {limits['stage_l_files']} Dateien")
    if big:
        stage = "L"
    elif len(files) <= limits["stage_s_files"] and len(blocks) == 1:
        stage = "S"
        reasons.append(f"Hoechstens {limits['stage_s_files']} Dateien, ein Block, kein Flag")
    else:
        stage = "M"
    floor = {"mini": "S", "standard": "M", "voll": "L"}.get(depth)
    if floor and "SML".index(floor) > "SML".index(stage):
        stage = floor
        reasons.append(f"Untergrenze aus Tiefe {depth}: {floor}")
    return stage, reasons


def cmd_stage(args):
    limits = parse_limits(args.limits)
    schema_rx = compile_re(args.schema_paths, "--schema-paths")
    security_rx = compile_re(args.security_paths, "--security-paths")
    stage, reasons = stage_plan(read_text(args.plan), args.depth, limits, schema_rx, security_rx)
    print("\n".join([stage] + reasons))
    return 0


def depth_for(areas, spec_sources, gate_points, files, flags, limits):
    """Planungstiefe aus Kennzahlen -> (mini|standard|voll, Gruende)."""
    reasons = [f"Bereiche: {areas}, Spec-Quellen: {spec_sources}, Gate-Punkte: {gate_points}, Dateien: {files}"]
    if flags:
        reasons.append("Flags: " + ", ".join(sorted(set(flags))))
    heavy = bool({"schema", "security"} & set(flags))
    mini = (areas <= limits["areas"] and spec_sources <= limits["spec_sources"]
            and gate_points <= limits["gate_points"] and files <= limits["files"] and not flags)
    if mini:
        return "mini", reasons
    if areas <= limits["standard_areas"] and not heavy:
        return "standard", reasons
    if heavy:
        reasons.append("Flag schema oder security verlangt voll")
    else:
        reasons.append(f"Mehr als {limits['standard_areas']} Bereiche")
    return "voll", reasons


def cmd_depth(args):
    limits = parse_limits(args.limits)
    numbers = (args.areas, args.spec_sources, args.gate_points, args.files)
    if min(numbers) < 0:
        raise InputError("Kennzahlen duerfen nicht negativ sein")
    word, reasons = depth_for(*numbers, args.flag, limits)
    print("\n".join([word] + reasons))
    return 0


def main(argv=None):
    args = build_parser().parse_args(argv)
    handler = {"lint": cmd_lint, "stage": cmd_stage, "depth": cmd_depth}[args.cmd]
    try:
        return handler(args)
    except InputError as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
