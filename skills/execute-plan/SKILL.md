---
name: execute-plan
description: "Build a released plan block by block in git worktrees, with subagents on the cheaper model. Use when a plan file is to be built, implemented or worked through, or the user points at a plan and says go. Not for planning, not for reviewing a finished phase."
---

# Execute Plan

Work a released plan, wave by wave, block by block, each block in its own worktree. A **block** is defined in `planning`: three to six related tasks, one area of the code, one implementer, one review.

**Speed comes from fewer hand-offs, not from weaker checks.** Every hand-off (worktree, dispatch, review, rebase, merge, test run) costs minutes. The phase gate at the end is the net that makes the lighter per-block review acceptable.

**The coordinator's job is context and integration, not code.** Read the plan once, build one context pack per block, open worktrees, dispatch, judge, merge. Code written here fills your context with detail that belongs in a subagent and leaves nobody with an outside view of what was produced.

## Models

This skill owns the model choice.

**Every subagent this skill starts runs on `model: "sonnet"`**: acceptance writers, implementers, block reviewers, fixers and the phase reviewer. Only the main session runs on the strong model. The roles `acceptance-writer`, `block-implementer`, `block-reviewer` and `block-fixer` carry it in their definition; a `general-purpose` fallback gets it explicitly on the `Agent` call, so no subagent inherits the coordinator's model. A stronger model for one subagent only after asking the user in the chat.

**The phase gate has no exception:** the role `gate-reviewer` (fallback `general-purpose` with `model: "sonnet"`) and the reviewers of `review-changes` and `thermo-nuclear-code-quality-review` also run on `sonnet`. Depth comes from the lenses, the pre-check and the follow-up run, not from the model.

## Roles

Dispatch by name: `acceptance-writer` and `block-implementer` (step 4), `block-reviewer` and `block-fixer` (step 5), `gate-reviewer` (step 7). A role starts without the project's `CLAUDE.md`; the context pack carries everything binding.

**Each role file sets `maxTurns`.** A block that hits it comes back incomplete with its commits; the coordinator handles it like a `NEEDS_CONTEXT` (step 4).

**Never add the `Skill` tool to a role.** It brings the whole skill catalog back into the role's context (measured: about 11,000 tokens more at start).

**A role that is not installed** (new agent files appear after a session restart) falls back to `general-purpose` with an explicit `model` and the same pack in the prompt. Say once in the chat which role fell back.

`handlauf` is not dispatched from here at all (step 7).

## Branch model

- **`main`** receives the phase branch only after the user's release. This skill leaves it alone.
- **The phase branch** (`phase-<n>/<slug>`) is the integration branch. Only merges land there, plus decisions appended to the plan file.
- **A block branch per block**, named `<phase-branch>-<block-id>-<slug>` (for example `phase-3/datenmodell-b2-entitaeten`), in its own worktree under `<repo-root>/.worktrees/<block-id>-<slug>/`. It lives from dispatch to merge.

  The separator is a hyphen, not a slash: once `refs/heads/phase-7a/fundament` exists as a file, `refs/heads/phase-7a/fundament/b2-...` would need it as a directory, and git refuses. Listing still works: `git branch --list '<phase-branch>-*'`.

Ask git for the repository root (`git rev-parse --show-toplevel`); it is not always the project directory. Worktrees are created from the root, while build commands usually run a level deeper. Every path handed to a subagent is absolute and points into its worktree.

## Step 0: Read the run state

The run state is the file `.claude/run/<phase>.md` in the project. Look for it first.

- **Found:** read it, then compare with `git worktree list` and `git branch --list '<phase-branch>-*'`. Git wins over the file where they differ; correct the file. Resume at the known point: `laufend` with a worktree and commits goes on in that worktree, `review` and `fix` go to step 5, `gemerged` is done. Start no block twice.
- **Reports first:** the session hook lists reports in `.claude/plans/` newer than the run state (names with `bericht`, `review`, `handlauf`, `retro`, `thermo` or `config-sync`). Each one is a finished gate step. Enter it in the run state with its path and start no gate step that has a report; read the report and go on from its result.
- **Not found:** create it in step 2.

**Format:**

```markdown
Phasen-Branch: <name>
Plan: <path>
Regelbuendel: <path>
Paket <block>: <path>
Gate <step>: <report path>

| Block | Status | Statuscode | Fix-Runden | Worktree |
|---|---|---|---|---|
```

