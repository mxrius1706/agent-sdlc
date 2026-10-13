---
name: execute-plan
description: "Build a released plan block by block in git worktrees, with subagents on the cheaper model. Use when a plan file is to be built, implemented or worked through, or the user points at a plan and says go. Not for planning, not for reviewing a finished phase."
---

# Execute Plan

Work a released plan, wave by wave, block by block, each block in its own worktree. A **block** is defined in `planning`: three to six related tasks, one area of the code, one implementer, one review.

**Speed comes from fewer hand-offs, not from weaker checks.** Every hand-off (worktree, dispatch, review, rebase, merge, test run) costs minutes. The phase gate at the end is the net that makes the lighter per-block review acceptable.

**The coordinator's job is context and integration, not code.** Read the plan once, write the rules bundle once, open worktrees, dispatch, judge, merge. Code written here fills your context with detail that belongs in a subagent and leaves nobody with an outside view of what was produced.

## Models

This skill owns the model choice.

**Every subagent this skill starts runs on `model: "sonnet"`**: implementers, block reviewers, fixers. Set it explicitly on every `Agent` call so no subagent inherits the coordinator's model. A stronger model for one block (delicate integrity-critical or schema logic, or a block that failed twice on the cheaper model) only after asking the user in the chat.

**The phase gate is the exception:** `review-changes` and `thermo-nuclear-code-quality-review` run on the **strong model** (`model: "opus"`). They are the net under the cheaper block review; a net on the cheap model defeats the trade.

`handlauf` is not dispatched from here at all (step 7).

## Branch model

- **`main`** receives the phase branch only after the user's release. This skill leaves it alone.
- **The phase branch** (`phase-<n>/<slug>`) is the integration branch. Only merges land there, plus decisions appended to the plan file.
- **A block branch per block**, named `<phase-branch>-<block-id>-<slug>` (for example `phase-3/datenmodell-b2-entitaeten`), in its own worktree under `<repo-root>/.worktrees/<block-id>-<slug>/`. It lives from dispatch to merge.

  The separator is a hyphen, not a slash: once `refs/heads/phase-7a/fundament` exists as a file, `refs/heads/phase-7a/fundament/b2-...` would need it as a directory, and git refuses. Listing still works: `git branch --list '<phase-branch>-*'`.

Ask git for the repository root (`git rev-parse --show-toplevel`); it is not always the project directory. Worktrees are created from the root, while build commands usually run a level deeper. Every path handed to a subagent is absolute and points into its worktree.

## Step 1: Read the plan, extract blocks and waves

Once, completely: context, goal, decisions, critical files, blocks, waves, tests, verification, out of scope.

If the plan lists single tasks without blocks, group them per `planning` before starting and show the grouping to the user in one short list before dispatch. A released plan keeps its cut unless the user agrees to a new one.

**Verify the waves** against the rules in `planning`. A shared file means the wave is wrong; move one block to the next wave and note it in the plan's decisions.

**Waves are a dependency graph, not a timetable.** A block of a later wave may start as soon as every block it depends on is merged and its file set is disjoint from everything still open.

Put the blocks in a todo list, grouped by wave.

## Step 2: Write the rules bundle, once per phase

One file in the scratchpad, `rules-bundle-<phase>.md`, written before the first dispatch and reused by every subagent of the phase:

- The binding rules from the root CLAUDE.md sections `Architecture rules`, `Security baseline`, `Testing requirements` and `Definition of done`.
- The path rules that will match in this phase: every file in `.claude/rules/` whose `paths:` frontmatter hits one of the plan's critical files, **content copied in**, not named.
- The **glossary terms** relevant to the phase's areas (from `GLOSSARY.md` in the knowledge base, reached through the knowledge base map in the root instructions), **content copied in**, including each term's `_Avoid_` aliases. A path in a prompt is a request; the terms themselves are simply there.
- The verification commands and what green means.
- The worktree contract (step 4).

Subagents read the bundle and the plan file themselves; the coordinator passes paths, block id and task ids.

## Step 3: Open the worktree

Per block, from the repository root, via the bootstrap script from row `execute-plan` / `worktree` in the root CLAUDE.md section `Project references` (scripts to open and remove a worktree, and how dependencies are provided); a half-prepared worktree fails in ways that look like code problems. No row: the general procedure below, and recommend the row in the phase report:

```
git worktree add .worktrees/<block-id>-<slug> -b <phase-branch>-<block-id>-<slug> <phase-branch>
```

A bare `worktree add` is not buildable. For dependencies, environment file, untracked generated files and code generation, and for safe removal, read [`references/worktree-setup.md`](references/worktree-setup.md).

The database and the dev port belong to the main checkout: a worktree starts no dev server and applies no migration.

Before opening the third worktree, check free memory. Three implementers plus their type checks can exhaust a 16 GB machine, and then the parallelism has cost more than it bought.

## Step 4: Dispatch the implementer

**Up to three blocks at a time** with disjoint files, each with one fresh subagent (`model: "sonnet"`), dispatched in the background so the coordinator can merge finished blocks while others run.

The prompt is short, because the bundle carries the rules:

- **Read first:** the rules bundle path, the plan file path, the block id and its task ids. The plan's goal, decisions and out-of-scope apply; the subagent does not re-decide what the plan settled.
- **Work order:** the tasks of the block in the plan's order, **one commit per task** (conventional message, task id in the subject). No push, no amend of foreign commits.
- **Checks inside the worktree:** type check and the tests of the touched files after each task. The full suite is the coordinator's job.
- **Worktree contract:** all paths inside the worktree; the main checkout is off limits.
- **Answer with exactly one status code**, plus one line per task:

```
DONE
DONE_WITH_CONCERNS: <the concerns>
NEEDS_CONTEXT: <what is missing>
BLOCKED: <the blocker>
```

### Handling the status

**DONE** goes to step 5. First check that the block branch carries the expected commits and that the main checkout is still clean. A dirty main checkout means the subagent left its worktree; revert with the user's knowledge first.

**DONE_WITH_CONCERNS**: a correctness or scope concern is resolved before the review; a plain observation is passed on to the reviewer.

**NEEDS_CONTEXT**: supply what is missing, dispatch a new subagent into the same worktree. Commits already made stay.

**BLOCKED** has four causes: missing context (bigger brief), block too large (split it), model not strong enough (ask the user before going up), or **the plan itself is wrong** (stop and go to the user, dispatch nothing further on that block).

After a block, change an input before re-dispatching; repeating unchanged is a loop.

## Step 5: One combined review per block

A fresh reviewer (`model: "sonnet"`) reads the block's diff (`git diff <phase-branch>...HEAD` in the worktree), the plan's text for the block's tasks, the rules bundle and, if the repo has one, `CODING_STANDARDS.md` (judgement rules that only reviewers read; implementers never get it). Names in the diff are checked against the glossary terms in the bundle. It answers two questions in one pass, in this order:

1. **Spec:** Is every task of the block implemented as the plan says? Is anything built the plan did **not** ask for? Do paths, names, types, constraints match? Is the written thing visible where the plan promises it?
2. **Quality:** the project's checklist from the bundle, security invariants by name from the root section `Security baseline` (authentication, authorisation, CSRF, rate limit, validation, audit trail, integrity chains, no hardcoded secrets), tests for new logic including failure cases.

Severity in four steps: exploitable or data-destroying; breaks a binding project rule or a plan decision (including scope creep); weakens a defence or leaves a test gap; cosmetic. **The first two block. The rest are collected** for the phase gate.

Answer: `APPROVED` with collected findings, or `CHANGES_REQUIRED` with the blocking list (file:line, rule, fix).

**Blocking findings:** a fresh fixer (`model: "sonnet"`) in the same worktree, one fix commit, then the reviewer checks **only the fix diff and the findings**. Two rounds without green: go to the user.

**Exclusive blocks** (schema, container composition, integrity-critical code, and the paths in row `planning` / `exclusive areas`) get the same single review, with the plan's rules for exactly that area called out by name in the brief.

## Step 6: Integrate

In the order blocks finish.

1. **Rebase** the block branch onto the current phase head inside the worktree. Clean rebase with disjoint file sets: the review holds. Conflict: a fresh subagent resolves it, the reviewer checks only the resolved files.
2. **Type check** in the worktree after the rebase.
3. **Merge** from the main checkout: `git checkout <phase-branch> && git merge --no-ff <block-branch>`. The merge commit records the block as a reviewed unit.
4. **Remove** worktree and branch (see the reference), branch with `-d`: one that refuses to delete has unmerged commits, and that is information.
5. **Schema changed?** Apply the migration to the dev database and re-run the code generation from the main checkout before any further worktree opens; a worktree from a stale phase head gets a stale client and fails in confusing ways.

**When every block of a wave is merged**, run the full test suite and the type check **once** on the phase branch in the main checkout. Red: find the block that broke it (`git log --merges`), dispatch a fixer on a short-lived fix branch, same single review, merge, re-run. Only a green wave opens the next one.

## Step 7: Close the plan

All waves merged and green: hand over to the phase gate, which runs per the ritual in `plan-build` (gate checklist, full suite, `handlauf` where there is an interface, `review-changes`, `thermo-nuclear-code-quality-review`, report). The reviews keep their full depth on the strong model.

Write the collected block-review findings into the plan file under `## Block-Befunde` (block id, severity, finding, one line each); they outlive this session there. `review-changes` gets them as input, and `retro` reads them from the plan file as one of its primary sources. `handlauf` gets none of them and is not started from this session; hand the user the branch and the surfaces to walk, and let them start it.

Check that `.worktrees/` is empty and `git worktree list` shows only the main checkout.

## Coordinator guardrails

- Subagents write the implementation; the coordinator does not.
- Every subagent carries `model: "sonnet"`; going up a model waits for the user.
- A released plan keeps its blocks unless the user agrees to a new cut.
- Three blocks at most, with disjoint files.
- Only worktrees are edited; the main checkout stays untouched.
- A block merges after its rebase and with no blocking finding open.
- The next wave opens after the full suite on the phase branch is green.
- Merges are `--no-ff`; deletions are `-d`; nothing is pushed.
- Deviations from the plan go to the user.

## Where this fits

`planning` writes the plan, including its blocks and waves, and gets it released; this skill builds it. Without a released plan there is nothing agreed to build.
