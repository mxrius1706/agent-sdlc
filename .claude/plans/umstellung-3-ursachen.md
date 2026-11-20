# Plan: Phase 3 Ursachen-Hebel

Rahmenplan: `umstellung-kosten.md`. Planungstiefe **Standard** (Skripte plus mehrere Skill-Texte, kein Schema, kein Sicherheitsbezug). Branch `umstellung/3-ursachen`, Status 🔄 (freigegeben, im Bau).

## Kontext und Ziel

Fixen kostet den größten Block der Bauzeit. Die Ursache liegt meist vor dem Bauen: Pläne mit überlappenden Dateien, Aufgaben ohne Testziel, Spec-Anforderungen ohne Aufgabe, Tests, die aus dem Code statt aus der Spec entstehen. Phase 3 prüft den Plan mechanisch, bevor gebaut wird, legt Planungstiefe und Prozessstufe per Skript fest, schreibt Abnahmetests vor dem Block und lässt `retro` jeden Fund bis zur frühesten vermeidbaren Stelle zurückverfolgen.

Ziel: `plan-check.py` prüft, stuft und bemisst Pläne deterministisch. `planning` und `execute-plan` benutzen es. Die Fix-Quote ist Pflichtzahl der Retro.

## Entscheidungen

| Frage | Antwort | Grund |
|---|---|---|
| Plan als Struktur | `planning` schreibt Blöcke und Aufgaben als **Tabellen** mit festen Spaltennamen, damit ein Skript sie liest. Das übrige bleibt Prosa | Struktur ist das, was der Plan-Lint prüfen kann (entschieden im Rahmenplan) |
| Ein Skript, drei Unterbefehle | `plan-check.py` mit `lint`, `stage`, `depth`. Das ist eine Abweichung vom Rahmenplan (drei Dateien) | Gemeinsamer Tabellenleser, kein Import zwischen Skripten nötig (`python3 -I` nimmt das Skriptverzeichnis nicht in den Suchpfad) |
| Abnahmetests | Neue Rolle `acceptance-writer` ab Stufe M, schreibt rote Tests aus den Anforderungen des Blocks, der Implementierer darf sie nicht ändern. Stufe S: Implementierer schreibt selbst | Entscheidung des Nutzers. Tests entstehen aus der Spec, nicht aus dem Code |
| Plan-Lint-Schleife | Verstöße gehen höchstens zweimal an die Planung zurück, danach an den Nutzer | Vorbild aus dem Geschichtenfluss |
| Anforderungsformat | Kennungen wie in `write-spec`: `REQ-`, `SEC-`, `CON-`, `GUD-`, `PAT-`, `AC-` plus Nummer. Das Muster ist per Option überschreibbar | Das Format steht schon im Baukasten |
| Stufenregel | Startwerte unten, pro Projekt über eine Zeile in `Project references` überschreibbar. Die Stufe kann nie unter der Planungstiefe liegen (Mini kann S, Standard kann M, Voll kann L) | Rahmenplan |
| Kalibrierung der Schwellen | Erst im Pilot an echten Daten. Bis dahin Startwerte | Daten fehlen noch |

## Tabellenformat im Plan (Vertrag für `planning`, `execute-plan` und `plan-check.py`)

Spaltennamen englisch, Groß- und Kleinschreibung egal, Reihenfolge egal, Zusatzspalten erlaubt. Pfade kommagetrennt, ein Verzeichnis gilt für alles darunter.

```markdown
| Block | Tasks | Files | Wave | Exclusive |
|---|---|---|---|---|
| b1 | a1, a2, a3 | skills/x/, tests/x/ | 1 | no |

| Id | Block | Task | Test target (seam) | Requirements |
|---|---|---|---|---|
| a1 | b1 | Parser für X | `parse()`: Fehlerfall leer | REQ-001, AC-002 |
```

Eine Aufgabe ohne Verhalten (reiner Text) trägt in `Test target` den Wert `n/a: text`. `Exclusive` ist `yes` für Schema, Compose, laufenden Stack und die exklusiven Bereiche des Projekts.

## Kommandozeile (Vertrag)

