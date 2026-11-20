# Plan: Umstellung auf Ursachen statt Prüfung, schlanke Rollen, deterministischen Kontext

Status: Entwurf zur Freigabe. Gilt als Rahmenplan. Jede Phase bekommt vor ihrem Bau einen eigenen Detailplan nach `planning` (Details früh zu entscheiden heißt, sie mit der wenigsten Information zu entscheiden).

## Kontext

Der Ablauf des Baukastens ist zu langsam und zu teuer. Messungen an zwei Pilotprojekten (Transkripte, mit `skills/retro/scripts/session-cost.py`):

- **Kalenderzeit ist Limit-Zeit.** Eine Bauphase spannte 37 Stunden bei rund 6 Stunden aktiver Hauptsitzung. Rund die Hälfte der Lücken folgt direkt auf eine "5-hour limit"-Meldung. Weniger Tokens bedeuten also kürzere Laufzeit.
- **Fixen kostet mehr als Prüfen.** Fix- und Umbauminuten lagen bei 46 % bis 75 % der Bauminuten. Die Opus-Gate-Reviews sind nur rund 18 % der Ausgabe-Tokens der Subagenten, Bauen allein rund 45 %.
- **Startlast.** Fast jeder Subagent ist `general-purpose` und startet mit 37.000 bis 49.000 Tokens Kontext (Skill-Katalog, Anweisungen, Werkzeug- und Agentenliste). Eigene Agentendefinitionen starten mit 5.000 bis 7.000 (Messung, Rollentest). Ein Block mit der Rolle lief fehlerfrei, der Reviewer in Rolle fand einen echten Fehler.
- **Prüfung kommt zu spät.** Ein Vorbild aus einem Pilotprojekt: Plan als Struktur, feste Regeln per Code vor dem Schreiben prüfen, höchstens zweimal zurück an den Planer. "Ausbessern danach gelang nie."

Referenzen (Ideen, kein Code übernommen): coleam00/ai-software-factory (Prüftiefe nach Risiko, Szenariofilter, Kontext als Datei, Evidenz-Gates), superplanehq/superplane (Ungeeignetes vor dem Lauf zurückgeben, fokussierter Kontext zwischen Versuchen, Median Tokens je abgeschlossenem Task), SWE-AF und loki-mode (Modell je Rolle, Budgets).

## Ziel

Pro Bauphase: weniger Fix-Runden, weniger Startkontext je Subagent, kein Warten auf Limits durch Verschwendung, und ein Kontextpaket, das ein Skript aus Plan und Vault baut statt das Modell suchen zu lassen. Belegt durch dieselben Messzahlen wie oben, vorher und nachher.

## Entscheidungen

