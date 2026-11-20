#!/usr/bin/env python3
"""Tokens und Dauer je Sitzung und Subagent aus den Claude-Code-Transkripten.

Liest nur lokale JSONL-Dateien und schreibt nichts. Ohne Argumente werden alle
Konten (~/.claude*/projects) durchsucht.

    python3 -I session-cost.py --project agent-sdlc --since 2026-11-01
    python3 -I session-cost.py --session 1f3e0557 --by-agent
    python3 -I session-cost.py --project agent-sdlc --json > kosten.json

Zahlen je Zeile: in = neue Eingabe, cw = Cache schreiben, cr = Cache lesen,
out = Ausgabe (inkl. Denken), alle in Token. Min = aktive Zeit: Abstaende zwischen Nachrichten,
je Abstand hoechstens 5 Minuten, damit Pausen und Warten auf dich nicht zaehlen.
"""
import argparse
import glob
import json
import os
import re
import sys
from datetime import datetime, timezone


def parse_ts(s):
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None


def read_transcript(path):
    """Eine JSONL-Datei -> {n, in, cw, cr, out, models, first, last}.

    Eine API-Antwort steht oft in mehreren Zeilen (je Inhaltsblock) mit gleicher
    message.id. Je id zaehlt nur die letzte Zeile, sonst wird doppelt gezaehlt.
    """
    by_id = {}
    first = last = None
    stamps = []
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                o = json.loads(line)
            except ValueError:
                continue
            ts = parse_ts(o.get("timestamp", "")) if o.get("timestamp") else None
            if ts:
                stamps.append(ts)
                first = ts if first is None or ts < first else first
                last = ts if last is None or ts > last else last
            if o.get("type") != "assistant":
                continue
            m = o.get("message") or {}
            u = m.get("usage")
            if not u:
                continue
            by_id[m.get("id") or o.get("uuid")] = (m.get("model", "?"), u)
    t = {"n": 0, "in": 0, "cw": 0, "cr": 0, "out": 0, "models": {}}
    for model, u in by_id.values():
        t["n"] += 1
        t["in"] += u.get("input_tokens", 0) or 0
        t["cw"] += u.get("cache_creation_input_tokens", 0) or 0
        t["cr"] += u.get("cache_read_input_tokens", 0) or 0
        t["out"] += u.get("output_tokens", 0) or 0
        t["models"][model] = t["models"].get(model, 0) + 1
    t["first"], t["last"], t["stamps"] = first, last, stamps
    return t


IDLE_CAP = 300  # Sekunden: laengere Pausen (z. B. Warten auf den Nutzer) zaehlen nur bis hierhin


def secs(t):
    """Aktive Zeit: Summe der Abstaende zwischen Nachrichten, je Abstand hoechstens IDLE_CAP."""
    ts = sorted(t.get("stamps", []))
    return sum(min((b - a).total_seconds(), IDLE_CAP) for a, b in zip(ts, ts[1:]))


# Reihenfolge der Rollenregeln, vom spezifischsten zum allgemeinsten, erste Treffer-Regel gewinnt:
#  1. gate-review  (phase review, oder gate/thermo plus review) - vor block-review, weil "block" auch im Gate-Text vorkommt
#  2. gate-fix     (fix plus gate/thermo/umbau)                 - vor block-fix, sonst gewinnt eine Block-Id im Text
#  3. block-review (review plus block)
#  4. block-fix    (fix plus Block-Id wie b3)                   - vor build, weil "Fix build b3" ein Fix ist
#  5. build        (build oder bau)
#  6. research     (read, fetch, research, lese)
#  7. other
def classify_role(description):
    """Rolle eines Subagenten aus seiner Beschreibung (Stichwortregeln, ohne Gross-/Kleinschreibung)."""
    d = (description or "").lower()
    has = lambda *words: any(w in d for w in words)
    if "phase review" in d or (has("gate", "thermo") and "review" in d):
        return "gate-review"
    if "fix" in d and has("gate", "thermo", "umbau"):
        return "gate-fix"
    if "review" in d and "block" in d:
        return "block-review"
    if "fix" in d and re.search(r"\bb\d+\b", d):
        return "block-fix"
    if has("build", "bau"):
        return "build"
    if has("read", "fetch", "research", "lese"):
        return "research"
    return "other"