```
plan-check.py lint  <plan.md> [--depth mini|standard|voll] [--specs <Datei-oder-Ordner> ...] [--req-pattern <regex>]
plan-check.py stage <plan.md> [--depth mini|standard|voll] [--limits k=v,...] [--schema-paths <regex>] [--security-paths <regex>]
plan-check.py depth --areas N --spec-sources N --gate-points N --files N [--flag schema|exclusive|security|dependency|nopattern ...] [--limits k=v,...]
```

Ausgabe: Zeilen `<Regel-ID> <Ort>: <Satz>` bei `lint`, Exit 1 bei Verstößen, sonst 0. `stage` und `depth` geben genau ein Wort (`S|M|L`, `mini|standard|voll`) in der ersten Zeile aus, danach die Gründe, Exit 0. Ein Fehler in der Eingabe (Datei fehlt, Tabelle fehlt) ist Exit 2 mit einem Satz.

**Lint-Regeln** (Startwerte):
- `L1` Pflichtabschnitte fehlen. Mini: Context, Goal, Blocks, Tasks, Tests, Verification, Out of scope. Standard und Voll zusätzlich Decisions, Critical files, Order, Waves.
- `L2` Out of scope leer oder nur ein Platzhalter.
- `L3` Block ohne Aufgaben oder ohne Dateien. Block mit einer Aufgabe nur bei `Exclusive` = yes. Mehr als 6 Aufgaben ist ein Verstoß.
- `L4` Eine Welle mit mehr als 3 Blöcken, ein Block in keiner Welle, oder zwei Blöcke einer Welle mit überlappenden Dateien (gleicher Pfad oder einer liegt unter dem anderen). Ein exklusiver Block teilt seine Welle mit keinem anderen.
- `L5` Aufgabe ohne Test target, oder Test target ohne Schnittstelle (leer oder ohne Backticks und ohne `n/a: text`).
- `L6` Mit `--specs`: eine Anforderungskennung der Specs steht weder in einer Aufgabe noch im Abschnitt Out of scope.
- `L7` Verification enthält keinen Befehl in Backticks.
- `L8` Decisions-Tabelle (ab Standard) mit leerer Begründungsspalte.

**Stufe** (`stage`): **L** bei einem exklusiven Block, bei einer Datei im Schema- oder Sicherheitsmuster oder bei mehr als 25 Dateien. **S** bei höchstens 5 Dateien, einem Block und ohne Flag. Sonst **M**. Danach die Untergrenze aus `--depth`.

**Tiefe** (`depth`): **mini** bei höchstens 1 Bereich, 1 Spec-Quelle, 3 Gate-Punkten, 5 Dateien und ohne Flag. **standard** bei höchstens 3 Bereichen und ohne Flag `schema` oder `security`. Sonst **voll**. Ein Flag `exclusive`, `dependency` oder `nopattern` hebt auf mindestens standard.

## Blöcke und Wellen

Zwei Blöcke, disjunkte Dateien, **eine** Welle.

**b1: Skript** (`skills/planning/scripts/plan-check.py`, `skills/planning/scripts/test_plan_check.py`)
- a1 Tabellenleser und `lint` mit den Regeln L1 bis L8.
- a2 `stage`.
- a3 `depth` mit `--limits`.

