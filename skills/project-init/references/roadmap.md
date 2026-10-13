# The roadmap

`roadmap.md` in the knowledge base is the only file that answers "where are we and what comes next". It starts as the setup process and grows into the build plan: the same document at two stages of a project's life, which is why it is created at the very beginning.

## Shipped filled in

`templates/roadmap.md` carries the steps, the skill that performs each one and the rules. Copy it in during phase 0, **before the product definition exists**, and adjust only what is project-specific.

Status marks: `⬜` open, `🔄` in progress, `✅` done, `❌` deliberately dropped. Drop steps that do not apply rather than marking them done: a project without an interface has no design system and no UI specs, and leaving them open makes the file look unfinished forever.

## Every step names what it needs

The `Setzt voraus` column lists the step numbers that must stand before a step starts, which turns an implied order into a checkable fact. `❌` counts as done, since a dropped step blocks nothing. The rule that goes with it (the wording is owned by `project-init`, see `references/routing.md`) sits in the template's **head** on purpose: once the build phases are in the file, the head is the only part injected regardless of size.

## Kept current

A roadmap that is not updated is worse than none, because the next session believes it.

**Each skill records its own step.** When a step completes, the skill that completed it writes that in, along with the next action. Nothing that depends on a person remembering survives a busy week.

**"Als Nächstes" is an action, not a phase name.** "Specs" tells a new session nothing; "Write the entity model first, everything else references it" says where to begin and why. The reasoning behind the order is the part nobody has after a few days.

Write what is true, not what is planned. A step that ran halfway is `🔄` with a note on what is missing.

## Reaching the session

**The SessionStart hook injects it**, so it is in context before the first prompt. Its path goes into `.claude/roadmap-path`, because the knowledge base sits outside the repository.

Once the build phases are in, the file is too large to inject whole. From then on the hook injects the head plus the one section named by the `**Aktuelle Bauphase:**` line, truncating neither. That line is load-bearing: pointing it at the wrong phase gives the next session the wrong phase with nothing failing. It is set at every phase change, in the same edit as the current position.

**The root configuration names it** as the place the status lives and states the obligation to keep it current. The hook covers the reading, the root file the writing.

## Where it does not overlap

The roadmap is a position marker, not a summary. The spec index owns which specs exist and their status; the roadmap carries at most a count and a pointer, and on a disagreement the index wins. The handoff in `.claude/state.md` owns the last session (see `references/state-file.md`).

## Later

Once the specs stand, `plan-build` writes the build phases into the `## Bauphasen` section of this file, derived from finished specs rather than guessed in advance. A second document answering the same question in more detail would drift apart from this one.
