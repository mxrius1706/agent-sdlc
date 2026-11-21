"""Lock je Lauf: ein zweiter Start desselben Laufs wird verweigert.

Aufruf:

    python3 -I run-lock.py acquire <lockfile> [--pid N]
    python3 -I run-lock.py release <lockfile>

`acquire` legt die Lockdatei an und schreibt die PID des Halters hinein
(Standard: der erste Vorfahre, der keine Shell ist, also die Sitzung und nicht
die Kurzzeit-Shell eines Bash-Aufrufs; `--pid N` ueberschreibt das). Exit 0: der Lauf darf starten. Exit 1:
ein lebender Halter hat den Lock, der Lauf startet nicht. Gehoert der Lock
einem toten Prozess, meldet das Skript ihn als veraltet, uebernimmt ihn und
gibt Exit 0. `release` loescht die Lockdatei; fehlt sie, ist das kein Fehler.
"""

import argparse
import os
import subprocess
import sys

SHELLS = ("sh", "bash", "zsh", "dash", "fish")


def alive(pid):
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def parent_and_name(pid):
    try:
        out = subprocess.run(
            ["ps", "-o", "ppid=,comm=", "-p", str(pid)],
            capture_output=True, text=True, timeout=10,
        ).stdout.strip()
        ppid, comm = out.split(None, 1)
        name = os.path.basename(comm.strip()).lstrip("-")
        return int(ppid), name
    except (OSError, ValueError, subprocess.SubprocessError):
        return None, None


def session_pid():
    """Erster Vorfahre, der keine Shell ist; sonst der oberste unterhalb von init."""
    pid = os.getppid()
    while True:
        parent, name = parent_and_name(pid)
        if name is None or name not in SHELLS:
            return pid
        if parent is None or parent <= 1:
            return pid
        pid = parent


def read_pid(path):
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return int(handle.read().strip())
    except (OSError, ValueError):
        return None


def create(path, pid):
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(str(pid) + "\n")


def acquire(path, pid):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    for _ in range(2):
        try:
            create(path, pid)
            print("Lock gesetzt: " + path)
            return 0
        except FileExistsError:
            holder = read_pid(path)
            if holder is not None and alive(holder):
                print("Lauf laeuft bereits (PID " + str(holder) + "), kein zweiter Start: " + path)
                return 1
            print("Lock veraltet (Prozess " + str(holder) + " ist tot), wird uebernommen: " + path)
            try:
                os.remove(path)
            except FileNotFoundError:
                pass
    print("Lock nicht zu bekommen: " + path)
    return 1


def release(path):
    try:
        os.remove(path)
        print("Lock freigegeben: " + path)
    except FileNotFoundError:
        print("Kein Lock vorhanden: " + path)
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description="Lock je Lauf")
    parser.add_argument("action", choices=("acquire", "release"))
    parser.add_argument("lockfile")
    parser.add_argument("--pid", type=int, default=None)
    args = parser.parse_args(argv)
    if args.action == "acquire":
        return acquire(args.lockfile, args.pid if args.pid is not None else session_pid())
    return release(args.lockfile)


if __name__ == "__main__":
    sys.exit(main())
