"""UserPromptSubmit hook: erzwingt den Handoff, wenn sich jemand verabschiedet.

Erkennt Abschiedsformeln und weist die Sitzung an, `session-recap` auszufuehren,
bevor sie antwortet. Ohne das wird der Handoff genau dann vergessen, wenn er
gebraucht wird, naemlich beim Aufhoeren.

Registrierung in `.claude/settings.json`:

    "hooks": {
      "UserPromptSubmit": [
        { "hooks": [ {
            "type": "command",
            "command": "python3 \\"$CLAUDE_PROJECT_DIR/.claude/hooks/session-recap-trigger.py\\" || true",
            "shell": "bash"
        } ] }
      ]
    }

## Ausloeser-Disziplin, bitte lesen bevor die Liste erweitert wird

Ein Phrasen-Hook feuert bei JEDEM Prompt und kostet dort Zeit und Kontext.
Er lohnt sich nur, wenn die Muster eindeutig sind.

Alltagswoerter gehoeren nicht hinein. Ein Hook, der auf "Schritt" oder
"machen wir" ausloest, feuert staendig und liegt fast immer falsch; er
erzeugt dann keine Nutzung, sondern nur Rauschen, und der erzwungene Skill
verliert seine Bedeutung, weil er ohnehin dauernd laeuft.

Der Test fuer ein Muster: Kann dieser Satz mitten in der Arbeit fallen, ohne
dass er das Ende meint? Wenn ja, gehoert er nicht in die Liste.

Deshalb stehen hier nur Formeln, die nichts anderes heissen koennen.
Sprachen ergaenzen ist richtig, Alltagswoerter ergaenzen nicht.
"""

import json
import os
import sys

PATTERNS = (
    # Deutsch
    "tschüss", "tschuss", "auf wiedersehen", "bis morgen", "bis dann",
    "feierabend", "machen wir schluss", "session beenden", "für heute war es das",
    "fuer heute war es das",
    # Englisch
    "goodbye", "good night", "see you tomorrow", "call it a day",
    "wrap up for today", "end the session", "that is it for today",
    "that's it for today",
)

# Teilen sich mehrere Sitzungen ein Repo, hat jede ihre eigene Uebergabe
# (PROJECT_STATE, wie in session-state.py).
STATE_FILE = os.environ.get("PROJECT_STATE") or ".claude/state.md"

INSTRUCTION = (
    "PFLICHT: Fuehre zuerst den Skill 'session-recap' aus, bevor du antwortest. "
    "Er schreibt die Uebergabe nach " + STATE_FILE + " und prueft dabei den Fahrplan "
    "in der Wissensbasis: hat diese Sitzung einen Schritt abgeschlossen, wird er "
    "dort eingetragen, bevor die Uebergabe geschrieben wird."
)


def main() -> None:
    data = json.load(sys.stdin)
    prompt = (data.get("prompt") or "").lower()

    if not any(p in prompt for p in PATTERNS):
        return

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": INSTRUCTION,
        }
    }))


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001 - ein Hook darf nie die Sitzung kippen
        sys.exit(0)
