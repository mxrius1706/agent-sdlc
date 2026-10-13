---
name: write-spec
description: "Write the technical specification for exactly one component, verified against the code rather than from memory, and connected to the specs around it. Covers the current state, the delta of what stays, changes, is new and becomes obsolete, the effects on neighbouring components, the requirements, the contracts and the acceptance criteria. Use it when a component needs specifying before it is built, when an existing spec has to be brought up to date after a change, or when a decision needs recording (the format comes from domain-modeling). Run it after the component map exists, one call per document."
---

# Write Spec

One call, one document.

A specification written from memory is a wish list. This one is written against the code, so every claim about what exists carries a file path, and every claim about what should exist carries a reason. The valuable half is not the requirements; it is the four checks around them, because those are what stop a set of specs from slowly contradicting itself.

## Ground rules

**Never write about the code from memory.** Every statement about what exists is verified by reading or searching, and cited with its path. Not verified means not claimed.

**The product definition is the product truth.** Where the code contradicts it, that is a delta to document, not a licence to quietly reinterpret the product. A real conflict is marked as an open point and raised, not resolved in passing.

**A spec describes the target state and the way there.** Not only "this is how it should be", but explicitly what stays, what changes, what is new, and **what the change leaves obsolete, inconsistent or in need of straightening**. A rebuild cuts both ways. Specifying only the additions and leaving the rest lying is half a spec.

**Leave empty template sections out.** Six filled sections beat fourteen half ones. Current state, delta and effects are the exception: they are why this skill exists and they always appear.

**Write links with the full path the knowledge base resolves unambiguously.** A shortened form that depends on a setting will one day resolve somewhere else, and following a broken link creates a document in the wrong place.

**Follow the project's own conventions** for documentation language, formatting and identifier language. They are recorded in the project configuration; read them rather than importing habits from elsewhere.

## Before anything: know where things are

The knowledge base map in the project configuration says where the product definition, the spec index and the decision records live. Read it rather than assuming a layout.

Where a tool is used to write into the knowledge base, check the name against the server that is actually running. Two servers can carry the same configured name while only one is connected, and their tools are named differently. A mandated tool that does not exist is worse than no instruction, because the step fails silently and the work continues without it.

## Phase 0: Load the sources

- **The product definition**, at least the sections that touch this component.
- **The neighbouring specs** named in the component map. Do not specify what they own; link to it.
- **The relevant path-scoped rules** in the repository, where the component touches paths they cover.
- **The incoming-link scan.** This one is cheap and easy to skip, and skipping it is the most common cause of contradictions.

### The incoming-link scan

Search the specs for links pointing **at** this document, then read only the sentences that reference it, not the whole documents.

The question is not "who mentions me" but **"what has someone already assumed about me?"** A field name, a behaviour, a state, a permission. Components written late get referenced before they exist, so the documents pointing at them carry expectations. This document must either honour those or knowingly break them.

Findings feed the reverse check in phase 2.

## Phase 1: Current state, from code only

Verify what exists for this area, and list it with paths. Only what this document needs, not an inventory of the repository.

Which paths those are follows from the stack: the schema or model definitions, the request handlers, the interface files, the shared libraries, the configuration, the tests. Read the stack decisions rather than assuming a layout.

**Code is the only authority for what exists.** A plan document drifts and cannot see reverts or half-built work.

**Enumerate structurally, do not only search.** List the affected trees rather than grepping for what you expect to find. The blind spot is not "searched and found nothing", it is "did not think to search for it".

**Check the existing state for internal consistency**, not just for presence. This is where the findings come from that nobody is looking for:

- **Declared versus enforced.** A permission, an enum value or a configuration key used in the code but defined nowhere. Or the reverse, defined and long dead.
- **Name drift.** A field or route still named after a concept that has since been replaced.
- **Remnants** of features that were removed except in one place.

These are the raw material for the sweep in phase 2. They fall through otherwise, because the natural question is "what am I building" and never "what is already wrong here".

## Phase 2: The delta

For each relevant existing piece, a classification with one sentence of reasoning:

- **Keep** - fits the target unchanged
- **Adapt** - stays, needs changing, and exactly what
- **New or replace** - with the reason from the product definition
- **Remove or check or straighten** - what the change makes obsolete, redundant or inconsistent

### The redundancy sweep

Not optional. **Additions announce themselves; redundancy does not.** So ask the existing system directly what this change leaves behind:

