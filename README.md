# agent-sdlc

**A Claude Code toolkit for the whole lifecycle: product definition, specs, build phases, gates, and the configuration that corrects itself.**

Ein Baukasten für die Arbeit mit Claude Code: Skills, die von der Produktidee bis zur laufend korrigierten Projektkonfiguration ineinandergreifen.

Der Ausgangspunkt ist eine Beobachtung. Ein Agent, der bei jeder Sitzung bei null anfängt, ist ein teurer Praktikant. Er stellt dieselben Fragen, trifft dieselben Entscheidungen neu und macht denselben Fehler ein zweites Mal. Was fehlt, ist nicht ein besseres Modell, sondern eine Struktur, in der Wissen liegen bleibt und sich selbst korrigiert.

**Wie die Teile zusammenspielen, steht in [LOOP.md](LOOP.md).**

## Was drin ist

| Skill | Wozu |
|---|---|
| `prd` | Produkt spezifizieren. Führt vorher ein Interview, statt Absichten aufzuschreiben |
| `stack-decisions` | Technische Entscheidungen treffen und als Datensatz festhalten. Auch einzeln, wenn später etwas getauscht wird |
| `design-system` | Visuelle Richtung, Tokens im Code, Begründungen im Vault, Beispielseite zur Freigabe |
| `create-specs` | Das Produkt in Komponenten zerlegen und als verbundenen Spec-Graph anlegen |
| `write-spec` | Eine Komponente spezifizieren, gegen den Code verifiziert, mit Ripple- und Reverse-Abgleich |
| `plan-pages` | Welche Seiten es gibt und wie man zwischen ihnen navigiert, aus den Specs abgeleitet |
| `write-ui-spec` | Eine Seite spezifizieren, Mockup vor dem Dokument, am Bild iteriert |
| `spec-consistency` | Den Spec-Graph auf Widersprüche prüfen. Auslöser statt Takt, reiner Bericht |
| `plan-build` | Aus den fertigen Specs die Bauphasen mit Gates ableiten und in den Fahrplan schreiben |
| `planning` | Plan je Bauphase, im Planungsmodus geschrieben, vor dem Branch, mit Blöcken, Wellen und Out of Scope |
| `execute-plan` | Den freigegebenen Plan abarbeiten, Block für Block im eigenen Worktree, bis zu drei parallel |
| `testing` | Testdisziplin. Zuerst der fehlschlagende Test, Verify Red ist Pflicht. Getestet wird an den Schnittstellen, die der Plan nennt |
| `handlauf` | Drittes Gate, vor den Code-Gates. Die gebaute Fläche im Browser ansehen und durchklicken, wie ein Nutzer sie erlebt. Eigene Sitzung, kein Review-Input, reiner Bericht |
| `review-changes` | Erstes Code-Gate am Phasenende. Drei Linsen parallel, Gate-Abgleich, reiner Bericht |
| `thermo-nuclear-code-quality-review` | Zweites Gate. Fragt nicht ob der Code richtig ist, sondern ob er wartbar bleibt |
| `retro` | Nach der Phase: Was hat die Arbeit schwer gemacht? Mechanisches wird ein Check, Urteilsfragen werden Regeln für die Reviewer. Ändert die Umgebung, nicht den Code |
| `config-sync` | Die Konfiguration gegen ihre vier Autoritäten prüfen und die Drift nachziehen |
| `session-recap` | Handoff am Sitzungsende, prüft dabei den Fahrplan auf Drift |
| `diagnosing-bugs` | Quereinstieg, jederzeit: etwas ist kaputt. Erst eine schnelle Prüfung, die genau diesen Fehler rot zeigt, dann eingrenzen, Hypothesen, Fix mit Regressionstest |
| `grill-me` → `grilling` + `domain-modeling` | Das Interview-Verfahren. Entscheidungsbaum in Runden, bis keine Verzweigung offen ist; pflegt dabei Glossar und Entscheidungsdatensätze |
| `domain-modeling` | Die Fachsprache im Glossar schärfen und Entscheidungen festhalten, wenn sie die drei Kriterien erfüllen. Hält das Format beider |
| `codebase-design` | Das Vokabular für tiefe Module: Modul, Schnittstelle, Tiefe, Naht, Adapter. Referenz für `testing`, Reviews und Architekturarbeit |
| `improve-codebase-architecture` | Pflege, nur per Hand: den Bestand nach Stellen absuchen, an denen ein Modul tiefer werden sollte, als HTML-Bericht. Gewähltes geht über `write-spec` und `planning` |
| `project-init` | Der Einstiegspunkt. Wissensbasis, PRD, Stack, Bereiche und die Anweisungsebenen eines Projekts aufbauen |
| `writing-for-agents` | Wie man Dokumente schreibt, die ein Agent liest: Skills, `CLAUDE.md`, Regeln. Leitwörter, Verweise, Kürzen |
| `skill-creator` | Skills bauen, verbessern und ihre Trefferquote messen. Nur per Hand |
| `claude-statusbar` | Die Statuszeile im Terminal einrichten und steuern. Optional, wird bei `project-init` angeboten. Nur per Hand |