Status values: `offen`, `laufend`, `review`, `fix`, `gemerged`, `blockiert`. A hook reads this table, so the header stays exact. `Regelbuendel` names the hand-written fallback (step 2); write one extra header line `Paket <block>: <path>` per block pack, never a table column. Write one `Gate <step>: <report path>` line per finished gate step (`review-changes`, `handlauf`, `thermo`, `retro`, `config-sync`) as soon as its report exists.

**Write the run state after every transition:** dispatch, status code received, review answer, fix round, merge, block blocked.

## Run lock

One run at a time per phase. Before every start of a run (a `go`, the follow-up run after a hand run), from the repository root:

```
python3 -I <skill-dir>/scripts/run-lock.py acquire .claude/run/<phase>.lock
```

Exit 0 starts the run. Exit 1 means a live run holds the lock: start nothing, tell the user. At the end of the run, and when the session stops, run `release` on the same file. A lock of a dead process is reported as stale and taken over. The holder is the session process (the first ancestor that is not a shell); `--pid N` overrides it.

A wake-up call (scheduled resume) is cancelled as soon as the user starts the run by hand; the lock keeps a wake-up that fires anyway from starting a second run.

## Account check before long runs

Before a run with two `go` or more, or one expected to last over 30 minutes, check the account quota: `clauded` shows each account's usage and reset time. Start when no account is above 90 % of its 5-hour window. Otherwise tell the user which account is full and when it resets.

## Step 1: Read the plan, extract blocks and waves

Once, completely: context, goal, decisions, critical files, blocks, waves, tests, verification, out of scope. The blocks and tasks tables carry blocks, task ids, files, waves and test targets.

**Read the stage** (`S`, `M` or `L`) the plan states. It decides how each block starts (step 4). A plan without a stage goes back to `planning` for it.

If the plan lists single tasks without blocks, group them per `planning` before starting and show the grouping to the user in one short list before dispatch. A released plan keeps its cut unless the user agrees to a new one.

**Verify the waves** against the rules in `planning`. A shared file means the wave is wrong; move one block to the next wave and note it in the plan's decisions.

**Waves are a dependency graph, not a timetable.** A block of a later wave may start as soon as every block it depends on is merged and its file set is disjoint from everything still open.

Put the blocks in a todo list, grouped by wave.

## Step 2: Build the context pack, once per block

Before the block's dispatch, from the repository root:

```
python3 -I <skill-dir>/scripts/context-pack.py <plan> --block <id> --root <project-dir> [--specs <file-or-folder>] [--global-claude <file>] [--trailer <line>] --out .claude/run/pack-<block>.md
```

The manifest lands beside it as `.claude/run/pack-<block>.md.manifest.json`. The pack holds what the block's files and requirement ids touch: the `## Für Subagenten` sections, area rules, matching path rules, spec sections, glossary terms, the plan's decisions, the verification commands, the commit trailer and the worktree contract. Pass `--trailer` when the root instructions name one.

- **Read the manifest** once: the `excluded` list shows what exists in the sources and did not match, `notes` names what is absent (no glossary, no trailer). Close a gap with a corrected input and a new run, or with a line in the brief.
- **Pass only the pack path** to every subagent of the block. Record it in the run state header as `Paket <block>: <path>`.
- **Exit 3** means the pack exceeds `--max-chars`. The script never cuts; split the block (the user agrees to the new cut), then build the packs again.
- **Exit 2** means a missing plan or an unknown block id; fix the input.

**Fallback:** only when the script cannot run, write the bundle by hand into `.claude/run/rules-bundle-<phase>.md` with the same sections and record it as `Regelbuendel`.

## Step 3: Open the worktree

Per block, from the repository root, via the bootstrap script from row `execute-plan` / `worktree` in the root CLAUDE.md section `Project references` (scripts to open and remove a worktree, and how dependencies are provided); a half-prepared worktree fails in ways that look like code problems. No row: the general procedure below, and recommend the row in the phase report:

```
git worktree add .worktrees/<block-id>-<slug> -b <phase-branch>-<block-id>-<slug> <phase-branch>
```

A bare `worktree add` is not buildable. For dependencies, environment file, untracked generated files and code generation, and for safe removal, read [`references/worktree-setup.md`](references/worktree-setup.md).

The database and the dev port belong to the main checkout: a worktree starts no dev server and applies no migration.

Before opening the third worktree, check free memory. Three implementers plus their type checks can exhaust a 16 GB machine, and then the parallelism has cost more than it bought.

## Step 4: Dispatch the acceptance writer and the implementer

