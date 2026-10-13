---
name: retro
description: "Run a retrospective on a session or build phase and propose changes to the agent's environment: automated checks, review standards, a slimmer CLAUDE.md. Use it after the phase reviews, or when the same mistake came back twice or someone asks what to improve for next time. Proposes only."
---

# Retro

Suggest improvements to the coding agent's **environment**, so that the next run goes better than this one. Not to the code, and not to the agent's habits: habits are not kept, files are.

> **Propose only.** Candidates go to the user. Nothing is changed before the user has picked.

## Steps

1. Call the Skill tool with "writing-for-agents" for the writing style. Every line this skill adds to a file the agent reads is written in it.

2. **Read the primary sources.** The session the user names, or the current one. In a build phase, also:
   - the report of `review-changes`, with its section "Candidates for retro" (`.claude/plans/<plan file name>-review.md`)
   - the report of `thermo-nuclear-code-quality-review` (`…-thermo.md` beside it)
   - the report of `handlauf`
   - the findings of the block reviews, in the phase's plan file under `## Block-Befunde`

   The reports say what went wrong; the session says why it was hard.

3. **Look for candidates** in these categories. Each has a trigger; without the trigger, skip the category.

   - **Navigation.** How easy was it to find the right files? Are there hidden dependencies between files? Would a pointer in the root instructions or an area file help? _Use when_ finding a piece of information took long.
   - **Automated checks.** Could a mechanical check have caught what the agent got wrong: lint, types, tests, a filesystem check? Read the project's own check commands first (its scripts, its CI workflow, `.claude/checks.json`), so that a check that exists but is unwired or broken is the finding, not a reinvention. _Use when_ the agent made a mistake a check could have caught.
   - **Coding standards.** Should a reviewer get a new rule, or an existing one removed or sharpened? _Use when_ a review missed a mistake, or a review rule produced noise. Classify first, see below.
   - **A slimmer CLAUDE.md.** Are there instructions in the root file or a global one that belong in `CODING_STANDARDS.md` or a check instead? _Use when_ the file is large.
   - **Tool economy.** Did the agent make expensive tool calls that could be shorter? Is custom tooling token-hungry? _Use when_ a call stood out as costly.
   - **No-ops.** Instructions that change no behaviour: the model does it anyway, or it never reads them. _Use when_ the instruction files are large and unwieldy.
   - **Information access.** Was a crucial piece of information out of the agent's reach? Dev server logs, read access to a service, a decision record that was not found. _Use when_ the agent guessed at something it could have known. When a skill lacked something specific to this project, the candidate is a source in the project plus a row in the root CLAUDE.md section `Project references`, never a change to the global skill and never a project copy of it.

4. **Classify every coding-standards candidate. This is mandatory.**
   - **Mechanical** (a fixed syntactic pattern, a banned API, an import shape, a file location, a naming pattern): a **check**, full stop. A lint rule in the project's own linter, an entry in `.claude/checks.json` (fast, runs after every edit), a pre-commit hook, or a CI job; whichever the project's language and existing guardrails make cheapest. Default to building the check over writing the rule.
   - **Judgement** (consistency across files, "fits the surrounding style", anything no tool can decide): a rule in **`CODING_STANDARDS.md`** in the repo. Reviewers read it; implementers do not.

   The reason for the split is context pressure. The implementing agent explores, writes and debugs, so every extra rule competes with the work and is the first thing to slip. The reviewer receives a diff and has the least pressure of anyone in the flow, so the standards belong to the reviewer. The always-loaded root file stays small, and a rule that a tool can enforce does not need to be remembered at all.

5. **Count repeats.** "Seen twice is a pattern."
   - A judgement-type mistake seen for the first time is not yet a rule. Note it in `CODING_STANDARDS.md` under `## Beobachtet (einmal)`: the generalised class of defect without file paths, plus the date or phase. Create the file and the section if they do not exist.
   - If the mistake is already there, this is the second occurrence: it moves out of that section into a rule in the body of the file, worded as something a reviewer can check against a diff.
   - Mechanical mistakes do not wait for a second occurrence. A check is cheap to add and silent when right.

6. **A project with no guardrail is a finding of its own.** If there is no `.claude/checks.json`, no pre-commit hook and no CI job running lint, types or tests, say so as the first candidate, with the cheapest option for this stack. An unchecked project is a standing missed opportunity, not a neutral default. The commands come from the testing decision in the stack decisions.

7. **Present the candidates**, most severe first. Per candidate:
   - **Where it came from:** the concrete moment in the session or the report line. A candidate without one is a guess and is dropped.
   - **Category and classification:** check or standard.
   - **The proposed change:** the exact file and the exact text or command.

   Then ask which to apply. Apply only those, one file at a time, and show what changed. Changes to `.claude/checks.json` are run once to see that the command works and is fast.

## Where things live

- `CLAUDE.md` / `AGENTS.md` load into every session. Use them for navigation pointers, and sparingly.
- `CODING_STANDARDS.md` is read during review, not during implementation. When it passes about a thousand lines, split it and leave navigation pointers.
- `.claude/checks.json` holds the commands of the after-edit hook. Only fast, deterministic ones.
- Docs are reference files that other files point at. Look for an existing doc before writing a new one.
- A skill is for a procedure or a user-invoked command; its description loads into every session, so it costs.

`config-sync` runs after this skill and checks what changed against reality. Do not duplicate its job here.
