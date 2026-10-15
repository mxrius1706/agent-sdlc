# Herkunft der übernommenen Skills

Der Baukasten enthält fremde Skills, teils unverändert, teils angepasst. Diese Datei hält fest, was woher kommt und was daran geändert wurde.

Dreizehn der 28 Skills stammen von anderen und stehen unten in der Tabelle. Die übrigen fünfzehn sind Eigenarbeit; zwei davon tragen einzelne Anleihen, die unten unter „Anleihen in eigenen Skills“ stehen.

Acht davon sind unmittelbar für diesen Baukasten entstanden: `create-specs`, `design-system`, `plan-pages`, `project-init`, `session-recap`, `stack-decisions`, `plan-build`, `planning`. Die anderen sieben sind aus älteren, selbst geschriebenen Skills des Autors hervorgegangen: `write-ui-spec`, `spec-consistency`, `execute-plan`, `review-changes`, `testing`, `config-sync`, `handlauf`. Das ist vom Autor bestätigt, nicht daraus geschlossen, dass ein Herkunftsvermerk fehlt - bei `write-spec` stand einer da, und der gehört deshalb in die Tabelle.

| Skill | Quelle | Lizenz | Beleg | Zustand |
|---|---|---|---|---|
| `skill-creator` | [anthropics/claude-plugins-official](https://github.com/anthropics/claude-plugins-official), `plugins/skill-creator`; bezogen über einen Marketplace-Spiegel | Apache 2.0 | `skills/skill-creator/LICENSE.txt` liegt bei, Aufbau deckt sich mit der offiziellen Fassung | Frontmatter angepasst |
| `prd` | [github/awesome-copilot](https://github.com/github/awesome-copilot) | MIT | Repo-Lizenz und `license: MIT` im Frontmatter des Skills | **angepasst** |
| `grill-me` | [mattpocock/skills](https://github.com/mattpocock/skills), `skills/productivity/grill-me` und `skills/engineering/grill-with-docs` | MIT | Repo-Lizenz | **angepasst** |
| `grilling` | [mattpocock/skills](https://github.com/mattpocock/skills), `skills/productivity/grilling` | MIT | Repo-Lizenz | unverändert, Stand `49dd158` |
| `claude-statusbar` | [leeguooooo/claude-code-usage-bar](https://github.com/leeguooooo/claude-code-usage-bar) | MIT | Metadaten des Pakets `claude_statusbar` 3.42.0 | Frontmatter angepasst |
| `write-spec` | mittelbar [github/awesome-copilot](https://github.com/github/awesome-copilot), `create-specification` | MIT | Herkunftsvermerk in der Vorlage, aus der dieser Skill entstand | **zweistufig angepasst** |
| `thermo-nuclear-code-quality-review` | [cursor/plugins](https://github.com/cursor/plugins/blob/main/cursor-team-kit/skills/thermo-nuclear-code-quality-review/SKILL.md), `cursor-team-kit` | MIT | Repo-Lizenz, dort als Werk von Cursor ausgewiesen | **angepasst** |
| `diagnosing-bugs` | [mattpocock/skills](https://github.com/mattpocock/skills), `skills/engineering/diagnosing-bugs` | MIT | Repo-Lizenz, Copyright 2026 Matt Pocock | **angepasst** |
| `domain-modeling` | [mattpocock/skills](https://github.com/mattpocock/skills), `skills/engineering/domain-modeling` | MIT | Repo-Lizenz, Copyright 2026 Matt Pocock | **angepasst** |
| `codebase-design` | [mattpocock/skills](https://github.com/mattpocock/skills), `skills/engineering/codebase-design` | MIT | Repo-Lizenz, Copyright 2026 Matt Pocock | fast unverändert |
| `improve-codebase-architecture` | [mattpocock/skills](https://github.com/mattpocock/skills), `skills/engineering/improve-codebase-architecture` | MIT | Repo-Lizenz, Copyright 2026 Matt Pocock | **angepasst** |
| `retro` | [mattpocock/skills](https://github.com/mattpocock/skills), `skills/engineering/retro` | MIT | Repo-Lizenz, Copyright 2026 Matt Pocock | **angepasst** |
| `writing-for-agents` | [mattpocock/skills](https://github.com/mattpocock/skills), `skills/productivity/writing-for-agents` | MIT | Repo-Lizenz, Copyright 2026 Matt Pocock | fast unverändert |

Alle Skills aus `mattpocock/skills` sind auf dem Stand von Commit `49dd158` (9. Oktober 2026) übernommen. Ihre Texte bleiben englisch wie die übrigen Skills; die Dateien `agents/openai.yaml` für Codex sind nicht übernommen.

## Vorgenommene Anpassungen

**`prd`** - Phase 1 hieß im Original „Discovery (The Interview)" und stellte ein paar Standardfragen. Sie heißt jetzt „Discovery (Grill the Idea)" und ruft verbindlich den `grill-me`-Skill auf. Begründung im Skill selbst: ein PRD aus oberflächlichen Antworten wird zu „aspirational fiction". Zusätzlich darf der Nutzer das Interview abkürzen, offene Punkte werden dann als `TBD` markiert statt erfunden. Beim Kürzen des Baukastens fiel der Abschnitt „When to Use“ weg, weil er nur die Beschreibung wiederholte; Aufbau, Schema und Beispiel sind unverändert.

**`grill-me`** - `disable-model-invocation` von `true` auf `false` gesetzt. Ohne diese Änderung kann `prd` den Skill nicht selbst aufrufen und die Kopplung oben läuft ins Leere. Außerdem ruft er nicht mehr nur `grilling` auf, sondern wie Matts `grill-with-docs` zusätzlich `domain-modeling`: Jedes Interview pflegt dabei Glossar und Entscheidungsdatensätze. Upstream ist `grill-me` bewusst zustandslos, weil es auch ohne Repo laufen soll; hier läuft jedes Interview in einem Projekt mit Wissensbasis, also gibt es keinen Grund für die zustandslose Fassung.

**`diagnosing-bugs`** - die Methode ist unverändert: erst eine schnelle, rote Prüfung, dann eingrenzen, Hypothesen, Instrumentierung, Fix mit Regressionstest, Aufräumen. Angepasst: Glossar und Entscheidungsdatensätze werden über die Wissensbasis-Tabelle gefunden, der Regressionstest folgt `testing`, ein fehlender sauberer Ansatzpunkt für den Test führt zur Empfehlung `/improve-codebase-architecture`, nach dem Fix wird `/retro` empfohlen, und eine falsche oder stumme Spec wird als Befund für `write-spec` gemeldet statt korrigiert. Deutsche Auslöser in der Beschreibung ergänzt.

**`domain-modeling`** - Glossar und Entscheidungsdatensätze liegen in der Wissensbasis statt im Repo (`GLOSSARY.md` neben dem PRD, `GLOSSARY-MAP.md` bei mehreren Kontexten). Aus `ADR-FORMAT.md` wurde `DECISION-FORMAT.md`: die bisherige Vorlage aus `write-spec`, verbunden mit Matts drei Kriterien (schwer umkehrbar, ohne Kontext überraschend, Ergebnis einer echten Abwägung) und seiner Liste, was einen Datensatz verdient. `stack-decisions` bleibt die Ausnahme und hält jede geklärte Stack-Frage fest.

**`codebase-design`** - bis auf die Beschreibung und den Glossar-Verweis in `DESIGN-IT-TWICE.md`, der jetzt in die Wissensbasis zeigt, unverändert.

**`improve-codebase-architecture`** - Ablauf unverändert: Brennpunkte aus der Git-Historie, Erkundung, HTML-Bericht im Temp-Verzeichnis, Auswahl, Grilling. Angepasst: Entscheidungsdatensätze aus der Wissensbasis werden nicht neu verhandelt, ein mit tragendem Grund abgelehnter Kandidat wird ein Datensatz, und ein gewählter Kandidat wird nicht frei umgebaut, sondern geht über `write-spec` und `planning` in den normalen Ablauf, damit der Fahrplan stimmt.

**`retro`** - Kategorien und die Pflicht, zwischen mechanisch (wird ein Check) und Urteil (wird eine Regel für die Reviewer) zu unterscheiden, sind übernommen. Angepasst: Neben der Sitzung sind die Berichte der Gates einer Phase Primärquelle, Urteilsregeln landen in `CODING_STANDARDS.md` im Repo, die Regel „einmal ist ein Vorfall, zweimal ein Muster“ ist aus `review-changes` hierher umgezogen, und Checks laufen über `.claude/checks.json` und den Hook `post-edit-check.py`.

**`writing-for-agents`** - unverändert bis auf die Beschreibung und einen Hinweis in `SKILL-MECHANICS.md`, dass hier Fahrplan und Phrasen-Tabelle die Rolle des Router-Skills übernehmen.

**`skill-creator`** und **`claude-statusbar`** - Inhalt unverändert, nur `disable-model-invocation: true` gesetzt. Beide werden selten gebraucht und hatten lange Beschreibungen, die in jeder Sitzung Kontext kosteten. Aufgerufen werden sie jetzt per Hand mit `/skill-creator` und `/claude-statusbar`.

**`write-spec`** - nicht direkt übernommen, sondern aus einer Vorlage entstanden, die sich selbst als Fork von `create-specification` aus `github/awesome-copilot` (MIT) ausweist. Das Original erzeugt leere Template-Specs in einem `spec/`-Ordner. Über zwei Stufen sind daraus geworden: Ablage im Spec-Graph der Wissensbasis statt im Repo, eine erzwungene Ist-Stand-Analyse gegen den echten Code vor jedem Dokument, Redundanz-Sweep, sowie Ripple-Prüfung vorwärts und Reverse-Abgleich über die eingehenden Links. Der Vermerk stand nur in der Zwischenstufe und fehlte hier zunächst - genau die Art Verweis, die beim Ableiten still verloren geht.

**`thermo-nuclear-code-quality-review`** - übernommen aus dem `cursor-team-kit` in [cursor/plugins](https://github.com/cursor/plugins/blob/main/cursor-team-kit/skills/thermo-nuclear-code-quality-review/SKILL.md), MIT, dort als Werk von Cursor ausgewiesen. Der Skill kursiert zusätzlich in weiteren öffentlichen Repos; maßgeblich für diesen Baukasten ist die genannte Quelle, weil sie der tatsächliche Bezugsweg ist. Ergänzt: der Abschnitt `Follow-up Run`, der nach einer Fix-Runde nur den Fix-Diff gegen die Befunde des letzten Laufs prüft.

Als einziger Bau-Skill wurde er **nicht** umgeschrieben. Bei allen anderen ist die Fassung hier eigen formuliert; hier nicht, weil genau diese Fassung bereits als Gate im Einsatz und erprobt ist. Der Preis dafür ist eine Einschränkung, die bekannt sein sollte: Ein Teil ihrer Beispiele ist auf TypeScript gemünzt (`any`, `unknown`, Casts). Die Regeln dahinter gelten sprachunabhängig, die Formulierung ist es nicht.

**`claude-statusbar`** - unverändert übernommen. Der Skill steuert das externe Werkzeug `cs`, das nicht Teil dieses Repos ist und über `cs --setup` installiert wird. `project-init` bietet das in Phase 0 an, wenn drei Bedingungen zusammenkommen: Arbeit im Terminal, noch keine `statusLine` konfiguriert, und Zustimmung des Nutzers. Es ist eine Einstellung je Rechner, nicht je Projekt, deshalb wird bei bereits gesetzter `statusLine` stillschweigend übersprungen statt erneut gefragt.

## Anleihen in eigenen Skills

**`testing`** - aus Matts `tdd` (`tests.md`, `mocking.md`): das Anti-Pattern des tautologischen Tests, Mocking nur an Systemgrenzen und der Grundsatz, dass Tests an vereinbarten Schnittstellen ansetzen. Bei uns vereinbart sie der freigegebene Plan (`planning`, Abschnitt Tests).

**`review-changes`** - aus Matts `code-review`: die Liste von zwölf Code-Smells nach Fowler als Urteilsheuristik der Struktur-Linse, mit Vorrang für dokumentierte Projektstandards.

## Aufrufkette

```
prd, stack-decisions, create-specs, write-spec, ...  ->  grill-me  ->  grilling + domain-modeling
```

`grill-me` ist nur ein Shim von wenigen Zeilen. Die eigentliche Methode steht in `grilling`: ein Entscheidungsbaum, der in Runden abgearbeitet wird. Pro Runde werden alle Fragen gestellt, deren Voraussetzungen geklärt sind, jeweils mit einer Empfehlung. Fakten beschafft der Agent selbst, Entscheidungen trifft der Nutzer.