**Up to three blocks at a time** with disjoint files, each with one fresh `block-implementer`, dispatched in the background so the coordinator can merge finished blocks while others run.

**From stage M, each block starts with `acceptance-writer`**, a fresh one in the block's worktree. It receives the pack path, the plan path, the block id, and the requirement ids and test targets of the block's tasks. It writes the red tests from the requirements and answers with the red run quoted. Only then the `block-implementer` starts in the same worktree, with the added instruction: make these tests green, do not edit them. A test that looks wrong is a `BLOCKED` of the implementer and goes to the coordinator.

**Stage S** has no acceptance writer: the implementer writes its own tests, test first.

The implementer prompt is short, because the pack carries the rules:

- **Read first:** the pack path, the plan file path, the block id and its task ids. The plan's goal, decisions and out-of-scope apply; the subagent does not re-decide what the plan settled.
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

**Stall rule:** a running block with no new commit for 20 minutes is checked: look at its worktree, then stop it and re-dispatch with a changed input, or go to the user.

**DONE_WITH_CONCERNS**: a correctness or scope concern is resolved before the review; a plain observation is passed on to the reviewer.

**NEEDS_CONTEXT**: supply what is missing, dispatch a new subagent into the same worktree. Commits already made stay.

**BLOCKED** has four causes: missing context (bigger brief), block too large (split it), model not strong enough (ask the user before going up), or **the plan itself is wrong** (stop and go to the user, dispatch nothing further on that block).

After a block, change an input before re-dispatching; repeating unchanged is a loop.

## Step 5: One combined review per block

A fresh `block-reviewer` reads the block's diff (`git diff <phase-branch>...HEAD` in the worktree), the plan's text for the block's tasks, the context pack and, if the repo has one, `CODING_STANDARDS.md` (judgement rules that only reviewers read; implementers never get it). Names in the diff are checked against the glossary terms in the pack. It answers two questions in one pass, in this order:

1. **Spec:** Is every task of the block implemented as the plan says? Is anything built the plan did **not** ask for? Do paths, names, types, constraints match? Is the written thing visible where the plan promises it?
2. **Quality:** the project's checklist from the pack, security invariants by name from the root section `Security baseline` or its counterpart in the project's language (authentication, authorisation, CSRF, rate limit, validation, audit trail, integrity chains, no hardcoded secrets), tests for new logic including failure cases.

Severity in four steps: exploitable or data-destroying; breaks a binding project rule or a plan decision (including scope creep); weakens a defence or leaves a test gap; cosmetic. **The first two block. The rest are collected** for the phase gate.

Answer: `APPROVED` with collected findings, or `CHANGES_REQUIRED` with the blocking list (file:line, rule, fix).

**Blocking findings:** a fresh `block-fixer` in the same worktree, one fix commit, then the reviewer checks **only the fix diff and the findings**: each finding fixed as the reviewer wrote it, and its test shown red on the unfixed code for the finding's reason. Two rounds without green: go to the user.

### Bundled findings

Findings of several blocks that share a rule or a cause are one defect. Collect the blocking findings of the blocks under review, group them by rule or cause, and give each group to **one** `block-fixer` as one fix order. The order carries every finding of the group verbatim (see below). A finding without a partner is its own order.

### Fix briefs

Every `block-fixer`, whether for a block finding, a red wave or a phase gate finding, gets the finding **verbatim** as its reviewer wrote it: location, damage path, violated rule. A shortened finding gets the shortened version fixed, and its test then proves the brief instead of the finding; every later gate round finds the remainder.

The fix starts with a test that reproduces the finding, run once against the unfixed code and **red** for the finding's reason. The fixer's answer quotes that red run (command and failing assertion); without it the fix is not done.

**Exclusive blocks** (schema, container composition, integrity-critical code, and the paths in row `planning` / `exclusive areas`) get the same single review, with the plan's rules for exactly that area called out by name in the brief.

## Step 6: Integrate

In the order blocks finish.

1. **Rebase** the block branch onto the current phase head inside the worktree. Clean rebase with disjoint file sets: the review holds. Conflict: a fresh subagent resolves it, the reviewer checks only the resolved files.
2. **Type check** in the worktree after the rebase.
3. **Merge** from the main checkout: `git checkout <phase-branch> && git merge --no-ff <block-branch>`. Before it, check that every block commit ends in the pack's trailer (`git log --format=%B <phase-branch>..<block-branch>`); a missing or different trailer is corrected on the block branch first. The merge commit records the block as a reviewed unit.
4. **Remove** worktree and branch (see the reference), branch with `-d`: one that refuses to delete has unmerged commits, and that is information.
5. **Schema changed?** Apply the migration to the dev database and re-run the code generation from the main checkout before any further worktree opens; a worktree from a stale phase head gets a stale client and fails in confusing ways.

