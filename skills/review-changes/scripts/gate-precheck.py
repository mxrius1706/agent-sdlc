#!/usr/bin/env python3
"""gate-precheck: mechanischer Vorlauf vor dem Modell-Review.

Aufruf:
  gate-precheck.py --base <ref> [--head <ref>] [--root <dir>]
                   [--cmd "<befehl>" ...] [--trailer "<zeile>"] [--size-limit N]

Prueft ohne Modell: Befehle (--cmd, ohne Shell), Trailer je Commit,
Dateigroesse, relative Markdown-Links. Nur Standardbibliothek.
"""
import shlex
import subprocess

TAIL_LINES = 15


def tail(text, n=TAIL_LINES):
    """Letzte n nicht leere Zeilen als ein Text."""
    rows = [r for r in text.splitlines() if r.strip()]
    return "\n".join(rows[-n:])


def run_one(cmd, root):
    """Fuehrt einen Befehl ohne Shell aus, gibt (status, check, detail) zurueck."""
    check = "cmd `%s`" % cmd
    try:
        argv = shlex.split(cmd)
    except ValueError as exc:
        return ("FAIL", check, "Befehl nicht lesbar: %s" % exc)
    if not argv:
        return ("FAIL", check, "leerer Befehl")
    try:
        res = subprocess.run(argv, cwd=root, capture_output=True, text=True,
                             errors="replace")
    except OSError as exc:
        return ("FAIL", check, "nicht ausfuehrbar: %s" % exc)
    if res.returncode == 0:
        return ("PASS", check, "Exit 0")
    out = tail(res.stdout + "\n" + res.stderr)
    return ("FAIL", check, "Exit %d\n%s" % (res.returncode, out))


def run_checks(cmds, root):
    """Ein Ergebnis je Befehl; ohne Befehle ein PASS mit Hinweis."""
    if not cmds:
        return [("PASS", "cmd", "keine Befehle angegeben")]
    return [run_one(c, root) for c in cmds]
