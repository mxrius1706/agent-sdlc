# Plan: Phase 1 Messen (Mini)

Rahmenplan: `umstellung-kosten.md`. Planungstiefe **Mini** (ein Bereich, eine Spec-Quelle, kein Schema, kein Sicherheitsbezug, keine neue Abhängigkeit). Branch `umstellung/1-messen`, Status ✅ (gebaut, Gate 1 bis auf Basiswerte erfuellt).

## Kontext und Ziel

Die Umstellung braucht Messwerte, bevor ihre Hebel greifen: Fix-Quote und Rollenverteilung je Phase, Limit-Lücken und welche Teile des Projektwissens in Sitzungen geladen werden. Danach gibt es Basiswerte für den Vergleich in Phase 5 und Eingaben für den Kontextpaket-Builder.

Ziel: `session-cost.py` ist versioniert und kann Rollen, Limit-Lücken und Fix-Quote ausgeben. Ein neuer Tracker `context-usage.py` zeigt je Abschnitt des Projektwissens, wie oft und über welchen Kanal er geladen wurde. `retro` kennt beides als Quelle.

## Entscheidungen

| Frage | Antwort | Grund |
|---|---|---|
| Abschnitts-ID | `<relativer Pfad>#<Überschriftenpfad>`, doppelte Pfade `~2`. Beginnt eine Überschrift mit einer Anforderungsnummer, gilt sie als Alias. Umbenennen ergibt einen neuen Abschnitt | Keine Änderung an den Notizen (entschieden) |
| Erkennung | Zeilenabgleich der Abschnitte mit Werkzeugergebnissen (Kanal `gelesen`), Anhängen (`injiziert`) und Subagenten-Prompts (`kopiert`). Gezählt werden **verschiedene** Zeilen, nicht Vorkommen. Keine Befehls-Parser | Eine Probe an einem Pilotprojekt erkannte 388 von 400 Abschnitten, `cat`, `sed`, `rg` und MCP brauchen keine Sonderbehandlung (entschieden) |
| Ausgabe | Nebendatei im Projekt (`.claude/context-usage.json`, nicht committet) und Markdown-Tabelle auf der Konsole | Nichts im Vault, kein Eingriff in den Cache (entschieden) |
| Schwellen | Volle Ladung ab 80 % verschiedener Zeilen, Teilladung ab 30 %. Nur Zeilen ab 25 Zeichen, nur Abschnitte mit mindestens 3 solchen Zeilen | Kurze Zeilen und Trenner erzeugen Zufallstreffer |
| Beweisstufen | Phase 1 liefert **Stufe B** (Teilladung, oder ein nur in diesem Abschnitt vorkommender Bezeichner taucht später in Werkzeugeingaben auf) und **C** (nur geladen). Stufe A (Zitat, Nachladen, Skill-Aufruf) folgt mit Phase 4 | Zitierpflicht gibt es erst nach der Messung |
| Fix-Quote | (Aktivminuten `block-fix` plus `gate-fix`) geteilt durch Aktivminuten `build`. Der Zeitraum einer Phase kommt über `--since` und `--until` | Das Skript bleibt projekt-unabhängig |

## Aufgaben in Reihenfolge

Zwei Blöcke mit disjunkten Dateien in **einer** Welle, danach t6 und t7 durch den Koordinator.

**b1: session-cost** (`skills/retro/scripts/session-cost.py`, `test_session_cost.py`)
- t1 `session-cost.py` committen, `.gitignore` bekommt `__pycache__/`.
- t2 Rollenzuordnung und Limit-Lücken aus dem Testbranch `rollentest-b` übernehmen (`git cherry-pick 77fa274 a4fe569`, sonst `git diff 02480ab..rollentest-b | git apply`). Dabei die Befunde der Review beheben: `--json` mit `--roles` oder `--gaps` liefert die Daten statt sie stumm zu verwerfen, der Schlüssel `"ts"` in `role_table` bekommt einen sprechenden Namen, ein Test für eine Nutzerzeile zwischen Limit-Meldung und Lücke.
- t3 Fix-Quote in `--roles` (Zeile und JSON) und `--since`, `--until`. `classify_role` um allgemeine deutsche Begriffe erweitern (zum Beispiel Befund, Nachprüfung, Folge-Review, Umbau, Cluster), geprüft an einer lokalen Liste echter Beschreibungen. Ziel: höchstens 30 % der Agenten unter `other`.

