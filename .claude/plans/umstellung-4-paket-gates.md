# Plan: Phase 4 Kontextpaket und Gates

Rahmenplan: `umstellung-kosten.md`. Planungstiefe **voll** (`plan-check.py depth`: mehr als 3 Bereiche). Stufe **L** (`plan-check.py stage`: die Tiefe voll setzt die Untergrenze). Gebaut wird deshalb mit Abnahmetests vor jedem Skript-Block und mit voller Gate-Reihenfolge, so wie es dieser Plan selbst für Stufe L vorsieht. Branch `umstellung/4-paket-gates`, Status 🔄 (freigegeben, im Bau).

## Context

Nach den Phasen 1 bis 3 starten Rollen schlank und Pläne werden vor dem Bauen geprüft. Zwei große Posten bleiben: Der Koordinator schreibt das Regelbündel jedes Mal von Hand zusammen, und der Phasen-Gate läuft streng nacheinander (Handlauf, Review, Fix, Thermo, Fix, Retro, Config-Sync), auch wo Stufe und Risiko das nicht verlangen. Phase 4 ersetzt das Handbündel durch ein Skript mit Manifest, schaltet vor jedes Modell-Review einen mechanischen Vorlauf und macht die Gate-Tiefe von der Stufe abhängig.

## Goal

`context-pack.py` baut das Bündel eines Blocks deterministisch und nennt im Manifest, was nicht enthalten ist. `gate-precheck.py` fängt mechanische Mängel vor dem Review ab und sagt, ob `thermo` nötig ist. Bei Stufe S und M laufen die Gates mit einer gemeinsamen Fix-Runde, bei Stufe L bleibt die Reihenfolge. `context-usage.py` misst, was das Paket verfehlt. `LOOP.md` beschreibt den neuen Ablauf.

## Decisions

| Question | Answer | Reason |
|---|---|---|
| Bündel | `context-pack.py` je Block statt einem Bündel je Phase | Ein Block bekommt nur, was seine Dateien und Anforderungen berühren |
| Zu großes Paket | Wird nie abgeschnitten, sondern endet mit Exit 3 und der Meldung, den Block zu teilen | Abgeschnittener Inhalt sieht in der Sitzung vollständig aus (Regel aus `session-state.py`) |
| Manifest | Zu jedem Paket eine Datei `<out>.manifest.json` mit eingeschlossenen Abschnitt-IDs, nicht eingeschlossenen und dem Hash | Die Nachlade-Quote braucht beide Listen |
| Abschnitts-IDs | Dasselbe Schema wie `context-usage.py` (`<relativer Pfad>#<Überschriftenpfad>`). Der Zerleger wird in beiden Skripten geführt, ein Test prüft, dass sie dasselbe liefern | Skripte importieren sich nicht (`python3 -I`, getrennt installierbare Skills) |
| Vorlauf | `gate-precheck.py` führt die Befehle der Projektzeile `planning` / `verification` aus und prüft Trailer, Dateigrößen und Verweisziele | Mechanisches kostet kein Modell |
| Thermo | Bei Stufe S und M nur, wenn der Vorlauf `thermo: yes` meldet (Datei überschreitet die Grenze) oder der Nutzer es verlangt. Stufe L immer | Rahmenplan |
| Parallele Gates | Bei S und M startet der Nutzer `handlauf` in seiner eigenen Sitzung gleichzeitig mit `review-changes`. Eine gemeinsame Fix-Runde nimmt beide Befundlisten, danach genau ein Nachtrags-Lauf. Bei L bleibt die Reihenfolge | `handlauf` bleibt eigene Sitzung ohne Review-Eingabe, das ändert sich nicht |
| Retro und Config-Sync | Nur bei Anlass: `retro`, wenn die Fix-Quote über 0,3 liegt, ein Befund der oberen Stufen auftrat oder der Nutzer es will. `config-sync`, wenn `ref-check.py` Abweichungen meldet oder eine Entscheidung sich änderte | Nicht jede kleine Phase braucht beides |
| Budgets | `maxTurns` je Rolle in der Agentendatei, Phasenbudget als Zeile im Plan (Abschnitt Decisions) und Warnung nach jeder Welle über `session-cost.py`, Stall-Regel im Text (ein Block ohne neuen Commit über 20 Minuten wird geprüft) | Startwerte, im Pilot zu kalibrieren |
| Nachlade-Quote | `context-usage.py --pack <Manifest>` zählt Abschnitte, die Subagenten außerhalb des Pakets lasen, und Paketabschnitte ohne Hinweis auf Nutzung | Entscheidet im Pilot über die Zitierpflicht |
| Config-Sync mechanisch | `ref-check.py` prüft, dass Pfade in Backticks in Anweisungsdateien existieren | Der prüfbare Teil von `config-sync` wird ein Skript |

