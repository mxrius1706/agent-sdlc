# The session handoff

`.claude/state.md` carries what happened in the last session, and nothing else. A SessionStart hook injects it before the first prompt.

It is committed, not ignored. What was done last session is a fact about the project, and an ignored file is gone after a machine change.

## Handoff vs roadmap

**The roadmap** answers *where are we and what comes next*. It changes when a step completes and lives in the knowledge base (`references/roadmap.md`). **The handoff** answers *what happened last time*. It is overwritten every session. The handoff never says where the project stands in the process; mixing them buries the durable answer under the volatile one.

## Shape

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

## Rules

**Facts only.** What the next session cannot reconstruct: which branch, which commit range, how many tests passed, which gate is through.

**"Nächstes" has to be actionable.** Name the file, the document or the command; if the order matters, say why, since that reasoning is what will be missing.

**Around fifteen lines.** Beyond it the file stops being read, and an unread handoff is the same as none.

**Omit empty sections.**

**Overwrite, do not append.** Only the last session is relevant; version control holds the history.

**A correction owed is the next step.** Something noticed but not fixed outranks the next new piece of work, otherwise it sinks and resurfaces as a bug.

## Who writes it

`session-recap` at the end of a session, triggered by a hook on farewell phrases.
