---
name: spec-consistency
description: "Check the written specs for contradictions - against the product definition, against the accepted decisions, and against each other. Reports findings sorted by severity and never fixes anything. Use it after a decision changes that existing specs cite, once a cluster of related specs is finished, before a phase that consumes the specs wholesale, or whenever someone asks whether the specs still fit together, are contradiction-free, or should be reviewed against each other. Not for reviewing code, and not for writing specs."
---

# Spec Consistency

Find the contradictions that individual spec writing cannot catch.

Writing one spec already checks two things: which other documents this change touches, and which of them had already assumed something about it. What that cannot catch is the third case, and it is the expensive one: **a decision changed after the specs were written against it.** Nobody notices, because nothing about writing spec twelve makes anyone reread spec three.

That is what this exists for. It reads and reports. It never edits.

## When to run it

The trigger is a change in what the specs depend on, not a count of specs written. A run after five specs in which nothing was decided differently searches for a class of defect that is not there, and a run scheduled five specs after a decision changed arrives once the mistake has been copied into five more documents.

**A decision was written or changed that existing specs cite.** Run immediately, over exactly the specs that cite it. This is the highest-yield case by a wide margin and it is cheap, because it touches a handful of documents rather than the graph.

**A spec deliberately broke an assumption another one had made.** Spec writing records that as a debt. While it is open, the two documents disagree on purpose, and the longer that stands the more likely a third is written against the wrong side.

**A cluster of related specs is finished.** They were written against each other, some against drafts of neighbours that changed afterwards. Run over the cluster.

**Before a phase that consumes the specs as a whole.** Planning the screens and deriving the build order both read everything at once. A contradiction that survives until then does not stay in a document, it propagates into the page list or the build sequence, where it is far more expensive.

**As a backstop, a count.** If several specs have been written since the last run and none of the triggers above fired, run anyway. Not because any particular number is right, but because a purely event-driven procedure fails silently when nobody recognises an event as one.

**Targeted or full.** A targeted run covers the specs citing one changed decision and is cheap enough to do the same day. A full run covers the graph and earns its cost only at the phase boundaries. Say which one is being done and why, because a targeted run reported as a full one leaves everything it did not look at appearing clean.

## Why not everyone against everyone

A contradiction between two specs is one fact, not two. Having every reviewer check every other document is quadratic, reports each finding twice, and spends most of its effort on pairs that have nothing to do with each other.

Real contradictions sit in two places: **against the invariants**, meaning the product definition, the accepted decisions and the canonical values, and **between specs that explicitly reference each other**, which every spec already lists in its effects and related-documents sections.

So: check the invariants for every spec, and check pairs only along the declared edges, each edge exactly once. Same coverage, a fraction of the work.

## Ground rules

**Read-only.** This never changes a spec, the product definition or a decision record. It produces a report. Fixing is a separate step the user starts, done with the spec-writing skill so the fix goes through the same checks as the original.

**The product definition and the accepted decisions are the truth.** A spec that contradicts either is the one that is wrong, and that is the highest severity. Where two specs disagree and neither cites the product definition, it is a judgement call and gets marked as one rather than decided here.

**Only written specs.** Read the status from the index and skip anything still planned. A link to a document that does not exist yet is deliberate, a known hole, and reporting it as a finding trains people to ignore the report.

**Delegation is not contradiction.** "Detail lives in that other document" is the structure working as intended. Only genuine conflicts of content count.

## Phase 0: Inventory, invariants, edges

Done once, by the coordinating session, and the result is handed to every reviewer so none of them has to derive it again.

**The inventory.** Read the spec index. Which specs are written, which are still planned.

**The invariant ledger.** Compact, keywords rather than full text:

- Every accepted decision, one sentence each on what it settled
- The canonical values from the entity model: the enums that exist and their valid members, which field carries which state
- The full permission or role vocabulary, with meanings
- The core glossary: `GLOSSARY.md` in the vault, found through the knowledge base map, with each term's `_Avoid_` list

This ledger is the single most useful artefact in the run. Most real breaks are a spec still using a value that was renamed, a permission that was consolidated away, or a sentence that quietly reverses a decision.

**The edge map.** From each spec, its declared effects and related documents. That is the pair list, and each pair appears once: assign it to whichever end comes first alphabetically so it is not checked from both sides.

## Phase 1: One reviewer per spec

Give each written spec its own read-only reviewer, working in parallel, each carrying the ledger and its assigned edges. Four axes:

**Product alignment.** Does the spec contradict the parts of the product definition it cites? Read those parts rather than assuming.

**Internal consistency.** Do its own requirements contradict each other? Do the acceptance criteria cover the requirements? Do the interfaces match what the requirements describe? Any dead or outdated value.

**Invariant fidelity.** Does it honour every accepted decision, every canonical value, every permission name in the ledger? The most common break by far. A term the glossary lists under `_Avoid_` but a spec uses is a finding too. It is minor as plain wording drift, and rises only where the stray word creates a contradiction, for instance by naming a different concept than the canonical term.

**The assigned edges.** For each, read the target and check whether their shared statements agree. Only the assigned ones.

Every finding carries a severity, the contradiction in one sentence, both locations with quotes, and which side is probably right with the reason. Nothing invented, nothing fixed.

**Severity:**

- **Critical** breaks an accepted decision or the product definition, or two specs state opposites about the same model, permission or transition.
- **Major** is a gap between requirement and acceptance criterion, an outdated canonical value, an interface that does not match its requirement.
- **Minor** is wording drift, a missing cross-link, an imprecise reference.

## Phase 2: Synthesis and report

Collect, **deduplicate** where both ends reported the same pair, sort by severity.

The report names what was checked and what was skipped, then the findings grouped by severity, each with both locations, the likely correct side and the reason, and a recommended direction. It also names the specs with no findings, because "checked and clean" is information and its absence reads like an oversight.

Say plainly which run this was, targeted or full, and what a targeted run did not look at.

**Do not fix.** Offer at the end to follow up individual findings through the spec-writing skill, one at a time, under the user's control. A consistency run that fixes as it goes is a run nobody reviewed.

## Scope discipline

No style or wording criticism unless it produces an actual contradiction.

Do not check against superseded documents. A frozen earlier version of the product definition will generate a stream of false alarms and, worse, tempt someone to "correct" a spec back to a superseded state.

Where a finding is one the spec-writing checks should have caught, report it anyway. This is the safety net, and a net that stays quiet about what slipped through is not measuring anything.

## Before finishing

Record the run in the roadmap: the date, whether it was targeted or full, how many findings by severity, and how many are still open. That is what makes the next run's timing decidable, because the question is always "what has changed since the last one" and that needs a last one on record.

Open critical findings become the next action. A contradiction against an accepted decision outranks the next new spec, because every document written while it stands may inherit it.
