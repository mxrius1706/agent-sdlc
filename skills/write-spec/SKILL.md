---
name: write-spec
description: "Write the technical specification for exactly one component, verified against the code. Use when a component needs specifying before it is built, when an existing spec must be brought up to date after a change, or when a decision needs recording. Run after the component map exists, one call per document."
---

# Write Spec

One call, one document.

A specification written from memory is a wish list. This one is written against the code: every claim about what exists carries a file path, every claim about what should exist carries a reason. The valuable half is the four checks around the requirements (redundancy sweep, ripple check, reverse check, incoming-link scan), because they stop a set of specs from slowly contradicting itself.

## Ground rules

**Code is the only authority for what exists.** Every statement about the code is verified by reading or searching and cited with its path; not verified means not claimed. A plan document drifts and cannot see reverts or half-built work.

**The product definition is the product truth.** Where the code contradicts it, that is a delta to document; a real conflict becomes an open point and is raised.

**A spec describes the target state and the way there**: what stays, what changes, what is new, and **what the change leaves obsolete, inconsistent or in need of straightening**. Specifying only the additions is half a spec.

**Empty template sections stay out.** Six filled sections beat fourteen half ones. Current state, delta and effects always appear.

**Links use the full path the knowledge base resolves unambiguously.** A shortened form will one day resolve somewhere else and create a document in the wrong place.

**The project's own conventions** for documentation language, formatting and identifier language are in the project configuration; read them.

## Before anything: know where things are

The knowledge base map in the project configuration says where the product definition, the spec index and the decision records live. Read it. Check tool names for writing into the knowledge base against the running server, per `config-sync`.

## Phase 0: Load the sources

- **The product definition**, at least the sections that touch this component.
- **The neighbouring specs** named in the component map. Link to what they own.
- **The path-scoped rules** in the repository that cover the component's paths.
- **The incoming-link scan.** Cheap, easy to skip, and the most common cause of contradictions.

### The incoming-link scan

Search the specs for links pointing **at** this document and read only the sentences that reference it. The question is **"what has someone already assumed about me?"**: a field name, a behaviour, a state, a permission. Components written late get referenced before they exist, so the documents pointing at them carry expectations. This document honours them or knowingly breaks them. Findings feed the reverse check in phase 2.

## Phase 1: Current state, from code only

List what exists for this area with paths, only what this document needs. The stack decisions tell which paths: schema or model definitions, request handlers, interface files, shared libraries, configuration, tests.

**Enumerate structurally.** List the affected trees rather than grepping for what you expect; the blind spot is "did not think to search for it".

**Check the existing state for internal consistency**, not just presence. These findings are the ones nobody is looking for:

- **Declared versus enforced.** A permission, enum value or configuration key used in code but defined nowhere, or defined and long dead.
- **Name drift.** A field or route still named after a replaced concept.
- **Remnants** of features removed except in one place.

They are the raw material for the sweep in phase 2: the natural question is "what am I building", never "what is already wrong here".

## Phase 2: The delta

For each relevant existing piece, a classification with one sentence of reasoning:

- **Keep** - fits the target unchanged
- **Adapt** - stays, needs changing, and exactly what
- **New or replace** - with the reason from the product definition
- **Remove or check or straighten** - what the change makes obsolete, redundant or inconsistent

### The redundancy sweep

Mandatory. **Additions announce themselves; redundancy does not.** Ask the existing system what this change leaves behind:

- **Becomes obsolete.** A model, field, permission or route whose purpose disappears. Remove it, or where only a product question is open mark it "check" with **who** decides. Delete only with evidence.
- **Needs straightening.** The phase 1 inconsistencies. If the document touches them they come along as an adaptation, otherwise the defect stays.
- **Classify honestly.** A genuine break goes out or gets straightened; a scope question becomes an open point. Wrongly declaring something redundant does as much damage as missing it.

### The ripple check, forwards

Which other components does each adaptation **and each straightening** touch? A field added to an entity reaches the contracts, the lists that display it, the integrity payload, the audit trail. A renamed permission reaches seeded roles, routes and interface labels. Note each as a link to the affected spec, **even when it does not exist yet**: a link to nothing is a known hole.

### The reverse check, backwards

For every assumption an **already written** spec made about this document (phase 0 scan): **confirm** it, or **break it deliberately** and mark the referencing spec with which assumption broke and that it needs following up. A break that neither side records is the quiet contradiction this check exists to prevent.

It finds "someone already relied on me". It cannot find "a decision changed afterwards"; that takes a decision record, the ripple list and a later consistency pass (`spec-consistency`).

## Phase 2b: Open points, grill rather than guess

An open point that blocks the document (architectural fork, unresolved delta, contradiction between system and product definition) is worked with `grill-me`.

Two kinds need opposite handling:

- **Decidable now**: a technical fork the product definition and the code settle between them. Grill until clear, write the result into the section it belongs to, and record it as a decision when it qualifies (Skill tool with "domain-modeling" holds the criteria).
- **Only answerable by someone else** (customer, stakeholder: will anyone pay, what must a field contain, what response time is expected). It stays an open point with a note on who answers it; the user is grilled only for knowledge they have.

Nothing just decided is left standing as open.

## Phase 3: Write

Use the template. Write to the location the component map assigned, then update the spec index with status and date; an index that is not updated hides the work from everyone who looks there first.

For a decision, call the Skill tool with "domain-modeling": it holds the record format. One page, one decision.

## Phase 4: Short report

What was decided, including what the grilling settled. Which ripple effects point at which documents. Which open points remain, and who answers them.

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