Zwei Dateien tragen über Sitzungsgrenzen. Der **Fahrplan** `roadmap.md` in der Wissensbasis beantwortet, wo das Projekt steht und was als Nächstes kommt; er wird gleich zu Beginn aus der mitgelieferten Vorlage kopiert, bereits mit dem Ablauf ausgefüllt, je Schritt samt seiner Voraussetzung und der Regel, dass ein Skill nicht läuft, solange die noch offen ist. Später wächst er um die Bauphasen, die `plan-build` aus den fertigen Specs ableitet. Ab dann ist er zu groß für jede Sitzung, deshalb injiziert der Hook nur noch den Kopf und den Abschnitt, auf den die Zeile `Aktuelle Bauphase` zeigt. `.claude/state.md` im Repo trägt die Übergabe der letzten Sitzung. Dazu drei Hooks, die `project-init` mit installiert: `session-state.py` injiziert Fahrplan und Übergabe bei Sitzungsstart und lässt die Sitzung mit dem nächsten Schritt eröffnen, `session-recap-trigger.py` erzwingt sie bei Abschiedsformeln, und `post-edit-check.py` führt nach jedem Edit die schnellen Checks aus `.claude/checks.json` aus.

Was aus Fehlern gelernt wird, landet nicht in der immer geladenen `CLAUDE.md`. `retro` macht aus Mechanischem einen Check und aus Urteilsfragen eine Regel in `CODING_STANDARDS.md`, die nur die Reviewer lesen. Die Fachsprache steht im Glossar `GLOSSARY.md` im Vault, das jedes Interview mitpflegt.

Der Kreislauf ist geschlossen: von der Idee über die Specs und die Bauphasen zurück in Specs, Umgebung und Konfiguration, die dabei gegen den gebauten Code korrigiert werden. Daneben gibt es zwei Einstiege ohne Voraussetzung: `diagnosing-bugs`, wenn etwas kaputt ist, und `improve-codebase-architecture` zur Pflege. Was noch fehlt, sagt die Tabelle am Ende von [LOOP.md](LOOP.md).

## Voraussetzungen

- [Claude Code](https://claude.com/claude-code)
- Ein Obsidian-MCP-Server für die Wissensbasis. `project-init` führt durch die Einrichtung, falls noch keiner läuft
- Python 3 mit `pyyaml`, nur für die Prüf- und Messskripte von `skill-creator`

## Installation

Alles liegt in `skills/`. Es dorthin zu kopieren, wo Claude Code nachschaut, ist die ganze Installation.

**macOS und Linux:**

```bash
git clone https://github.com/mxrius1706/agent-sdlc.git
cp -r agent-sdlc/skills/* ~/.claude/skills/
```

**Windows, PowerShell:**

```powershell
git clone https://github.com/mxrius1706/agent-sdlc.git
Copy-Item -Recurse -Force agent-sdlc\skills\* $HOME\.claude\skills\
```

Damit gilt es in jedem Projekt. Soll es nur für eines gelten, geht es nach `.claude/skills/` in dessen Ordner statt nach `~/.claude/skills/`.

**Prüfen:** In Claude Code `/project-init` tippen. Erscheint der Skill nicht, Sitzung neu starten.

**Aktualisieren:** Im geklonten Ordner `git pull`, dann dieselbe Kopierzeile noch einmal.

**Entfernen:** Die kopierten Ordner aus `~/.claude/skills/` löschen. Welche das sind, steht in der Tabelle oben.

Die beiden Hooks und die Fahrplan-Vorlage brauchen keinen eigenen Schritt. Sie liegen bei `project-init` und werden von ihm eingerichtet, wenn ein Projekt aufgesetzt wird — je Projekt, denn dort gehören sie hin.

> **Was es kostet.** Claude Code legt bei jedem Sitzungsstart Name und Beschreibung aller Skills in den Kontext, damit es weiß, wann welcher dran ist. Diese Liste ist auf etwa 1 % des Kontextfensters gedeckelt, und darüber werden Beschreibungen abgeschnitten, ohne Warnung. Die Beschreibungen der 28 Skills hier sind deshalb kurz gehalten: Zusammen belegen sie rund 6.900 Zeichen, grob 1.900 Token. Drei Skills kosten gar nichts, weil nur der Nutzer sie aufrufen kann (`skill-creator`, `claude-statusbar`, `improve-codebase-architecture`, erkennbar an `disable-model-invocation: true`); sie werden mit `/name` gestartet. Wer schon viele eigene Skills hat, installiert besser nur die, die er wirklich braucht: `project-init`, `prd`, `grill-me`, `grilling` und `domain-modeling` sind der kleinste sinnvolle Anfang.

## Loslegen

Im leeren Projektordner:

```
Neues Projekt aufsetzen
```

`project-init` übernimmt von dort: erst die Wissensbasis, dann das PRD, dann ein eigenes Interview über den Stack, dann ein Plan zur Freigabe. Geschrieben wird erst danach.

## Zwei Regeln, die alles zusammenhalten

**Eine Wahrheit, ein Ort.** Keine Aussage steht in zwei Dateien. Wo eine zweite sie braucht, verweist sie. Zwei Kopien einer Regel werden irgendwann uneins, und dann folgt die Arbeit der falschen.

**Bestand mit Ablaufdatum.** Was noch läuft, aber abgelöst wird, sagt das in seinem eigenen Dokument: was heute gilt, was es ersetzt und worauf nicht mehr aufgebaut werden darf.

## Herkunft

Der Baukasten enthält fremde Skills, teils angepasst. Quellen, Lizenzen und die vorgenommenen Änderungen stehen in [CREDITS.md](CREDITS.md).
