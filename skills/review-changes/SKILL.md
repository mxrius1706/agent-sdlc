---
name: review-changes
description: "Review open or phase changes against specs, accepted decisions and the project's own patterns, in three parallel lenses (security, spec fidelity, structure), and check the phase gate item by item. Use before a commit or push, at the end of a build phase, or when someone asks whether changes are sound or good to release, even without the word review."
---

# Review Changes

Judge the changes against the contract, not against taste: **does the code do what the specs say, in the way this project does it everywhere else?** The specs are the truth about what should be; the code is the current approximation. A review that does not open the specs reviews an opinion.

> **Report only.** Findings are written down, not fixed.

## Phase 0: Scope

`git status --short` and `git diff HEAD --stat` for the extent. For a phase review also `git diff <base>...HEAD --stat`, because the phase diff is what the gate is about.

Cluster the files by the project's own area boundaries. Above roughly thirty changed files, review cluster by cluster, riskiest first.

## Phase 0b: Load the governing specs

The step that gets skipped. Load a handful, not the graph: for each changed area, the spec that owns it, via the project's path-to-document mapping or else the spec index.

From each spec, four parts matter: requirements and rules, interfaces and data contracts, acceptance criteria, and its **open points**. What stands open there must not have been quietly decided in the code; where it has been, that is a finding in its own right.

Plus **one** roadmap section: the current phase with goal, content and gate.

**A changed file with no spec is itself a finding.** Either the document is missing or something unspecified is being built; the second is scope creep and more serious.

## Phase 0c: The pre-check

Before reading code, from the file list alone: which of the project's invariants does this touch? Derive them from what the project settled, not from a generic catalogue: accepted decisions, mandatory rules in the root instructions, legal or domain constraints from the product definition, anything explicitly declared dead. A change that reintroduces something a decision removed is a finding however well it is written.

If the repo has a `CODING_STANDARDS.md` (the judgement rules `retro` collected from earlier reviews), read it here and hand it to the structure lens. Reviewers read it; implementing sessions never load it.

## Phase 1: Three lenses, in parallel

Depth comes from **one lens per head**.

**Up to about thirty files, split by concern.** Three reviewers in parallel, each seeing all files through one lens:

| Lens | Question |
|---|---|
| **Security** | How do I break this? Authentication, scope, input validation, error leakage, auditing, the project's own security rules |
| **Spec fidelity** | Line against document: requirements met, contracts kept, acceptance criteria achievable? Open point silently decided? Accepted decision violated? |
| **Structure** | Does it fit the house? Existing patterns, naming, error catalogue, edge cases, state transitions, query behaviour, dead code, tests, front/back contract. Plus the standards, glossary and smell baseline below |

**Above thirty files, split by cluster.** One reviewer per area carries all three lenses over its own files; the file sets are disjoint, so nothing needs deduplicating.

Use full-reading agents: exploits and contracts need the whole file, and what is missing usually lies outside an excerpt.

### The structure lens in detail

Four sources, in this order of authority:

1. **The project's standards:** `CODING_STANDARDS.md` and the root-instruction rules. They win over everything below.
2. **The glossary.** Check names in the diff (types, functions, fields, routes, user-facing text) against `GLOSSARY.md` in the knowledge base. A name that is an `_Avoid_` alias of a glossary term is a finding: same concept, wrong word. Without a glossary, skip this.
3. **The design vocabulary.** Call the Skill tool with "codebase-design" and word design findings in its terms (module, interface, depth, seam, adapter, leverage, locality): "shallow module, interface as wide as its implementation" instead of "feels overengineered".
4. **The smell baseline.** Fowler's twelve, as judgement heuristics. The repo's own standards override it (suppress a smell they endorse), and anything tooling already enforces is skipped. Label every hit "possible X", informational unless a project standard or spec also says so.
   - **Mysterious Name**: a name that does not reveal what it does or holds. Rename; if no honest name comes, the design is murky.
   - **Duplicated Code**: the same logic shape in more than one place in the change. Extract.
   - **Feature Envy**: a method that reaches into another object's data more than its own. Move it onto the data.
   - **Data Clumps**: the same few fields or parameters always travel together. Bundle them into one type.
   - **Primitive Obsession**: a primitive or string standing in for a domain concept. Give the concept a small type.
   - **Repeated Switches**: the same switch or if-cascade on the same type recurs. Use polymorphism or one shared map.
   - **Shotgun Surgery**: one logical change forces scattered edits in many files. Gather what changes together.
   - **Divergent Change**: one file edited for several unrelated reasons. Split so each module changes for one reason.
   - **Speculative Generality**: abstraction, parameters or hooks for needs the spec does not have. Inline back until a real need shows.
   - **Message Chains**: long `a.b().c().d()` navigation. Hide the walk behind one method.
   - **Middle Man**: a class or function that mostly delegates onward. Call the target directly.
   - **Refused Bequest**: a subclass that ignores or overrides most of what it inherits. Use composition.