## Critical files

| File | Change |
|---|---|
| `skills/execute-plan/scripts/context-pack.py` | neu |
| `skills/review-changes/scripts/gate-precheck.py` | neu |
| `skills/retro/scripts/context-usage.py` | `--pack`, Nachlade-Quote |
| `skills/config-sync/scripts/ref-check.py` | neu |
| `skills/execute-plan/SKILL.md` | Paket statt Handbündel, Budgets, Stufen-Gates |
| `skills/review-changes/SKILL.md` | Vorlauf, gemeinsame Fix-Runde |
| `skills/plan-build/SKILL.md` | Ritual je Stufe |
| `skills/config-sync/SKILL.md`, `skills/retro/SKILL.md`, `skills/thermo-nuclear-code-quality-review/SKILL.md` | Auslöser |
| `agents/*.md` | `maxTurns` |
| `LOOP.md`, `README.md` | neuer Ablauf |

## Blocks

| Block | Tasks | Files | Wave | Exclusive |
|---|---|---|---|---|
| b1 | p1, p2, p3 | skills/execute-plan/scripts/ | 1 | no |
| b2 | g1, g2, g3 | skills/review-changes/scripts/ | 1 | no |
| b3 | r1, r2, c1 | skills/retro/scripts/, skills/config-sync/scripts/ | 1 | no |
| b4 | t1, t2, t3, t4, t5 | skills/execute-plan/SKILL.md, skills/review-changes/SKILL.md, skills/plan-build/SKILL.md, skills/config-sync/SKILL.md, skills/retro/SKILL.md, skills/thermo-nuclear-code-quality-review/SKILL.md, agents/, LOOP.md, README.md | 2 | no |

## Tasks

| Id | Block | Task | Test target (seam) | Requirements |
|---|---|---|---|---|
| p1 | b1 | Plan lesen (Blocks-, Tasks-, Decisions-Tabelle, Verification), Dateien und Anforderungen des Blocks bestimmen | `block_scope(plan, block)`: bekannter Plan gibt Dateien und Kennungen, unbekannter Block gibt Fehler | - |
| p2 | b1 | Abschnitte sammeln: `## Für Subagenten` (Projekt und global), Bereichs-`CLAUDE.md`, Pfadregeln mit passendem `paths:`, Spec-Abschnitte nach Anforderungskennung, Glossarbegriffe per Textvergleich | `collect(scope, root, specs)`: ein Abschnitt je Fach, Abschnitt ohne Treffer fehlt und steht im Manifest | - |
| p3 | b1 | Bündel schreiben, Manifest, Hash, Kommandozeile, Exit 3 bei zu großem Paket | `main(argv)`: gleiche Eingabe gleicher Hash, zu große Eingabe Exit 3 ohne Ausgabedatei, fehlender Plan Exit 2 | - |
| g1 | b2 | Befehle aus `--cmd` ausführen (ohne Shell), Ergebnis je Befehl | `run_checks(cmds)`: grüner und roter Befehl, nicht vorhandener Befehl als FAIL | - |
| g2 | b2 | Trailer je Commit, Größengrenze (neu über der Grenze, oder von darunter darüber), Verweisziele geänderter Markdown-Dateien | `check_trailer`, `check_sizes`, `check_links` gegen ein synthetisches Git-Repo im Temp-Ordner | - |
| g3 | b2 | Kommandozeile, Berichtzeilen `PASS`/`FAIL`, letzte Zeile `thermo: yes\|no`, Exit-Codes | `main(argv)`: alles grün Exit 0 und `thermo: no`, ein Mangel Exit 1, Datei über Grenze `thermo: yes` | - |
| r1 | b3 | `--pack <Manifest>`: Nachlade-Quote und Paketabschnitte ohne Nutzungshinweis | `reload_report(manifest, scans)`: Abschnitt außerhalb des Pakets gelesen zählt als Nachladen, Paketabschnitt Stufe C wird gemeldet | - |
| r2 | b3 | Zerleger-Parität mit `context-pack.py` | `chunk_markdown(...)` in beiden Skripten: dieselben Abschnitt-IDs für denselben Text | - |
| c1 | b3 | `ref-check.py`: Pfade in Backticks in Anweisungsdateien auf Existenz prüfen | `check_file(path, root)`: vorhandener Pfad ok, fehlender Pfad gemeldet mit Zeile, URL und Platzhalter übersprungen | - |
| t1 | b4 | `execute-plan`: Paket je Block statt Handbündel, Budgets und Stall-Regel, Gates je Stufe | n/a: text | - |
| t2 | b4 | `review-changes`: Vorlauf vor dem Modell-Review, gemeinsame Fix-Runde und ein Nachtrags-Lauf | n/a: text | - |
| t3 | b4 | `plan-build` Ritual je Stufe, `thermo`, `retro`, `config-sync` mit Auslöser | n/a: text | - |
| t4 | b4 | `maxTurns` in den Agentendateien | n/a: text | - |
| t5 | b4 | `LOOP.md` und README beschreiben den neuen Ablauf | n/a: text | - |

