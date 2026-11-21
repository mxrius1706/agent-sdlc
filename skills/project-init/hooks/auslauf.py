"""Hook gegen zu volle Sitzungen: misst die Fuellung, setzt die Auslauf-Marke.

Ab einer Schwelle soll die Sitzung nichts Neues mehr beginnen, sondern
ihre laufenden Bloecke zu Ende bringen, den Laufzustand schreiben und mit
einer neuen Sitzung weitermachen. Dieser Hook uebernimmt drei Aufgaben:

1. Messen (`UserPromptSubmit`, `PostToolUse`): Fuellung = input_tokens +
   cache_creation_input_tokens + cache_read_input_tokens der letzten
   Assistenten-Nachricht im Transkript, geteilt durch `fenster`.
2. Marke anlegen: ab `kontext` entsteht `.claude/run/auslauf-<session_id>`
   und die Anweisung wird genau einmal ausgegeben. Ab `notbremse` kommt
   einmal eine haertere Anweisung.
3. Verweigern (`PreToolUse`, Matcher `Agent`): Ist die Marke da, wird ein
   Auftrag nur durchgelassen, wenn er die ID eines Blocks nennt, dessen
   Status im Laufzustand `laufend`, `review` oder `fix` ist.

Konfiguration in `.claude/auslauf.json` (alle Schluessel optional):
`fenster` (1000000), `kontext` (0.6), `notbremse` (0.8). Kaputte Datei
heisst Standardwerte.

Der Laufzustand ist die neueste `.claude/run/*.md` mit der Tabelle
`| Block | Status | Statuscode | Fix-Runden | Worktree |`. Gibt es keinen,
passiert beim Verweigern nichts.

Subagenten (Eingabe enthaelt `agent_id`) werden nie angefasst.

Registrierung in `.claude/settings.json`:

    "hooks": {
      "UserPromptSubmit": [
        { "hooks": [ {
            "type": "command",
            "command": "python3 \\"$CLAUDE_PROJECT_DIR/.claude/hooks/auslauf.py\\" || true",
            "shell": "bash"
        } ] }
      ],
      "PostToolUse": [
        { "hooks": [ {
            "type": "command",
            "command": "python3 \\"$CLAUDE_PROJECT_DIR/.claude/hooks/auslauf.py\\" || true",
            "shell": "bash"
        } ] }
      ],
      "PreToolUse": [
        { "matcher": "Agent", "hooks": [ {
            "type": "command",
            "command": "python3 \\"$CLAUDE_PROJECT_DIR/.claude/hooks/auslauf.py\\" || true",
            "shell": "bash"
        } ] }
      ]
    }

Das `|| true` ist Absicht: ein Fehler hier darf keine Sitzung blockieren.
"""

import glob
import json
import os
import re
import sys

DEFAULTS = {"fenster": 1000000, "kontext": 0.6, "notbremse": 0.8}
RUNNING = ("laufend", "review", "fix")

INSTRUCTION = (
    "AUSLAUF: Der Kontext ist voll genug, diese Sitzung laeuft aus. "
    "Starte keine neuen Bloecke und keine neue Welle. Bringe, was laeuft, "
    "bis zu seinem Endschritt. Aktualisiere dann den Laufzustand, fuehre "
    "session-recap aus und sage dem Nutzer, dass er eine neue Sitzung "
    "starten soll. Ist ein /goal gesetzt, beende ihn mit /goal clear, "
    "damit keine Leerturns folgen."
)
EMERGENCY = (
    "NOTBREMSE: Der Kontext ist fast voll. Hoere jetzt auf. Schreibe sofort "
    "den Laufzustand und die Uebergabe (session-recap), starte nichts und "
    "sage dem Nutzer, dass er eine neue Sitzung starten soll. Ist ein "
    "/goal gesetzt, beende ihn mit /goal clear."
)


def fill(transcript_path, fenster):
    """Anteil des Fensters, den die letzte Assistenten-Nachricht belegt."""
    last = None
    try:
        with open(transcript_path, "r", encoding="utf-8") as handle:
            for line in handle:
                try:
                    entry = json.loads(line)
                except ValueError:
                    continue
                message = entry.get("message") if isinstance(entry, dict) else None
                if not isinstance(message, dict):
                    continue
                if entry.get("type") == "assistant" and isinstance(message.get("usage"), dict):
                    last = message["usage"]
    except (OSError, TypeError):
        return 0
    if not last or not fenster:
        return 0
    total = sum(int(last.get(key) or 0) for key in (
        "input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens"))
    return total / fenster