| Frage | Antwort | Grund |
|---|---|---|
| Wo setzen wir an? | Ursache vor Prüfung: Plan-Lint, Abnahmetests vor dem Block, Fehlerklassen unmöglich machen | Fixen ist der größte Posten |
| Subagenten | Eigene Agentendefinitionen je Rolle in `agents/` mit `omitClaudeMd`, schmalen Werkzeugen, festem Modell | Startlast sinkt um rund 85 % (gemessen) |
| Regeln für Subagenten | Abschnitt `## Für Subagenten` in globaler und Projekt-`CLAUDE.md`, der Builder kopiert ihn wörtlich ins Regelbündel | Eine Wahrheit, Auswahl pro Regel beim Nutzer (entschieden) |
| Stufen S/M/L | Skript schlägt aus harten Kriterien vor, der Nutzer bestätigt bei der Freigabe, Absenken nur mit Begründung | Kontrolle bleibt, Vorschlag kostet nichts (entschieden) |
| Kontext-Tracking | Zuerst nachträglich aus Transkripten, Beweisstufen A (Beleg), B (Indiz), C (unbekannt). Gelöscht wird nie nach Statistik allein, die Ablation bestätigt | "Geladen" ist nicht "gebraucht" |
| Zitierpflicht ("Angewandt: IDs") | Nur falls Stufe B nicht trägt, entscheidet Phase 4 | Erst messen, dann den Prozess ändern |
| Gates | Parallel nur bei Stufe S und M, bei L bleibt die Reihenfolge. Eine gemeinsame Fix-Runde, höchstens zwei Gate-Runden | Zeit sparen ohne die Tiefe bei L zu senken |
| Planungstiefe | Ein Skript `plan-depth.py` schlägt Mini, Standard oder Voll vor, aus Zahl der Spec-Quellen, Bereiche, Gate-Punkte, kritischen Dateien und Flags (Schema, exklusive Bereiche, Sicherheitsbezug, neue Abhängigkeit, kein Muster im Code). Du bestätigst. Schwellen: Standardwerte im Skript, pro Projekt über eine Zeile in `Project references` überschreibbar, an den Pilotdaten kalibriert. Die Prozessstufe nach dem Plan kann nur höher sein als die Tiefe | Ein Detailplan nur dort, wo er sich lohnt, und die Regel steht an einer Stelle (entschieden) |
| Pilot | Zuerst Pilotprojekt 1 (kleiner Test), danach Pilotprojekt 2 (entschieden) | Erst klein belegen |
| MemPalace | Geparkt: nach Phase 3, schreibgeschützter Suchindex, Vergleich mit `rg` an etwa zehn echten Fragen | Löst Wiederfinden, nicht Kosten |
| Sitzungswechsel | Nie kompaktieren. **Auslauf** statt Kompaktierung: ab 60 % Kontextfüllung keine neuen Starts, alles Laufende läuft bis zum logischen Endschritt zu Ende, dann Laufzustand und Übergabe, dann Ende der Arbeit. Dieselbe Prozedur bei 85 % des 5-Stunden-Limits und von Hand | Die Spitzen lagen bei Median 49 %, 7 von 22 Sitzungen über 60 %, 5 wurden kompaktiert. Kompaktierung verliert Detail, Auslauf nicht (entschieden) |
| Kontowechsel | Keine eigene Logik im Toolkit. Der Auslauf macht jede Sitzung wiederaufnehmbar, die Umgebung wählt das Konto | Ein Wechsel ist ein Neustart mit Übergabe, mehr nicht |
| Öffentliches Repo | Keine Namen, Pfade oder Zahlen mit Projektbezug in Dateien, Tests oder Commits. Testdaten synthetisch (`projekt-a`) | Regel des Baukastens |

## Bauphasen

Ordnungsprinzip: **erst messen, dann die größten Hebel, dann alles, was Messung oder Rollen voraussetzt.**

### Phase 1: Messen (Grundlage) ⬜
Branch `umstellung/1-messen`. Startet nach: nichts, liefert die Eingaben aller anderen. Planungstiefe: **Mini** (Tabelle aus Phase 3, bis dahin von Hand angewandt).
- `skills/retro/scripts/session-cost.py` committen (liegt unversioniert) und um Rollenzuordnung (`--roles`), Limit-Lücken (`--gaps`) und Fix-Quote je Phase erweitern. Die Rollenzuordnung und die Lücken-Erkennung liegen fertig, getestet und vom Reviewer freigegeben auf dem Testbranch `rollentest-b` (Commits `77fa274`, `a4fe569`) und werden daraus übernommen. `.gitignore` bekommt `__pycache__/`.
- Neuer Tracker `skills/retro/scripts/context-usage.py`: Dateien in Abschnitte nach Überschriften-Pfad zerlegen (stabile ID, Hash), aus Transkripten Lesezugriffe über Read **und** Bash (`cat`, `sed -n`, `rg`) und Obsidian-MCP zuordnen, je Abschnitt Ladungen, Sitzungen, Phasen, Beweisstufe ausgeben, Startlast je Subagent getrennt zeigen, Bericht als Nebendatei im Projekt (`.claude/context-usage.json`), nichts in den Vault-Dateien.
- `retro` liest den Bericht (neue Quelle, neue Kategorie "Kontextballast").

**Gate 1**
- [ ] `python3 -I -m unittest discover -s skills/retro/scripts -p 'test_*.py'` grün
- [ ] `session-cost.py --roles` und `--gaps` laufen auf den Transkripten beider Pilotprojekte ohne Fehler
- [ ] `context-usage.py` liefert für ein Pilotprojekt einen Bericht, in dem mindestens 5 Abschnitte mit Beweisstufe A oder B stehen
- [ ] Die Fix-Quote der zwei letzten Phasen beider Pilotprojekte ist als Basiswert festgehalten

