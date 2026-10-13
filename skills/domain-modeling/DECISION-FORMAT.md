# Decision Record Format

One page, one decision. Records live in the decisions directory of the knowledge base (named in the knowledge base map; `specs/decisions/` in a project set up by `project-init`), one file per decision, outside the repository. The repository holds the consequences of a decision, each pointing at the record rather than restating it.

Create the directory lazily, when the first record is needed.

## When a record is warranted

All three must be true:

1. **Hard to reverse.** The cost of changing your mind later is meaningful.
2. **Surprising without context.** A future reader will look at the result and wonder why on earth it was done this way.
3. **The result of a real trade-off.** There were genuine alternatives and one was picked for specific reasons.

If a decision is easy to reverse, skip it: you will just reverse it. If it is not surprising, nobody will wonder. If there was no real alternative, there is nothing to record beyond "we did the obvious thing."

`stack-decisions` is the exception: it records every settled stack question, because stack choices carry lock-in.

### What qualifies

- **Architectural shape.** "We use a monorepo." "The write model is event-sourced, the read model is projected into Postgres."
- **Integration patterns between contexts.** "Ordering and Billing communicate via domain events, not synchronous HTTP."
- **Technology choices that carry lock-in.** Database, message bus, auth provider, deployment target. Not every library, only the ones that would take a quarter to swap out.
- **Boundary and scope decisions.** "Customer data is owned by the Customer context; others reference it by ID only." The explicit no-s are as valuable as the yes-s.
- **Deliberate deviations from the obvious path.** "Manual SQL instead of an ORM, because X." Anything where a reasonable reader would assume the opposite. These stop the next engineer from "fixing" something deliberate.
- **Constraints not visible in the code.** "No AWS because of compliance." "Responses under 200 ms because of the partner API contract."
- **Rejected alternatives when the rejection is non-obvious.** If GraphQL was considered and REST picked for subtle reasons, record it, or someone suggests GraphQL again in six months.

## Numbering

Scan the decisions directory for the highest existing number and add one: `NNN-slug.md`.

## Template

```md
---
title: <NNN> - <Decision>
status: accepted   # proposed | accepted | superseded by <link>
date: <YYYY-MM-DD>
tags: [decision]
---

# <NNN>: <The decision in one sentence>

## Status
<Accepted since ... / superseded by ...>

## Context
<The problem and the forces at work. Three to six sentences.>

## Decision
<What we do. Active voice.>

## Reasoning
<Why this option won, including the main rejected alternatives with one
sentence each on why not.>

## Consequences
<Positive and negative. Debt taken on. The trigger that would reopen this,
in the form "only once X, then Y".>
```

A record can be short. The value is in recording that a decision was made and why, not in filling sections. Context, Decision and Reasoning always appear. Status and Consequences appear when they carry something: a revisited decision, a non-obvious downstream effect, a reopening trigger. Leave an empty section out rather than writing filler.
