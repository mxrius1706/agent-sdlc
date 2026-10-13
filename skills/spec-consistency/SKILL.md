---
name: spec-consistency
description: "Check written specs for contradictions against the product definition, accepted decisions and each other. Use after a decision changes that specs cite, when a cluster of specs is finished, before a phase that consumes the specs wholesale, or when someone asks whether the specs still fit together. Not for code review, not for writing specs."
---

# Spec Consistency

Find the contradictions that individual spec writing cannot catch. Writing one spec checks which other documents it touches and what they had assumed. It cannot catch the expensive case: **a decision changed after the specs were written against it.** Nothing about writing spec twelve makes anyone reread spec three.

> **Report only.**

## When to run it

The trigger is a change in what the specs depend on, not a count of specs written: a run after five specs with no changed decision hunts a defect class that is not there, and a run scheduled five specs after a decision changed arrives once the mistake has been copied further.

- **A decision was written or changed that existing specs cite.** Run immediately over exactly the specs that cite it. Highest yield by far, and cheap.
- **A spec deliberately broke an assumption another one had made.** Spec writing records that as a debt. While it is open the two documents disagree on purpose, and a third may be written against the wrong side.
- **A cluster of related specs is finished.** They were written against each other, some against drafts that changed later.
- **Before a phase that consumes the specs as a whole** (planning the screens, deriving the build order). A contradiction that survives until then propagates into the page list or build sequence, where it costs far more.
- **As a backstop, a count.** If several specs were written since the last run and no trigger fired, run anyway: a purely event-driven procedure fails silently when nobody recognises an event.

**Targeted or full.** Targeted covers the specs citing one changed decision; full covers the graph and earns its cost at phase boundaries. Say which one and why: a targeted run reported as full makes everything it skipped look clean.

## Why not everyone against everyone

A contradiction between two specs is one fact. All-pairs checking is quadratic, reports each finding twice, and spends effort on unrelated pairs. Real contradictions sit **against the invariants** (product definition, accepted decisions, canonical values) and **between specs that explicitly reference each other** (each lists them in its effects and related-documents sections). So: check the invariants for every spec, and pairs only along declared edges, each edge once.

## Ground rules

**The product definition and the accepted decisions are the truth.** A spec contradicting either is the one that is wrong, at the highest severity. Where two specs disagree and neither cites the product definition, mark it a judgement call rather than deciding it here.

**Fixing is a separate step** the user starts, through `write-spec`, so the fix passes the same checks as the original.

**Only written specs.** Read the status from the index and skip anything planned. A link to a not-yet-existing document is a deliberate, known hole; reporting it trains people to ignore the report.

**Delegation is not contradiction.** "Detail lives in that other document" is the structure working. Only genuine conflicts of content count.

## Phase 0: Inventory, invariants, edges

Done once by the coordinating session; the result goes to every reviewer.

**The inventory.** From the spec index: which specs are written, which planned.

**The invariant ledger**, compact (keywords, not full text):

- Every accepted decision, one sentence on what it settled
- The canonical values from the entity model: enums and their valid members, which field carries which state
- The full permission or role vocabulary, with meanings
- The core glossary: `GLOSSARY.md` in the vault, found through the knowledge base map, with each term's `_Avoid_` list

This ledger is the most useful artefact of the run. Most real breaks are a renamed value still in use, a consolidated-away permission, or a sentence that quietly reverses a decision.

**The edge map.** From each spec, its declared effects and related documents. Each pair appears once, assigned to whichever end comes first alphabetically.

## Phase 1: One reviewer per spec

Each written spec gets its own read-only reviewer, in parallel, carrying the ledger and its assigned edges. Four axes:

**Product alignment.** Does the spec contradict the parts of the product definition it cites? Read those parts.

**Internal consistency.** Do its requirements contradict each other? Do acceptance criteria cover the requirements? Do interfaces match the requirements? Any dead or outdated value?

**Invariant fidelity.** Does it honour every accepted decision, canonical value and permission name in the ledger? The most common break by far. A term the glossary lists under `_Avoid_` is a finding too: minor as plain wording drift, higher only where the stray word names a different concept than the canonical term and so creates a contradiction.

**The assigned edges.** For each, read the target and check whether the shared statements agree. Only the assigned ones.

Every finding carries a severity, the contradiction in one sentence, both locations with quotes, and which side is probably right with the reason.

**Severity:**

- **Critical**: breaks an accepted decision or the product definition, or two specs state opposites about the same model, permission or transition.
- **Major**: a gap between requirement and acceptance criterion, an outdated canonical value, an interface that does not match its requirement.
- **Minor**: wording drift, a missing cross-link, an imprecise reference.

## Phase 2: Synthesis and report

Collect, **deduplicate** where both ends reported the same pair, sort by severity.

The report names what was checked and skipped, then findings grouped by severity (both locations, likely correct side and reason, recommended direction), and the specs with no findings: "checked and clean" is information. State whether the run was targeted or full and what a targeted run did not look at.

Offer at the end to follow up individual findings through `write-spec`, one at a time, under the user's control.

## Scope discipline

Style and wording criticism only where it produces an actual contradiction.

Check against current documents only. A frozen earlier version of the product definition generates false alarms and tempts someone to "correct" a spec back to a superseded state.

Report a finding even when the spec-writing checks should have caught it: this is the safety net, and a net silent about what slipped through measures nothing.

## Before finishing

Record the run in the roadmap: date, targeted or full, findings by severity, how many still open. The next run's timing depends on "what changed since the last one", which needs a last one on record.

Open critical findings become the next action: a contradiction against an accepted decision outranks the next new spec, because every document written while it stands may inherit it.
