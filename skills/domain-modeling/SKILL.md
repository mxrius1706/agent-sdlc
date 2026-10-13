---
name: domain-modeling
description: Build and sharpen a project's domain language and decisions. Use when terminology is fuzzy or contested, when a glossary term is resolved or GLOSSARY.md is edited, or when a decision should be recorded or a record's format is needed.
---

# Domain Modeling

Actively build and sharpen the project's domain model while designing: challenge terms, invent edge-case scenarios, and write the glossary and the decisions down the moment they crystallise. Merely reading `GLOSSARY.md` for vocabulary is not this skill; that is a one-line habit any skill has. This skill is for when the model is being changed, not just consumed.

## Where things live

Both artefacts live in the knowledge base, not in the repository. The knowledge base map in the project's root `CLAUDE.md` says where; read it rather than assuming a layout.

- **The glossary:** `GLOSSARY.md` next to the product definition. Most projects have a single context and a single glossary.
- **Several contexts:** a `GLOSSARY-MAP.md` in the vault lists them, where each glossary lives and how the contexts relate. Format in [GLOSSARY-FORMAT.md](./GLOSSARY-FORMAT.md).
- **Decision records:** the decisions directory the map names (`specs/decisions/` in a project set up by `project-init`). Format in [DECISION-FORMAT.md](./DECISION-FORMAT.md).

Create files lazily, only when there is something to write. No `GLOSSARY.md` yet: create it when the first term is resolved. No decisions directory: create it when the first record is needed. If the map has no row for the glossary or says `TBD`, create the file next to the product definition and fill the row in.

## During the session

### Challenge against the glossary

When the user uses a term that conflicts with the glossary, say so at once. "The glossary defines 'cancellation' as X, but you seem to mean Y. Which is it?"

### Sharpen fuzzy language

When a term is vague or overloaded, propose a precise canonical term. "You say 'account': the Customer or the User? Those are different things."

### Discuss concrete scenarios

When relationships between concepts are discussed, stress-test them with specific scenarios. Invent ones that probe the edges and force the user to be precise about where one concept ends and the next begins.

### Cross-reference with code

When the user states how something works, check whether the code agrees. A contradiction gets surfaced: "The code cancels whole Orders, but you just said partial cancellation is possible. Which is right?"

### Update the glossary inline

When a term is resolved, update `GLOSSARY.md` right there. Do not batch; capture terms as they happen, in the format of [GLOSSARY-FORMAT.md](./GLOSSARY-FORMAT.md).

The glossary holds no implementation detail. It is not a spec, not a scratch pad and not a place for implementation decisions. It is a glossary and nothing else.

### Offer records sparingly

Offer a decision record only when all three criteria hold. If one is missing, skip it. The criteria and the format are in [DECISION-FORMAT.md](./DECISION-FORMAT.md).

**Stack decisions are the exception to the weighing.** `stack-decisions` records every settled stack question by its own rule, because stack choices carry lock-in, and it writes them in this format.
