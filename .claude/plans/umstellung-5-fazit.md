# Plan: Phase 5 Fazit, die Merkpunkte abarbeiten

Rahmenplan: `.claude/plans/umstellung-kosten.md` (Phase 5). Branch `umstellung/5-fazit`. Planungstiefe **voll** (`plan-check.py depth`: 6 Bereiche). Stufe L.
Ablage bei Freigabe: `.claude/plans/umstellung-5-fazit.md` (ohne Projektnamen, öffentliches Repo).

## Context

Der Pilot im Videoprojekt lief (Gate 3, Fix-Runde, thermo, config-sync). Er hat 30 Merkpunkte erzeugt (Datei `pilot-auswertung-merkpunkte.md`) und Zahlen: im alten Setup kosteten Reviews so viel wie das Bauen (1,98 gegen 1,91 Mio Ausgabe-Token), im Pilot kam Doppelarbeit dazu (Review nach Resume doppelt, Handlauf-Nachlauf dreimal, ca. 15 von 40 Min doppelt). Ziel des Gesamtvorhabens: schlanker, günstiger, schneller bei gleicher oder besserer Qualität, Qualität belegt durch Handlauf-Befunde und Fix-Quote.

## Goal

Jeder Merkpunkt ist erledigt, bewusst verworfen oder als Versuch für Pilot 2 eingetragen, mit Grund. Doppelarbeit tritt im Pilot 2 nicht mehr auf. Alle Kürzungen der Review-Menge sind als Versuch mit Messvorschrift und Rückfallregel eingetragen, keine ist ungemessen scharf. Danach wird die Merkpunkte-Datei gelöscht.

## Decisions

| Frage | Antwort | Grund |
|---|---|---|
| Reihenfolge | Erst Fehler ohne Qualitätsrisiko (Doppelarbeit, Widersprüche, Messlücken), dann Kürzungen als Versuch | Der erste Teil spart sicher; der zweite braucht Daten |
| Wie wird gekürzt | Kürzungen 1 bis 3 gehen als Schalter in Pilot 2 (je Plan abschaltbar), nicht sofort als Regel | Nach deinem Maßstab: belegt, nicht gefühlt |
| Rückfallregel | Fand der Handlauf oder die Tests im Pilot 2 etwas Kritisches (K1/K2), das ein gestrichenes Review hätte finden müssen, wird die Kürzung zurückgenommen | Macht die Qualität prüfbar |
| Deterministisch vor Text | Resume-Erkennung, Lock, Kontostand-Prüfung sind Skripte/Hook mit Test, keine Textbitten | Texte erodieren (Resume-Fehler entstand so) |
| Globale Konfiguration | `autoMode`-Pflege, Kontoeinstellungen: nur Vorschlagsliste, Änderung nach deiner Freigabe | Out of scope des Rahmenplans |
| Sicherheitslinse | Nur bei Risiko-Etikett im Plan, Cloudflare-Klassen als Prompt-Inhalt, ein Probelauf im Videoprojekt nach dem Release | Dein Vorschlag aus den Merkpunkten |
| Wo ein Fix wirkt | Immer im Baukasten, nie im Projekt-Fahrplan kopiert (eine Wahrheit pro Ort) | Fahrplan-Kopie war die Ursache des thermo-Konflikts |

## Critical files

| Datei | Änderung |
|---|---|
| `skills/project-init/hooks/session-state.py` (und Test) | listet Berichte in `.claude/plans/`, die neuer sind als der Laufzustand; Lock-Hinweis |
| `skills/execute-plan/SKILL.md` | Schritt 0 prüft Berichte, Laufzustand führt fertige Gate-Schritte mit Berichtspfad; keine Wakeup-Doppelstarts; Cluster-Zerlegung nur mit Begründung; Kontoprüfung vor langen Läufen |
| `skills/execute-plan/scripts/` (neu: `run-lock.py` oder in `auslauf.py`) | Lock je Lauf, Start verweigert bei laufendem Lauf |
| `skills/project-init/hooks/auslauf.py` | `/goal`-Schleife und Konto-Limit: Marke beendet Leerturns, Text für "bis Limit, nicht darüber" |
| `skills/plan-build/SKILL.md` | Fahrplan verweist auf das Ritual statt es zu kopieren; thermo-Auslöser nur nach Regel (kein freier Auslöser) |
| `skills/review-changes/scripts/gate-precheck.py` | Exit-Code von `plugin validate` erhalten; `--exclude` nur falls der Release-Commit es braucht |
| `skills/config-sync/scripts/ref-check.py` | Filter gegen Falschmeldungen (30 von 30 falsch), Test mit den realen Fällen |
| `skills/retro/scripts/session-cost.py` | Fix-Quote auch ohne `build`-Agents (Hauptsitzung als Bauer), Handlauf als eigene Rolle statt `other` |
| `agents/block-fixer.md`, `README.md` | Auflage "kein Gesamt-Gate im Block"; Rollenpfad `.claude/agents/` |
| `skills/handlauf/SKILL.md` | Turn-Limit oder Seitenumfang je Lauf, Nachlauf nicht aus der Bausitzung starten |
| `skills/review-changes/SKILL.md`, `skills/execute-plan/SKILL.md` | Schalter für Kürzungen 1 bis 3 mit Messvorschrift |

