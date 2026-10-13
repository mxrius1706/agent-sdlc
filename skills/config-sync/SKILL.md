---
name: config-sync
description: "Check the project configuration against reality and pull the drift back into line. Every claim is verified against its own authority - the code for what exists, the decision records for what was settled, the product definition for scope, and the referenced thing itself for external references. Reports findings by file with evidence, then corrects them after release. Use it at the end of a build phase, after a decision changes, when a reference target moves, or when someone asks whether the instructions still match the code, whether the configuration needs updating, or what has to be pulled back into line."
---

# Config Sync

Keep the configuration honest.

The configuration is **instruction to a model**, not documentation for people. A wrong line in it produces wrong code, repeatedly and quietly, because it is read as truth. That is the whole reason this exists, and it is why the standard is verification rather than tidiness.

It runs repeatedly. What follows is a run.

## When it is due

The trigger is a change in what the configuration depends on, not a schedule.

**At the end of a build phase**, after the reviews and before the release. The main case: a phase changes code, and the code is the authority for the largest class of claims. After the reviews, because those still change code; before the release, so the drift appears in the same report the user decides on.

**When a decision changes**, targeted at the files that cite it. Cheap and high-yield, the same as for the specs.

**When a reference target moves.** The knowledge base restructured, a rule file renamed, a tool or server swapped. This one hangs off no phase and is triggered by nothing in the build.

**Not before a build phase.** Correcting configuration against code that is about to be rebuilt produces work the phase immediately invalidates.

## Four authorities, kept apart

The most common mistake when pulling things back into line is checking everything against one source. Every claim has **its own** authority:

| Kind of claim | Authority |
|---|---|
| Current state: "the function is called X", "the field exists", "the route lives at Y" | **The code.** Look, never remember, and never read a spec for this. Specs describe the target state; reading them as current state documents things nobody has built |
| Decision: "we no longer use Y", "sealing happens on close" | **The decision records and specs** |
| Product: audience, scope, deliberate non-goals | **The product definition** |
| External reference: a path in the knowledge base, a tool name, a linked file | **The referenced thing itself.** Look whether it exists |

When it is unclear which applies: *could I disprove this by looking?* If yes, it is a current-state claim and the code decides.

**The fourth row is the one that gets forgotten and it is expensive.** A reference to a note, to a server's tool, or to another rule file is not checked when written and ages silently afterwards. It does not announce itself when it breaks either: the session looks, finds nothing, and carries on with less than it could have had. Anyone checking only code, decisions and product never finds this class, because it falls into none of the three.

Tool names carry an extra trap: only what the **running** server offers counts. Two servers can carry the same configured name while only one is connected, and their tools are named differently. A rule that then prescribes a tool the running server does not have is worse than no rule.

## Scope

**In:** the root instructions, every area instruction file in the tree, and everything under the rules and references directories. Also in scope: `CODING_STANDARDS.md` in the repo, if there is one, and `.claude/checks.json`. A standard that names a path, an API or a check that no longer exists is checked like any other claim, and so is every command in `checks.json`: it must still exist and run. For rules, the `paths:` frontmatter is checked too: a glob pointing at paths that no longer exist means the rule never loads, and nothing else will ever notice.

**Out:** the skills, because they describe ways of working rather than project facts, and a skill that rewrites skills is needlessly delicate. The user's personal configuration, because it is theirs. And the specs themselves - this reads them and never changes them. Contradictions *between* specs belong to `spec-consistency`; if one turns up here it is reported, not resolved.

## Phase 1: Inventory

The map before the work. **Enumerate the configuration files, do not assume them** - a newly added one otherwise falls straight through. List the rules and references directories as well.

## Phase 2: Pull out the checkable claims

Go through each file and collect the statements that **can be wrong**. Not every sentence is checkable: "only solve the task you were given" is the user's working instruction and is none of this skill's business. Checkable are:

- Code references: function names, signatures, file paths, field names, enum values, routes
- Architecture statements: "we use X", "Y runs through Z"
- References: links to specs, to the product definition, to other rule files
- **Example code in reference documents - the most dangerous kind, because it gets copied**

Note the responsible authority for each. That decides where you look in phase 3.

## Phase 3: Verify

Each claim against its authority. Write down the evidence - file and line, not "checked".

**For example code the unit of checking is the claim, not the line.** A single call contains several, and a name that does exist creates false confidence: you tick it off and miss that everything around it is wrong. So go through each call separately:

- **Name** - does the function exist at all?
- **Arity** - how many arguments does it actually take?
- **Parameter types** - a request object or a string? A key or a payload?
- **Return** - a value, nothing, an object, a finished response? The line *below* depends on it
- **Field names in object literals** - checked against the schema, not against the library. They are the most common silent deviation because they sound plausible
- **Completeness** - does the example omit a step the project's own mandatory sequence requires? A missing security step is more dangerous than a wrong one, because nobody notices it
- **The described mechanism** - not only *whether* something is called but *how it works*. "Fields are sorted alphabetically" is a checkable claim about the implementation and can be entirely invented while everything around it is correct

