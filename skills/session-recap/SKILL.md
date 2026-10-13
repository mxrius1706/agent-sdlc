---
name: session-recap
description: "Write the handoff for the next session into .claude/state.md. Use at the end of a working session, when the user says goodbye or signals stopping for the day, or asks for a handoff or where things stand. A hook triggers it on farewell phrases."
---

# Session Recap

Every session starts with an empty context window. What the last one learned is gone unless it was written down, and reconstructing it costs more than writing it did. This writes the handoff: a minute now, twenty saved later.

## Where it goes and what it looks like

Into `.claude/state.md`, overwritten each time. It answers *what happened last time*; where the project stands belongs to the roadmap, never to this file.

### Shape

```markdown
# Letzte Sitzung <date> · <branch>

Ziel: <one sentence>

Gemacht:
- <file or area>: <what>
- ...

Entschieden: <only non-obvious decisions, otherwise omit>

Nächstes: <the concrete next action, one sentence>

Offen: <only if it blocks something, otherwise omit>
```

Write it in the project's documentation language. The headings are an example, not a fixed wording.

### Rules

**Facts only.** What the next session cannot reconstruct: which branch, which commit range, how many tests passed, which gate is through.

**"Nächstes" has to be actionable.** Name the file, the document or the command; if the order matters, say why, since that reasoning is what will be missing.

**Around fifteen lines.** Beyond it the file stops being read, and an unread handoff is the same as none.

**Omit empty sections.**

**Overwrite, do not append.** Only the last session is relevant; version control holds the history.

**A correction owed is the next step.** Something noticed but not fixed outranks the next new piece of work, otherwise it sinks and resurfaces as a bug.

## Check the roadmap first

The end of a session is when the roadmap is most likely stale, because a step may have been completed by hand rather than through the skill that would have recorded it. Read it, compare it with what actually happened, and correct it. If the session completed a step, the roadmap says so before the handoff is written; a drifted roadmap is worse than none, because the next session believes it.

## Afterwards

Give the user two or three lines in the chat saying what was written. They are ending the session, not starting a review.
