# Fahrplan

**Jetzt:** Aufbau, Schritt 1 · **Als Nächstes:** Wissensbasis einrichten und dieses Dokument in den Vault legen
**Aktuelle Bauphase:** noch keine

Dieser Fahrplan beantwortet, wo das Projekt steht und was als Nächstes kommt. Er ist die einzige Datei, die das beantwortet. Wer einen Schritt abschließt, trägt ihn hier ein, bevor er weitergeht.

Zeichen: `⬜` offen · `🔄` läuft · `✅` fertig · `❌` bewusst entfallen

**Die Reihenfolge ist bindend.** Jeder Schritt nennt unten in der Spalte „Setzt voraus", was vorher stehen muss. Bevor ein Skill aus diesem Ablauf läuft, wird hier nachgesehen: steht seine Voraussetzung noch auf `⬜` oder `🔄`, wird er **nicht ausgeführt**. Stattdessen wird der fehlende Schritt benannt und angeboten. `✅` und `❌` zählen beide als erledigt.

Das gilt auch dann — und vor allem dann —, wenn direkt nach dem Ergebnis gefragt wird statt nach dem Schritt. „Schreib die Spec für X" ist ein Aufruf von Schritt 7 und wird genauso geprüft wie „lass uns die Specs machen".

Außerhalb dieser Reihenfolge stehen nur zwei Skills, und sie haben keine Voraussetzung: `diagnosing-bugs`, wenn etwas kaputt ist, und `improve-codebase-architecture` zur Pflege des Bestands.

---

## Aufbau

Der Weg von der Idee bis zu vollständigen Spezifikationen. Jeder Schritt hat den Skill, der ihn ausführt.

| # | Schritt | Skill | Setzt voraus | Stand | Notiz |
|---|---|---|---|---|---|
| 1 | Wissensbasis | `project-init` Phase 0 | — | ⬜ | Vault einrichten, Struktur anlegen. Das Glossar entsteht im ersten Interview, nicht hier |
| 2 | Produktdefinition | `prd` | 1 | ⬜ | Interview zuerst, dann schreiben |
| 3 | Stack | `stack-decisions` | 2 | ⬜ | Getrennt vom Produktgespräch |
| 4 | Design-System | `design-system` | 3 | ⬜ | Entfällt ohne Oberfläche |
| 5 | Projektkonfiguration | `project-init` Phasen 3 bis 5 | 3, 4 | ⬜ | Wurzel, Bereiche, Pfad-Regeln, Hooks |
| 6 | Komponentenkarte | `create-specs` | 5 | ⬜ | Grenzen werden gegrillt, nicht abgeleitet |
| 7 | Specs | `write-spec` | 6 | ⬜ | 0 von 0, eine Komponente je Aufruf |
| 8 | Seitenplanung | `plan-pages` | 7 vollständig | ⬜ | Je Oberfläche eine Übersicht, aus den Specs abgeleitet |
| 9 | UI-Specs | `write-ui-spec` | 8 | ⬜ | 0 von 0, je Seite eine, Mockup vor dem Dokument |
| 10 | Konsistenzprüfung | `spec-consistency` | 7 | ⬜ | Kein fester Takt, siehe Regel unten |
| 11 | Bauplan | `plan-build` | 9, 10 | ⬜ | Füllt den Abschnitt „Bauphasen" unten, erst wenn alle Specs stehen |

Schritte, die dieses Projekt nicht braucht, werden auf `❌` gesetzt und nicht als offen mitgeschleppt. Ein Projekt ohne Oberfläche hat kein Design-System und keine UI-Specs.

### Konsistenzläufe

**Letzter Lauf:** noch keiner · **Seitdem:** 0 Specs · **Offene Annahmebrüche:** 0

Kein fester Takt. Ein Lauf ist fällig, wenn einer dieser Fälle eintritt:

- Eine **Entscheidung wurde geändert**, die bestehende Specs zitieren. Sofort, gezielt über die zitierenden Specs.
- Eine Spec hat **bewusst eine Annahme gebrochen** und die Gegenseite ist noch nicht nachgezogen.
- Ein **Cluster ist fertig**, dessen Specs gegeneinander geschrieben wurden.
- **Vor der Seitenplanung und vor dem Bauplan**, jeweils vollständig, weil beide die Specs als Ganzes lesen.
- **Als Netz:** fünf oder mehr Specs seit dem letzten Lauf, ohne dass einer der Fälle gefeuert hat.

Der Grund gegen einen festen Takt: Widersprüche entstehen durch **Ändern**, nicht durch Schreiben. Ein Lauf nach fünf Specs, in denen nichts umentschieden wurde, sucht eine Fehlerklasse, die es dort nicht gibt. Und ein Lauf, der erst fünf Specs nach einer geänderten Entscheidung kommt, findet den Fehler in sechs Dokumenten statt in einem.

---

## Bauphasen

Bleibt leer, bis die Specs stehen. `plan-build` schreibt diesen Abschnitt, wenn Schritt 10 durch ist, und füllt ihn mit:

- **Ablauf je Phase.** Das Ritual, das für jede Phase gleich gilt, ohne Ausnahme: `planning` → Freigabe → Branch → `execute-plan` → `handlauf` (nur mit Oberfläche) → `review-changes` → `thermo-nuclear-code-quality-review` → `retro` → Rückfluss über `write-spec` und `config-sync` → Freigabe zum Push. Es gehört **in den Kopf dieses Dokuments**, nicht in diesen Abschnitt: sobald Bauphasen existieren, injiziert der Hook nur noch den Kopf und die eine aktuelle Phase, und ein Ritual in einem Nachbarabschnitt liegt dann in keiner Sitzung mehr.
- **Kernprinzipien.** Was über alle Phasen hinweg gilt und in keiner einzelnen steht.
- **Die Phasen selbst.** Je Phase: startet nach was und warum, Spec-Quellen als Links, Ziel, Inhalt, das Gate als Liste nachprüfbarer Sätze.
- **Meilensteine.** Zwei bis vier benannte Punkte über die ganze Strecke, geschäftlich statt technisch.
- **Was der Plan bewusst nicht enthält.** Der negative Umfang, damit Verworfenes nicht in sechs Monaten neu vorgeschlagen wird.
- **Entscheidungen.** Jede Reihenfolge-Entscheidung mit Begründung. Das ist der Teil, der zuerst verloren geht.

Die Baureihenfolge wird **aus den fertigen Specs abgeleitet**, nicht vorher geplant: erst wenn die Komponenten beschrieben sind, ist zu sehen, was worauf aufbaut und was zuerst Wert liefert.

Das ist eine andere Frage als die Schreibreihenfolge aus Schritt 6. Schreibreihenfolge folgt den Verweisen, Baureihenfolge folgt dem Nutzen.

---

## Regeln für dieses Dokument

**Als Nächstes trägt eine Handlung, keinen Schrittnamen.** „Specs schreiben" sagt einer neuen Sitzung nichts. „Zuerst das Datenmodell, alles andere zeigt darauf" sagt, wo sie anfängt und warum. Die Begründung ist der Teil, der nach ein paar Tagen fehlt.

**Eintragen, was wahr ist, nicht was geplant war.** Ein halb gelaufener Schritt ist `🔄` mit Notiz, was fehlt, nie `✅`, weil es fast geklappt hat.

**Nichts zusammenfassen, was anderen gehört.** Der Spec-Index besitzt den Status je Spec, hier steht höchstens eine Zahl und ein Verweis. Beim Widerspruch gewinnt der Index.

**Die Zeile `Aktuelle Bauphase` wird maschinell gelesen.** Sobald der Bauplan steht, ist dieses Dokument zu groß, um in jede Sitzung zu passen. Der SessionStart-Hook injiziert deshalb nur noch den Kopf bis zum ersten Trenner und **genau den Abschnitt, dessen Überschrift diesen Text enthält**. Zeigt die Zeile auf die falsche Phase, arbeitet die nächste Sitzung mit der falschen Phase im Kontext, ohne dass etwas fehlschlägt. Sie wird beim Phasenwechsel gesetzt, im selben Zug wie „Jetzt".
