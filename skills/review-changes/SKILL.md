---
name: review-changes
description: "Review the open or phase changes against the specs, the accepted decisions and the project's own patterns. Fans out into three parallel lenses - security, spec fidelity and structure - validates every finding before reporting it, and checks the phase gate item by item. Reports only, never fixes. Use it before a commit or a push, at the end of a build phase, or whenever someone asks whether changes are sound, ready to commit or good to release, even without the word review."
---

# Review Changes

Judge the changes against the contract, not against taste.

The standard here is not general code aesthetics. It is: **does the code do what the specs say, in the way this project does it everywhere else?** The specs are the truth about what should be; the code is the current approximation. A review that does not open the specs reviews an opinion.

> **Report only.** Findings are written down, not fixed. No code changes, no refactoring, no "I quickly fixed it while I was there". A review that edits as it goes is a review nobody reviewed.

## Phase 0: Scope

`git status --short` and `git diff HEAD --stat` for the extent. For a phase review, `git diff <base>...HEAD --stat` as well, because the phase diff is what the gate is about, not just what is still uncommitted.

Cluster the files by area, using the project's own area boundaries. Above roughly thirty changed files, review cluster by cluster, and start with whatever carries the most risk in this project.

## Phase 0b: Load the governing specs

The most important step, and the one that gets skipped.

**Load deliberately, not everything.** A review needs a handful of specs, not the whole graph. Choose them from the changed paths: for each changed area, the spec that owns it. Where the project's rules already carry a path-to-document mapping, use it; otherwise derive it from the spec index, which lists what each component covers.

From every loaded spec, four parts matter: its requirements and rules, its interfaces and data contracts, its acceptance criteria, and its **open points**. The last is the most valuable. What stands there as open must not have been quietly decided in the code. Where it has been, that is a finding in its own right: a decision made in code that no document carries.

Plus **one** section of the roadmap: the current phase, with its goal, content and gate. Not the other phases.

**A changed file with no spec is itself a finding.** Either the document is missing, or something is being built that nobody specified. The second is scope creep and the more serious of the two.

## Phase 0c: The pre-check

Before reading any code, from the file list alone: which of the project's invariants does this touch?

Derive the list from what the project has actually settled, not from a generic catalogue: the accepted decisions, the mandatory rules in the root instructions, the legal or domain constraints the product definition names, and anything the project has explicitly declared dead. A change that reintroduces something a decision removed is a finding regardless of how well it is written.

If the repo has a `CODING_STANDARDS.md`, it is a standards source too: the judgement rules that `retro` collected from earlier reviews. Read it here and hand it to the structure lens. It is read by reviewers only, which is the point: it never loads into an implementing session.

The checklist is project-specific by nature. Build it once from the decisions and keep it with the project, not here.

## Phase 1: Three lenses, in parallel

Fan-out buys depth through **one lens per head**, not five lenses in one overloaded head.

**Up to about thirty files, split by concern.** Three reviewers in parallel, each seeing all the files, each looking through exactly one lens:

| Lens | Question |
|---|---|
| **Security** | How do I break this? Authentication, scope, input validation, error leakage, auditing, the project's own security rules |
| **Spec fidelity** | Line against document: are the requirements met, the contracts kept, the acceptance criteria achievable? Was an open point silently decided? Is an accepted decision violated? |
| **Structure** | Does it fit the house? Existing patterns, naming, error catalogue, edge cases, state transitions, query behaviour, dead code, tests, the contract between front and back. Also the standards, the glossary and the smell baseline below |

These are three different ways of thinking. Merging security and spec fidelity costs depth in both; separating structure from correctness only opens a crack for findings to fall through.

**Above thirty files, split by cluster instead.** One reviewer per area, carrying all three lenses over only its own files. The file sets are disjoint, so nothing needs deduplicating.

Use a full-reading agent, not an excerpt-reading one. Constructing an exploit and checking a contract both need the whole file, and what is missing is usually outside the window an excerpt search would have picked.

### The structure lens in detail

Four sources, in this order of authority:

1. **The project's standards:** `CODING_STANDARDS.md` and the rules in the root instructions. They win over everything below.
2. **The glossary.** Check the names in the diff (types, functions, fields, routes, user-facing text) against the terms in `GLOSSARY.md` in the knowledge base. A name that is an `_Avoid_` alias of a glossary term is a finding: same concept, wrong word, and the next reader cannot tell it is the same thing. Without a glossary, skip this.
3. **The design vocabulary.** Call the Skill tool with "codebase-design" and use its terms (module, interface, depth, seam, adapter, leverage, locality) to word design findings, so that "shallow module, interface as wide as its implementation" replaces "feels overengineered".
4. **The smell baseline.** Fowler's twelve, as judgement heuristics. Two rules bind it: the repo's own standards override it (where they endorse something the baseline flags, suppress the smell), and anything tooling already enforces is skipped. Every hit is labelled "possible X", never a hard violation, and never above informational unless a project standard or a spec also says so.
   - **Mysterious Name**: a name that does not reveal what it does or holds. Rename; if no honest name comes, the design is murky.
   - **Duplicated Code**: the same logic shape in more than one place in the change. Extract and call it from both.
   - **Feature Envy**: a method that reaches into another object's data more than its own. Move it onto the data it envies.
   - **Data Clumps**: the same few fields or parameters always travel together. Bundle them into one type.
   - **Primitive Obsession**: a primitive or string standing in for a domain concept. Give the concept a small type.
   - **Repeated Switches**: the same switch or if-cascade on the same type recurs. Replace with polymorphism or one shared map.
   - **Shotgun Surgery**: one logical change forces scattered edits in many files. Gather what changes together into one module.
   - **Divergent Change**: one file edited for several unrelated reasons. Split so each module changes for one reason.
   - **Speculative Generality**: abstraction, parameters or hooks for needs the spec does not have. Delete; inline back until a real need shows.
   - **Message Chains**: long `a.b().c().d()` navigation the caller should not depend on. Hide the walk behind one method.
   - **Middle Man**: a class or function that mostly delegates onward. Cut it and call the target directly.
   - **Refused Bequest**: a subclass that ignores or overrides most of what it inherits. Use composition.

### The brief

Every reviewer runs as a subagent on the **strong model**, set explicitly rather than inherited. This is the phase gate, and it is what makes a lighter per-block review during the build acceptable: a net on the cheap model defeats the trade that `execute-plan` makes. Every reviewer gets: the changed files, the governing specs with their relevant requirement numbers, the current phase with its gate, the project's architecture rules, the true pre-check flags, `CODING_STANDARDS.md` if there is one, the glossary terms for the changed areas (content, not a path), and its own lens. The structure reviewer also gets the smell baseline pasted in full, since it has no other access to it. Plus two instructions that do the actual work:

**Stay in your lens.** A finding outside it is not yours; a sibling covers it. Deep in one lens beats broad and shallow.

**Validate before reporting.** For every candidate finding: the path from step one to the damage or the violated rule with its number, then the counter-evidence, then the verdict. Is there a database constraint, a middleware, a framework guarantee, a validation layer that already covers it? Does the spec cover it deliberately? No demonstrable path means it does not go in the report, or goes in as informational.

For the spec lens specifically: **every finding cites the requirement number it violates.** A spec finding without a number is an opinion, and belongs in the structure lens or nowhere.

## Phase 2: Merge and report

The three reviewers saw the same files, so the same location can arrive twice. Deduplicate by location and cause; the highest severity wins, and the note of which lenses flagged it stays. **Being flagged from two lenses is a stronger signal, not a weaker one** — confirm the severity rather than softening it. Disagreement between lenses is normal and is not grounds for a downgrade on its own.

Five severities: something exploitable without authentication or destroying data; something exploitable with it, or a broken contract, or a reintroduced dead pattern; a weakened defence, a deviation from the house pattern, a missing test on a critical path, an open point decided in code; a functional bug with no security or contract bearing; and everything informational.

More than a couple in the top band usually means the validation step was skipped. Between two bands, take the lower one. Severity inflation costs the report its credibility on the one day it matters.

The report carries: the verdict, the specs consulted, the findings with location, lens, violated rule, demonstration and a suggested fix, then the **gate comparison** item by item, then the test gaps, then what was solved well, then the **candidates for retro**. A gate item that cannot be checked without a running system is "not checkable", never "met" — that distinction is the whole value of the gate section, and it is the part the user reads before releasing.

Say what was clean. "Checked and clean" is information, and its absence reads like an oversight.

## Phase 3: Spec backflow

A review regularly finds that **the spec** is the problem, not the code: a rule that cannot be built as written, two documents that disagree, a contract with no case for what actually happens.

These findings otherwise vanish, because the report only judges code. Collect them in their own section at the end: which document, which place, what is missing or contradictory. The user decides whether that becomes a spec run. **Change no spec here** — this skill writes neither code nor documents.

## Phase 4: Candidates for retro

A finding in the top two bands may be a class of defect rather than an incident. This skill does not turn it into a rule, because it reports only. It collects the candidates in their own section at the end of the report: the generalised class of defect without file paths, the location of this instance, and whether it looks mechanical (a check could catch it) or a judgement call. Whether it is a second occurrence is for `retro` to decide, which counts in `CODING_STANDARDS.md`. Nothing is written here.

## Anti-hallucination rules

**Finding nothing is a result.** Clean code gets a clean report. A report without findings is a good outcome, not a sign of laziness.

**Demonstration or it does not count.** Nothing above informational without a constructible path or a named requirement number.

**The spec beats the opinion.** Code that departs from your taste but follows the spec is not a finding. Code that departs from the spec but looks nicer is.

**Read the current-state sections.** Every spec also describes what exists today. What stands there as existing is not a defect of this diff.

**Use what the platform guarantees.** Frameworks, query builders and validation layers already cover a good deal; theoretical bugs they close are not findings.

**Respect the scope.** A finding in code this change did not touch is informational.
