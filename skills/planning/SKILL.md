---
name: planning
description: "Write the implementation plan for one build phase before anything is touched, in plan mode, and get it released. Reads the phase entry from the roadmap and the specs it names, grills the open decisions, and produces a plan file with context, goal, decisions, critical files, order, tests, verification and an explicit out-of-scope. Use it before starting a phase or any non-trivial piece of work, when someone asks how something should be built, or when work spans more than one session. Building starts only after the user releases the plan."
---

# Planning

The plan is written before the branch exists.

That order is the whole point. The roadmap's phase entry says the intent; it deliberately does not say the way. If the way is not settled beforehand, it gets settled during the build, one decision at a time, in the place where changing them is most expensive. Plan mode forces reading and asking first.

One plan, one phase. If it turns out to need more than about three sub-plans, the phase was cut too large; split the phase rather than fraying the plan.

## Phase 0: Plan mode, and read

Enter plan mode before anything else. In it, nothing is written, not even the branch.

Read, in this order:

- **The roadmap's entry for this phase**: what it starts after, its goal, its content, its gate. Not the other phases.
- **The specs it names** in its spec sources. All of them, fully.
- **The product definition**, the parts the specs cite.
- **The project's own rules**: the root instructions, the area instructions for the directories this touches, the path rules that will match.
- **The current code** in the affected areas. What is there, what already does part of this, what is being replaced.

**Check for an existing plan first.** If one exists for this phase, continue it rather than starting a second. Two plan files for one phase is the same defect as two roadmaps.

## Phase 1: The plan file

`.claude/plans/<phase>-<slug>.md`, named after the branch so the two are obviously one thing.

Sections, all of them mandatory:

**Context.** Why this is being built, which part of the product definition it serves, what came before it. A plan whose context cannot name a spec or a phase is planning something nobody asked for.

**Goal.** What is true afterwards that is not true now. One paragraph, in terms someone can check.

**Decisions.** A table: question, chosen answer, reason. Filled during the grilling in phase 2 and appended to during the build, never at the end.

**Critical files.** Which files change and how. This is where the reading in phase 0 pays off, and where a wrong assumption becomes visible before it costs anything.

**Order.** The concrete steps, in sequence, each one small enough to be finished and checked. Each step gets a short id (`a1`, `a2`, ...) so commits and findings can name it.

**Blocks.** The unit `execute-plan` builds: a group of **three to six tasks** that share an area of the code or build on each other, run in one worktree by one implementer and checked by one review. Each block gets an id (`b1`, `b2`, ...), its task ids, and its file area in one line. Cut blocks along the code, not along the roadmap's bullet points: tasks that touch the same files belong together, because splitting them only creates rebases between siblings. A block of one task is allowed only when the task is exclusive (schema, compose, running stack) or genuinely stands alone. Every hand-off costs minutes, so twenty single tasks are the slow plan and five blocks the fast one.

**Waves.** Which blocks may run at the same time. `execute-plan` runs up to **three** blocks of a wave in parallel, so the plan has to say where that is safe. Blocks in one wave have **disjoint** file areas and touch neither the schema, nor the compose files, nor anything that needs the running dev stack (database, dev server, a manual pass through the interface). Anything of that kind is marked **exclusive** and forms a wave of its own; keep exclusive blocks small (the migration alone, not the migration plus the features on top). List the waves in order, each with its block ids and one line on why the file areas do not overlap. Aim for few waves: a plan of three or four waves is normal, ten is a sign the blocks are too small. When in doubt about an overlap, put the block in the next wave rather than shrinking it.

**Tests.** Case and expectation, including the failure cases. Each test target names the **seam** (public interface) it is tested at, with one line on what a test there catches and what it misses. Releasing the plan releases the seams. Follow the project's test rules for what is mandatory.

**Verification.** The commands that have to come back clean, with what clean means.

**Out of scope.** Mandatory and never empty. It is the section that stops adjacent work from drifting in, and it is the one people leave out because it feels like it says nothing.

## Phase 2: Grill the plan

Invoke `grill-me` on every open decision in it. One round at a time, each question with a recommendation.

**Write each resolved decision into the plan immediately**, with its reason, rather than collecting them and writing at the end. A decision recorded later is a reconstruction, and the reason is what gets lost first.

The questions worth asking here are the ones the specs left open on purpose, plus the ones nobody noticed were open: what happens on the failure path, what is done with existing data, what is deliberately not migrated, what gets built provisionally and thrown away.

Where a spec turns out not to answer something it should, that is a finding about the spec. Note it; do not decide it in the plan and move on silently.

## Phase 3: Point the roadmap at it

The phase entry in the roadmap gets a line naming the plan file and its status. No plan file without an entry, or there are two truths about the same phase.

Plan status: `⬜` planned · `🔄` in progress · `🔍` code done, review open · `✅` code and review green · `❌` blocked, with the reason written down.

## Phase 4: Release

Put the plan to the user. Before doing so, check it yourself:

- Every goal traces to a spec or the phase entry.
- Out of scope covers the neighbouring work that could drift in.
- The phase's gate items appear in verification.
- The failure cases are in the tests, not only the happy path, and every test target names its seam.
- Nothing in it decides something a spec left open without saying so.

Then wait. **Building starts after the release, not before.** This is the point of the whole skill and the easiest one to erode, because the plan usually looks obviously right to the person who just wrote it.

## During the build

The plan is a living document in exactly one respect: **decisions taken on the way go into it as they are taken.** Everything else stays as released; if the way itself turns out wrong, that is a conversation with the user, not a quiet edit.

## When the phase is done

Set the plan status, run the gate and the review, and only then mark it green. A plan marked done before its review has been through is a plan nobody can trust afterwards.

## What this is not

**Not a protocol.** The plan says what will be done and why, not what was done. Implementation detail that belongs in the code does not belong here.

**Not a second spec.** Where the plan starts describing behaviour the specs should own, the spec is missing. Write the spec.

**Not one plan for several phases.** One phase, one plan, one branch, one review.
