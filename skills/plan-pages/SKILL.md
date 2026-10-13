---
name: plan-pages
description: "Decide which screens a product needs and how they connect, before any is specified: inventory of what exists, navigation graph, findings, target page list (new, kept, dropped). Use once component specs stand, when asked what pages a product needs, how navigation works, or which screens survive a rebuild."
---

# Plan Pages

Settle which screens exist and how you get between them.

A product definition says what the product can do; only the specs say what a working day looks like, and screens follow the working day. A page list derived from the product definition mirrors the document structure instead of the work. The leading question is **"what daily work do these specs actually describe"**, so read the component specs fully.

## One overview per surface

A surface is a place with its own navigation and layout rules: a web portal, a chat bot, a mobile app, an admin console. Ask which surfaces exist first. Each gets its own overview; a shared page list becomes a table with a column saying "does not apply here".

## What the overview contains

Four parts. The first three are about what is, the fourth about what should be; keeping them apart stops the plan from describing a rebuild as already done.

### 1. The inventory of what exists

Every screen that exists today, with route and file path, verified by reading the code. If nothing exists yet, say so in one line; "greenfield" is information.

### 2. The navigation graph

Mandatory. A diagram of which screen reaches which, with permission-dependent edges marked. It is the only artefact that shows whether a screen is reachable at all: a target list without a graph can contain an island, found during the build instead of the planning. Marked gates also make missing gating visible, since an unrestricted edge stands out next to restricted ones.

Draw the current graph and, once the target list exists, the target graph. The difference is a large part of the work ahead.

### 3. Findings, without judgement

What the code review of the current surface turned up, as observation rather than verdict: dead controls, more than one layout family, inconsistent permission gating, filters over a field being removed.

A finding is true today; a target is decided for tomorrow. Merged, nobody can tell observations from plans.

### 4. The target page list

Three groups, each entry with its reason:

- **New pages.** What they are for, and why a page rather than a panel or dialog; the alternative gets proposed again in six months.
- **Kept, with changes.** What stays, what changes, what is removed. Name the removals; they are the part forgotten and left in the code.
- **Dropped.** With the reason, or someone rebuilds it assuming an oversight.

Derive each entry from a spec and cite it. A page that traces to no component spec is a missing spec or a page nobody needs.

## Settle the cuts by conversation

Invoke `grill-me` for decisions that could go either way, the component-boundary questions one level up:

**Page or panel?** The test is how many independent decisions the user makes there at once, not how much data it shows.

**One screen or several?** Two jobs sharing data but not rhythm want separate screens; sharing rhythm, one screen with a filter.

**Which screen owns an action** that plausibly belongs to two.

**What the navigation looks like.** One entry with tabs or several entries; visible on every page, cheap now, expensive later.

Give a recommendation with each question and let the user decide: these are product decisions about how the work feels.

## Status per page

The overviews live in the knowledge base, next to the specs; fill the page plans' row in the knowledge base map when the first one is written. The overview carries how far each target page has got (planned, specified, with a link to its spec once written). It is the entry point for the next step and stays current as each page spec lands.

## Boundaries

**Page content belongs in the page's own spec** (`write-ui-spec`), decided against a mockup. Half-specified here, it is an unreviewed decision and a second version of what the spec will say.

**Every target page has at least one inbound edge** in the target graph, or a note saying why it is entered from outside the surface.

## Before finishing

Update the roadmap in the knowledge base: mark the page planning step, record how many pages are planned, and set the next action to the **first page spec, with the reason it goes first**, usually the screen the most others lead into, because its decisions constrain theirs.
