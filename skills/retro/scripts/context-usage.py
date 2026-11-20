#!/usr/bin/env python3
"""Welche Abschnitte des Projektwissens werden in Sitzungen geladen, und ueber welchen Kanal.

Liest nur lokale Dateien (Projektdokumente, Transkripte unter ~/.claude*/projects).

    python3 -I context-usage.py --project agent-sdlc --since 2026-11-01 --top 20
    python3 -I context-usage.py --json-out .claude/context-usage.json

Abschnitts-ID: <relativer Pfad>#<Ueberschriftenpfad>, doppelte mit ~2. Beginnt eine
Ueberschrift mit einer Anforderungsnummer (z. B. R12), gilt <Pfad>#R12 als Alias.
"""
import argparse
import glob
import json
import os
import re
import sys
from datetime import datetime, timezone

MIN_LINE = 25  # Zeichen: kuerzere Zeilen zaehlen nicht (Trenner, Zufallstreffer)
MIN_LINES = 3  # Abschnitte mit weniger verschiedenen Zeilen entfallen
FULL = 0.8     # ab diesem Anteil verschiedener Zeilen gilt ein Abschnitt als voll geladen
PARTIAL = 0.3  # ab diesem Anteil als teilweise geladen
CHANNELS = ("gelesen", "injiziert", "kopiert")
COPY_TOOLS = ("Agent", "Task", "SendMessage")  # Werkzeuge, deren Eingabe an einen Subagenten geht
SKIP_DIRS = {".git", "node_modules", ".worktrees", ".obsidian", "__pycache__", ".venv"}

HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
LINE_NO = re.compile(r"^\d+[\u2192\t]")  # Zeilennummer-Praefix der Lese-Ausgabe
IDENT = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_./-]{6,}")
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


def strings(o):
    """Alle Texte in einer verschachtelten JSON-Struktur."""
    if isinstance(o, str):
        yield o
    elif isinstance(o, dict):
        for v in o.values():
            yield from strings(v)
    elif isinstance(o, list):
        for v in o:
            yield from strings(v)


def text_lines(text):
    """Verschiedene Zeilen ab MIN_LINE (ohne Zeilennummer-Praefix)."""
    out = set()
    for ln in text.splitlines():
        ln = ln.strip()
        ln = LINE_NO.sub("", ln).strip()
        if len(ln) >= MIN_LINE:
            out.add(ln)
    return out


def idents(text):
    """Bezeichner-artige Woerter: lang genug und mit Sonderzeichen, Ziffer oder Binnen-Grossbuchstaben."""
    out = set()
    for w in IDENT.findall(text):
        w = w.rstrip("./-")
        if len(w) >= 8 and (re.search(r"[_./\-0-9]", w) or re.search(r"[a-z][A-Z]", w)):
            out.add(w)
    return out


def build_index(sections):
    """Zeile -> Abschnitts-IDs, Abschnitts-ID -> Zeilenzahl, Bezeichner -> ID (nur wenn eindeutig)."""
    by_line = {}
    total = {}
    ident_owner = {}
    for sec in sections:
        total[sec["id"]] = len(sec["lines"])
        for ln in sec["lines"]:
            by_line.setdefault(ln, []).append(sec["id"])
        for w in idents("\n".join(sec["lines"])):
            ident_owner.setdefault(w, set()).add(sec["id"])
    unique = {w: next(iter(ids)) for w, ids in ident_owner.items() if len(ids) == 1}
    return {"by_line": by_line, "total": total, "unique": unique}


def new_entry():
    e = {c: {"full": 0, "partial": 0} for c in CHANNELS}
    e["ident_later"] = False
    return e


def match_text(text, index):
    """Text -> {Abschnitts-ID: "full" | "partial"} nach Anteil verschiedener Zeilen."""
    hits = {}
    for ln in text_lines(text):
        for sid in index["by_line"].get(ln, ()):
            hits[sid] = hits.get(sid, 0) + 1
    out = {}
    for sid, n in hits.items():
        frac = n / index["total"][sid]
        if frac >= FULL:
            out[sid] = "full"
        elif frac >= PARTIAL:
            out[sid] = "partial"
    return out


def records(path):
    """JSONL -> Datensaetze in Reihenfolge, ohne kaputte Zeilen und ohne doppelte uuid."""
    seen = set()
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                o = json.loads(line)
            except ValueError:
                continue
            if not isinstance(o, dict):
                continue
            u = o.get("uuid")
            if u:
                if u in seen:
                    continue
                seen.add(u)
            yield o


