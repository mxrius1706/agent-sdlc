---
name: config-sync
description: "Check the project configuration (CLAUDE.md files, rules, references) against reality and correct the drift. Use at the end of a build phase, after a decision changes, when a reference target moves, or when someone asks whether the instructions still match the code or what has to be pulled back into line."
---

# Config Sync

Keep the configuration honest. It is **instruction to a model**, not documentation for people: a wrong line produces wrong code, repeatedly and quietly, because it is read as truth. So the standard is verification, not tidiness.

## When it is due

The trigger is a change in what the configuration depends on, not a schedule.

- **End of a build phase**, after the reviews and after `retro`, before the release. The phase changes code, and code is the authority for the largest class of claims. After the reviews, because those still change code; after `retro`, because it changes the environment (`CODING_STANDARDS.md` and `.claude/checks.json` are configuration too); before the release, so the drift lands in the same report the user decides on.
- **A decision changes**, targeted at the files that cite it.
- **A reference target moves**: knowledge base restructured, rule file renamed, tool or server swapped. Nothing in the build triggers this one.

**Never before a build phase**: correcting against code that is about to be rebuilt produces work the phase invalidates.

## Four authorities, kept apart

Every claim has **its own** authority; checking everything against one source is the common mistake.

| Kind of claim | Authority |
|---|---|
| Current state: "the function is called X", "the field exists", "the route lives at Y" | **The code.** Look, never remember, never read a spec for this: specs describe the target state, and reading them as current state documents things nobody has built |
| Decision: "we no longer use Y", "sealing happens on close" | **The decision records and specs** |
| Product: audience, scope, deliberate non-goals | **The product definition** |
| External reference: a path in the knowledge base, a tool name, a linked file | **The referenced thing itself.** Look whether it exists |

When unclear which applies: *could I disprove this by looking?* If yes, it is a current-state claim and the code decides.

**The fourth row gets forgotten and is expensive.** A reference to a note, a server's tool or another rule file is not checked when written, ages silently, and does not announce its breakage: the session finds nothing and carries on with less. Checking only code, decisions and product never finds this class.

**Tool names only count on the running server.** Two servers can carry the same configured name while only one is connected, with differently named tools. A rule prescribing a tool the running server lacks is worse than no rule.

## Scope

**In:** the root instructions, every area instruction file, the root CLAUDE.md section `Project references` (below), everything under the rules and references directories, `CODING_STANDARDS.md` if present, and `.claude/checks.json`. A standard naming a path, API or check that no longer exists is checked like any claim; every command in `checks.json` must still exist and run. For rules, check the `paths:` frontmatter too: a glob matching no existing paths means the rule never loads and nothing else will notice.

**Out:** the global skills themselves (they describe ways of working, not project facts; a project copy of one is in scope, see below), the user's personal configuration, and the specs themselves: read, never changed. A spec error found here is reported and corrected through `write-spec`; contradictions *between* specs belong to `spec-consistency` and are reported, not resolved.

## Phase 1: Inventory

**Enumerate the configuration files, do not assume them**, or a newly added one falls through. List the rules and references directories as well.

## Phase 2: Pull out the checkable claims

Collect the statements that **can be wrong**. The user's working instructions ("only solve the task you were given") are not checkable and not yours. Checkable:

- Code references: function names, signatures, file paths, field names, enum values, routes
- Architecture statements: "we use X", "Y runs through Z"
- References: links to specs, the product definition, other rule files
- **Example code in reference documents: the most dangerous kind, because it gets copied**

Note the responsible authority for each; it decides where to look.

## Phase 3: Verify

Each claim against its authority, with evidence: file and line, not "checked".

**For example code the unit of checking is the claim, not the line.** A name that does exist creates false confidence while everything around it is wrong. Go through each call:

- **Name**: does the function exist?
- **Arity**: how many arguments does it take?
- **Parameter types**: request object or string? Key or payload?
- **Return**: value, nothing, object, finished response? The next line depends on it
- **Field names in object literals**: checked against the schema, not the library; the most common silent deviation because they sound plausible
- **Completeness**: does the example omit a step the project's mandatory sequence requires? A missing security step goes unnoticed
- **The described mechanism**: not only *whether* something is called but *how it works*. "Fields are sorted alphabetically" can be entirely invented while everything around it is correct

The last three tend to surface *while correcting*, because the eye stops at the function name. Do that closer reading here, or the finding grows during release and the report no longer matches the change. **Anything that turns up late still goes in the report.**

