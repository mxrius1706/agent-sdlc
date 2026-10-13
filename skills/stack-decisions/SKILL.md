---
name: stack-decisions
description: "Settle the technical decisions a project runs on (language, framework, data layer, validation, auth, testing, deployment, secrets) and record each as a traceable decision. Use at project start, when a technology is added, replaced or dropped, when asked which database or ORM to pick, or when config describes a stack nobody confirmed."
---

# Stack Decisions

Settle what the project is built with, and leave a record of why.

A product definition never answers this, so guessing from one produces confident rules for technology nobody chose. And the decisions recur: an ORM gets replaced, an auth broker dropped, a queue added, each the same conversation on a smaller scale.

## Two ways this runs

**As part of setting a project up.** `project-init` calls this in its phase 2, after the product definition exists and before any configuration is written. Nothing is built yet, so every answer is a choice.

**On its own, later.** A technology is being added, replaced or dropped in a project that already runs. Most answers exist in the code; only the ones in question are open.

## Before asking anything, read what is already true

Unless the repository is empty, read the package manifest, the lockfile, the container and deployment files, the test configuration, the schema or migration directory. The code is the current state; asking the user to recite it invites a wrong answer from memory.

Come to the interview with the current state established and ask only what is open. "You are on Prisma with MySQL and Vitest. The question on the table is the queue, correct?" is a better opening than a blank questionnaire, and it lets the user correct you where the code and their intention have drifted apart.

## The interview

Invoke `grill-me`. It works the decisions as a tree, one round per set of questions whose prerequisites are settled, each with a recommendation.

Cover at least these, and skip any that are already settled and not in question:

- **Language and runtime**, with versions where a version actually changes what you can write
- **Framework**, and specifically which of its conventions this project adopts and which it deliberately does not
- **Data layer**: database, ORM or query layer, migration tooling
- **Validation**: where input is checked, with what, and what happens when it fails
- **Authentication and authorization**, including where in the request path the check sits
- **Testing**: framework, what must be covered, and what is deliberately left uncovered. This decision also settles the **after-edit check**: the fast, deterministic commands that run after every edit (type check, lint of the touched file via the `{file}` placeholder, never the full suite). `project-init` writes them to `.claude/checks.json`, so name each command exactly as it will be run
- **Deployment target**, to the depth that it affects the code
- **Secret handling**: where secrets live and how the code reaches them

Push on secret handling even when it sounds settled: it is the decision most often left implicit, and its absence shows up as credentials in a config file.

Anything the user cannot answer stays `TBD`, with a note on what would settle it; a future session can act on that, where it would trust an invented answer. Put each question to the user with your recommendation and wait.

## Recording the outcome

A decision that exists only in a chat log did not happen. Each settled question becomes a record before this skill is done.

**Where it goes:** the decisions directory of the project's knowledge base, outside the repository, one file per decision. The repository holds the consequences, not the decision: reasoning duplicated into a `CLAUDE.md` becomes the second version that will eventually disagree with the first.

**What a record carries, and how it is written:** the format comes from calling the Skill tool with "domain-modeling". Stack choices carry lock-in, so every settled question gets a record by this skill's own rule, without weighing the three criteria again. Record what it replaces if anything, and the rejected options: they are the part people skip and the part that pays off, because the question comes back and without them it gets re-argued from zero.

**What changes in the repository:** only what follows from the decision. A stack entry, a rule, a convention. Each pointing at the decision record rather than restating it.

## When something is being replaced

The old technology keeps running while the new one is built, and documentation written as though the new one were in place teaches every session the wrong thing. Apply the "stock with an expiry date" rule from the root `CLAUDE.md` (written by `project-init`): the old thing's documentation gets an expiry note, not a deletion. The useful sentence is a ban on new work ("No new workflows here"), true immediately, where "We do not use this" is false until the day it is not.

Delete only when the thing is gone from the code.

## Boundaries

**Rules need a confirmed technology.** Confident rules for an unchosen stack are indistinguishable from correct ones and will be followed; the product definition contains no stack.

**Settle only what is in question.** Reopening working decisions costs attention and invites churn.

## When called by project-init

Return the settled decisions and the open `TBD` items. Phase 3 derives the area map from them, so a decision left vague here becomes a vague area file later.

## Before finishing

Update the roadmap in the knowledge base: mark the stack step, and set the next action to whatever actually comes next. If decisions were left open, say so there rather than marking the step done: the next session stops asking about a step marked complete.