**b2: Tracker** (`skills/retro/scripts/context-usage.py`, `test_context_usage.py`)
- t4 Abschnitte: `chunk_markdown`, `load_docs` (Standard: Projekt-`CLAUDE.md`, `.claude/rules/*.md`, Vault-Wurzel über `.claude/roadmap-path` nach oben bis `.obsidian`).
- t5 Zählung: `scan_transcript` (drei Kanäle, verschiedene Zeilen), `evidence_tier`, Aggregation je Abschnitt (Ladungen, Teilladungen, Kanäle, Zeichen), "Ballast" = Zeichen mal Ladungen bei Stufe C, Startlast je Agententyp (Anhänge und Tokens im ersten Aufruf). Kommandozeile `--project`, `--docs`, `--since`, `--top`, `--json-out`.

**Danach**
- t6 `skills/retro/SKILL.md`: Bericht als Quelle und Kategorie "Context ballast" (Auslöser: Anweisungsdateien groß oder Startlast fiel auf). Wenige Zeilen, im Stil von `writing-for-agents`.
- t7 Basiswerte lokal festhalten (Fix-Quote der zwei letzten Phasen je Pilotprojekt, Startlast je Agententyp), in einer privaten Datei außerhalb des Repos. Nichts davon in Repo oder Commit.

Gebaut wird nach `execute-plan` mit den Rollen `block-implementer` und `block-reviewer` (erster echter Einsatz). Prüfung nach Stufe S: ein `review-changes`-Lauf auf dem starken Modell über den ganzen Diff, `thermo` nur bei Schwellenwert-Treffern (Datei über 1.000 Zeilen), kein `handlauf` (keine Oberfläche).

## Tests (Schnittstellen)

Schnittstelle: die öffentlichen Funktionen und die Kommandozeile als Unterprozess gegen ein synthetisches Projekt in einem Temp-Ordner (Dokumente und Transkripte mit neutralen Namen wie `projekt-a`).

- `classify_role`: Tabelle je Rolle, Reihenfolge, deutsche Begriffe. Findet falsche Regeln, übersieht reale Varianten (deshalb die lokale Probe).
- `role_table` und Fix-Quote: synthetische Agenten mit bekannten Minuten, Zahl und Rundung.
- `limit_gaps`: Lücke nach Limit-Meldung, Lücke nach normaler Meldung, kurze Pause, Nutzerzeile dazwischen.
- `chunk_markdown`: Überschriftenpfade, doppelte Pfade `~2`, Alias für Anforderungsnummer, zu kurze Abschnitte entfallen.
- `scan_transcript`: ein Abschnitt je Kanal, Teilladung, **dieselbe Zeile zehnmal ändert das Ergebnis nicht**.
- `evidence_tier`: B bei Teilladung, B bei späterem Bezeichner, sonst C.
- Kommandozeile Ende zu Ende: JSON-Datei hat die erwarteten Schlüssel, `--json` mit `--roles` liefert Daten.

## Verifikation

- `python3 -I -m unittest discover -s skills/retro/scripts -p 'test_*.py'` grün, dazu `session-cost.py --help` und `context-usage.py --help` mit Exit 0.
- Lokal an beiden Pilotprojekten: `--roles` und `--gaps` ohne Fehler, `context-usage.py` liefert einen Bericht mit mindestens 5 Abschnitten der Stufe B.
- `grep` gegen die Liste der Projektnamen über Diff und Commit-Texte: keine Treffer. Keine Geviertstriche.

## Out of scope

Kein Hook, keine Zitierpflicht, keine Stufe A, keine Änderung an `execute-plan`, `review-changes` oder `planning`, keine Skript-Ausgabe im Vault, keine Löschempfehlung allein nach Zahlen, keine Dollar-Beträge, kein Commit mit Projektdaten oder Berichten.

## Gate 1

- [ ] Alle Tests grün
- [ ] `--roles` und `--gaps` laufen auf den Transkripten beider Pilotprojekte
- [ ] `context-usage.py` liefert für ein Pilotprojekt einen Bericht mit mindestens 5 Abschnitten der Stufe B
- [ ] Basiswerte (Fix-Quote der zwei letzten Phasen je Pilotprojekt) liegen lokal vor
- [ ] Keine Datei, kein Test und kein Commit nennt ein Pilotprojekt
