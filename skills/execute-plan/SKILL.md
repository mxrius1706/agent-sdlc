---
name: execute-plan
description: "Execute a released implementation plan block by block. A block is a coherent group of three to six tasks that runs in one git worktree on a block branch off the phase branch, built by one fresh subagent and checked by one combined review; up to three blocks of a wave run in parallel, all subagents on the cheaper model, and green blocks are rebased and merged into the phase branch by the coordinator, worktree and branch removed. The full test suite runs once per wave on the phase branch. The coordinator reads the plan once, writes one shared rules bundle, manages branches and judges results; it writes no code itself. Use it when a plan file is to be built, implemented or worked through, or when the user points at a plan and says to go. Not for planning and not for reviewing a finished phase."
---

# Execute Plan

Work a released plan, wave by wave, block by block, each block in its own worktree.

**Speed comes from fewer hand-offs, not from weaker checks.** The unit of work is the **block**, not the single task: a handful of related tasks that touch one area of the code, built in one go by one implementer and reviewed once. Every hand-off (worktree, dispatch, review, rebase, merge, test run) costs minutes; a plan cut into twenty single tasks pays that twenty times. The safety net that makes a lighter per-block review acceptable is the phase gate at the end (`review-changes` and `thermo-nuclear-code-quality-review`), which stays unchanged.

**The coordinator's job is context and integration, not code.** Read the plan once, write the rules bundle once, open worktrees, dispatch, judge, merge. Writing code yourself fills your context with detail that belongs in a subagent and leaves nobody with an outside view of what was produced.

## Models

**Every subagent this skill starts runs on `model: "sonnet"`**: implementers, block reviewers, fixers. Set it explicitly on every `Agent` call; never let a subagent inherit the coordinator's model. A stronger model for one block — delicate integrity-critical or schema logic, or a block that failed twice on the cheaper model — only after asking the user in the chat.

**The phase gate is the exception:** `review-changes` and `thermo-nuclear-code-quality-review` at the end of the phase run on the **strong model** (`model: "opus"`). They are the net that makes the cheaper block review acceptable, and a net on the cheap model defeats the trade.

The third gate, `handlauf`, is not dispatched from here at all: it runs in a session of its own and takes no input from this skill. See step 7.

## Branch model

Three layers, fixed:

- **`main`** receives the phase branch only after the user's release. This skill never touches `main`.
- **The phase branch** (`phase-<n>/<slug>`) is the integration branch. Nothing is edited on it directly; only merges land there, plus decisions appended to the plan file.
- **A block branch per block**, named `<phase-branch>-<block-id>-<slug>` (for example `phase-3/datenmodell-b2-entitaeten`), in its own worktree under `<repo-root>/.worktrees/<block-id>-<slug>/`. It lives from dispatch to merge.

  The separator is a hyphen, not a slash. Git refs are files: once `refs/heads/phase-7a/fundament` exists as a file, `refs/heads/phase-7a/fundament/b2-...` would need the same name as a directory, and git refuses. A block branch is a sibling of the phase branch. Listing still works: `git branch --list '<phase-branch>-*'`.

The repository root is not always the project directory — ask git rather than assuming: `git rev-parse --show-toplevel`. Worktrees are created from the root, while the build commands usually run a level deeper. Every path handed to a subagent is absolute and points into its worktree.

## Step 1: Read the plan, extract blocks and waves

Once, completely: context, goal, decisions, critical files, blocks, waves, tests, verification, out of scope.

The plan names **blocks** (id, tasks, file area) and **waves** (which blocks may run together). If the plan still lists single tasks without blocks, group them before starting: tasks that share files or build on each other go into one block, three to six tasks per block, and show the grouping to the user in one short list before dispatch. Do not silently re-cut a released plan.

**Verify the waves.** Blocks in one wave must have disjoint file sets and must not touch the schema, the compose files or the running dev stack. A shared file means the wave is wrong; move one block to the next wave and note it in the plan's decisions.

**Waves are a dependency graph, not a timetable.** A block of a later wave may start as soon as every block it depends on is merged and its file set is disjoint from everything still open.

Put the blocks in a todo list, grouped by wave.

## Step 2: Write the rules bundle, once per phase

One file in the scratchpad, `rules-bundle-<phase>.md`, written before the first dispatch and reused by every subagent of the phase:

- The project's binding rules from the root instructions (architecture rules, security minimums, test duty, definition of done).
- The path rules that will match in this phase, meaning every file in `.claude/rules/` whose `paths:` frontmatter hits one of the plan's critical files, **content copied in**, not named.
- The **glossary terms** relevant to the phase's areas (from `GLOSSARY.md` in the knowledge base, reached through the knowledge base map in the root instructions), **content copied in**, including each term's `_Avoid_` aliases. A path in a prompt is a request; the terms themselves are simply there. Leave the rest of the glossary out.
- The verification commands and what green means.
- The worktree contract (below).

Subagents read the bundle and the plan file themselves; the coordinator passes paths, block id and the list of task ids. Re-embedding the same rules into every prompt is what used to make each dispatch slow and each prompt huge.

## Step 3: Open the worktree

Per block, from the repository root, via the project's own bootstrap script when it has one. A project that opens worktrees regularly should have one, because the setup below is easy to get subtly wrong and a half-prepared worktree fails in ways that look like code problems. Without a script:

```
git worktree add .worktrees/<block-id>-<slug> -b <phase-branch>-<block-id>-<slug> <phase-branch>
```

then make the worktree actually buildable, which a bare `worktree add` does not:

- **Dependencies:** link or share the installed packages from the main checkout rather than installing them again per worktree. On Windows a directory junction; elsewhere a symlink. Some toolchains refuse a linked dependency directory — check once per project, and if so, install in the worktree instead.
- **Environment:** copy the local environment file. It is untracked, so `worktree add` does not bring it.
- **Untracked generated files** the framework needs to type-check, since they are untracked for the same reason.
- **Code generation** (client from a schema, generated types) if the schema changed on the phase branch.

Removing a worktree needs the same care: a linked dependency directory means a naive recursive delete can follow the link and empty the main checkout. Use `git worktree remove`, or the project's teardown script.

Never start a dev server or apply a migration from a worktree; the database and the dev port belong to the main checkout.

Before opening the third worktree, check free memory. Three implementers plus their type checks is a real load, and on a 16 GB machine it can exhaust it — at which point everything slows down and the parallelism has cost more than it bought.

## Step 4: Dispatch the implementer

**Up to three blocks at a time**, each with one fresh subagent (`model: "sonnet"`), dispatched in the background so the coordinator can merge finished blocks while others run.

The prompt is short, because the bundle carries the rules:

- **Read first:** the rules bundle path, the plan file path, the block id and its task ids. The plan's goal, decisions and out-of-scope apply; the subagent does not re-decide what the plan settled.
- **Work order:** the tasks of the block in the plan's order, **one commit per task** (conventional message, task id in the subject). No push, no amend of foreign commits.
- **Checks inside the worktree:** type check and the tests of the touched files after each task (the project's hooks do much of this per edit); the full suite is not the implementer's job.
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

Never re-dispatch unchanged after a block. Repeating without changing an input is a loop.

## Step 5: One combined review per block

A fresh reviewer (`model: "sonnet"`) reads the block's diff (`git diff <phase-branch>...HEAD` in the worktree), the plan's text for the block's tasks, the rules bundle and, if the repo has one, `CODING_STANDARDS.md` (judgement rules that only reviewers read; implementers never get it). Names in the diff are checked against the glossary terms in the bundle. It answers two questions in one pass, in this order:

1. **Spec:** Is every task of the block implemented as the plan says? Is anything built the plan did **not** ask for? Do paths, names, types, constraints match? Is the written thing visible where the plan promises it?
2. **Quality:** the project's checklist from the bundle, security invariants by name, taken from the project's own baseline rather than a generic list (authentication, authorisation, CSRF, rate limit, validation, audit trail, integrity chains, no hardcoded secrets), tests for new logic including failure cases.

Severity in four steps: exploitable or data-destroying; breaks a binding project rule or a plan decision (including scope creep); weakens a defence or leaves a test gap; cosmetic. **The first two block. The rest are collected** for the phase gate.

Answer: `APPROVED` with collected findings, or `CHANGES_REQUIRED` with the blocking list (file:line, rule, fix).

**Blocking findings:** a fresh fixer (`model: "sonnet"`) in the same worktree, one fix commit, then the reviewer checks **only the fix diff and the findings**, not the whole block again. Two rounds without green: go to the user.

**Exclusive blocks** — schema, container composition, anything touching integrity-critical code — get the same single review, with the plan's rules for exactly that area called out by name in the brief. Being alone in its wave is what makes a block exclusive, not what makes it exempt.

## Step 6: Integrate

In the order blocks finish.

1. **Rebase** the block branch onto the current phase head inside the worktree. Clean rebase with disjoint file sets: the review holds. Conflict: a fresh subagent resolves it, the reviewer checks only the resolved files.
2. **Type check** in the worktree after the rebase.
3. **Merge** from the main checkout: `git checkout <phase-branch> && git merge --no-ff <block-branch>`. Never fast-forward; the merge commit records the block as a reviewed unit.
4. **Remove** worktree and branch, via the project's teardown script when it has one, and `git worktree remove` rather than a recursive delete. Branch with `-d`, never `-D`: a branch that refuses to delete has commits that are not merged, and that is information, not an obstacle.
5. **Schema changed?** Apply the migration to the dev database and re-run the code generation from the main checkout before any further worktree opens. A worktree created from a phase head whose schema has moved on gets a stale client and fails in confusing ways.

**When every block of a wave is merged**, run the full test suite and the type check **once** on the phase branch in the main checkout. Red: find the block that broke it (`git log --merges`), dispatch a fixer on a short-lived fix branch, same single review, merge, re-run. Only a green wave opens the next one.

## Step 7: Close the plan

All waves merged and green: hand over to the phase gate. It is the project's gate checklist, the full test suite, a walkthrough of the interface where the phase has one (`handlauf`), then `review-changes` and `thermo-nuclear-code-quality-review`, then the report. Those gates keep their full depth and run on the strong model; they are what makes the lighter per-block review safe.

The collected findings from the block reviews go to **`review-changes`**, and to **`retro`** afterwards as one of its primary sources. `handlauf` gets none of them, and it is not started from this session: it runs clean, so that it looks at the interface rather than at a list somebody else wrote. Hand the user the branch and the surfaces to walk, and let them start it.

Check that `.worktrees/` is empty and `git worktree list` shows only the main checkout.

## What the coordinator does not do

- Write the implementation itself.
- Start a subagent without `model: "sonnet"`, or go up a model without asking.
- Cut a released plan into different blocks without showing it to the user.
- Run more than three blocks at once, or blocks with overlapping files together.
- Let a subagent edit the main checkout.
- Merge a block with a blocking finding open, or without the rebase.
- Open the next wave before the full suite on the phase branch is green.
- Fast-forward, force-delete, push.
- Accept a deviation from the plan because it looks reasonable.
- Apply a migration or start a dev server from a worktree.

## Where this fits

`planning` writes the plan, including its blocks and waves, and gets it released. This skill builds it. The phase gate reviews what the blocks add up to. Running this without a released plan means building something nobody agreed to.