### Phase 2: Rollen und Startlast ⬜
Branch `umstellung/2-rollen`. Startet nach Phase 1, weil der Vergleich die Messwerkzeuge braucht.
- `agents/block-implementer.md`, `agents/block-reviewer.md` (Entwürfe liegen vor), dazu `block-fixer` und `gate-reviewer`. Alle mit `omitClaudeMd`, schmalen Werkzeugen, festem Modell.
- `execute-plan` ruft die Rollen beim Namen auf. Fehlt eine Rolle (nicht installiert), Rückfall auf `general-purpose` mit explizitem `model` und demselben Bündel. Der Rückfall steht im Skill.
- Neue Zeilen in `execute-plan`: Dateien einzeln `git add`en, nie `git add -A` im Worktree.
- Regelbündel (Schritt 2 in `execute-plan`) liest die Abschnitte `## Für Subagenten` aus der globalen und der Projekt-`CLAUDE.md` und kopiert sie wörtlich. `project-init` legt den Abschnitt in die Vorlage der Projekt-`CLAUDE.md`. Für die globale Datei des Nutzers liefert die Phase einen Textvorschlag, geändert wird sie nur mit seiner Freigabe.
- `README`: Installationsschritt für `agents/` (Kopie nach `~/.claude/agents/`) und die Tabelle der Skills.
- Test, ob der Skill-Katalog zurückkehrt, sobald `Skill` in der Werkzeugliste steht. Plugin-Skills, die ein Projekt nicht braucht, über `enabledPlugins` je Projekt abschalten (Empfehlung in `project-init`, kein Eingriff in Nutzer-Einstellungen).
- Vergleichslauf wie der Rollentest an einem echten Block des Pilotprojekts 1, gemessen mit `session-cost.py`.
- **Laufzustand:** `execute-plan` schreibt nach jedem Übergang (versendet, Review, Fix, gemerged) eine kleine Datei `.claude/run/<phase>.md`: Phasen-Branch, Plan, Blocktabelle (Status, letzter Statuscode, Fix-Runden, Worktree), Pfad des Regelbündels. Nicht committet (flüchtig, `.gitignore`). Das Regelbündel liegt dort statt im Scratchpad der Sitzung. Schritt 0 von `execute-plan`: findet er einen Laufzustand, gleicht er ihn mit `git worktree list` und den Block-Branches ab und macht an der bekannten Stelle weiter. `session-state.py` hängt eine Kurzfassung an Fahrplan und Übergabe.
- **Auslauf** (löst die Kompaktierung ab), Eigentümer ist `session-recap`:
  - Messung: Hook `auslauf.py` (PostToolUse, UserPromptSubmit) liest `transcript_path` aus der Hook-Eingabe, nimmt die Tokens der letzten Antwort (Eingabe plus Cache) und teilt durch das Fenster aus `.claude/auslauf.json` (`fenster`, `kontext` = 0,6, `limit` = 0,85, `notbremse` = 0,8).
  - Beim ersten Überschreiten legt er `.claude/run/auslauf` an und gibt einmal die Anweisung aus. Ein `PreToolUse`-Hook auf `Agent` verweigert danach neue Starts, **außer** für einen Block, der im Laufzustand als laufend steht (sein Review, sein Fix). Eine Anweisung ist eine Bitte, der Hook ist hart.
  - Endschritt: bei `execute-plan` ist ein Block fertig, wenn er gemerged ist oder nach zwei Fix-Runden als `BLOCKED` beim Nutzer liegt. Keine neue Welle, kein neuer Block. Bei Planung, Interview oder Spec-Arbeit ist es das Ende der laufenden Runde oder des laufenden Dokuments.
  - Danach: Laufzustand aktualisieren, `session-recap` schreiben (mit Verweis auf den Laufzustand), dem Nutzer sagen, dass er eine neue Sitzung startet. Die Sitzung beendet sich nicht selbst, sie hört auf zu arbeiten.
  - **Notbremse** bei 80 % Kontext, falls der Auslauf nicht rechtzeitig endet: sofort Laufzustand und Übergabe, laufende Blöcke bleiben auf ihrem letzten Commit, die nächste Sitzung setzt sie in denselben Worktree.
  - Zweiter Auslöser ist das Limit: ab 85 % des 5-Stunden-Limits dieselbe Prozedur. Die Limit-Quelle (etwa eine Datei der Statusleiste) ist optional und liegt in der Umgebungskonfiguration des Nutzers, nicht im Toolkit.

