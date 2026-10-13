---
name: plan-build
description: "Derive the build order from finished specs and write it into the roadmap as phases with gates. Use once specs and page plans stand and building is next, when asked in which order to build or how to cut phases, or to re-cut the plan after specs changed."
---

# Plan Build

Turn the finished specs into a build order.

Build order is a different question from writing order, and running them together is the usual mistake. **Writing order follows the references:** the entity model first, because everything points at it. **Build order follows the value:** what has to exist before anyone outside the project can see anything work. The two rarely coincide.

It runs once the specs stand, and again whenever enough changed that the cut no longer fits (see Re-running).

## Preconditions

**All planned specs are written, and the page plans exist** where the product has an interface. A half-written spec set gets phases cut around holes.

**A full consistency run has happened and its critical findings are closed.** A contradiction that survives to here becomes a phase boundary in the wrong place, found during the build.

If either is missing, name what is open and stop; a caveat is read once and the plan is read for months.

## Phase 0: Read everything

The spec index, every written spec, the page plans, the accepted decisions, the product definition. For brownfield, the current code as well: what exists, what already works, what is being replaced.

Read all of it: this step is the one place where a single reader holds the entire product in view.

## Phase 1: The dependency skeleton

Before any preference enters, establish the facts: **what cannot be built before what.**

From the spec graph. A spec that references another's model, its permissions or its interface cannot be built first. Record each edge with the sentence that creates it: "needs the status field from X, see REQ-004" is checkable and survives a change to X; "cannot start before X" is not.

The result is a partial order: it says what is forbidden, not what is best. The real decisions are among the orderings it still allows.

## Phase 2: Settle the cutting principle

Invoke `grill-me`. This is the most expensive single decision in the plan, and the specs cannot settle it; it depends on what only the user knows.

Three archetypes; a project usually mixes them:

**Inside out, layer by layer.** Data model, then the core interfaces, then the surfaces on top. Strong where the model is being reworked, because the alternative bends the model to fit whichever surface is being built. Weak on early visibility: the first two phases show nothing.

**Vertical slices.** Each phase carries one complete capability through every layer. Strong on visibility and feedback. Weak where the model is unsettled, because every slice touches it and the last slice pays for the first four.

**Wedge first.** The smallest piece that delivers value outside the project goes first. Strong when the product has to prove itself to someone. Weak when the wedge needs half the model anyway; check rather than assume.

Ask, with a recommendation from what the specs actually show:

- **Who sees the first working result, and when?** This settles more of the order than any technical argument.
- **Greenfield or brownfield?** Where something exists, the cut also says what is switched off when; switching off is often its own phase.
- **Is there a wedge**, and does it need so much underneath it that it stops being one?
- **What must not be built twice?** Anything built provisionally early and thrown away later is a reason to move it, or to accept the throwaway deliberately.
- **What is fixed from outside?** A date, an external system's availability, someone's holiday.

Record the answer as the ordering principle in one sentence. It goes at the top of the plan, and every later "why is this here" refers to it.

## Phase 3: Cut the phases

**A phase is one branch and one review**, so it has to be reviewable in one go. The sub-plan limit that marks a phase as too big is owned by `planning`.

**A phase ends in something demonstrable:** what can be shown or measured once it is done, beyond "the model is migrated". A phase that genuinely delivers nothing visible says so explicitly; if half the phases say it, the cut is wrong.

**Every phase names what it starts after, with the reason.** The reason is what stays useful: "after the portal core, because the agent delivers into triage and without triage it collects reports nobody looks at" is still true in six months; "after phase 3" is not information.

**Every phase names its spec sources as links**, which makes its content checkable rather than remembered.

## Phase 4: Gates

Every phase ends in a gate, and the gate is a list of sentences that are true or false.

The test for a gate item: **could someone who did not build it check it?** "Data model cleanly implemented" fails. "Migration runs through on a fresh database and on the dev database, schema diff empty" passes. "Tests written" fails; "existing suite green, new routes covered" passes.

Two or three items should be about the product rather than the code, phrased as the path a person takes through it. They catch a phase that is technically complete and practically unusable.

State in the plan that an open item means the phase is not finished; a gate that can be waved through is a checklist.

## Phase 5: Milestones

Two to four named points across the whole distance, each covering several phases, in business terms: "the wedge stands", "first real customer". They are what you tell someone who is not building, and the only place where the plan says "good enough for X".

## Phase 6: The ritual

Write the procedure once, at the top, and state that it holds for every phase without exception, so "how do we do this" is never asked again mid-build. This section owns the ritual and its gate order; other skills point here.