def events(o):
    """Datensatz -> Liste (Kanal, Text) fuer Ladungen und Liste Texte aller Werkzeugeingaben."""
    loads = []
    inputs = []
    msg = o.get("message") if isinstance(o.get("message"), dict) else {}
    content = msg.get("content")
    kind = o.get("type")
    if kind == "attachment":
        loads.append(("injiziert", "\n".join(strings(o.get("attachment")))))
    elif kind == "user" and isinstance(content, list):
        for b in content:
            if isinstance(b, dict) and b.get("type") == "tool_result":
                loads.append(("gelesen", "\n".join(strings(b.get("content")))))
    elif kind == "assistant" and isinstance(content, list):
        for b in content:
            if isinstance(b, dict) and b.get("type") == "tool_use":
                text = "\n".join(strings(b.get("input")))
                inputs.append(text)
                if b.get("name") in COPY_TOOLS:
                    loads.append(("kopiert", text))
    return loads, inputs


def scan_transcript(path, sections, index=None):
    """Ein Transkript -> {Abschnitts-ID: {gelesen|injiziert|kopiert: {full, partial}, ident_later}}.

    Nur Abschnitte mit mindestens einer Ladung kommen vor. Gezaehlt werden verschiedene
    Zeilen je Ereignis, nie Vorkommen. ident_later: ein nur in diesem Abschnitt vorkommender
    Bezeichner steht nach der ersten Ladung in einer Werkzeugeingabe.
    """
    index = index or build_index(sections)
    res = {}
    for o in records(path):
        loads, inputs = events(o)
        for text in inputs:  # zuerst pruefen: Eingabe derselben Zeile ist kein spaeterer Beleg
            for w in idents(text):
                sid = index["unique"].get(w)
                if sid in res:
                    res[sid]["ident_later"] = True
        for channel, text in loads:
            for sid, kind in match_text(text, index).items():
                res.setdefault(sid, new_entry())[channel][kind] += 1
    return res


def evidence_tier(partial, ident_later):
    """Stufe B: Teilladung oder spaeter genutzter Bezeichner, sonst C (nur geladen)."""
    return "B" if partial or ident_later else "C"


def aggregate(sections, scans):
    """Sections plus Scan-Ergebnisse -> Zeilen je Abschnitt, geladene zuerst (nach Ballast)."""
    # scans: Scan-Dicts oder Paare (Empfaenger, Scan). Ohne Empfaenger gilt "sub".
    # Injiziert ist immer geladen und sagt nichts ueber Nutzung: es zaehlt nicht
    # zum Ballast, sondern wird nach Hauptsitzung und Subagent getrennt gezeigt.
    scans = [s if isinstance(s, tuple) else ("sub", s) for s in scans]
    rows = []
    for sec in sections:
        sid = sec["id"]
        ch = {c: 0 for c in CHANNELS}
        partial = 0
        ident = False
        inj_main = inj_sub = 0
        for who, sc in scans:
            e = sc.get(sid)
            if not e:
                continue
            for c in CHANNELS:
                ch[c] += e[c]["full"]
                partial += e[c]["partial"]
            if who == "main":
                inj_main += e["injiziert"]["full"]
            else:
                inj_sub += e["injiziert"]["full"]
            ident = ident or e["ident_later"]
        loads = sum(ch.values())
        deliberate = ch["gelesen"] + ch["kopiert"]
        tier = evidence_tier(partial, ident) if loads or partial else None
        rows.append({"id": sid, "alias": sec.get("alias"), "loads": loads, "partial": partial,
                     "channels": ch, "chars": sec["chars"], "tier": tier,
                     "inj_main": inj_main, "inj_sub": inj_sub, "sub_chars": sec["chars"] * inj_sub,
                     "ballast": sec["chars"] * deliberate if tier == "C" else 0})
    rows.sort(key=lambda r: (r["tier"] is None, -r["ballast"], -r["sub_chars"], -r["loads"], -r["partial"], r["id"]))
    return rows


