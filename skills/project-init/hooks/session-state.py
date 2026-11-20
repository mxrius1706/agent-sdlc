"""SessionStart hook: legt Fahrplan und letzte Uebergabe in jede neue Sitzung.

Zwei Dateien, zwei Fragen:

- Der **Fahrplan** sagt, wo das Projekt steht und was als Naechstes kommt.
  Er liegt in der Wissensbasis ausserhalb des Repos, deshalb muss sein Pfad
  hier konfiguriert werden (siehe roadmap_path unten).
- Die **Uebergabe** in `.claude/state.md` sagt, was letzte Sitzung lief.
  Teilen sich mehrere Sitzungen ein Repo, bekommt jede ihre eigene Datei:
  Umgebungsvariable `PROJECT_STATE`, relativ zum Projekt oder absolut.

Beide werden injiziert statt nur erwaehnt. Eine Anweisung, eine Datei zu
lesen, ist eine Bitte; injizierter Inhalt liegt einfach da. Genau deshalb
gibt es diesen Hook ueberhaupt.

Der Fahrplan waechst. In der Aufbauphase ist er kurz; sobald die Bauphasen
darin stehen, wird er lang - ausgewachsen leicht 60.000 Zeichen und mehr.
Stumpfes Abschneiden waere hier der schlimmste Fehlermodus, weil
abgeschnittener Inhalt in der Sitzung wie vollstaendiger aussieht. Deshalb wird ab dem Moment, in dem der Fahrplan eine aktuelle
Bauphase nennt, in zwei Stuecken injiziert:

1. der Kopf bis zum ersten Trenner, also Position und Regeln, und
2. genau der Abschnitt, auf den die Zeile `**Aktuelle Bauphase:**` zeigt.

Fehlt die Marke, geht der ganze Fahrplan rein. Das ist der Normalfall bis
zum Bauplan und braucht keine Sonderbehandlung.

Konfiguration des Fahrplan-Pfads, erste Fundstelle gewinnt:

1. Umgebungsvariable `PROJECT_ROADMAP`
2. Die Datei `.claude/roadmap-path` im Projekt, eine Zeile mit dem Pfad
3. `roadmap.md` im Projekt (Fallback, falls die Wissensbasis im Repo liegt)

`project-init` schreibt Variante 2, weil es den Vault-Pfad ohnehin kennt.
Fehlt der Pfad, wird nur die Uebergabe injiziert, statt zu scheitern.

Registrierung in `.claude/settings.json`:

    "hooks": {
      "SessionStart": [
        { "hooks": [ {
            "type": "command",
            "command": "python3 \\"$CLAUDE_PROJECT_DIR/.claude/hooks/session-state.py\\" || true",
            "shell": "bash"
        } ] }
      ]
    }

Das `|| true` ist Absicht: ein Fehler hier darf keine Sitzung blockieren.
"""

import json
import os
import re
import sys

MAX_ROADMAP_CHARS = 8000
MAX_HANDOFF_CHARS = 6000
MAX_HEAD_CHARS = 4000
MAX_SECTION_CHARS = 7000

MARKER = re.compile(r"^\*\*Aktuelle Bauphase:\*\*\s*(.+?)\s*$", re.MULTILINE)
HEADING = re.compile(r"^(#{2,6})\s+(.*)$")


def read_file(path):
    """Datei lesen. None, wenn es sie nicht gibt oder sie leer ist."""
    if not path or not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as handle:
            content = handle.read().strip()
    except OSError:
        return None
    return content or None


def clip(text, limit, path):
    if len(text) > limit:
        return text[:limit] + "\n\n[gekuerzt, vollstaendig in " + path + "]"
    return text


def split_head(content):
    """Kopf bis zum ersten Trenner. Ohne Trenner ist der ganze Text der Kopf."""
    for rule in ("\n---\n", "\n***\n", "\n___\n"):
        cut = content.find(rule)
        if cut != -1:
            return content[:cut].strip()
    return content.strip()


def find_section(content, needle):
    """Den Abschnitt zurueckgeben, dessen Ueberschrift `needle` enthaelt.

    Verglichen wird kleingeschrieben und ohne Sternchen, damit die Marke
    `Phase 4` auch auf `## 4. Phase 4 - Datenmodell **im Bau**` passt. Der
    Abschnitt endet bei der naechsten Ueberschrift gleicher oder hoeherer
    Ebene, Unterabschnitte kommen also mit.
    """
    needle = needle.replace("*", "").strip().lower()
    if not needle:
        return None

    lines = content.splitlines()
    start = None
    level = 0
    for index, line in enumerate(lines):
        match = HEADING.match(line)
        if not match:
            continue
        if start is None:
            if needle in match.group(2).replace("*", "").lower():
                start = index
                level = len(match.group(1))
        elif len(match.group(1)) <= level:
            return "\n".join(lines[start:index]).strip()
    if start is None:
        return None
    return "\n".join(lines[start:]).strip()