def read_config(project_dir):
    """Konfiguration mit Standardwerten. Kaputte Datei gibt die Standardwerte."""
    config = dict(DEFAULTS)
    path = os.path.join(project_dir, ".claude", "auslauf.json")
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        for key in DEFAULTS:
            value = data.get(key)
            if isinstance(value, (int, float)) and not isinstance(value, bool) and value > 0:
                config[key] = value
    except (OSError, ValueError, AttributeError):
        pass
    return config


def newest_state(run_dir):
    files = glob.glob(os.path.join(run_dir, "*.md"))
    if not files:
        return None
    return max(files, key=os.path.getmtime)


def parse_blocks(run_dir):
    """Liste (Block, Status) aus der Tabelle des neuesten Laufzustands, sonst None."""
    path = newest_state(run_dir)
    if not path:
        return None
    try:
        with open(path, "r", encoding="utf-8") as handle:
            lines = handle.read().splitlines()
    except OSError:
        return None
    blocks = []
    in_table = False
    for line in lines:
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if not line.strip().startswith("|"):
            in_table = False
            continue
        if cells[:2] == ["Block", "Status"]:
            in_table = True
            continue
        if in_table and len(cells) >= 2 and not set(cells[0]) <= set("-: "):
            blocks.append((cells[0], cells[1]))
    return blocks


def running_blocks(run_dir):
    return [name for name, status in (parse_blocks(run_dir) or []) if status in RUNNING]


def mentions(prompt, block):
    return re.search(r"(?<![\w-])" + re.escape(block) + r"(?![\w-])", prompt) is not None


def set_mark(path, level):
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(level)


def measure(event, data, project_dir, run_dir):
    config = read_config(project_dir)
    share = fill(data.get("transcript_path"), config["fenster"])
    if share >= config["notbremse"]:
        level = "notbremse"
    elif share >= config["kontext"]:
        level = "kontext"
    else:
        return None
    mark = os.path.join(run_dir, "auslauf-" + str(data.get("session_id")))
    try:
        with open(mark, "r", encoding="utf-8") as handle:
            if handle.read().strip() == "notbremse" or level == "kontext":
                return None
    except OSError:
        pass
    os.makedirs(run_dir, exist_ok=True)
    set_mark(mark, level)
    return INSTRUCTION if level == "kontext" else EMERGENCY


def refuse(data, run_dir):
    if data.get("tool_name") != "Agent":
        return None
    if not os.path.exists(os.path.join(run_dir, "auslauf-" + str(data.get("session_id")))):
        return None
    if parse_blocks(run_dir) is None:
        return None
    tool_input = data.get("tool_input")
    prompt = str(tool_input.get("prompt", "")) if isinstance(tool_input, dict) else ""
    if any(mentions(prompt, block) for block in running_blocks(run_dir)):
        return None
    return (
        "AUSLAUF: Die Sitzung laeuft aus, es startet nichts Neues. Erlaubt "
        "sind nur Auftraege mit der ID eines Blocks im Status laufend, "
        "review oder fix."
    )


def decide(event, data, project_dir):
    """Ausgabe fuer das Ereignis als Text, oder None."""
    if data.get("agent_id"):
        return None
    run_dir = os.path.join(project_dir, ".claude", "run")
    if event == "PreToolUse":
        reason = refuse(data, run_dir)
        if reason is None:
            return None
        return json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason}})
    if event in ("UserPromptSubmit", "PostToolUse"):
        text = measure(event, data, project_dir, run_dir)
        if text is None:
            return None
        if event == "PostToolUse":
            return json.dumps({"hookSpecificOutput": {
                "hookEventName": "PostToolUse", "additionalContext": text}})
        return text
    return None


def main() -> None:
    data = json.load(sys.stdin)
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or "."
    output = decide(data.get("hook_event_name"), data, project_dir)
    if output:
        print(output)


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001 - ein Hook darf nie die Sitzung kippen
        sys.exit(0)