The last three tend to surface **while correcting**, not while checking, because the eye stops at the function name. Anyone touching a file necessarily reads it more closely than someone skimming it. That thoroughness belongs in this phase, or the finding grows during release and the report no longer matches what was changed.

**Anything that turns up later still goes in the report**, even late. A report that ends up containing less than what was changed is worthless on the next run.

## Phase 4: Classify

Three categories. The middle one is why this is not simply a diff.

**A - Wrong.** The configuration contradicts its authority without cause. Pull it into line. A command in `.claude/checks.json` that no longer exists or no longer runs belongs here: the after-edit hook would fail on every edit, or worse, be silently skipped.

**B - Existing, with an expiry date.** The configuration describes the current state **correctly**, and that state is going away on purpose. **Do not touch it.** A model working on that system still needs the description. What gets checked is only whether the expiry note is there, whether it names the right decision, and whether it is still current. Deleting here prematurely takes away the configuration's knowledge of a running system.

**C - Missing.** A decision was made, the configuration is silent on it although it covers the area otherwise. Add it, briefly.

Severity follows **what the error causes**:

- **Critical** - following it produces wrong code or breaks a security rule. Anything in a mandatory-read file with example code belongs here.
- **Important** - describes a superseded architecture as present truth without marking it as legacy. Leads to wrong decisions rather than immediately wrong code.
- **Minor** - dead references, outdated wording, moved paths.

## Phase 5: The report

Written to a file in the project, grouped **by file** rather than by severity, and within a file sorted by severity. Per finding: the place, the claim, what actually holds, the evidence, the category, the proposal.

The report stays. It is the anchor when the release runs over several sessions, and the starting point for the next run.

## Phase 6: Release and correct

Two kinds of finding, two ways of asking.

**Factual corrections** - a wrong signature, a dead link, a moved path - are put forward **bundled per file**: "this file, four findings, pull them into line?" With one file in view the user knows immediately what belongs there. Grouping by severity would force them to jump between four files and re-enter each one every time.

**Judgement calls are asked one at a time**, each with a recommended answer and its reason, the `grill-me` pattern. A judgement call is anything with more than one defensible answer: whether a legacy section stays, how an expiry note is worded, whether a decision belongs in the configuration at all. Keeping these apart is the point of the phase - waving through and deciding must not blur into each other.

When changing:

- **Cut minimally.** Correct the affected line, do not rewrite the paragraph. The configuration has a voice grown over many sessions; smoothing it while correcting makes the change impossible to review.
- **Carry the evidence** where it helps. A file and line reference in the text beats any assertion, because the next reader can check it in two seconds.
- **Rewriting configuration text:** call the Skill tool with "writing-for-agents" first, and follow it.
- **Invent nothing.** Where configuration and authority disagree and *neither* is evidently right, that is a question for the user, not a correction.

Show what changed after each file, then move to the next.

## Where drift starts

Not a substitute for checking, an order of attack:

- **Reference documents with example code.** The centre of gravity for damage. Every call in the block gets checked separately.
- **Reference documents for things that are being removed.** Category B while the thing still exists, worthless the day it goes.
- **The technology section.** Fond of naming building blocks that were dropped long ago.
- **Architecture rules.** This is where the decisions live, so they drift with every new one.
- **Path and naming conventions.** They break on every rename.
- **File-context tables** ("when working on X, read Y"). They point at files that were moved or deleted. **And check the other direction:** are there reference documents in *no* table? Those are never loaded, never maintained, and reliably the most drifted. Comparing directory contents against the table costs nothing and often explains *why* a file is so old.

Two patterns that concern a file's whole purpose rather than a line. For these the question is "does this file have a job of its own?":

- **A summary with no source of its own.** A document that only restates what is authoritative elsewhere has no truth anchor and drifts by construction - and nobody notices, because it looks plausible. Check whether it does something the source does not (findable in the flow of work, a tighter cut). If not, deleting is more honest than maintaining. If so, cut it down to exactly that part.
- **Two places with the same kind of rule.** When two files both settle what to do when - routing, ordering, obligations - they eventually disagree, and then the model follows the wrong one with nobody seeing the contradiction. One truth, one place; the other file keeps only what the first lacks.

## What this does not do

**No spec changes.** A spec error found here is reported and corrected through `write-spec`.

**No code changes.** Where the code deviates from a *decision*, that is an implementation backlog, not a configuration problem. Report it.

**No rewriting the user's working instructions.** Communication style, scope discipline, definition of done are theirs. If they contradict a spec, that is a question, not a correction.

**No pretending completeness.** What was not verified stands in the report as unverified. A report that hides its gaps is worse than none, because it suggests a check that did not happen.

## Before finishing

Three things, briefly: what changed, by file. What was found and deliberately not changed, with the reason. And what could not be verified. Then record the run in the roadmap, so the next one knows what has changed since.
