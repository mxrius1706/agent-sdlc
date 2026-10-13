---
name: stack-decisions
description: "Settle the technical decisions a project runs on - language, framework, data layer, validation, auth, testing, deployment and secret handling - and record each one as a decision that can be traced later. Use this at the start of a project, and use it again whenever a technology is being added, replaced or dropped. Triggers include asking which database to pick, whether to switch ORM, how to handle secrets, whether to drop an auth broker, or saying the stack needs deciding. Also use it when configuration files describe a stack nobody ever confirmed. Deliberately separate from the product definition, because a product document never says what to build with."
---

# Stack Decisions

Settle what the project is built with, and leave a record of why.

Two things make this worth its own conversation. A product definition never answers it, so guessing from one produces confident rules for technology nobody chose. And these decisions do not all happen at the start: an ORM gets replaced, an auth broker gets dropped, a queue gets added, and each of those is the same conversation again on a smaller scale.

## Two ways this runs

**As part of setting a project up.** `project-init` calls this in its phase 2, after the product definition exists and before any configuration is written. Nothing is built yet, so every answer is a choice.

**On its own, later.** A technology is being added, replaced or dropped in a project that already runs. Most answers already exist in the code; only the ones in question are open.

The difference matters mainly for what you do first.

## Before asking anything, read what is already true

Skip this only when the repository is genuinely empty.

Finding facts is your job, not the user's. Read the package manifest, the lockfile, the container and deployment files, the test configuration, the schema or migration directory. What the code says is the current state, and asking someone to recite it wastes their attention and invites a wrong answer from memory.

Come to the interview with the current state established and ask only what is actually open. "You are on Prisma with MySQL and Vitest. The question on the table is the queue, correct?" is a better opening than a blank questionnaire, and it lets the user correct you where the code and their intention have drifted apart.

## The interview

Invoke `grill-me`. It works the decisions as a tree, one round per set of questions whose prerequisites are settled, each with a recommendation.

Cover at least these, and skip any that are already settled and not in question:

- **Language and runtime**, with versions where a version actually changes what you can write
- **Framework**, and specifically which of its conventions this project adopts and which it deliberately does not
- **Data layer**: database, ORM or query layer, migration tooling
- **Validation**: where input is checked, with what, and what happens when it fails
- **Authentication and authorization**, including where in the request path the check sits
- **Testing**: framework, what must be covered, and what is deliberately left uncovered. This decision also settles the **after-edit check**: the fast, deterministic commands that run after every edit (type check, lint of the touched files, never the full suite). `project-init` writes them to `.claude/checks.json`, so name each command exactly as it will be run
- **Deployment target**, to the depth that it affects the code
- **Secret handling**: where secrets live and how the code reaches them

The last one is worth pushing on even when it sounds settled. It is the decision most often left implicit, and the one whose absence shows up as credentials in a config file.

Anything the user cannot answer stays `TBD`, with a note on what would settle it. A `TBD` a future session can act on beats an invented answer it will trust. Recommend, do not decide: put each question to the user with your recommendation and wait.

## Recording the outcome

A decision that exists only in a chat log did not happen. Each settled question becomes a record before this skill is done.

**Where it goes:** the decisions directory of the project's knowledge base, outside the repository, one file per decision. The repository holds the consequences of a decision, not the decision itself. Duplicating the reasoning into a `CLAUDE.md` creates the second version that will eventually disagree with the first.

**What a record carries, and how it is written:** the format comes from calling the Skill tool with "domain-modeling". Stack choices carry lock-in, so every settled question gets a record by this skill's own rule, without weighing the three criteria again. Record what it replaces if anything, and the rejected options: they are the part people skip and the part that pays off, because the question comes back and without them it gets re-argued from zero.

**What changes in the repository:** only what follows from the decision. A stack entry, a rule, a convention. Each pointing at the decision record rather than restating it.

## When something is being replaced

This is the case that goes wrong most often, and it has its own discipline.

A replacement is almost never instant. The old technology keeps running while the new one is built, and during that window both are real. Documentation written as though the new one were already in place quietly teaches every session the wrong thing about what is actually running.

So when a decision retires something, the documentation for the old thing gets an expiry note rather than a deletion: what runs today, what replaces it, which decision settled that, and what may no longer be built on it. Concretely, the useful sentence is a prohibition on new work, not a claim about the present. "No new workflows here" is true immediately. "We do not use this" is false until the day it is not.

Delete only when the thing is actually gone from the code. A trimmed document for a system still in the repository leaves the files without guidance, which is worse than a document that is honest about its own expiry date.

## What not to do

**Do not read the stack out of the product definition.** It does not contain one, and a good product document says so by leaving it open rather than guessing.

**Do not write a rule for a technology that was not confirmed.** Specific, confident rules for an unchosen stack are indistinguishable from correct ones, and they will be followed.

**Do not settle everything at once when only one thing is in question.** Reopening decisions that are working costs attention and invites churn.

## When called by project-init

Return the settled decisions and the open `TBD` items. Phase 3 derives the area map from them, so a decision left vague here becomes a vague area file later.

## Before finishing

Update the roadmap in the knowledge base: mark the stack step, and set the next action to whatever actually comes next. The roadmap is the one place that answers where the project stands, and one nobody updates is wrong within two weeks.

If decisions were left open, say so there rather than marking the step done. A step marked complete that was not is worse than one marked open, because the next session stops asking.
