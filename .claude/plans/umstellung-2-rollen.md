# Plan: Phase 2 Rollen, Startlast, Laufzustand, Auslauf

Rahmenplan: `umstellung-kosten.md`. Planungstiefe **Standard** (mehrere Bereiche: Agenten, Hooks, Skill-Texte, README; kein Schema, kein Sicherheitsbezug). Branch `umstellung/2-rollen`, Status 🔄 (freigegeben, im Bau).

## Kontext und Ziel

Subagenten starten mit rund 41.000 Tokens Kontext statt 5.000 bis 7.000, und eine Sitzung, die zu voll wird, wird kompaktiert und verliert Detail. Phase 2 senkt die Startlast mit Rollen und ersetzt die Kompaktierung durch den Auslauf (Laufzustand, Hook, Übergabe).

## Belegte Grundlagen (Doku, Zusammenfassung, vor dem Bau im Wortlaut prüfen)

- `PreToolUse` greift für `Agent` und kann mit `permissionDecision: "deny"` verweigern. Ein Alias `Task` ist nicht dokumentiert.
- Hook-Eingabe: `session_id`, `transcript_path`, `cwd`, `hook_event_name`. In Subagenten feuern dieselben Hooks, die Eingabe trägt `agent_id` und `agent_type`. Die Hauptsitzung hat keine `agent_id`.
- `PostToolUse` kann Kontext nur über `hookSpecificOutput.additionalContext` einspeisen, nicht über Klartext. `UserPromptSubmit` und `SessionStart` nehmen Klartext. Grenze 10.000 Zeichen.
- Das Fenster steht **nicht** in der Hook-Eingabe, nur in der Statusleisten-Eingabe. Opus 5.5 läuft laut Doku mit 1 Mio. (fällt unter "Opus 4.7 and later", nicht ausdrücklich genannt).
- Nicht belegt, im Gate geprüft: `transcript_path` in Subagenten-Hooks, Nutzlast von `UserPromptSubmit`.

## Entscheidungen

| Frage | Antwort | Grund |
|---|---|---|
| Fenstergröße | Standard 1.000.000, überschreibbar in `.claude/auslauf.json` (`fenster`) | Hook bekommt sie nicht geliefert, die Doku nennt 1 Mio. für diese Modelle |
| Füllung | Tokens der letzten Antwort der Hauptsitzung (Eingabe plus Cache) aus `transcript_path`, geteilt durch das Fenster | Dieselbe Rechnung wie in der Messung |
| Schwellen | Auslauf bei 0,6, Notbremse bei 0,8, alles in `.claude/auslauf.json` | Rahmenplan, nach Pilotdaten nachzujustieren |
| Hauptsitzung oder Subagent | Hook handelt nur ohne `agent_id` | Subagenten haben ihr eigenes kleines Fenster |
| Marke | `.claude/run/auslauf-<session_id>`, flüchtig, nicht committet | Mehrere Sitzungen im Repo stören sich nicht |
| Was bei Auslauf noch starten darf | Ein `Agent`-Aufruf, dessen Auftrag eine Block-ID enthält, die im Laufzustand mit Status `laufend` steht (Review, Fix) | Angefangene Blöcke laufen zu Ende, nichts Neues beginnt |
| Laufzustand | `.claude/run/<phase>.md`, eine Tabelle `Block, Status, Statuscode, Fix-Runden, Worktree`, dazu Kopfzeilen für Phasen-Branch, Plan und Pfad des Regelbündels | Maschinenlesbar für den Hook, lesbar für den Menschen |
| Regelbündel | Liegt künftig in `.claude/run/` statt im Scratchpad | Übersteht den Sitzungswechsel |
| Rollen | `block-implementer`, `block-reviewer` (liegen vor), neu `block-fixer`, `gate-reviewer` | Rahmenplan |
| Rückfall | Fehlt eine Rolle, startet `execute-plan` `general-purpose` mit explizitem `model` und demselben Bündel | Neue Agentendateien erscheinen erst nach Sitzungsneustart |
| Status des Auslaufs für den Nutzer | Hook gibt beim ersten Überschreiten einmal Text aus (Anweisung: nichts Neues starten, Endschritt, Laufzustand, `session-recap`, neue Sitzung) | `UserPromptSubmit` nimmt Klartext, `PostToolUse` nur `additionalContext` |
| Limit-Auslöser | Nicht in dieser Phase | Die Quelle (Statusleiste) ist Umgebungssache, nicht Toolkit. Nur ein optionaler Hinweis in der README |

## Blöcke und Wellen

Alle drei Blöcke haben disjunkte Dateien und laufen in **einer** Welle.

**b1: Hooks** (`skills/project-init/hooks/auslauf.py`, `test_auslauf.py`, `skills/project-init/hooks/session-state.py`, `test_session_state.py` falls vorhanden sonst neu)
- t1 `auslauf.py`: Funktionen `fill(transcript_path, fenster)`, `read_config(project_dir)`, `running_blocks(run_dir)`, `decide(event, ...)`. Ereignisse: `UserPromptSubmit` und `PostToolUse` (Messung, Marke anlegen, Anweisung ausgeben, bei Notbremse stärkere Anweisung), `PreToolUse` mit Matcher `Agent` (verweigern, wenn Marke da und keine laufende Block-ID im Auftrag). Fehler im Hook blockieren nie (`|| true`, Rückgabe leer).
- t2 `session-state.py` hängt eine Kurzfassung des Laufzustands an (Phase, Blöcke und Status, Hinweis "Weitermachen mit execute-plan Schritt 0").
- t3 Registrierungsbeispiel in der Docstring von `auslauf.py`, wie bei `session-state.py`.

