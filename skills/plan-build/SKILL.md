---
name: plan-build
description: "Derive the build order from the finished specs and write it into the roadmap as phases with gates. Settles the cutting principle by conversation, then produces per phase what it starts after and why, its spec sources, its content and a gate of verifiable sentences, plus the named milestones, the negative scope and the ordering decisions with their reasons. Use it once the specs and page plans stand and building is the next thing, when someone asks in which order to build, how to cut the phases, or what has to be done before what. Also used to complete or re-cut an existing build plan when specs changed."
---

# Plan Build

Turn the finished specs into a build order.

This is a different question from the writing order, and running them together is the usual mistake. **Writing order follows the references:** the entity model first, because everything points at it. **Build order follows the value:** what has to exist before anyone outside the project can see anything work. The two rarely coincide, and neither answers the other's question.

It runs once the specs stand, and again whenever enough changed that the cut no longer fits. The second case is the normal one after a while, and it is not a rewrite: what already happened stays.

## Preconditions

**All planned specs are written, and the page plans exist** where the product has an interface. A build order derived from a half-written spec set cuts phases around holes.

**A full consistency run has happened and its critical findings are closed.** This step reads every spec at once and turns them into a sequence. A contradiction that survives to here does not stay in a document, it becomes a phase boundary in the wrong place, and that is found during the build.

If either is missing, say so and name what is open. Do not derive the order anyway with a caveat; the caveat is read once and the plan is read for months.

## Phase 0: Read everything

The spec index, every written spec, the page plans, the accepted decisions, the product definition. For brownfield, the current code as well: what exists, what already works, what is being replaced.

Nothing here is skimmed. The whole point of this step is that one reader holds the entire product in view at once, which no single spec-writing session ever does.

## Phase 1: The dependency skeleton

Before any preference enters, establish the facts: **what cannot be built before what.**

From the spec graph. A spec that references another's model, its permissions or its interface cannot be built first. Record each edge with the sentence that creates it, not just an arrow. "Cannot start before X" is worth little; "needs the status field from X, see REQ-004" is checkable and survives a change to X.

This yields a partial order, and it is deliberately partial. It says what is forbidden, not what is best. Most of the real decisions are among the orderings it still allows, and those are the next phase.

## Phase 2: Settle the cutting principle

Invoke `grill-me`. This is the most expensive single decision in the whole plan and it cannot be derived from the specs, because it depends on things only the user knows: who sees the result first, whether there is existing software in the way, when something has to be shown to someone.

Three archetypes, and a project usually mixes them rather than picking one:

**Inside out, layer by layer.** Data model, then the core interfaces, then the surfaces on top. Each layer is finished before the next sits on it. Strong where the model is being reworked, because the alternative bends the model to fit whichever surface is being built. Weak on early visibility: the first two phases show nothing.

**Vertical slices.** Each phase carries one complete capability through every layer. Strong on visibility and on feedback. Weak where the model is unsettled, because every slice touches it and the last slice pays for the first four.

**Wedge first.** The smallest piece that delivers value outside the project goes first, everything else afterwards. Strong when the product has to prove itself to someone. Weak when the wedge needs half the model anyway, which is common enough to check rather than assume.

Ask, with a recommendation from what the specs actually show:

- **Who sees the first working result, and when?** This settles more of the order than any technical argument.
- **Greenfield or brownfield?** Where something exists, the cut also has to say what is switched off when, and switching off is its own phase far more often than people expect.
- **Is there a wedge**, and does it need so much underneath it that it stops being one?
- **What must not be built twice?** Anything that would be built provisionally in an early phase and thrown away later is a reason to move it, or a reason to accept the throwaway deliberately.
- **What is fixed from outside?** A date, an external system's availability, someone's holiday.

Record the answer as the ordering principle in one sentence. It goes at the top of the plan and every later "why is this here" refers to it.

## Phase 3: Cut the phases

**A phase is one branch and one review.** That is the size, and it is a practical bound rather than an aesthetic one: what is reviewed in one go has to be reviewable in one go.

**A phase ends in something demonstrable.** Not "the model is migrated" alone, but what can be shown or measured once it is. Where a phase genuinely delivers nothing visible, say so explicitly in it. That is honest and it is rare; if half the phases say it, the cut is wrong.

**Too big shows up as sub-plans.** A phase needing more than about three sub-plans was cut too large. Split the phase rather than fraying the plan.

**Every phase names what it starts after, with the reason.** The dependency is one thing, the reason is another and is what stays useful. "After the portal core, because the agent delivers into triage and without triage it collects reports nobody looks at" is still true in six months. "After phase 3" is not information.

**Every phase names its spec sources as links.** That is the connection back to the graph, and it is what makes a phase's content checkable rather than remembered.

## Phase 4: Gates

Every phase ends in a gate, and the gate is a list of sentences that are true or false.

The test for a gate item: **could someone who did not build it check it?** "Data model cleanly implemented" fails. "Migration runs through on a fresh database and on the dev database, schema diff empty" passes. "Tests written" fails; "existing suite green, new routes covered" passes.