def roadmap_for_session(path):
    """Ganzer Fahrplan, oder Kopf plus aktuelle Bauphase, wenn er eine nennt."""
    content = read_file(path)
    if not content:
        return None

    head = split_head(content)
    marker = MARKER.search(head)
    if marker:
        section = find_section(content, marker.group(1))
        if section:
            return (
                clip(head, MAX_HEAD_CHARS, path)
                + "\n\n"
                + clip(section, MAX_SECTION_CHARS, path)
                + "\n\n[Nur Kopf und aktuelle Bauphase. Die uebrigen Phasen "
                "stehen in " + path + " und werden bei Bedarf dort gelesen.]"
            )

    return clip(content, MAX_ROADMAP_CHARS, path)


def roadmap_path(project_dir):
    from_env = os.environ.get("PROJECT_ROADMAP")
    if from_env:
        return from_env

    pointer = os.path.join(project_dir, ".claude", "roadmap-path")
    if os.path.exists(pointer):
        try:
            with open(pointer, "r", encoding="utf-8") as handle:
                configured = handle.read().strip()
            if configured:
                return os.path.expanduser(configured)
        except OSError:
            pass

    return os.path.join(project_dir, "roadmap.md")


def state_path(project_dir):
    from_env = os.environ.get("PROJECT_STATE")
    if from_env:
        return os.path.join(project_dir, os.path.expanduser(from_env))
    return os.path.join(project_dir, ".claude", "state.md")


def run_summary(project_dir):
    """Kurzfassung des neuesten Laufzustands in .claude/run/*.md, sonst None."""
    run_dir = os.path.join(project_dir, ".claude", "run")
    try:
        names = [n for n in os.listdir(run_dir) if n.endswith(".md")]
        newest = max(names, key=lambda n: os.path.getmtime(os.path.join(run_dir, n)))
    except (OSError, ValueError):
        return None
    content = read_file(os.path.join(run_dir, newest))
    if not content:
        return None

    branch = re.search(r"^Phasen-Branch:\s*(.+?)\s*$", content, re.MULTILINE)
    blocks = []
    in_table = False
    for line in content.splitlines():
        if not line.strip().startswith("|"):
            in_table = False
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if cells[:2] == ["Block", "Status"]:
            in_table = True
        elif in_table and len(cells) >= 2 and not set(cells[0]) <= set("-: "):
            blocks.append(cells[0] + ": " + cells[1])

    lines = ["LAUFZUSTAND (aus .claude/run/" + newest + ")"]
    if branch:
        lines.append("Phasen-Branch: " + branch.group(1))
    if blocks:
        lines.append("Bloecke: " + "; ".join(blocks))
    lines.append("Weitermachen mit execute-plan Schritt 0")
    return "\n".join(lines)


def main() -> None:
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", ".")

    roadmap = roadmap_for_session(roadmap_path(project_dir))

    handoff_path = state_path(project_dir)
    handoff = read_file(handoff_path)
    if handoff:
        handoff = clip(handoff, MAX_HANDOFF_CHARS, handoff_path)

    summary = run_summary(project_dir)
    if not roadmap and not handoff and not summary:
        return

    parts = []
    if roadmap:
        parts.append("FAHRPLAN (wo steht das Projekt, was kommt als Naechstes)\n" + roadmap)
    if handoff:
        shown = os.path.relpath(handoff_path, project_dir)
        parts.append("LETZTE SITZUNG (aus " + shown + ")\n" + handoff)

    if roadmap:
        parts.append(
            "Beginne die Sitzung damit, wo wir stehen und was als Naechstes ansteht, "
            "und biete diesen Schritt an, statt auf eine Frage zu warten. Wer einen "
            "Schritt abschliesst, traegt ihn im Fahrplan ein, bevor es weitergeht. "
            "Bevor ein Skill aus diesem Ablauf laeuft, wird seine Zeile im Fahrplan "
            "gelesen: steht die Voraussetzung dort noch offen, wird er nicht "
            "ausgefuehrt, sondern der fehlende Schritt benannt und angeboten. Das "
            "gilt auch, wenn nach dem Ergebnis gefragt wird statt nach dem Schritt."
        )
    else:
        parts.append(
            "Kein Fahrplan gefunden. Falls das Projekt einen hat, liegt sein Pfad "
            "nicht in .claude/roadmap-path; sonst ist er noch nicht angelegt."
        )

    if summary:
        parts.append(summary)

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": "\n\n".join(parts),
        }
    }))


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001 - ein Hook darf nie die Sitzung kippen
        sys.exit(0)