### The brief

Every reviewer runs as a subagent on the **strong model**, set explicitly rather than inherited. This is the phase gate; a net on the cheap model defeats the trade `execute-plan` makes with its lighter per-block review. Every reviewer gets: the changed files, the governing specs with relevant requirement numbers, the current phase with its gate, the architecture rules, the true pre-check flags, `CODING_STANDARDS.md` if present, the glossary terms for the changed areas (content, not a path), and its own lens. The structure reviewer also gets the smell baseline pasted in full, having no other access to it. Plus two instructions:

**Stay in your lens.** A sibling covers findings outside it.

**Validate before reporting.** For every candidate: the path from step one to the damage or the violated rule with its number, then the counter-evidence (a database constraint, middleware, framework guarantee or validation layer that already covers it; a deliberate spec choice), then the verdict. No demonstrable path means it stays out of the report or goes in as informational.

**Every spec finding cites the requirement number it violates.** Without a number it is an opinion, for the structure lens or nowhere.

## Phase 2: Merge and report

The same location can arrive from several lenses. Deduplicate by location and cause; the highest severity wins and the note of which lenses flagged it stays. **A flag from two lenses is a stronger signal**: confirm the severity. Disagreement between lenses alone is no grounds for a downgrade.

Five severities: exploitable without authentication or destroying data; exploitable with it, a broken contract, or a reintroduced dead pattern; a weakened defence, a deviation from the house pattern, a missing test on a critical path, an open point decided in code; a functional bug with no security or contract bearing; everything informational.

More than a couple in the top band usually means validation was skipped. Between two bands, take the lower; inflation costs the report its credibility on the one day it matters.

The report carries: the verdict, the specs consulted, the findings (location, lens, violated rule, demonstration, suggested fix), the **gate comparison** item by item, the test gaps, what was solved well, the **candidates for retro**. A gate item that cannot be checked without a running system is "not checkable", never "met": this is what the user reads before releasing. Say what was clean; "checked and clean" is information.

## Phase 3: Spec backflow

Often **the spec** is the problem: a rule that cannot be built as written, two documents that disagree, a contract with no case for what actually happens. Collect these in their own section at the end (which document, which place, what is missing or contradictory); the user decides whether it becomes a spec run. This skill writes neither code nor documents.

## Phase 4: Candidates for retro

A finding in the top two bands may be a class of defect rather than an incident. Collect candidates in their own section at the end: the generalised class without file paths, the location of this instance, and whether it looks mechanical (a check could catch it) or a judgement call. Whether it is a second occurrence is for `retro` to decide, which counts in `CODING_STANDARDS.md`. Nothing is written here.

## Anti-hallucination rules

**Finding nothing is a result.** Clean code gets a clean report.

**Demonstration or it does not count.** Nothing above informational without a constructible path or a named requirement number.

**The spec beats the opinion.** Code that departs from your taste but follows the spec is not a finding; code that departs from the spec but looks nicer is.

**Read the current-state sections.** What a spec lists as existing today is not a defect of this diff.

**Use what the platform guarantees.** Theoretical bugs that frameworks, query builders and validation layers close are not findings.

**Respect the scope.** A finding in code this change did not touch is informational.
