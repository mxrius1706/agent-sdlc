---
name: handlauf
description: "Handlauf: walk a built phase through the real interface in a browser as a demanding user and report what is wrong (layout, states, speed, usability, edge cases, console, network, saved for real). EN: manual test, smoke test, click through, UX review, walkthrough, sign off the pages. DE: Handlauf, durchklicken, im Browser testen, UI pruefen, Seiten abnehmen, sieht das gut aus, nach dem Fix nochmal alles pruefen. Also after a phase is built and the question is whether the interface works, even without the word. Not automated tests, code review or page design."
---

# Handlauf - check the interface the way a user experiences it

Walk through the product holding the handrail, one page at a time, and notice everything a careful person would notice.

> **REPORT ONLY.** Find it, prove it, rank it. Fixing runs separately afterwards, through `execute-plan`; a walkthrough that repairs as it goes reviews a state nobody built.

## What this is for

The review no test and no code review can do: **what is it like to use this page?** Does it look finished or skewed? Is it clear what happened? Does the layout hold when the data is not the mockup's data? Does it survive the unexpected?

The specs are **orientation, not a checklist**: they say what a page is for. Whether it does that *well* is decided by looking at the real page. A page can satisfy every requirement and still be crooked, slow or confusing; that is what should surface here.

**The standard:** an attentive first-time user expecting quality, plus a designer who notices alignment and rhythm. Whatever either would notice at first glance belongs in the report.

**One tab, one step at a time**, no parallel subagents: the user often works in the same browser and against the same dev server.

## A clean session, and no review input

**Run in a session of its own**, started for this purpose: not as a subagent of the gate chain, not in the session that built the phase, not alongside the code reviews.

**It takes no input from `review-changes`, `thermo-nuclear-code-quality-review` or the per-block reviews**: no findings list, no report, no "watch out for X". If one has run, its output stays out of this brief.

The reason: this pass is UX work and its entire value is being the **first** look. One that has read "the permission check is fine" hunts for the permission check instead of looking at the page. One that has read nine findings confirms those nine and misses the tenth, the crooked column nobody wrote down. Primed eyes are not fresh eyes, and fresh is the only thing this pass has that the others lack.

It reads intent, not judgement: the phase plan (goal, gate, decisions), the page's UI spec, the mockup, earlier walkthrough reports. The findings go to the user and into the phase plan; the code reviews are not their audience either, since three gates with their own heads is the point.

## Phase 0 - understand, do not tick off

1. **The surfaces** from the request, or derived from the phase plan and briefly confirmed. Then cross-check against the code: from `git diff <base>...HEAD --stat`, the pages and components the phase touched, plus the pages that use a changed component (search for its imports, following how the project routes pages). Whatever turns up and is not in scope goes to the user, who decides; this catches pages changed along the way.
2. **Get oriented**, a few minutes per surface. What is the page for, who uses it, what is the main path? Sources as above. Gate sentences become mandatory flows.
3. **An inventory, not a spec matrix**, written into the report file from `references/report-template.md`. Per surface:
   - the **states** to be seen (empty, one row, many, long, loading, error, locked, archived, draft, preview),
   - the **flows** (main path first, then side paths),
   - the **data variants** that stress the layout (very long name, many tags, no tags, many steps, accents, special characters).

   Give them ids (`V1.2` visual, `A1.3` flow, `E1.4` edge case) for the report.

## Phase 1 - set up

What is specific to the project comes from the rows for `handlauf` in the root CLAUDE.md section `Project references`. Each step below names its topic and what to do when the row is missing; every missing row is named in the report under the environment section.

1. **Load the browser skill** for the project's browser (topic `browser`; no row: the browser the user has connected), and the tools you expect to need in **one** `ToolSearch` call. Which tools those are depends on the family the session has, Claude in Chrome or Chrome DevTools: `references/browser-tools.md` maps every purpose below to its tool in both.
2. **A dev server with a log.** Reuse one from this session if it has a log; otherwise start it through `scripts/start-dev-logged.sh <logfile>` with `run_in_background`, after asking the user. The values come from topic `dev server` (command, directory, port, health URL, build marker, error markers), set as the `HL_*` variables the two scripts list in their headers. Where the app does not sit at the repository root (a monorepo, an app in a subfolder), the row sets the directory as `HL_DIR`. No row: ask the user for command and port.
3. **Watch the log**: a `Monitor` on `scripts/watch-dev-log.sh <logfile>`, `timeout_ms` at maximum, re-armed on expiry. Assign every message to the step running when it appeared.
4. **Your own window**: a tab of your own, size fixed at 1440 x 900 so screenshots are comparable.
5. **Check the session**: account, role, permissions. Test accounts and roles come from topic `accounts`, a pointer to where they are kept, never the credentials themselves. No row, or expired: ask the user.
6. **Read the pitfalls first**: `references/pitfalls.md` for the generic ones, topic `pitfalls` for the project's own (no row: none known).