**b2: Rollen** (`agents/block-fixer.md`, `agents/gate-reviewer.md`, kleine Anpassung `block-implementer.md`)
- t4 `block-fixer`: Sonnet, Werkzeuge wie der Implementierer, Auftrag: Fund wörtlich, roter Test am alten Code, ein Fix-Commit, Statuscode.
- t5 `gate-reviewer`: starkes Modell, nur lesende Werkzeuge, Auftrag: Diff der ganzen Phase gegen Plan und Bündel, Befund nur mit Beleg.
- t6 `block-implementer`: Regel "Dateien einzeln `git add`en, nie `git add -A`" aus dem Rollentest.

**b3: Skill-Texte** (`skills/execute-plan/SKILL.md`, `skills/session-recap/SKILL.md`, `skills/project-init/SKILL.md` mit Vorlage, `README.md`)
- t7 `execute-plan`: Schritt 0 (Laufzustand lesen und mit `git worktree list` abgleichen), Laufzustand schreiben nach jedem Übergang, Bündel in `.claude/run/`, Rollen beim Namen, Rückfall, `## Für Subagenten` ins Bündel kopieren, Auslauf-Abschnitt (was "Endschritt" heißt, nicht neu starten).
- t8 `session-recap`: Abschnitt "Auslauf": wann er läuft, dass er Laufzustand und Übergabe schreibt und die neue Sitzung ankündigt.
- t9 `project-init`: Abschnitt `## Für Subagenten` in der Vorlage der Projekt-`CLAUDE.md`, Hook-Registrierung für `auslauf.py`, `.gitignore`-Eintrag `.claude/run/`, Empfehlung `enabledPlugins` je Projekt.
- t10 `README`: Installationsschritt für `agents/` (Kopie nach `~/.claude/agents/`), Auslauf in einem Absatz, Skill-Tabelle.

Danach durch den Koordinator: t11 Probeläufe (Gate 2).

## Tests (Schnittstellen)

`auslauf.py` über ihre Funktionen **und** als Unterprozess mit JSON auf stdin gegen ein synthetisches Projekt im Temp-Ordner.
- `fill`: Transkript mit bekannten Tokenwerten gibt den erwarteten Anteil, mehrere Zeilen derselben `message.id` zählen einmal, leeres oder fehlendes Transkript gibt 0.
- Schwellen: knapp unter, genau auf, knapp über 0,6 und 0,8.
- Marke: wird einmal angelegt, die Anweisung erscheint nur beim ersten Überschreiten, nicht bei jedem Aufruf.
- `PreToolUse` mit Marke: Auftrag ohne Block-ID wird verweigert, Auftrag mit der ID eines laufenden Blocks darf, mit der ID eines gemergten Blocks wird verweigert.
- Mit `agent_id` in der Eingabe passiert nichts (Subagent).
- Kaputte Konfiguration, fehlender Laufzustand, Ordner ohne Schreibrecht: Ausgabe leer, Exit 0.
- `session-state.py`: Kurzfassung erscheint bei vorhandenem Laufzustand, fehlt sie, bleibt die Ausgabe unverändert.

Rollen und Skill-Texte werden nicht per Unit-Test geprüft, sondern in Gate 2.

## Gate 2 (durch den Koordinator)

- [ ] Alle Tests grün
- [ ] **Hook-Probe:** `PreToolUse` auf `Agent` verweigert in einer echten Sitzung (mit künstlich niedriger Schwelle) einen neuen Start und lässt einen laufenden Block durch. Dabei werden auch `agent_id` und `transcript_path` aus der Eingabe protokolliert (offene Punkte der Recherche).
- [ ] **Füllung stimmt** mit dem Wert der Statusleiste überein (Stichprobe), sonst Fenster oder Rechnung anpassen
- [ ] **Startlast:** erster Aufruf jeder neuen Rolle höchstens 8.000 Tokens, gemessen mit `context-usage.py`
- [ ] **Katalog-Test:** erscheint der Skill-Katalog, wenn `Skill` in der Werkzeugliste einer Rolle steht? Ergebnis in der README
- [ ] **Rückfall:** fehlt eine Rolle, läuft `execute-plan` mit `general-purpose` durch (Probelauf mit umbenannter Datei)
- [ ] **Wiederaufnahme:** eine neue Sitzung macht an einem angelegten Laufzustand weiter, ohne einen Block doppelt zu bauen
- [ ] **Vergleichslauf** an einem echten Block des Pilotprojekts 1 mit Rollen, gemessen mit `session-cost.py`: Funde im Phasen-Review nicht höher als der Basiswert (braucht dich, weil es eine echte Phase ist)
- [ ] `grep`: keine Projektnamen, Pfade oder Geviertstriche in Dateien und Commits

## Prüfung während des Baus

Stufe S: Tests und `grep`, kein Review-Lauf (entschieden). `thermo` nicht, keine Oberfläche, kein `handlauf`.

## Out of scope

Limit-Auslöser über die Statusleiste, Kontextpaket-Builder (Phase 4), Plan-Lint und Stufen (Phase 3), Parallel-Gates, Budgets, Änderungen an der globalen `CLAUDE.md` des Nutzers (nur Textvorschlag), Dollar-Beträge.

## Risiken

- Verweigern per Hook ist in der Doku nur allgemein belegt. Die Hook-Probe in Gate 2 entscheidet. Fällt sie negativ aus, bleibt der Auslauf eine Anweisung im Text und `execute-plan` prüft die Marke selbst vor jedem Start.
- Die 1-Mio.-Annahme kann falsch sein. Die Stichprobe gegen die Statusleiste fängt das.
- Neue Agentendateien erscheinen erst nach Sitzungsneustart. Der Rückfall deckt das ab.