## Phase 4: Classify

Three categories; the middle one is why this is not simply a diff.

**A - Wrong.** The configuration contradicts its authority without cause. Pull it into line. A `.claude/checks.json` command that no longer exists or runs belongs here: the after-edit hook would fail on every edit or be silently skipped.

**B - Existing, with an expiry date.** The configuration describes the current state **correctly**, and that state is going away on purpose. **Leave it untouched**: a model working on that system still needs the description. Check only that the expiry note exists, names the right decision, and is current. Deleting early removes the configuration's knowledge of a running system.

**C - Missing.** A decision was made and the configuration is silent although it covers the area otherwise. Add it, briefly.

### `Project references` and project copies

The section is checked like every other pointer, plus three checks of its own:

- **Every row resolves**: the source exists, and the row names an installed skill and a topic that skill's text actually asks for. Otherwise **A**.
- **Every row a running skill needs is there.** For each skill the roadmap or the phrase table uses, read its text for the topics it looks up; a missing row is **C**, minor, with the skill's fallback named.
- **No project copy of a global skill.** A folder under `.claude/skills/` with the name of an installed global skill hides it and cuts the project off from every toolkit update. It is a finding of its own, important: compare the copy with the global skill, move what is project knowledge into a source plus a row, and propose deleting the copy. A skill of the project's own, under its own name, is fine.

Severity follows **what the error causes**:

- **Critical**: following it produces wrong code or breaks a security rule. Anything in a mandatory-read file with example code.
- **Important**: describes a superseded architecture as present truth without marking it legacy.
- **Minor**: dead references, outdated wording, moved paths.

## Phase 5: The report

Written to `.claude/plans/<plan file name>-config-sync.md` at the end of a phase, otherwise to `.claude/plans/config-sync-<YYYY-MM-DD>.md`; grouped **by file**, within a file by severity. Per finding: place, claim, what actually holds, evidence, category, proposal. The report stays: it anchors a release spanning several sessions and starts the next run.

## Phase 6: Release and correct

**Factual corrections** (wrong signature, dead link, moved path) are put forward **bundled per file**: "this file, four findings, pull them into line?"

**Judgement calls are asked one at a time**, each with a recommended answer and its reason, the `grill-me` pattern. A judgement call is anything with more than one defensible answer: whether a legacy section stays, how an expiry note is worded, whether a decision belongs in the configuration at all. Waving through and deciding must not blur.

When changing:

- **Cut minimally.** Correct the affected line, not the paragraph; smoothing makes the change impossible to review.
- **Carry the evidence** where it helps: a file and line reference lets the next reader check in two seconds.
- **Rewriting configuration text:** call the Skill tool with "writing-for-agents" first.
- Where configuration and authority disagree and *neither* is evidently right, ask the user.

Show what changed after each file, then move to the next.

## Where drift starts

An order of attack:

- **Reference documents with example code.** The centre of gravity for damage; check every call separately.
- **Reference documents for things being removed.** Category B while the thing exists, worthless the day it goes.
- **The technology section.** Fond of naming building blocks dropped long ago.
- **Architecture rules.** The decisions live here, so they drift with every new one.
- **Path and naming conventions.** They break on every rename.
- **The knowledge base map and `Project references`**. They point at moved or deleted files. **Check the other direction too:** reference documents in *no* table are never loaded, never maintained, and reliably the most drifted. Comparing directory contents against the table costs nothing.

Two patterns concern a file's whole purpose; ask "does this file have a job of its own?":

- **A summary with no source of its own.** A document that only restates what is authoritative elsewhere drifts by construction. If it does something the source does not (findable in the flow of work, a tighter cut), cut it down to exactly that; otherwise deleting is more honest than maintaining.
- **Two places with the same kind of rule.** Two files both settling what to do when (routing, ordering, obligations) eventually disagree, and the model follows the wrong one. One truth, one place (`project-init` writes this rule into the root CLAUDE.md); the other file keeps only what the first lacks.

## Boundaries

**No code changes.** Where code deviates from a *decision*, that is an implementation backlog; report it.

**No rewriting the user's working instructions** (communication style, scope discipline, definition of done). If they contradict a spec, that is a question, not a correction.

**Unverified stays visible.** What was not verified stands in the report as unverified; a report that hides its gaps suggests a check that did not happen.

## Before finishing

Report three things briefly: what changed, by file; what was found and deliberately not changed, with the reason; what could not be verified. Then record the run in the roadmap, so the next one knows what changed since.
