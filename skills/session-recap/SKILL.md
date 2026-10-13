---
name: session-recap
description: "Write the handoff for the next session into .claude/state.md. Use at the end of a working session, when the user says goodbye or signals stopping for the day, or asks for a handoff or where things stand. A hook triggers it on farewell phrases."
---

# Session Recap

Every session starts with an empty context window. What the last one learned is gone unless it was written down, and reconstructing it costs more than writing it did. This writes the handoff: a minute now, twenty saved later.

## Where it goes and what it looks like

Into `.claude/state.md`, overwritten each time. Format, rules (facts only, actionable "Nächstes", around fifteen lines, omit empty sections, overwrite) and the split from the roadmap are owned by `project-init/references/state-file.md`; read it before writing.

## Check the roadmap first

The end of a session is when the roadmap is most likely stale, because a step may have been completed by hand rather than through the skill that would have recorded it. Read it, compare it with what actually happened, and correct it. If the session completed a step, the roadmap says so before the handoff is written; a drifted roadmap is worse than none, because the next session believes it.

## Afterwards

Give the user two or three lines in the chat saying what was written. They are ending the session, not starting a review.
