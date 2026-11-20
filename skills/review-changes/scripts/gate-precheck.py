#!/usr/bin/env python3
"""gate-precheck: mechanischer Vorlauf vor dem Modell-Review.

Aufruf:
  gate-precheck.py --base <ref> [--head <ref>] [--root <dir>]
                   [--cmd "<befehl>" ...] [--trailer "<zeile>"] [--size-limit N]

Prueft ohne Modell: Befehle (--cmd, ohne Shell), Trailer je Commit,
Dateigroesse, relative Markdown-Links. Nur Standardbibliothek.
"""
import posixpath
import re
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


def git(root, *args):
    """Fuehrt git in root aus, gibt (Exitcode, stdout als Bytes) zurueck."""
    res = subprocess.run(["git", *args], cwd=root, capture_output=True)
    return res.returncode, res.stdout


def git_text(root, *args):
    code, out = git(root, *args)
    return code, out.decode("utf-8", errors="replace")


def check_trailer(base, head, trailer, root):
    """Jeder Commit in base..head (ohne Merges) enthaelt die Trailer-Zeile woertlich."""
    if not trailer:
        return [("PASS", "trailer", "kein --trailer angegeben, uebersprungen")]
    code, out = git_text(root, "log", "--no-merges", "--format=%H%x00%B%x01",
                         "%s..%s" % (base, head))
    if code != 0:
        return [("FAIL", "trailer", "git log fehlgeschlagen")]
    missing = []
    total = 0
    for entry in out.split("\x01"):
        if not entry.strip():
            continue
        sha, _, body = entry.strip("\n").partition("\x00")
        total += 1
        if trailer not in [l.rstrip() for l in body.splitlines()]:
            missing.append(sha.strip()[:7])
    if missing:
        return [("FAIL", "trailer", "Trailer fehlt in %d von %d Commits: %s"
                 % (len(missing), total, ", ".join(missing)))]
    return [("PASS", "trailer", "%d Commits mit Trailer" % total)]


def count_lines(data):
    """Zeilenzahl eines Bytes-Blocks, None bei Binaerdaten."""
    if b"\x00" in data:
        return None
    return data.count(b"\n") + (1 if data and not data.endswith(b"\n") else 0)


def changed_files(base, head, root):
    """Namen der im Bereich hinzugekommenen oder geaenderten Dateien (relativ zu root)."""
    code, out = git(root, "diff", "--name-only", "-z", "--relative",
                    "--diff-filter=ACMR", base, head, "--", ".")
    if code != 0:
        return []
    return [n for n in out.decode("utf-8", errors="replace").split("\0") if n]


def lines_at(ref, path, root):
    """Zeilenzahl der Datei bei ref, None wenn fehlend oder binaer."""
    code, out = git(root, "show", "%s:./%s" % (ref, path))
    if code != 0:
        return None
    return count_lines(out)


def check_sizes(base, head, limit, root):
    """FAIL bei Ueberschreitung der Grenze; schon grosse, gewachsene Dateien nur Hinweis."""
    results = []
    for path in changed_files(base, head, root):
        now = lines_at(head, path, root)
        if now is None or now <= limit:
            continue
        before = lines_at(base, path, root)
        if before is None or before <= limit:
            was = "neu" if before is None else "%d Zeilen" % before
            results.append(("FAIL", "groesse", "%s hat %d Zeilen (Grenze %d, vorher %s)"
                            % (path, now, limit, was)))
        elif now > before:
            results.append(("PASS", "groesse", "Hinweis: %s war schon ueber der Grenze "
                            "und wuchs von %d auf %d Zeilen" % (path, before, now)))
    if not results:
        return [("PASS", "groesse", "keine Datei neu ueber %d Zeilen" % limit)]
    return results


LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)[^)]*\)")
SKIP_PREFIX = ("http:", "https:", "mailto:", "ftp:", "/", "#")


def extract_links(text):
    """Relative Link-Ziele mit Zeilennummer, ohne Anker, URLs und Codebloecke."""
    found = []
    fenced = False
    for no, line in enumerate(text.splitlines(), 1):
        if line.lstrip().startswith("```"):
            fenced = not fenced
            continue
        if fenced:
            continue
        for target in LINK_RE.findall(line):
            if target.lower().startswith(SKIP_PREFIX):
                continue
            target = target.split("#", 1)[0]
            if target:
                found.append((no, target))
    return found


def exists_at(ref, path, root):
    code, _ = git(root, "cat-file", "-e", "%s:./%s" % (ref, path))
    return code == 0


def check_links(base, head, root):
    """Relative Markdown-Links in geaenderten .md-Dateien muessen bei head existieren."""
    results = []
    checked = 0
    for path in changed_files(base, head, root):
        if not path.lower().endswith(".md"):
            continue
        code, out = git(root, "show", "%s:./%s" % (head, path))
        if code != 0:
            continue
        checked += 1
        folder = posixpath.dirname(path)
        for no, target in extract_links(out.decode("utf-8", errors="replace")):
            norm = posixpath.normpath(posixpath.join(folder, target))
            if norm.startswith("..") or not exists_at(head, norm, root):
                results.append(("FAIL", "links", "%s:%d Ziel fehlt: %s" % (path, no, target)))
    if not results:
        return [("PASS", "links", "%d geaenderte Markdown-Dateien ohne kaputte Links" % checked)]
    return results