**Gate 2**
- [ ] Erster Aufruf jeder Rolle höchstens 8.000 Tokens, gemessen
- [ ] Ein echter Block läuft mit Rollen ohne mehr Funde im Phasen-Review als der Basiswert
- [ ] Fehlt eine Rolle, läuft `execute-plan` mit dem Rückfall durch (Probelauf)
- [ ] Auslauf-Probelauf mit künstlich niedriger Schwelle: der Hook verweigert einen neuen Block, lässt Review und Fix eines laufenden Blocks durch, danach liegen Laufzustand und Übergabe vor
- [ ] Wiederaufnahme: eine neue Sitzung macht am Laufzustand weiter, ohne einen Block doppelt zu bauen und ohne das Regelbündel neu zu schreiben
- [ ] Die Füllung, bei der der Auslauf greift, stimmt mit dem Wert der Statusleiste überein (Stichprobe)
- [ ] Keine Datei im Repo nennt ein Pilotprojekt

### Phase 3: Ursachen-Hebel ⬜
Branch `umstellung/3-ursachen`. Startet nach Phase 2, weil Abnahmetests und Rollen zusammen im Block laufen.
- `planning`: **Plan-Lint** `skills/planning/scripts/plan-lint.py`, vor der Freigabe verpflichtend. Prüft: Blöcke mit disjunkten Dateimengen, jede Task mit Testziel und Schnittstelle, Out of scope nicht leer, Gate-Punkte prüfbar, jede Anforderungsnummer der Spec-Quellen einer Task zugeordnet. Verstöße gehen höchstens zweimal an die Planung zurück.
- `planning`: **Stufenvorschlag** `skills/planning/scripts/plan-stage.py` (S, M, L aus Diffgröße, Schema, Sicherheitspfaden, exklusiven Bereichen), Ergebnis steht im Plan, Bestätigung bei der Freigabe.
- `planning`: **Planungstiefe** `skills/planning/scripts/plan-depth.py`, läuft nach Phase 0 (Lesen) und vor dem Schreiben. Startwerte: **Mini** bei höchstens 1 Bereich, 1 Spec-Quelle, 3 Gate-Punkten, 5 Dateien und ohne Flag (eine Seite: Ziel, Dateien, Tests mit Schnittstelle, Out of scope, offene Entscheidungen als Frage, kein Grill). **Standard** bei höchstens 3 Bereichen ohne Schema und ohne Sicherheitsbezug (voller Plan, Grill nur für markierte Entscheidungen). **Voll** darüber oder bei einem Flag (voller Plan mit Grill). Die Regel steht nur im Skript, `planning` verweist darauf. Kalibrierung an den Plänen und Review-Berichten der Pilotphasen.
- `planning` und `execute-plan`: **Abnahmetests vor dem Block.** Jeder Block beginnt mit den roten Tests aus dem Plan, der Implementierer arbeitet dagegen, der Fixer bekommt den Fund wörtlich plus roten Test (bleibt wie heute).
- `execute-plan`: Block-Funde nach Muster bündeln, bevor Fixer starten, statt einzeln zu fixen.
- `retro`: **Ursachenleiter**. Je Fund die Frage, an welcher Stelle er am frühesten vermeidbar war (Spec, Plan, Brief, Werkzeug, Review). Eine Reviewer-Regel entsteht erst, wenn nichts weiter vorne greift. Die Fix-Quote ist Pflichtkennzahl im Bericht.
- Vorlage in `project-init`: Eintrag für `__pycache__/` und Build-Artefakte in `.gitignore`.

**Gate 3**
- [ ] `plan-lint.py` erkennt in einem Testplan mit sechs eingebauten Fehlern alle sechs (synthetisch)
- [ ] `plan-stage.py` ist deterministisch (gleiche Eingabe, gleiche Ausgabe) und hat Tests für jede Stufe
- [ ] `plan-depth.py` ist deterministisch, hat Tests an jeder Schwelle (knapp darunter, genau darauf, knapp darüber) und ordnet die Pilotphasen so ein, wie die Messung es stützt
- [ ] Eine echte Phase des Pilotprojekts 1 läuft durch und die Fix-Quote liegt unter dem Basiswert

