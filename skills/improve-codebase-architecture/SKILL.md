---
name: improve-codebase-architecture
description: Survey the existing code for places where shallow modules can be deepened, show the candidates as a visual HTML report, and work the chosen one through the normal spec and plan flow.
disable-model-invocation: true
---

# Improve Codebase Architecture

Surface architectural friction in the existing code and propose **deepening opportunities**: refactors that turn shallow modules into deep ones. The aim is testability and navigability, for people and agents alike.

This is maintenance on the stock, run on the user's own initiative. It is not a review of a diff; that is `thermo-nuclear-code-quality-review`.

It is built on a shared design vocabulary and on the project's own records:

- Call the Skill tool with "codebase-design" for the architecture vocabulary (**module**, **interface**, **depth**, **seam**, **adapter**, **leverage**, **locality**) and its principles (the deletion test, "the interface is the test surface", "one adapter = hypothetical seam, two = real"). Use these terms exactly in every suggestion, and don't drift into "component," "service," "API," or "boundary."
- The domain language in `GLOSSARY.md` gives names to good seams. The decision records record what is settled and are **not re-litigated**. Both live in the knowledge base; find them via the knowledge base map in the root CLAUDE.md.

## Process

### 1. Explore

**Scope before you scan: YAGNI.** Deepening a module pays off by making future changes to it easier, so put extra weight on the parts of the codebase that have recently changed. Decide *where* to look before you look:

- If the user named a direction (a module, a subsystem, a pain point), take it, and skip the inference below.
- Otherwise, walk back a good stretch of the commit history (`git log --oneline`) to find the codebase's hot spots, the files and areas that keep coming up, and let those paths pull your attention first. If the changes are scattered with no clear hot spot, widen the net.

Read `GLOSSARY.md` and the decision records for the area you're touching first.

Then spawn a sub-agent to walk the codebase. Don't follow rigid heuristics; explore organically and note where you experience friction:

- Where does understanding one concept require bouncing between many small modules?
- Where are modules **shallow**, with an interface nearly as complex as the implementation?
- Where have pure functions been extracted just for testability, but the real bugs hide in how they're called (no **locality**)?
- Where do tightly-coupled modules leak across their seams?
- Which parts of the codebase are untested, or hard to test through their current interface?

Apply the **deletion test** to anything you suspect is shallow: would deleting it concentrate complexity, or just move it? A "yes, concentrates" is the signal you want.

### 2. Present candidates as an HTML report

Write a self-contained HTML file to the OS temp directory so nothing lands in the repo. Resolve the temp dir from `$TMPDIR`, falling back to `/tmp` (or `%TEMP%` on Windows), and write to `<tmpdir>/architecture-review-<timestamp>.html` so each run gets a fresh file. Open it for the user (`xdg-open <path>` on Linux, `open <path>` on macOS, `start <path>` on Windows) and tell them the absolute path.

The report uses **Tailwind via CDN** for layout and styling, and **Mermaid via CDN** for graph-shaped diagrams (call graphs, dependencies, sequences). Use hand-built divs/SVG for the more editorial visuals (mass diagrams, cross-sections). Each candidate gets a **before/after visualisation**. Be visual.

For each candidate, render a card with:

- **Files**: which files/modules are involved
- **Problem**: why the current architecture is causing friction
- **Solution**: plain English description of what would change
- **Benefits**: explained in terms of locality and leverage, and how tests would improve
- **Before / After diagram**: side-by-side, custom-drawn, illustrating the shallowness and the deepening
- **Recommendation strength**: one of `Strong`, `Worth exploring`, `Speculative`, rendered as a badge

End the report with a **Top recommendation** section: which candidate you'd tackle first and why.

**Use `GLOSSARY.md` vocabulary for the domain, and the `codebase-design` vocabulary for the architecture.** If `GLOSSARY.md` defines "Order," talk about "the Order intake module," not "the FooBarHandler," and not "the Order service."

**Decision conflicts**: if a candidate contradicts an accepted decision record, only surface it when the friction is real enough to warrant revisiting the decision. Mark it clearly in the card (e.g. a warning callout: _"contradicts the decision on X, but worth reopening because…"_). Don't list every theoretical refactor a decision forbids.

See [HTML-REPORT.md](HTML-REPORT.md) for the full HTML scaffold, diagram patterns, and styling guidance.

Do NOT propose interfaces yet. After the file is written, ask the user: "Which of these would you like to explore?"

### 3. Grilling loop

Once the user picks a candidate, call the Skill tool with "grilling" to walk the decision tree with them: constraints, dependencies, the shape of the deepened module, what sits behind the seam, what tests survive.

Side effects happen inline as decisions crystallize; call the Skill tool with "domain-modeling" to keep the domain model current as you go:

- **Naming a deepened module after a concept not in `GLOSSARY.md`?** Add the term. Sharpening a fuzzy term during the conversation? Update it right there.
- **User rejects the candidate with a load-bearing reason?** Offer a decision record, framed as: _"Want me to record this as a decision so future architecture reviews don't re-suggest it?"_ Only offer when the reason would actually be needed by a future explorer to avoid re-suggesting the same thing; skip ephemeral reasons ("not worth it right now") and self-evident ones.
- **Want to explore alternative interfaces for the deepened module?** Call the Skill tool with "codebase-design" and use its design-it-twice parallel sub-agent pattern.

### 4. A chosen candidate enters the normal flow

A chosen candidate is **not refactored freely**. A restructuring that bypasses the specs and the roadmap leaves both describing code that no longer exists. Once the grilling has settled the shape:

1. Call the Skill tool with "write-spec" for the affected component, so the delta (what changes, what stays, what the neighbours see) is written down.
2. Call the Skill tool with "planning" for the work, so it gets a plan, tests at the agreed seams, and a place in the roadmap.

Building starts after the plan is released, like any other phase.