1. **Plan mode first**, before anything is touched and before the branch exists. Read and ask.
2. **A plan file per phase** via `planning`.
3. **The roadmap points at the plan.** No plan file without an entry here, or there are two truths about the same phase.
4. **The user releases the plan.** Only then is anything built.
5. **A branch per phase**, off the main branch, never on the previous phase's branch.
6. **Build along the plan** via `execute-plan`. Decisions go into the plan file as `planning` says.
7. **Tests** per the project's rules, `testing`.
8. **The gate**, item by item.
9. **The walkthrough** via `handlauf`, wherever the phase produced an interface, in a session of its own and with no input from any review (`handlauf` owns why). It runs before the code reviews because it answers a different question - is the thing usable - and a finding there sometimes means the code review is reviewing the wrong design. Report only; its findings are fixed like any other.
10. **Two reviews, both mandatory, in this order.** First `review-changes` over the whole phase diff: correct, secure, faithful to the spec? Findings fixed, then checked again. Then `thermo-nuclear-code-quality-review` over the same changes: maintainable? The second run is **a gate of its own**: "correct" and "still changeable in six months" are different questions, and one run asked to answer both answers neither thoroughly. Whatever stays open after both is named in the report as deliberately open, with the reason.
11. **Learn from the phase** via `retro`. After both reviews, because their reports are its primary sources. It proposes what to change in the environment: a check for what is mechanical, a rule in `CODING_STANDARDS.md` for what is judgement. Nothing changes before the user picks.
12. **Pull the configuration back into line** via `config-sync`, at the point its own timing rule names: after `retro`, before the release.
13. **Release.** The report goes to the user; pushing and the next phase wait for an explicit go.

Adjust the steps to what the project has and leave out what it lacks: a step naming a skill that does not exist is read as a working instruction and fails silently.

## Phase 7: Negative scope and decisions

**What the plan deliberately does not contain**, each with its reason; otherwise everything cut in the discussion gets proposed again.

**The decisions table.** Every ordering decision, one row, with its reasoning. This section decays first: after two months nobody remembers why the auth rebuild sits in phase 9, and without the reason it gets moved by whoever finds it inconvenient.

## Phase 8: Write it into the roadmap

The build plan is the `## Bauphasen` section of the roadmap, not a separate document; a second document answering "where are we" drifts from the first.

Write the section per the template below, then three more things:

- **Set `Jetzt` and `Als Nächstes`** to the first phase and its first action.
- **Set `Aktuelle Bauphase`** to text that appears in that phase's heading. The SessionStart hook injects only the roadmap head and that one section; set it wrong and the next session works from the wrong phase without anything failing.
- **Mark step 11 in the setup table** as done.

## Re-running

On an existing plan this completes rather than replaces. What already happened stays:

**History stays verbatim.** Finished phases, ticked gate items, decisions and their dates, including recorded deviations. A build plan is also the record of what happened.

**A changed cut is a new decision**, with a row in the decisions table and its reason.

**Say what moved.** The report names which phases changed, which are new, and which spec change caused it.

---

## Template

The ritual goes into the **head** of the roadmap, above its first `---`, as a block `**Ablauf je Phase:**` with the numbered steps. Once build phases exist, the SessionStart hook injects only the head and the current phase; a ritual under `## Bauphasen` would reach no session.

```md
## Bauphasen

**Ordnungsprinzip:** <one sentence: what determines the order and why>

### Kernprinzipien

<what holds across all phases and belongs in none of them individually>

### 1. Phase 1 — <name> ⬜

> **Branch:** `phase-1/<slug>`
> **Startet nach:** <what, and why>
> **Spec-Quellen:** <links>

**Ziel:** <what is true afterwards that was not before>

**Inhalt**

- <what is built, changed, removed>

**Gate 1**

- [ ] <verifiable sentence>
- [ ] <verifiable sentence>

### <further phases in the same shape>

### Meilensteine

- **<name>** — after phase <n>. <what is true then, in business terms.>

### Was dieser Plan bewusst nicht enthält

- **<topic>** — <reason and, where applicable, the condition under which it returns>

### Entscheidungen

| Entscheidung | Begründung |
|---|---|
| <ordering decision> | <why> |
```

## What not to do

**Planning the details of a phase here.** The plan file does that, in plan mode, right before the phase is built; details decided months early are decided with the least information anyone will have.

**Cutting around the code that exists.** In brownfield the phases follow the target product, and what is switched off when is part of the plan; a cut that follows the current structure rebuilds it.

**Carrying a status per spec.** The spec index owns that; phases link to their specs and stop there.

## Before finishing

Report: the ordering principle and the reason it won, the number of phases, the milestones, and the first phase with its first action. The next step is plan mode for phase 1, not building.