### Phase 4: Kontextpaket und Gates ⬜
Branch `umstellung/4-paket-gates`. Startet nach Phase 3, weil Plan-Lint und Stufen den Builder speisen.
- **Kontextpaket-Builder** `skills/execute-plan/scripts/context-pack.py`: aus Plan, Fahrplan-Abschnitt, Spec-Abschnitten (nach Anforderungsnummern), Bereichs-`CLAUDE.md`, Pfadregeln, Glossar (Textvergleich), Entscheidungen (Rückverweise) und `## Für Subagenten` ein Paket mit **Manifest "nicht enthalten"** bauen. Ersetzt das handgeschriebene Regelbündel, gleiche Ausgabe je Eingabe.
- Abnehmer: Implementierer (Bündel), Gate-Reviewer (Diff-Paket in `review-changes`), Hauptsitzung (`session-state.py` hängt das Manifest an den Fahrplan-Abschnitt). Unterhalb einer Größengrenze wird nichts abgeschnitten, sondern das Paket geteilt.
- **Gates:** `gate-precheck.py` (Typprüfung, Lint, Tests, Größenschwellen, Trailer, Verweisziele) vor jedem Modell-Review. Stufe S und M: `handlauf` parallel zu `review-changes` und `thermo`, eine gemeinsame Fix-Runde, ein Nachtrags-Lauf. Stufe L: Reihenfolge wie heute. `handlauf` bleibt in eigener Sitzung ohne Review-Input und geht nur durch berührte Seiten plus den Pfad ab neuen Einstiegen. `thermo`: Umbau nur bei Schwellenwert-Treffern oder auf Anforderung. `retro` und `config-sync` nur bei Anlass, der mechanische Teil von `config-sync` als Skript.
- **Budgets:** je Phase ein Token-Budget mit Warnung, `maxTurns` je Rolle, Stall-Abbruch, höchstens zwei Gate-Runden. Der Koordinator bleibt klein: Subagenten antworten nur mit Statuszeile, Berichte gehen in Dateien, das Kontextpaket senkt seine Lesezugriffe. Limit und Kontextfüllung lösen den Auslauf aus Phase 2 aus.
- **Nachlade-Quote** aus dem Tracker misst, was das Paket verfehlt. Daraus folgt die Entscheidung über die Zitierpflicht.
- `LOOP.md` beschreibt den neuen Mechanismus (Ablauf je Stufe, Paket, Gates), `README` bleibt Übersicht. Eine Wahrheit je Aussage.

**Gate 4**
- [ ] `context-pack.py`: gleiche Eingabe liefert denselben Hash, Tests für jedes Eingabefach
- [ ] Hauptsitzung liest in den ersten Turns einer Phase weniger Dateien als der Basiswert (gemessen mit `context-usage.py`)
- [ ] Eine Stufe-M-Phase läuft mit parallelen Gates durch, Kalenderzeit des Gate-Abschnitts unter dem Basiswert
- [ ] Ein absichtlich fehlender Kontext erscheint im Manifest und löst keine stille Vermutung aus (Probelauf)

### Phase 5: Pilot und Bewertung ⬜
Branch `umstellung/5-pilot`. Startet nach Phase 4.
- Erst Pilotprojekt 1, dann Pilotprojekt 2: je eine echte Bauphase nach dem neuen Ablauf. Vergleich mit den Basiswerten aus Phase 1 (Fix-Quote, Tokens je Rolle, aktive Zeit, Kalenderzeit, Funde je Gate).
- Ablation für große Kontext-Kandidaten, die der Tracker meldet (ein Block ohne den Abschnitt, Vergleich der Funde).
- Entscheidung: Zitierpflicht ja oder nein. MemPalace-Versuch (geparkt) nur starten, wenn der Builder steht und Wiederfinden ein Befund aus den Pilotphasen ist.
- `retro` über die Umstellung selbst, danach `config-sync` über die Skills und die README.

**Gate 5**
- [ ] Die Zahlen beider Pilotphasen stehen im Bericht neben den Basiswerten, ohne Projektnamen
- [ ] Jeder Hebel ist als behalten, geändert oder zurückgenommen eingetragen, mit der Messung als Grund
- [ ] Keine Datei im Repo nennt ein Pilotprojekt

## Kritische Dateien

