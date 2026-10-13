# Routing in the root CLAUDE.md

Read this when writing the root file's phrase routing and the roadmap precondition rule.

## Path routing

A rule with `paths:` frontmatter is loaded by the tooling when a matching file is touched. Write the globs; a table restating them is a second copy.

## Phrase routing

A table in the root file mapping what the user actually says to the skill that should run. Use their real phrases, in every language they work in. This is the only routing table and it lives in the root file alone; routing kept in two places drifts apart.

A third column gives the skill's place in the roadmap. Skills of the per-phase ritual have no step number, since they repeat every phase, so they carry their position in the ritual instead (the ritual itself is owned by `plan-build`).

| Was der Nutzer sagt | Skill | Fahrplan |
|---|---|---|
| „Komponenten schneiden", „Specs anlegen" | `create-specs` | Schritt 6 |
| „Schreib die Spec für X", „X spezifizieren" | `write-spec` | Schritt 7 |
| „Lass uns Phase 4 bauen", „den Plan abarbeiten" | `execute-plan` | Ritual, nach Freigabe |
| „Klick das mal durch", „sieht das gut aus" | `handlauf` | Ritual, Gate |
| „Was können wir besser machen", „das passiert uns schon wieder" | `retro` | Ritual, nach den Reviews |
| „Das ist kaputt", „geht nicht", „warum passiert X" | `diagnosing-bugs` | Jederzeit, ohne Voraussetzung |
| „Wo ist der Code verknotet", „Architektur aufräumen" | `/improve-codebase-architecture` vorschlagen | Jederzeit, nur per Hand |

A user-only skill still earns a row when its phrase does not name it; the row then means *suggest the command*, since no model can start it.

**Which skills earn a row:** those whose natural way of asking does not contain their name. "Write the PRD" needs no row; "Does this actually work?" is `handlauf` and is reachable otherwise only through the skill's description, the layer this table reinforces. The ritual skills earn rows as much as the setup ones and are forgotten more often, since they run on every phase for the life of the project. The installed skills are the truth about what exists; a fixed list copied here drifts the first time one is added.

Where a phrase must always trigger its skill, a `UserPromptSubmit` hook enforces it, and the table documents what the hook does.

## The precondition rule

A phrase table says which skill a sentence means, not whether that skill's turn has come. A skill running early produces a document resting on undecided things, and the output looks like the output. This rule goes into the root file next to the table, in this wording:

> Bevor ein Skill aus diesem Ablauf läuft, wird seine Zeile im Fahrplan gelesen. Steht die Voraussetzung dort noch offen, wird der Skill **nicht** ausgeführt: der fehlende Schritt wird benannt und angeboten. Das gilt auch, wenn nach dem Ergebnis gefragt wird statt nach dem Schritt — „schreib die Spec für X" ist ein Aufruf von Schritt 7. Bei den Skills des Rituals ist die Voraussetzung ihre Stelle im Ritual statt eine Schrittnummer: `handlauf` läuft nach dem Bauen, nicht während.

Why it holds:

- **It is a pointer.** The order lives in the roadmap's `Setzt voraus` column only; a restated sequence in the root file drifts.
- **The roadmap is injected** by the SessionStart hook, so the lookup costs nothing and the rule has no way out.
- **It names the fallback** (say which step is missing, offer it), so a session has nothing to improvise when the user sounds hurried.
- **It covers the phrasing the failure arrives in**: nobody asks for step 7 by name.

The roadmap template's head carries the same rule and the hook repeats it, so it holds even in a session that never reaches the root file.