**b2: Rolle und Texte** (`agents/acceptance-writer.md`, `skills/planning/SKILL.md`, `skills/execute-plan/SKILL.md`, `skills/retro/SKILL.md`, `skills/project-init/SKILL.md`, `README.md`)
- a4 `acceptance-writer`: Sonnet, Werkzeuge wie der Implementierer ohne `Skill`, schreibt aus den Anforderungen des Blocks rote Tests (nur Tests, kein Produktionscode), zitiert den roten Lauf, ein Commit, Statuscode.
- a5 `planning`: Tabellenformat statt freier Blöcke und Aufgaben, Phase 0 endet mit `plan-check.py depth` (Tiefe laut Skript, Nutzer bestätigt), vor der Freigabe `plan-check.py lint` und `stage` (höchstens zwei Rückläufe, Stufe steht im Plan), Abschnitt Tests verlangt je Anforderung einen Testfall mit Schnittstelle. Die Regel steht nur im Skript, der Text verweist darauf.
- a6 `execute-plan`: Schritt 1 liest die Stufe aus dem Plan. Ab Stufe M startet je Block zuerst `acceptance-writer`, dann `block-implementer` mit der Anweisung, die Abnahmetests nicht zu ändern. Block-Funde mehrerer Blöcke werden nach Muster gebündelt (gleiche Regel oder Ursache), und ein Fixer bekommt ein Bündel mit allen wörtlichen Funden statt je einen Auftrag.
- a7 `retro`: Ursachenleiter (an welcher Stelle war der Fund am frühesten vermeidbar: Spec, Plan, Auftrag, Werkzeug, Review). Eine Reviewer-Regel erst, wenn nichts weiter vorne greift. Fix-Quote als Pflichtzahl im Bericht, Quelle `session-cost.py --roles`.
- a8 `project-init`: Vorlage `.gitignore` mit `__pycache__/` und Build-Artefakten. `README`: Zeile zu `plan-check.py` und `acceptance-writer`.

## Tests (Schnittstellen)

`plan-check.py` über ihre Funktionen und als Unterprozess gegen synthetische Pläne im Temp-Ordner.
- Je Lint-Regel ein Plan, der genau diesen Verstoß enthält, und ein sauberer Plan ohne Verstoß. **Ein Plan mit sechs eingebauten Fehlern wird vollständig gefunden.**
- Welle: überlappende Dateien (gleicher Pfad, Eltern und Kind), disjunkte Dateien, exklusiver Block in Gemeinschaft, vierter Block in einer Welle.
- Anforderungsabdeckung: Spec-Ordner mit drei Kennungen, eine fehlt im Plan, eine steht in Out of scope (zulässig).
- `stage`: je Stufe ein Fall, knapp unter, genau auf, knapp über 5 und 25 Dateien, Untergrenze aus `--depth`.
- `depth`: dasselbe an den Schwellen, jede Flagge, `--limits` überschreibt.
- Determinismus: dieselbe Eingabe, dieselbe Ausgabe. Kaputte Tabelle und fehlende Datei geben Exit 2.

Rolle und Skill-Texte: keine Unit-Tests, Gate 3.

## Gate 3

- [ ] Alle Tests grün (Hooks, Messskripte, `plan-check`)
- [ ] `lint` findet in einem synthetischen Plan mit sechs eingebauten Fehlern alle sechs
- [ ] `stage` und `depth` sind deterministisch und haben Tests an jeder Schwelle
- [ ] Die Pläne der Phasen 1 und 2 (freie Form) werden mit klarer Meldung (Exit 2) abgewiesen, nicht mit einem Absturz
- [ ] `acceptance-writer` im Probelauf an einem kleinen Block: roter Lauf zitiert, nur Testdateien im Commit, Startlast höchstens 8.000 Tokens
- [ ] Phase 4 wird nach dem neuen Format geplant und mit `lint` geprüft (Probe am echten Einsatz)
- [ ] `grep`: keine Projektnamen, Pfade oder Geviertstriche
- [ ] Läuft im Pilot mit: eine echte Phase im neuen Ablauf, Fix-Quote unter dem Basiswert

## Prüfung während des Baus

Stufe S: Tests und `grep`, kein Review-Lauf. Kein `thermo`, kein `handlauf`.

## Out of scope

Kontextpaket-Builder und `gate-precheck.py` (Phase 4), parallele Gates, Budgets, Umbau bestehender Pläne auf das Tabellenformat, Kalibrierung der Schwellen an Pilotdaten (Pilot), Dollar-Beträge, Änderungen an der globalen `CLAUDE.md` des Nutzers.

## Risiken

- Plan-Lint gegen freie Pläne: Wer Tabellen weglässt, bekommt Exit 2, keinen stillen Durchlauf. Das ist gewollt.
- `acceptance-writer` kann Tests schreiben, die zu eng am erwarteten Code kleben. Der Block-Review prüft sie gegen die Spec, der Probelauf prüft den Anfang.
- Zusätzlicher Auftrag je Block ab Stufe M kostet Zeit. Der Pilot misst, ob die gesparten Fix-Runden ihn tragen, sonst wird er zur Option.