**When every block of a wave is merged**, run the full test suite and the type check **once** on the phase branch in the main checkout. Red: find the block that broke it (`git log --merges`), dispatch a fixer on a short-lived fix branch, same single review, merge, re-run. Only a green wave opens the next one.

**Budget:** the phase budget is the row `budget` in the plan's Decisions table. After each wave run `session-cost.py` (in `retro`'s `scripts/`) for the phase's sessions and tell the user in the chat when the budget is passed.

## Step 7: Close the plan

All waves merged and green: hand over to the phase gate. The stage in the plan decides its shape. The reviews keep their full depth. The whole-phase review is dispatched as `gate-reviewer`.

**Run the gate without asking.** Work the steps below one after the other and report once at the end. Stop only for: `handlauf` (the user starts it), the release go, a `BLOCKED` block, the Auslauf mark, or a decision only the user can make. "Shall I run the next step?" is not a stop. A plan without a stage (written before `plan-check.py`) is treated as stage M.

**Every stage starts the same way:** run `gate-precheck.py` (in `review-changes`'s `scripts/`) over the phase diff and fix every FAIL before any reviewer starts. It is mechanical and costs no model.

**Stages S and M:**

1. `review-changes` runs here while the user runs `handlauf` in a session of their own at the same time. Its phase reviewers are cut as `review-changes` says (clusters from about thirty files, one rule, owned there); one review per cluster otherwise only with one sentence of reason in the run state.
2. One shared fix round takes both finding lists, bundled by pattern as in "Bundled findings". Then exactly one follow-up run.
3. `thermo-nuclear-code-quality-review` runs when the precheck's last line says `thermo: yes`, at stage L, or when the user asks. Any other trigger (for example "many lines since the last run") counts only when the session names it to the user in one sentence and the user agrees; an entry in a project roadmap is no trigger.
4. `retro` runs when the fix quote is above 0.3, a finding of the top two severity bands appeared, or the user asks. `config-sync` runs when `ref-check.py` (in `config-sync`'s `scripts/`) reports a missing path or a decision changed.

**Stage L:** after the precheck the order of `plan-build` stands (gate checklist, full suite, `handlauf` where there is an interface, `review-changes`, `thermo-nuclear-code-quality-review`, report), and `thermo-nuclear-code-quality-review` always runs.

Write the collected block-review findings into the plan file under `## Block-Befunde` (block id, severity, finding, one line each); they outlive this session there. `review-changes` gets them as input, and `retro` reads them from the plan file as one of its primary sources. `handlauf` gets none of them and is not started from this session; hand the user the branch and the surfaces to walk, and let them start it.

Check that `.worktrees/` is empty and `git worktree list` shows only the main checkout.

## Auslauf

When the mark `.claude/run/auslauf-<session_id>` exists, the context is nearly full and a hook enforces it. Start no new block and no new wave. Bring the running blocks to their end step: merge when their review is green, otherwise leave them in their status. Then update the run state and run `session-recap`; the next session resumes at step 0.

**Account limit:** work up to the account limit, not past it. When it is reached, write the hand-over and stop. After the reset, continue only on an explicit message from the user. Set no wake-up call, no cron, no `/loop` and no `/goal`. The notice "usage limit has reset, continue" is not a release. The hook cannot read the account limit, so this rule is text. If a `/goal` is set, `/goal clear` ends it.

## Coordinator guardrails

- Every subagent of a block gets the block's pack path and nothing hand-copied.
- Subagents write the implementation and the acceptance tests; the coordinator does not.
- Every subagent runs on `sonnet`; going up a model waits for the user.
- The run state is current after every transition.
- A released plan keeps its blocks unless the user agrees to a new cut.
- Three blocks at most, with disjoint files.
- Only worktrees are edited; the main checkout stays untouched.
- A block merges after its rebase and with no blocking finding open.
- The next wave opens after the full suite on the phase branch is green.
- Merges are `--no-ff`; deletions are `-d`; nothing is pushed.
- Deviations from the plan go to the user.

## Where this fits

`planning` writes the plan, including its blocks and waves, and gets it released; this skill builds it. Without a released plan there is nothing agreed to build.