ROLES = ["build", "block-review", "block-fix", "gate-review", "gate-fix", "research", "other"]


def role_table(data):
    """Je Rolle ein dict: role, agents (Anzahl), minutes (aktive Minuten), out (Ausgabe-Token)."""
    rows = {r: {"role": r, "agents": 0, "minutes": 0.0, "out": 0} for r in ROLES}
    for s in data:
        for ag in s["agents"]:
            row = rows[classify_role(ag["label"])]
            row["agents"] += 1
            row["minutes"] += secs(ag) / 60
            row["out"] += ag["out"]
    return [rows[r] for r in ROLES]


def print_roles(data):
    print(f"{'Rolle':<14} {'Agents':>6} {'Min':>8} {'out':>10}")
    for row in role_table(data):
        print(f"{row['role']:<14} {row['agents']:>6} {row['minutes']:>8.1f} {row['out']:>10,}")


def message_text(o):
    """Text einer Assistenten-Zeile (alle Textbloecke), sonst leer."""
    c = (o.get("message") or {}).get("content")
    if isinstance(c, str):
        return c
    return " ".join(b.get("text", "") for b in c or [] if isinstance(b, dict) and b.get("type") == "text")


def limit_gaps(path, gap_min=20):
    """Luecken zwischen aufeinanderfolgenden Zeitstempeln ueber gap_min Minuten.

    Je Luecke ein dict: start (ISO), minutes (gerundet), limit (True, wenn die Assistenten-Nachricht
    davor die Woerter "limit" und "resets" enthaelt, ohne Gross-/Kleinschreibung).
    """
    events = []
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                o = json.loads(line)
            except ValueError:
                continue
            ts = parse_ts(o["timestamp"]) if isinstance(o, dict) and o.get("timestamp") else None
            if ts:
                events.append((ts, message_text(o).lower() if o.get("type") == "assistant" else None))
    events.sort(key=lambda e: e[0])
    gaps = []
    last_text = ""
    for (a, text), (b, _) in zip(events, events[1:]):
        if text is not None:
            last_text = text
        minutes = (b - a).total_seconds() / 60
        if minutes > gap_min:
            gaps.append({"start": a.isoformat(), "minutes": round(minutes),
                         "limit": "limit" in last_text and "resets" in last_text})
    return gaps


def gap_table(data, gap_min):
    """Je Sitzung ein dict: project, session, gaps (Liste aus limit_gaps)."""
    return [{"project": s["project"], "session": s["session"], "gaps": limit_gaps(s["main_path"], gap_min)}
            for s in data]


def print_gaps(data, gap_min):
    for s in gap_table(data, gap_min):
        gaps = s["gaps"]
        print(f"{s['project'][-18:]} {s['session'][:8]}: {len(gaps)} Luecken")
        for g in gaps:
            print(f"  {g['start']}  {g['minutes']:>5} Min{'  LIMIT' if g['limit'] else ''}")


def short_model(models):
    if not models:
        return "-"
    return ",".join(m.replace("claude-", "") for m in sorted(models, key=models.get, reverse=True)[:2])


def collect(roots, project, session, since):
    out = []
    seen_roots = set()
    for root in roots:
        real = os.path.realpath(root)
        if real in seen_roots:  # Konten koennen auf einen gemeinsamen Ordner zeigen
            continue
        seen_roots.add(real)
        for proj in sorted(glob.glob(os.path.join(root, "*"))):
            if project and project not in os.path.basename(proj):
                continue
            for main in glob.glob(os.path.join(proj, "*.jsonl")):
                sid = os.path.basename(main)[:-6]
                if session and not sid.startswith(session):
                    continue
                st = read_transcript(main)
                if since and (not st["first"] or st["first"] < since):
                    continue
                agents = []
                for sub in sorted(glob.glob(os.path.join(proj, sid, "subagents", "agent-*.jsonl"))):
                    meta = {}
                    try:
                        with open(sub[:-6] + ".meta.json", encoding="utf-8") as fh:
                            meta = json.load(fh)
                    except (OSError, ValueError):
                        pass
                    a = read_transcript(sub)
                    a["label"] = (meta.get("description") or meta.get("agentType") or os.path.basename(sub))[:50]
                    a["type"] = meta.get("agentType", "?")
                    agents.append(a)
                out.append({"account": os.path.basename(os.path.dirname(root)) or root,
                            "project": os.path.basename(proj), "session": sid,
                            "main": st, "agents": agents, "main_path": main})
    out.sort(key=lambda s: s["main"]["first"] or datetime.min.replace(tzinfo=timezone.utc))
    return out