- **Becomes obsolete.** A model, field, permission or route whose purpose disappears with the change. Remove it, or, where only a product question is open, mark it as "check" with a note on **who** decides. Never delete blind.
- **Needs straightening.** The inconsistencies found in phase 1. Even when they are not strictly part of this document, if the document touches them they come along as an adaptation, otherwise the defect stays.
- **Classify honestly.** Not every finding is a removal. Separate a genuine break, which goes out or gets straightened, from a scope question, which becomes an open point. Wrongly declaring something redundant does as much damage as missing it.

### The ripple check, forwards

Which other components does each adaptation **and each straightening** touch? A field added to an entity reaches the contracts, the lists that display it, the integrity payload, the audit trail. A renamed permission reaches the seeded roles, the routes and the interface labels.

Note each as a link to the affected spec, **even when that document does not exist yet**. A link to nothing is a known hole, and a known hole is the point.

### The reverse check, backwards

For every assumption a **already written** spec made about this document, from the phase 0 scan: either **confirm** it, or **break it deliberately** and mark the referencing spec with a note saying which assumption broke and that it needs following up. Never diverge silently.

A break that neither side records is exactly the quiet contradiction this check exists to prevent.

Know what this does not catch: it finds "someone already relied on me". It does not find "a decision changed afterwards". That needs a decision record, the ripple list and a later consistency pass across the whole graph.

## Phase 2b: Open points, grill rather than guess

The moment an open point blocks the document, an architectural fork, an unresolved delta, a contradiction between the existing system and the product definition, it is neither written away as a silent `TBD` nor asked casually in passing. Invoke `grill-me` and work it properly.

**Separate two kinds of open point, because they need opposite handling:**

- **Decidable now**, a technical fork that the product definition and the code can settle between them. Grill it until it is clear, then write the result into the document, and record it as a decision if it meets the three criteria (hard to reverse, surprising without context, the result of a real trade-off), which come from calling the Skill tool with "domain-modeling".
- **Only answerable by someone else**, typically a customer or a stakeholder. Whether anyone will pay for something, what a field must contain in practice, what response time is expected. Do **not** grill the user for knowledge they do not have. It stays an open point with a note on who has to answer it.

Grilling means sharpening decisions, not interrogating someone where the knowledge is simply absent.

Anything settled in the round goes into the document, in the section it belongs to. Nothing that was just decided is left standing as open.

## Phase 3: Write

Use the template. Write to the location the component map assigned, then update the spec index with the new status and date. An index that has not been updated hides the work from everyone who looks there first.

For a decision, call the Skill tool with "domain-modeling": it holds the decision record format and the criteria for when a record is warranted. One page, one decision.

## Phase 4: Short report

Three things, no more. What was decided, including what the grilling settled. Which ripple effects point at which other documents. Which open points remain, and who has to answer them.

---

## Spec template

```md
---
title: <Title>
status: draft
date: <YYYY-MM-DD>
product: "[[<product definition>#<section>]]"
tags: [spec, <area>]
---

# <Title>

<Two or three sentences. What this document settles, and for whom.>

## Purpose and scope

<What is covered. What is deliberately not, each with a link to whoever owns it.>

## Terms

<Only terms that are new here. The rest links to `GLOSSARY.md` in the vault; a term that
is new and will be reused goes into the glossary, not only here.>

## Current state (verified <date>)

<What exists, with file paths. The result of phase 1.>

## Delta

<Keep, adapt, new, remove or check. Bold keyword first, then the reason.
Mandatory even when it looks empty: what the change leaves obsolete,
redundant or in need of straightening. Separate a genuine break from a
scope question; the latter belongs in open points.>

## Effects on other components

<The ripple list, as links. Per entry, what has to happen there.>

## Requirements and rules

<Numbered so they can be referenced. Prefixes: REQ functional, SEC security,
CON constraint, GUD guideline, PAT pattern.>

- **REQ-001**: ...
- **SEC-001**: ...
- **CON-001**: ...

## Interfaces and contracts

<Routes, payloads, models, events. As code blocks, not wide tables.>

## Acceptance criteria

- **AC-001**: Given <context>, when <action>, then <result>.

## Test strategy

<Which test cases cover which acceptance criteria, against the project's
stated testing requirements.>

## Reasoning and context

<Why this way, only where it does not follow obviously from the product
definition. Anything worth a decision record goes there instead and is
linked from here.>

## Open points

<What has to be clarified, and by whom. TBD explicitly. Invent nothing.>

## Related documents

<Links: product sections, neighbouring specs, decision records, repository rules.>
```

## Before finishing

Update the spec index with this document's status, then the roadmap in the knowledge base: raise the written count and set the next action to the next document in the writing order. The index owns the per-spec status, the roadmap only points at it; on a disagreement the index wins.

Where this spec produced ripple effects that oblige another document to change, name that as the next action instead, so a correction that is owed does not sink beneath the next new spec.