def start_load(path):
    """Startlast eines Transkripts: Anhaenge vor dem ersten Aufruf und Tokens im ersten Aufruf."""
    attachments = 0
    for o in records(path):
        if o.get("type") == "attachment":
            attachments += 1
        elif o.get("type") == "assistant":
            u = (o.get("message") or {}).get("usage")
            if u:
                tokens = sum((u.get(k) or 0) for k in
                             ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens"))
                return {"attachments": attachments, "tokens": tokens}
    return {"attachments": attachments, "tokens": 0}


def startlast_by_type(pairs):
    """[(Agententyp, start_load)] -> {Typ: {n, attachments, tokens}} als Mittelwerte."""
    acc = {}
    for typ, sl in pairs:
        a = acc.setdefault(typ, [0, 0, 0])
        a[0] += 1
        a[1] += sl["attachments"]
        a[2] += sl["tokens"]
    return {t: {"n": n, "attachments": at / n, "tokens": tk / n} for t, (n, at, tk) in acc.items()}


def first_ts(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                ts = json.loads(line).get("timestamp")
            except (ValueError, AttributeError):
                continue
            if ts:
                try:
                    return datetime.fromisoformat(ts.replace("Z", "+00:00"))
                except ValueError:
                    continue
    return None


def find_sessions(roots, project, since):
    """Hauptsitzungen mit ihren Subagenten. Konten, die auf denselben Ordner zeigen, zaehlen einmal."""
    out = []
    seen = set()
    for root in roots:
        for folder in sorted(glob.glob(os.path.join(root, "*"))):
            real = os.path.realpath(folder)
            if real in seen or not os.path.isdir(folder):
                continue
            if project and project not in os.path.basename(folder):
                continue
            seen.add(real)
            for main in sorted(glob.glob(os.path.join(folder, "*.jsonl"))):
                if since:
                    ts = first_ts(main)
                    if not ts or ts < since:
                        continue
                sid = os.path.basename(main)[:-6]
                subs = []
                for sub in sorted(glob.glob(os.path.join(folder, sid, "subagents", "agent-*.jsonl"))):
                    meta = {}
                    try:
                        with open(sub[:-6] + ".meta.json", encoding="utf-8") as fh:
                            meta = json.load(fh)
                    except (OSError, ValueError):
                        pass
                    subs.append((sub, meta.get("agentType") or "?"))
                out.append({"main": main, "subs": subs})
    return out


def fmt_table(rows, top):
    shown = [r for r in rows if r["tier"] is not None][:top]
    lines = ["| Abschnitt | Teil | gelesen | kopiert | inj. Haupt | inj. Sub | Zeichen | Stufe | Ballast | Sub-Zeichen |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for r in shown:
        c = r["channels"]
        lines.append(f"| {r['id']} | {r['partial']} | {c['gelesen']} | {c['kopiert']} | {r['inj_main']} | "
                     f"{r['inj_sub']} | {r['chars']} | {r['tier']} | {r['ballast']} | {r['sub_chars']} |")
    return "\n".join(lines)


def fmt_startlast(start):
    lines = ["| Agententyp | Anzahl | Anhaenge | Tokens im ersten Aufruf |", "|---|---|---|---|"]
    for t in sorted(start, key=lambda k: -start[k]["tokens"]):
        v = start[t]
        lines.append(f"| {t} | {v['n']} | {v['attachments']:.1f} | {v['tokens']:.0f} |")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", action="append", help="projects-Ordner, mehrfach moeglich (Standard: ~/.claude*/projects)")
    ap.add_argument("--project", help="Teil des Projektordner-Namens (Standard: Name des Projektordners)")
    ap.add_argument("--project-dir", default=os.getcwd(), help="Projektordner mit den Dokumenten (Standard: aktueller Ordner)")
    ap.add_argument("--docs", action="append", help="Dateien oder Ordner statt der Standard-Dokumente, mehrfach moeglich")
    ap.add_argument("--since", help="nur Sitzungen ab Datum (YYYY-MM-DD)")
    ap.add_argument("--top", type=int, default=20, help="Zeilen der Tabelle (Standard 20)")
    ap.add_argument("--json-out", help="Pfad der JSON-Datei")
    a = ap.parse_args()

    roots = a.root or sorted(glob.glob(os.path.expanduser("~/.claude*/projects")))
    project = a.project or os.path.basename(os.path.abspath(a.project_dir))
    since = None
    if a.since:
        since = datetime.fromisoformat(a.since).replace(tzinfo=timezone.utc)

    sections = []
    docs = load_docs(a.project_dir, a.docs)
    for name, text in docs:
        sections += chunk_markdown(name, text)
    index = build_index(sections)
    sessions = find_sessions(roots, project, since)

    scans = []
    pairs = []
    n_subs = 0
    for s in sessions:
        scans.append(("main", scan_transcript(s["main"], sections, index)))
        pairs.append(("main", start_load(s["main"])))
        for sub, typ in s["subs"]:
            n_subs += 1
            scans.append((typ, scan_transcript(sub, sections, index)))
            pairs.append((typ, start_load(sub)))
    rows = aggregate(sections, scans)
    start = startlast_by_type(pairs)

    loaded = sum(1 for r in rows if r["tier"] is not None)
    tiers = {t: sum(1 for r in rows if r["tier"] == t) for t in ("B", "C")}
    print(f"Sitzungen: {len(sessions)}, Subagenten: {n_subs}, Dokumente: {len(docs)}, "
          f"Abschnitte: {len(rows)}, davon geladen: {loaded} (Stufe B: {tiers['B']}, C: {tiers['C']})\n")
    print(fmt_table(rows, a.top))
    print()
    print(fmt_startlast(start))
    if a.json_out:
        meta = {"project": project, "since": a.since, "sessions": len(sessions), "subagents": n_subs,
                "docs": len(docs), "sections": len(rows), "loaded": loaded}
        d = os.path.dirname(os.path.abspath(a.json_out))
        os.makedirs(d, exist_ok=True)
        with open(a.json_out, "w", encoding="utf-8") as fh:
            json.dump({"meta": meta, "sections": rows, "startlast": start}, fh, indent=2, ensure_ascii=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