def fmt_row(label, t):
    return f"{label:<50} {short_model(t['models']):<26} {t['n']:>5} {t['in']:>9,} {t['cw']:>10,} {t['cr']:>12,} {t['out']:>9,} {secs(t)/60:>7.1f}"


HEAD = f"{'':<50} {'Modell':<26} {'Turns':>5} {'in':>9} {'cw':>10} {'cr':>12} {'out':>9} {'Min':>7}"


def total(parts):
    """Summe. Die Zeitstempel werden vereinigt, parallele Subagenten zaehlen also nicht doppelt."""
    t = {"n": 0, "in": 0, "cw": 0, "cr": 0, "out": 0, "models": {}, "first": None, "last": None, "stamps": []}
    for p in parts:
        for k in ("n", "in", "cw", "cr", "out"):
            t[k] += p[k]
        for m, c in p["models"].items():
            t["models"][m] = t["models"].get(m, 0) + c
        t["stamps"] += p.get("stamps", [])
    return t


def to_json(s):
    def c(t):
        return {k: (v.isoformat() if hasattr(v, "isoformat") else v) for k, v in t.items() if k != "stamps"} | {"active_minutes": round(secs(t) / 60, 2)}
    return {"account": s["account"], "project": s["project"], "session": s["session"],
            "main": c(s["main"]), "agents": [c(a) | {"label": a["label"], "type": a["type"]} for a in s["agents"]]}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", action="append", help="projects-Ordner, mehrfach moeglich (Standard: ~/.claude*/projects)")
    ap.add_argument("--project", help="Teil des Projektordner-Namens")
    ap.add_argument("--session", help="Sitzungs-ID oder Anfang davon")
    ap.add_argument("--since", help="nur Sitzungen ab Datum (YYYY-MM-DD)")
    ap.add_argument("--by-agent", action="store_true", help="auch Zeile je Subagent")
    ap.add_argument("--roles", action="store_true", help="Tabelle je Rolle der Subagenten")
    ap.add_argument("--gaps", action="store_true", help="lange Pausen je Sitzung, Limit-Luecken markiert")
    ap.add_argument("--gap-min", type=int, default=20, help="Mindestlaenge einer Luecke in Minuten (Standard 20)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    roots = a.root or sorted(glob.glob(os.path.expanduser("~/.claude*/projects")))
    since = datetime.fromisoformat(a.since).replace(tzinfo=timezone.utc) if a.since else None
    data = collect(roots, a.project, a.session, since)
    if a.json:
        if a.roles or a.gaps:
            result = {}
            if a.roles:
                result["roles"] = role_table(data)
            if a.gaps:
                result["gaps"] = gap_table(data, a.gap_min)
        else:
            result = [to_json(s) for s in data]
        json.dump(result, sys.stdout, indent=1, ensure_ascii=False)
        print()
        return
    if not data:
        print("Keine Sitzungen gefunden.", file=sys.stderr)
        sys.exit(1)
    if a.gaps:
        print_gaps(data, a.gap_min)
        return
    if a.roles:
        print_roles(data)
        return
    print(HEAD)
    grand = []
    for s in data:
        everything = total([s["main"]] + s["agents"])
        grand.append(everything)
        day = s["main"]["first"].strftime("%m-%d %H:%M") if s["main"]["first"] else "?"
        print(fmt_row(f"{day} {s['project'][-18:]} {s['session'][:8]} (gesamt)", everything))
        if a.by_agent:
            print(fmt_row("  Hauptsitzung", s["main"]))
            for ag in s["agents"]:
                print(fmt_row(f"  {ag['type'][:14]}: {ag['label']}"[:50], ag))
    if len(data) > 1:
        print(fmt_row(f"SUMME {len(data)} Sitzungen", total(grand)))


if __name__ == "__main__":
    main()