## Phase 2 - look (every page, every state)

The core. **A full-resolution screenshot**, and actually look: first as a whole (the impression in one sentence: tidy? finished? calm?), then area by area, zoomed in. Reading the page text supplements looking, never replaces it.

Check against `references/ux-checklist.md`, above all:

- **Alignment and grid:** same things in the same place? Table columns under one another, equal widths for equal elements, flush edges, one spacing rhythm. **Compare repeated blocks against each other** (groups, cards, rows, list entries): same thing looking different is a finding.
- **Stability under different data:** does a long title, a missing tag or a large number change the layout around it? Does anything shift while loading, on hover, on open? Produce the phase 0 data variants on purpose and look again.
- **Overflow and truncation:** text escaping its box, cut off without a hint, broken mid-word, tooltips missing where truncated.
- **Hierarchy and readability:** is it clear what matters and what the main action is? Labels understandable, jargon-free, consistent in tone and terminology?
- **Consistency with the app:** the same building blocks, button styles, pills, spacing, icons, design tokens as neighbouring pages?
- **States:** loading (how long? right skeleton shape? jump afterwards?), empty, error, locked (does the page say why?), success (any feedback?).

**Load time is UX:** note anything above roughly 2 seconds to content, with a measurement. After a fresh server start, load once before measuring; compilation does not count.

## Phase 3 - use it

The inventory's flows, main path first. Act like a person: click, type, Enter, Escape, Back.

After every action, **three looks**:
- **The page:** what changed, is it understandable, is there feedback (toast, status change, focus), is the new state cleanly presented (the phase 2 look again)?
- **The network** (with Claude in Chrome, read it once before the action so capture is running): 4xx/5xx, duplicate or unnecessary calls, slow responses.
- **Console and log:** console messages filtered to `error|warn|Uncaught|hydration`, plus the monitor messages.

**Does it make sense?** At every dialog, field and button, ask as the user: why am I being asked this? Does the system not know it already? What would I enter without prior knowledge? Does the page offer the next step? A step that only a tester's knowledge fills in correctly is a finding, however clean it looks.

**Verify that it is really saved:** reload, reopen the page, or read the data through topic `data access` (a read-only API route or database access; no row: reload and reopen only, and name the gap). A success toast is not proof.

**Edge cases** from `references/edge-cases.md`, chosen to fit the surface: double clicks, two tabs, Back, reload mid-dialog, boundary inputs, deep links, foreign ids, caches after dialogs.

**Test data:** created only through the interface, prefixed `HL`, all noted in the report. Existing data is read only unless the user releases it. To check a write path against data you may not touch, use probes that write nothing (a wrong revision to provoke a conflict). Write or delete through the database only after asking.

## Phase 4 - the cross-cutting pass and roles

For **every** page checked, with a screenshot and the phase 2 look:
- **Dark mode:** contrast, invisible text, harsh white areas, charts.
- **The other language**, where the product has one: raw keys, untranslated leftovers, longer strings breaking the layout.
- **Narrow** (390 x 844): no horizontal page scroll, nothing overlapping, main action reachable.
- **Keyboard:** tab order, visible focus, Escape, Enter.

**Roles in one batch** at the end: send the user the list (account, role, scope, what will be checked), wait, verify the session, check, then ask to be switched back.

## Phase 5 - close

1. **The report**, following `references/report-template.md`. Severity:
   - **S1** broken or data lost (crash, 5xx, a save that disappears, the wrong record, a permission leak).
   - **S2** the main path is disturbed, or the page looks broken or unfinished at first glance (visibly skewed main page, 4xx in the normal flow, wrong data, a violated gate sentence, a load time that leaves you unsure anything is happening).
   - **S3** operation or appearance grates (inconsistency with neighbours, unclear text, missing feedback, focus, edge-case overflow, dark mode or narrow defects).
   - **S4** polish (a few pixels, wording, an icon).

   Every visual finding has a screenshot saved to disk (topic `screenshots`; no row: the OS temp directory) with its path in the report, and says *what* is wrong and *compared with what*: "the Status column starts at x=612 in group A and at x=540 in group B".
2. **An overall impression** per page in two or three sentences, with the single most valuable improvement.
3. **A plan entry** in the phase plan: a short decision entry with the numbers and a reference to the report.
4. **Clean up:** stop the monitor, close your tab, leave the dev server running.
5. **To the user:** overall impression, S1 and S2 individually, S3 and S4 summarised, what could not be checked, the report path.

## Where this fits

`execute-plan` builds the phase; this runs after it and before the phase gate, or again after a round of fixes. It answers whether the thing works and looks right; `review-changes` whether the code is sound; `thermo-nuclear-code-quality-review` whether it stays maintainable. Only this one requires looking at the product.
