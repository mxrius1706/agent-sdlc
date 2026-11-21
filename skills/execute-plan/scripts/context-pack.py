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
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys

MIN_LINE = 25  # Zeichen: kuerzere Zeilen zaehlen nicht (Trenner, Zufallstreffer)
MIN_LINES = 3  # Abschnitte mit weniger verschiedenen Zeilen entfallen

HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
REQ_NO = re.compile(r"^([A-Za-z]{1,4}-?\d+[a-z]?|\d+(?:\.\d+)+)(?=$|[\s:.)\]-])")
SKIP_DIRS = {".git", "node_modules", ".worktrees", ".obsidian", "__pycache__", ".venv"}
DEFAULT_MAX = 60000
SUB_TITLES = ("für subagenten", "fuer subagenten")

REQ_ID = re.compile(r"\b[A-Z]{2,6}-\d+[a-z]?\b")
SPEC_QUAL = re.compile(r"([A-Za-z0-9_.\-]+)(?:\s*:\s*|\s+)$")


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
        cell = column(t, "requirements")
        for m in REQ_ID.finditer(cell):
            q = SPEC_QUAL.search(cell[:m.start()])
            qual = q.group(1) if q and not REQ_ID.fullmatch(q.group(1)) else None
            item = f"{qual} {m.group(0)}" if qual else m.group(0)
            if item not in reqs:
                reqs.append(item)
    return files, reqs, rows


def spec_name(path):
    """Spec-Datei -> Name: Dateiname ohne .md, kleingeschrieben."""
    base = os.path.basename(path)
    return (base[:-3] if base.lower().endswith(".md") else base).lower()


def req_pattern(rid):
    return r"(?<![\w-])" + re.escape(rid) + r"(?![\w-])"


def split_reqs(reqs, names):
    """Kennungen des Blocks -> (nackte Kennungen, {Kennung: Spec-Namen}). Ein Name, der keine Spec ist, zaehlt nicht."""
    bare, qual = [], {}
    for item in reqs:
        head, _, rid = item.rpartition(" ")
        if head and head.lower() in names:
            qual.setdefault(rid, set()).add(head.lower())
        elif rid not in bare:
            bare.append(rid)
    return bare, qual


def spec_list_of(specs):
    return [p for p in spec_files(specs) if os.path.basename(p) != "GLOSSARY.md"]


def ambiguous_reqs(scope, specs):
    """Nackte Kennungen, die in mehr als einer Spec-Datei vorkommen -> Liste (Kennung, Anzahl)."""
    paths = spec_list_of(specs)
    bare, _ = split_reqs(scope[1], {spec_name(p) for p in paths})
    texts = [read_text(p) or "" for p in paths]
    out = []
    for rid in bare:
        n = sum(1 for t in texts if re.search(req_pattern(rid), t))
        if n > 1:
            out.append((rid, n))
    return out


# ---- Abschnitte sammeln ----