## Tasks

| Id | Block | Task | Test target (seam) | Requirements |
|---|---|---|---|---|
| t1 | b1 | `session-state.py` meldet Berichte neuer als der Laufzustand | `session-state.py main`: Plan mit Bericht neuer als Laufzustand, Ausgabe nennt den Bericht; ohne Bericht nichts | Merkpunkt KRITISCH Resume |
| t2 | b1 | Laufzustand führt fertige Gate-Schritte mit Berichtspfad, Schritt 0 liest das | `n/a: text` plus Probelauf Wiederaufnahme | Resume |
| t3 | b1 | Lock je Lauf: zweiter Start verweigert, Wakeup storniert bei Handeingabe | Skript `run-lock`: zweiter `acquire` exit 1, `release` räumt auf | Doppelstart |
| t4 | b1 | Konto-Vorprüfung vor Läufen mit zwei go: Text plus Aufruf der `clauded`-Prüfliste | `n/a: text` (Skript existiert) | Kontoprüfung |
| t5 | b1 | `auslauf.py`: Marke beendet `/goal`-Leerturns, Hinweis `/goal clear` | `auslauf.py` Hook-Aufruf mit Marke: Ausgabe enthält Hinweis | /goal-Konflikt |
| t6 | b1 | Regel "bis Limit, nicht darüber": nur Text und Meldung (Kontolimit ist im Hook nicht lesbar) | `n/a: text` | Limit-Regel |
| t7 | b2 | `plan-build`: Fahrplan verweist aufs Ritual; `ref-check` findet Kopien der Gate-Reihenfolge | `ref-check.py` mit Fixture, die eine Kopie enthält | Fahrplan-Kopie |
| t8 | b2 | `ref-check` Filter (Wissensbasis-Pfade, Dateinamen ohne Ordner, Daten- und Paketnamen) | `ref-check.py` mit den 30 echten Fällen als Fixture: 0 Falschmeldungen, 2 echte bleiben | ref-check 100 % falsch |
| t9 | b2 | `gate-precheck` hält den Exit-Code von `plugin validate` | `gate-precheck.py` mit Fixture, Befehl endet 1 | validate-Exit |
| t10 | b3 | `session-cost`: Fix-Quote ohne build-Agents, Rolle `handlauf` | `session-cost.py --roles` mit synthetischem Transkript | Messlücken |
| t11 | b3 | Handlauf: Turn-Limit oder Seitenumfang, Start nur aus eigener Sitzung | `n/a: text` | Handlauf-Cache |
| t12 | b3 | Fix-Quote und Handlauf-Rolle in `retro`-Text nachführen | `n/a: text` | Messlücken |
| t13 | b4 | `block-fixer`-Auflage, README-Pfad, Cluster-Regel, thermo-Auslöser nur nach Regel | `n/a: text` | Textpunkte |
| t14 | b4 | Schalter für Kürzungen 1 bis 3 mit Messvorschrift und Rückfallregel | `n/a: text` | Review-Volumen |
| t15 | b4 | Sicherheitslinse nur bei Risiko-Etikett; Cloudflare-Klassen als Prompt-Inhalt | `n/a: text` | Sicherheit |
| t16 | b5 | Pilot 2: echte Bauphase mit den Schaltern; Zahlen neben die Basiswerte; Ablation eines großen Kontext-Kandidaten | Messung mit `session-cost.py --roles` | Gate 5 |
| t17 | b5 | Bericht ohne Projektnamen, Hebel behalten/ändern/zurück, `retro`, `config-sync`, Memory-Datei löschen | `n/a: text` | Gate 5 |

## Order

t1 bis t6 zuerst (kritisch, deterministisch). Dann t7 bis t12 (unabhängig, ohne Qualitätsrisiko). t13 bis t15 danach, weil sie Texte aus b1 bis b3 berühren. t16/t17 zuletzt. Block b5 startet nur mit deinem Go, weil Pilot 2 eine echte Phase und Kontingent braucht.

## Blocks