Two or three of the items should be about the product rather than the code, phrased as the path a person takes through it. Those are the ones that catch a phase which is technically complete and practically unusable.

An open item means the phase is not finished. That has to be stated in the plan, because a gate that can be waved through is a checklist, not a gate.

## Phase 5: Milestones

Two to four named points across the whole distance, each covering several phases. They are business-facing, not technical: "the wedge stands", "first real customer". They are what you tell someone who is not building, and they are the only place where the plan says "good enough for X".

More than four and they stop being milestones.

## Phase 6: The ritual

Write the procedure once, at the top, and state that it holds for every phase without exception. It exists so that the question "how do we do this" is never asked again mid-build:

1. **Plan mode first**, before anything is touched and before the branch exists. Read and ask, do not write.
2. **A plan file per phase** via `planning`, with its decisions, its critical files, its order, its tests and its out-of-scope.
3. **The roadmap points at the plan.** No plan file without an entry here, or there are two truths about the same phase.
4. **The user releases the plan.** Only then is anything built.
5. **A branch per phase**, never on the main branch and never on the previous phase's branch.
6. **Build along the plan** via `execute-plan`. Decisions taken on the way go into the plan file immediately, not at the end.
7. **Tests** per the project's rules, `testing`.
8. **The gate**, item by item.
9. **The walkthrough** via `handlauf`, wherever the phase produced an interface, **in a session of its own and with no input from any review**. Before the code reviews, because it answers a different question - whether the thing is usable, whether the layout holds, whether the interface makes sense - and because a finding there sometimes means the code review is reviewing the wrong design. Its value is that it is a first look, so a brief carrying someone else's findings destroys exactly what it is for. Report only; its findings are fixed like any other.
10. **Two reviews, both mandatory, in this order.** First `review-changes` over the whole phase diff: is the code correct, secure and faithful to the spec? Findings fixed, then checked again. Then `thermo-nuclear-code-quality-review` over the same changes: is it maintainable? That second run is **a gate of its own** - a green `review-changes` alone is not enough, because "correct" and "still changeable in six months" are different questions, and one run asked to answer both answers neither thoroughly. Separate gates also stop the second question being deprioritised against the first. Whatever stays open after both is named in the report as deliberately open, with the reason.
11. **Learn from the phase** via `retro`. After both reviews, because their reports are its primary sources. It proposes what to change in the environment: a check for what is mechanical, a rule in `CODING_STANDARDS.md` for what is judgement. Nothing changes before the user picks.
12. **Pull the configuration back into line** via `config-sync`. After `retro`, because `retro` changes the environment and `config-sync` checks the configuration against what is then real; before the release, so the drift is in the same report the user decides on.
13. **Release.** The report goes to the user; pushing and the next phase wait for an explicit go.

Adjust the steps to what the project actually has, and leave out what it does not. What must not happen is a step naming a skill that does not exist: a dangling reference in the ritual is read as a working instruction and fails silently the first time someone follows it.

## Phase 7: Negative scope and decisions

**What the plan deliberately does not contain**, each with its reason. Without this, everything cut in the discussion gets proposed again by the next person, including by the same person six months later.

**The decisions table.** Every ordering decision, one row, with the reasoning that produced it. This is the section that decays first and is missed most: after two months nobody remembers why the auth rebuild sits in phase 9, and without the reason it gets moved by whoever finds it inconvenient.

## Phase 8: Write it into the roadmap

The build plan is not a separate document. It is the `## Bauphasen` section of the roadmap, because the roadmap already answers "where are we and what comes next" and a second document answering it in more detail produces two answers that drift.

Write the section per the template below, then three more things:

- **Set `Jetzt` and `Als Nächstes`** to the first phase and its first action.
- **Set `Aktuelle Bauphase`** to text that appears in that phase's heading. This line is read by the SessionStart hook, which from now on injects only the roadmap head and that one section. Set it wrong and the next session works from the wrong phase without anything failing.
- **Mark step 11 in the setup table** as done.

## Re-running

On an existing plan this completes rather than replaces. Three rules:

**History is not rewritten.** Finished phases, ticked gate items, decisions taken and their dates stay verbatim, including the deviations recorded in them. A build plan is also the record of what happened.

**A changed cut is a new decision**, with a row in the decisions table and its reason, not a silent edit to the old order.

**Say what moved.** The report names which phases changed, which are new, and which spec change caused it. Otherwise the next session cannot tell an updated plan from the original one.

---

## Template

```md
## Bauphasen

**Ordnungsprinzip:** <one sentence: what determines the order and why>

### Ablauf je Phase

<the ritual, binding, no exceptions>

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

**Do not plan the phase.** The plan file per phase does that, in plan mode, right before it is built. What is here is the intent; details decided months early are decided with the least information anyone will ever have on them.

**Do not cut around the code that exists.** In brownfield the phases follow the target product, and what is switched off when is part of the plan. A cut that follows the current structure rebuilds it.

**Do not carry a status per spec.** The spec index owns that. Phases link to their specs and stop there.

## Before finishing

Report: the ordering principle and the reason it won, the number of phases, the milestones, and the first phase with its first action. Then say the next step plainly, which is plan mode for phase 1, not building.