def read_text(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError:
        return None


def rel_id_path(path, root):
    """Pfad -> Pfad relativ zu root mit /; ausserhalb von root: externer Ordnername und Dateiname."""
    absp, absr = os.path.abspath(path), os.path.abspath(root)
    if absp == absr or absp.startswith(absr + os.sep):
        return os.path.relpath(absp, absr).replace(os.sep, "/")
    return "extern/" + os.path.basename(os.path.dirname(absp)) + "/" + os.path.basename(absp)


def walk_files(top, name=None, suffix=None):
    """Alle Dateien unter top (sortiert, ohne SKIP_DIRS), gefiltert nach Name oder Endung."""
    out = []
    for base, dirs, files in os.walk(top):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
        for f in sorted(files):
            if (name and f == name) or (suffix and f.endswith(suffix)):
                out.append(os.path.join(base, f))
    return out


def glob_match(pattern, path):
    """Glob mit *, ** und ? gegen einen Pfad mit /. * und ? bleiben innerhalb eines Ordners."""
    rx = ""
    i = 0
    while i < len(pattern):
        c = pattern[i]
        if pattern.startswith("**/", i):
            rx += "(?:.*/)?"
            i += 3
            continue
        if pattern.startswith("**", i):
            rx += ".*"
            i += 2
            continue
        rx += "[^/]*" if c == "*" else "[^/]" if c == "?" else re.escape(c)
        i += 1
    return re.fullmatch(rx, path) is not None


def rule_paths(text):
    """Regeltext -> (Glob-Liste aus dem Frontmatter-Schluessel paths, Text nach dem Frontmatter)."""
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return [], text
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        return [], text
    paths = []
    in_paths = False
    for ln in lines[1:end]:
        m = re.match(r"^paths:\s*(.*?)\s*$", ln)
        if m:
            in_paths = True
            val = m.group(1)
            if val.startswith("["):
                paths += [clean_glob(x) for x in val.strip("[]").split(",") if clean_glob(x)]
            elif val:
                paths.append(clean_glob(val))
            continue
        item = re.match(r"^\s+-\s+(.*?)\s*$", ln)
        if in_paths and item:
            paths.append(clean_glob(item.group(1)))
        elif ln.strip() and not ln.startswith(" "):
            in_paths = False
    return [p for p in paths if p], "".join(lines[end + 1:])


def clean_glob(raw):
    return raw.strip().strip("\"'").strip()


def is_sub_title(title):
    return title.strip().lower() in SUB_TITLES


def sub_sections(relpath, text):
    """Abschnitte "Für Subagenten" samt Unterabschnitten, woertlich -> Liste {id, kind, text}."""
    raw = split_raw(text)
    out = []
    i = 0
    while i < len(raw):
        path, title, level, lines = raw[i]
        if level and is_sub_title(title):
            parts = ["\n".join(lines)]
            j = i + 1
            while j < len(raw) and raw[j][2] > level:
                parts.append("\n".join(raw[j][3]))
                j += 1
            out.append({"id": f"{relpath}#{path}", "kind": "subagenten", "text": "\n".join(parts) + "\n"})
            i = j
        else:
            i += 1
    return out


def covered(sid, chosen):
    """Ist die ID ein gewaehlter Abschnitt oder liegt sie darunter?"""
    return any(sid == c or sid.startswith(c + " > ") for c in chosen)


def as_items(chunks, kind):
    return [{"id": c["id"], "kind": kind, "text": c["text"]} for c in chunks]


def area_dirs(files):
    """Dateien des Blocks -> Ordner darueber, nahe zuerst, ohne Wurzel, ohne Wiederholung."""
    out = []
    for f in files:
        d = f.strip("/") if f.endswith("/") else os.path.dirname(f)
        while d and d != ".":
            if d not in out:
                out.append(d)
            d = os.path.dirname(d)
    out.sort(key=lambda x: (-x.count("/"), x))
    return out


def avoid_last(text):
    """Glossarabschnitt: die _Avoid_-Zeilen (Aliase) stehen nach der Beschreibung."""
    lines = text.rstrip("\n").split("\n")
    avoid = [ln for ln in lines if ln.lstrip().lower().startswith("_avoid_")]
    return "\n".join([ln for ln in lines if ln not in avoid] + avoid) + "\n"


def word_in(term, text):
    pat = r"(?<![A-Za-z0-9\u00c0-\u024f])" + re.escape(term) + r"(?![A-Za-z0-9\u00c0-\u024f])"
    return re.search(pat, text, re.IGNORECASE) is not None


def spec_files(specs):
    out = []
    for s in specs:
        if os.path.isdir(s):
            out += walk_files(s, suffix=".md")
        elif os.path.isfile(s):
            out.append(s)
    return out


def collect(scope, root, specs, global_claude):
    """Block-Umfang -> (included, excluded): Listen {id, kind, text} in Buendel-Reihenfolge."""
    files, reqs, rows = scope
    inc, exc = [], []

    def take(chunks, kind, hit):
        (inc if hit else exc).extend(as_items(chunks, kind))

    # 1. Subagenten-Abschnitte: Projekt, dann global
    root_claude = os.path.join(root, "CLAUDE.md")
    sources = [(root_claude, "CLAUDE.md")]
    if global_claude:
        sources.append((global_claude, "global/" + os.path.basename(global_claude)))
    for path, rel in sources:
        text = read_text(path)
        if text is None:
            continue
        subs = sub_sections(rel, text)
        inc.extend(subs)
        chosen = [x["id"] for x in subs]
        exc.extend(as_items([c for c in chunk_markdown(rel, text) if not covered(c["id"], chosen)],
                            "subagenten"))
    # 2. Bereichs-CLAUDE.md, nahe zuerst
    wanted = []
    for d in area_dirs(files):
        path = os.path.join(root, *d.split("/"), "CLAUDE.md")
        if os.path.isfile(path):
            wanted.append(os.path.abspath(path))
    for path in walk_files(root, name="CLAUDE.md"):
        rel = rel_id_path(path, root)
        if rel == "CLAUDE.md":
            continue
        if os.path.abspath(path) not in wanted:
            exc.extend(as_items(chunk_markdown(rel, read_text(path) or ""), "bereich"))
    inc_area = [it for w in wanted for it in as_items(
        chunk_markdown(rel_id_path(w, root), read_text(w) or ""), "bereich")]
    inc.extend(inc_area)
    # 3. Pfadregeln
    for path in sorted(walk_files(os.path.join(root, ".claude", "rules"), suffix=".md")):
        rel = rel_id_path(path, root)
        globs, rest = rule_paths(read_text(path) or "")
        hit = any(glob_match(g, f) for g in globs for f in files)
        chunks = chunk_markdown(rel, rest)
        if hit and not chunks and rest.strip():
            chunks = [{"id": rel + "#", "text": rest}]
        take(chunks, "regel", hit)
    # 4. Spec-Abschnitte nach Anforderungskennung
    spec_list = spec_list_of(specs)
    bare, qual = split_reqs(reqs, {spec_name(p) for p in spec_list})
    ambiguous = {rid for rid, _ in ambiguous_reqs(scope, specs)}
    bare = [r for r in bare if r not in ambiguous]
    for path in spec_list:
        mine = bare + [r for r, ns in qual.items() if spec_name(path) in ns]
        for c in chunk_markdown(rel_id_path(path, root), read_text(path) or ""):
            hit = any(re.search(req_pattern(r), c["text"]) for r in mine)
            take([c], "spec", hit)
    # 5. Glossarbegriffe per Textvergleich
    haystack = "\n".join([column(r, "task") for r in rows] + list(files))
    seen = set()
    parents = [os.path.join(os.path.dirname(os.path.abspath(s)), "GLOSSARY.md")
               for s in specs if os.path.isdir(s)]
    parents = [p for p in parents if os.path.isfile(p)]
    for path in walk_files(root, name="GLOSSARY.md") + [p for p in spec_files(specs)
                                                       if os.path.basename(p) == "GLOSSARY.md"] + parents:
        if os.path.abspath(path) in seen:
            continue
        seen.add(os.path.abspath(path))
        for c in chunk_markdown(rel_id_path(path, root), read_text(path) or ""):
            c = dict(c, text=avoid_last(c["text"]))
            take([c], "glossar", bool(c["heading"]) and word_in(c["heading"], haystack))
    return inc, exc


# ---- Buendel und Kommandozeile ----

CONTRACT = """- Work only inside the worktree named in your dispatch. The main checkout, the dev server, the database and migrations are off limits.
- Read the files your tasks touch before you change them. The plan decides the way; a plan that looks wrong is a BLOCKED, not a quiet edit.
- Write the failing test first and watch it fail, then build. Run the type check and the tests of the touched files after each task.
- One commit per task, task id in the subject, ending with the trailer above. Stage files one by one with `git add <path>`. No push, no amend."""

GROUPS = (("subagenten", "Für Subagenten"), ("bereich", "Bereichsregeln"), ("regel", "Pfadregeln"),
          ("spec", "Spec-Abschnitte"), ("glossar", "Glossar"))


def last_trailer(message):
    """Commit-Nachricht -> letzte Co-Authored-By-Zeile oder None."""
    found = [ln.strip() for ln in message.splitlines() if ln.strip().lower().startswith("co-authored-by:")]
    return found[-1] if found else None


def git_trailer(root):
    """Letzte Co-Authored-By-Zeile des neuesten Commits im Ordner root, sonst None."""
    try:
        p = subprocess.run(["git", "log", "-1", "--format=%B"], cwd=root, capture_output=True,
                           text=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return None
    return last_trailer(p.stdout) if p.returncode == 0 else None


def fence(lines):
    return "\n".join(lines).strip("\n")


def render(plan_path, block_id, scope, included, trailer, secs):
    files, reqs, rows = scope
    out = [f"# Kontextpaket: Block {block_id}", "", f"- Plan: {os.path.basename(plan_path)}",
           f"- Block: {block_id}", "- Dateien: " + (", ".join(files) if files else "-"),
           "- Anforderungen: " + (", ".join(reqs) if reqs else "-"), "", "## Aufgaben", ""]
    for r in rows:
        out.append(f"- {column(r, 'id')}: {column(r, 'task')}")
    out.append("")
    for kind, title in GROUPS:
        items = [i for i in included if i["kind"] == kind]
        if not items:
            continue
        out += [f"## {title}", ""]
        for it in items:
            out += [f"<!-- Abschnitt: {it['id']} -->", it["text"].rstrip("\n"), ""]
    out += ["## Decisions", "", fence(secs.get("decisions", [])), "",
            "## Verification", "", fence(secs.get("verification", [])), "",
            "## Trailer", "", trailer if trailer else "(none)", "", "## Worktree contract", "", CONTRACT, ""]
    return "\n".join(out)


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise ValueError("Ungueltige Kommandozeile: " + message.split("\n")[0])


def parse_args(argv):
    ap = Parser(prog="context-pack.py", add_help=False)
    ap.add_argument("plan")
    ap.add_argument("--block", required=True)
    ap.add_argument("--root", required=True)
    ap.add_argument("--specs", action="append", default=[])
    ap.add_argument("--global-claude")
    ap.add_argument("--trailer")
    ap.add_argument("--out")
    ap.add_argument("--max-chars", type=int, default=DEFAULT_MAX)
    return ap.parse_args(argv)


def main(argv):
    try:
        a = parse_args(argv)
        if not os.path.isfile(a.plan):
            raise ValueError(f"Der Plan {a.plan} fehlt.")
        if not os.path.isdir(a.root):
            raise ValueError(f"Das Projektverzeichnis {a.root} fehlt.")
        scope = block_scope(a.plan, a.block)
        secs = read_plan(a.plan)
    except (ValueError, OSError, UnicodeDecodeError) as e:
        print(str(e).rstrip(".") + ".", file=sys.stderr)
        return 2
    included, excluded = collect(scope, a.root, a.specs, a.global_claude)
    notes = []
    for rid, n in ambiguous_reqs(scope, a.specs):
        notes.append(f'{rid} ist ambiguous (in {n} Specs): Spec nennen, etwa "<spec> {rid}"')
    has_glossary = any(i["kind"] == "glossar" for i in included + excluded)
    if not has_glossary:
        notes.append("no glossary found")
    trailer = a.trailer or git_trailer(a.root)
    if not trailer:
        notes.append("no trailer found")
    text = render(a.plan, a.block, scope, included, trailer, secs)
    if len(text) > a.max_chars:
        print(f"Das Paket fuer Block {a.block} hat {len(text)} Zeichen, mehr als die Grenze {a.max_chars}.",
              file=sys.stderr)
        return 3
    data = text.encode("utf-8")
    if a.out:
        manifest = {"block": a.block, "hash": hashlib.sha256(data).hexdigest(),
                    "included": [i["id"] for i in included], "excluded": [e["id"] for e in excluded],
                    "notes": notes}
        try:
            with open(a.out, "wb") as fh:
                fh.write(data)
            with open(a.out + ".manifest.json", "w", encoding="utf-8") as fh:
                json.dump(manifest, fh, ensure_ascii=False, indent=2)
                fh.write("\n")
        except OSError as e:
            print(f"Die Ausgabe nach {a.out} ging nicht: {e.strerror}.", file=sys.stderr)
            return 2
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
