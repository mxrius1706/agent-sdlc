"""PostToolUse hook: schnelle Pruefungen direkt nach jedem Edit.

Ein Fehler, der sofort auffaellt, kostet eine Zeile Korrektur. Derselbe
Fehler am Phasenende kostet einen Review-Durchlauf. Deshalb laufen nach
jedem Edit, Write und MultiEdit die schnellen, deterministischen Befehle
des Projekts: Typpruefung, Lint der beruehrten Dateien.

Konfiguration in `.claude/checks.json` im Projekt:

    {"commands": ["npx tsc --noEmit", "npx eslint --quiet ."], "timeout_s": 60}

`stack-decisions` legt die Befehle fest, `project-init` schreibt die Datei.
Fehlt sie, tut der Hook nichts. Das ist der Normalfall in einem Projekt,
das noch keinen Stack hat.

Verhalten:

- alle Befehle gruen: Exit 0, keine Ausgabe
- ein Befehl rot: Exit 2, Befehl und gekuerzte Ausgabe auf stderr, damit
  Claude den Fehler sieht und korrigiert
- ein Befehl ueber dem Zeitlimit: Exit 2 mit einem klaren Hinweis. Ein
  Check, der nicht schnell ist, gehoert nicht in diesen Hook.

Gekuerzt wird von hinten: Der Schluss einer Fehlerausgabe enthaelt die
Zusammenfassung, der Anfang meist nur den Lauf.

Registrierung in `.claude/settings.json`:

    "hooks": {
      "PostToolUse": [
        { "matcher": "Edit|Write|MultiEdit",
          "hooks": [ {
            "type": "command",
            "command": "python3 \\"$CLAUDE_PROJECT_DIR/.claude/hooks/post-edit-check.py\\"",
            "shell": "bash"
        } ] }
      ]
    }

Anders als bei session-state.py gibt es hier kein `|| true`: Exit 2 ist
das Signal, das Claude erreichen soll.
"""

import json
import os
import subprocess
import sys

MAX_OUTPUT_CHARS = 3000
DEFAULT_TIMEOUT_S = 60


def load_config(project_dir):
    """checks.json lesen. None, wenn es sie nicht gibt oder sie unbrauchbar ist."""
    path = os.path.join(project_dir, ".claude", "checks.json")
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as handle:
            config = json.load(handle)
    except (OSError, ValueError):
        return None
    if not isinstance(config, dict):
        return None
    return config


def tail(text, limit):
    if len(text) > limit:
        return "[gekuerzt, nur das Ende]\n" + text[-limit:]
    return text


def decode(data):
    if data is None:
        return ""
    if isinstance(data, bytes):
        return data.decode("utf-8", errors="replace")
    return data


def report(message):
    """Auf stderr schreiben, als UTF-8 auch unter Windows."""
    sys.stderr.buffer.write(message.encode("utf-8", errors="replace"))
    sys.stderr.buffer.flush()


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except (ValueError, OSError):
        payload = {}
    if not isinstance(payload, dict):
        payload = {}

    project_dir = os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("cwd") or "."

    config = load_config(project_dir)
    if not config:
        return

    commands = [c for c in config.get("commands", []) if isinstance(c, str) and c.strip()]
    if not commands:
        return

    timeout_s = config.get("timeout_s", DEFAULT_TIMEOUT_S)
    if not isinstance(timeout_s, (int, float)) or timeout_s <= 0:
        timeout_s = DEFAULT_TIMEOUT_S

    for command in commands:
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=project_dir,
                capture_output=True,
                timeout=timeout_s,
            )
        except subprocess.TimeoutExpired as expired:
            partial = tail((decode(expired.stdout) + decode(expired.stderr)).strip(), MAX_OUTPUT_CHARS)
            message = (
                "Sofortpruefung abgebrochen: `" + command + "` brauchte laenger als "
                + str(timeout_s) + " s. Ein Check im After-Edit-Hook muss schnell sein; "
                "den Befehl beschleunigen oder aus .claude/checks.json nehmen.\n"
            )
            if partial:
                message += partial + "\n"
            report(message)
            sys.exit(2)

        if result.returncode != 0:
            output = (decode(result.stdout) + decode(result.stderr)).strip()
            report(
                "Sofortpruefung fehlgeschlagen: `" + command + "` (Exit "
                + str(result.returncode) + ")\n" + tail(output, MAX_OUTPUT_CHARS) + "\n"
            )
            sys.exit(2)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception:  # noqa: BLE001 - ein kaputter Hook darf die Arbeit nicht kippen
        sys.exit(0)