`skills/execute-plan/SKILL.md`, `skills/review-changes/SKILL.md`, `skills/planning/SKILL.md`, `skills/plan-build/SKILL.md` (Ritual, Stufen), `skills/retro/SKILL.md`, `skills/handlauf/SKILL.md` (Umfang), `skills/thermo-nuclear-code-quality-review/SKILL.md` (Umbau-Grenze), `skills/project-init/SKILL.md` und `hooks/session-state.py`, `README.md`, `LOOP.md`. Neu: `agents/*.md`, `skills/retro/scripts/{session-cost,context-usage}.py`, `skills/planning/scripts/{plan-lint,plan-stage}.py`, `skills/execute-plan/scripts/context-pack.py`, `…/gate-precheck.py`, jeweils mit `test_*.py`. Wiederverwendet: `session-cost.py` (`read_transcript`, `secs`), `session-state.py` (`find_section`, `split_head`), das Regelbündel aus `execute-plan` Schritt 2.

## Tests und Verifikation

- Alle Skripte: `unittest` mit synthetischen Daten, Standardbibliothek, kein Netz. Befehl: `python3 -I -m unittest discover -s skills -p 'test_*.py'`.
- Jede Rolle und jeder Skill-Umbau: Vergleichslauf wie der Rollentest (gleicher Auftrag, zwei Worktrees, blinder Review), gemessen mit `session-cost.py`.
- `writing-for-agents` gilt für jeden geänderten Skill-Text: Zeilen kürzen, nichts doppelt führen, positiv formulieren.
- Vor jedem Commit: `review-changes` über den Diff, öffentliche Regel (keine Projektdaten) per `grep` gegen die Liste der Projektnamen.

## Risiken

- `omitClaudeMd` lässt Regeln still verschwinden. Gegenmittel: Bündel enthält `## Für Subagenten` als Pflichtteil, Gate 2 prüft es.
- Eigene Agenten haben nur den Text der Definition als Systemprompt. Qualität wird im Vergleichslauf geprüft, nicht angenommen.
- Neue Agentendateien werden erst beim nächsten Sitzungsstart oder Nutzer-Turn geladen. `execute-plan` nennt den Rückfall und das Neuladen.
- Parallele Gates können Arbeit verschwenden, wenn der Handlauf ein Designproblem findet. Deshalb nur Stufe S und M.
- Die Wirkung auf das Limit ist eine Hypothese (Cache-Lesen kann anders zählen). Gate 5 stützt sich auf gemessene Kalenderzeit, nicht auf die Annahme.
- Die Fenstergröße (1 Mio. oder weniger) steht nicht in den Transkripten und kommt aus der Konfiguration. Falsch gesetzt greift der Auslauf zu früh oder zu spät. Detailplan Phase 2 klärt, woher der Hook sie sicher bekommt.
- Offen und vor dem Bau zu prüfen: welche Hook-Ereignisse nach `/clear`, `--resume` und Neustart feuern, ob die Hook-Eingabe `transcript_path` zuverlässig liefert, und ob `PreToolUse` auf `Agent` greift.
- 60 % bei einem Fenster von 1 Mio. sind 600.000 Tokens je Turn. Die Kosten wachsen mit dem absoluten Kontext, deshalb ist die Schwelle konfigurierbar und wird nach den ersten Pilotphasen anhand der Messung nachjustiert.
- Messungen sind kleine Stichproben (ein Lauf je Variante). Keine Zahl gilt als Beleg, bevor sie in zwei Phasen wiederkehrt.

## Out of scope

Autonome Timer-Schleifen und Holdout-Szenarien (coleam00), Superplane als Plattform, MemPalace-Integration vor Phase 5, Änderung der Regel "Handlauf in frischer Sitzung ohne Review-Input", geringere Review-Tiefe bei Stufe L, Dollar-Beträge, Löschen von Kontext allein nach Nutzungszahlen, Änderungen an der globalen Konfiguration des Nutzers ohne Freigabe, Commits vor der Durchsicht.

## Vorbedingung vor dem Bau

Dieser Plan wird bei der Freigabe unter `.claude/plans/umstellung-kosten.md` im Repo abgelegt (Projekttatsache, ohne Projektnamen), im `LOOP.md`-Abschnitt "Stand des Baukastens" verlinkt, und die Testbranches `rollentest-a/b` bleiben bis Gate 1 erhalten, weil Phase 1 aus `rollentest-b` übernimmt.