| Block | Tasks | Files | Wave | Exclusive |
|---|---|---|---|---|
| b1 | t1, t2, t3, t4, t5, t6 | `skills/project-init/hooks/session-state.py`, `skills/project-init/hooks/auslauf.py`, `skills/execute-plan/` | 1 | no |
| b2 | t7, t8, t9 | `skills/config-sync/scripts/`, `skills/review-changes/scripts/`, `skills/plan-build/SKILL.md` | 1 | no |
| b3 | t10, t11, t12 | `skills/retro/`, `skills/handlauf/SKILL.md` | 1 | no |
| b4 | t13, t14, t15 | `agents/block-fixer.md`, `README.md`, `skills/review-changes/SKILL.md`, `skills/thermo-nuclear-code-quality-review/SKILL.md` | 2 | no |
| b5 | t16, t17 | Pilotprojekt, `.claude/plans/` | 3 | yes |

## Waves

1. b1 bis b3: getrennte Dateibereiche (Hooks und execute-plan, Skripte und plan-build, retro und handlauf).
2. b4: berührt Texte, die b1 bis b3 schon geändert haben.
3. b5: Pilot, braucht laufende Konten, exklusiv.

## Tests

- t1: Bericht neuer als Laufzustand wird genannt; ohne Bericht keine Meldung; Bericht älter wird nicht genannt (Fehlerfall).
- t3: zweiter Start verweigert; nach `release` wieder möglich; veralteter Lock (Prozess tot) wird erkannt.
- t8: reale Falschmeldungsfälle als Fixture ergeben keine Meldung, ein echter Fall (fehlende Datei in Backticks) bleibt.
- t9: Exit 1 des Befehls bleibt Exit 1, nicht 0.
- t10: Transkript ohne build-Agents, Fix-Quote aus Hauptsitzungs-Commits; Rolle `handlauf` erkannt.
- Pariätstest `chunk_markdown` bleibt grün. Textblöcke: `writing-for-agents` je geändertem Skill.

## Verification

- Jeder Testordner einzeln grün: `for d in skills/*/scripts skills/*/hooks; do python3 -I -m unittest discover -s $d -p "test_*.py"; done` (ein Sammellauf über `skills` findet nichts).
- `python3 -I skills/config-sync/scripts/ref-check.py` auf dem Repo: nur echte Treffer.
- Probelauf Wiederaufnahme: Plan mit Bericht neuer als Laufzustand, `session-state.py` meldet ihn; Probelauf Doppelstart: zweiter Start verweigert.
- `grep` gegen die Liste der Projektnamen: keine Treffer im Repo.
- Gate 5 aus dem Rahmenplan: Zahlen beider Pilotphasen neben den Basiswerten, Hebel mit Entscheidung, kein Pilotprojekt im Repo.
- Pilot 2: Reviewanteil an der Bauzeit (Ziel unter 0,5 gegen alt ca. 1,0), Fix-Quote (alt 0,11 bis 0,13), Handlauf-Befunde je Phase, kein K1/K2 durchgerutscht.

## Out of scope

Änderung der globalen Konfiguration (`autoMode`, Kontoeinstellungen) ohne deine Freigabe; Kontolimit im Hook auslesen (nicht möglich); Cloudflare-Skill vollständig installieren oder in den Baukasten übernehmen; Umbau von `handlauf` über Turn-Limit hinaus; MemPalace; Produktbefunde des Videoprojekts (N1 bis N4 usw.); Löschen von Kontext nach Nutzungszahlen allein; Dollar-Beträge; Release des Videoprojekts; Commits vor der Durchsicht.

## Offene Entscheidungen für dich

1. Pilot 2 mit den Kürzungsschaltern 1 bis 3 gleichzeitig oder nacheinander? (Empfehlung: gleichzeitig, weil ein Pilot teuer ist, mit je Schalter einzeln auswertbarer Messung.)
2. Welches Projekt für Pilot 2 und wann (Kontingent)?

## Block-Befunde

| Block | Stufe | Befund |
|---|---|---|
| b3 | 3 | `session-cost.py` `COMMIT_RE`: `git commit -am "fix: x"` und Typ mit Großbuchstaben werden nicht erkannt |
| b3 | 4 | Satz zur Doppelarbeit in `retro/SKILL.md` steht nicht wörtlich in t12 |
| b2 | 3 | `gate-precheck.py` `split_pipe`: zitiertes `"|"` allein wird als Pipe gelesen (Test fehlt) |
| b2 | 3 | `||` wird als Argument durchgereicht, nicht dokumentiert |
| b2 | 3 | `ref-check.py` Präfixfilter `specs/` und `refs/` verschluckt auch echte Pfade unter `specs/` (breit, laut Plan gewollt) |
| b2 | 4 | Tests fehlen für GATE-ORDER auf zwei Zeilen und in Codeblöcken |
| b1 | 3 | `run-lock.py` Rennen: leere Datei nach `O_EXCL` gilt als veraltet, zwei Übernehmer eines toten Locks; Test für leere/kaputte Lockdatei fehlt |
| b1 | 3 | `session-state.py` Namensteile als Teilstring: `phase-3-code-review-tool.md` wird als Bericht gemeldet, wenn neuer als der Laufzustand |