## Order

p1, p2, p3 und g1, g2, g3 und r1, r2, c1 laufen parallel in Welle 1. Die Texte (t1 bis t5) folgen in Welle 2, weil sie das tatsächliche Verhalten der Skripte beschreiben.

## Waves

- **Welle 1:** b1, b2, b3. Dateibereiche getrennt (`execute-plan/scripts`, `review-changes/scripts`, `retro/scripts` mit `config-sync/scripts`).
- **Welle 2:** b4. Eigene Welle, weil sie fünf Skills und `agents/` berührt und das Verhalten der Skripte aus Welle 1 kennen muss.

## Tests

Alle Skripte über ihre öffentlichen Funktionen und als Unterprozess gegen synthetische Projekte im Temp-Ordner (neutrale Namen, kein Netz).
- `context-pack.py`: gleiche Eingabe liefert gleichen Hash, jedes Fach (Subagenten-Abschnitt, Bereichsregel, Pfadregel, Spec-Abschnitt, Glossar) hat einen Fall mit Treffer und einen ohne, ein absichtlich fehlender Glossarbegriff erscheint im Manifest, zu großes Paket gibt Exit 3 ohne Datei.
- `gate-precheck.py`: je Prüfung ein grüner und ein roter Fall im synthetischen Git-Repo, Schwelle der Dateigröße knapp darunter, genau darauf, knapp darüber, `thermo: yes` nur beim Überschreiten.
- `context-usage.py --pack`: Nachladen und Überversorgung an einem synthetischen Transkript.
- `ref-check.py`: vorhandene, fehlende, URL- und Platzhalter-Pfade.
- Zerleger-Parität: eine Test-Datei lädt beide Skripte und vergleicht die IDs.

## Verification

- `python3 -I -m unittest discover -s skills/execute-plan/scripts -p 'test_*.py'`
- `python3 -I -m unittest discover -s skills/review-changes/scripts -p 'test_*.py'`
- `python3 -I -m unittest discover -s skills/retro/scripts -p 'test_*.py'`
- `python3 -I -m unittest discover -s skills/config-sync/scripts -p 'test_*.py'`
- `python3 -I -m unittest discover -s skills/planning/scripts -p 'test_*.py'`
- `python3 -I skills/planning/scripts/plan-check.py lint .claude/plans/umstellung-4-paket-gates.md --depth voll`
- `grep` auf Projektnamen, Pfade und Geviertstriche im Diff

## Gate 4

- [ ] Alle Tests grün
- [ ] `plan-check.py lint` über diesen Plan ist grün (erster Einsatz im neuen Format)
- [ ] `context-pack.py`: gleiche Eingabe gleicher Hash, absichtlich fehlender Kontext steht im Manifest (Probelauf)
- [ ] `gate-precheck.py` an einem echten Diff der Repos: fängt einen eingebauten Mangel
- [ ] Zerleger-Parität grün
- [ ] `grep`: keine Projektnamen, Pfade oder Geviertstriche
- [ ] Läuft im Pilot mit: Hauptsitzung liest in den ersten Turns weniger Dateien als der Basiswert, eine Stufe-M-Phase mit parallelen Gates, Kalenderzeit des Gate-Abschnitts unter dem Basiswert, Nachlade-Quote an einem echten Paket

## Out of scope

Zitierpflicht (entscheidet Phase 5 nach der Nachlade-Quote), Löschen von Kontext nach Zahlen, MemPalace, automatisches Starten von `handlauf` durch den Koordinator, Umbau der Wellenlogik, Dollar-Beträge, Änderungen an der globalen `CLAUDE.md` des Nutzers.

## Risks

- `maxTurns` kann einen Block mitten in der Arbeit beenden. Die Commits bleiben, der Block geht als unvollständig zurück an den Koordinator. Die Startwerte sind bewusst großzügig.
- Parallele Gates können Arbeit verschwenden, wenn der Handlauf ein Designproblem findet. Deshalb nur bei S und M.
- Das Paket kann Kontext verfehlen. Das Manifest macht das sichtbar, die Nachlade-Quote misst es, die Zitierpflicht bleibt als Rückfall offen.
