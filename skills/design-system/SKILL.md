---
name: design-system
description: "Define a project's design system, write tokens into the codebase and reasoning into the knowledge base, approved via an example page. Use when a look needs defining, for brand colours, fonts, dark mode, tokens, a redesign, or when UI keeps coming out inconsistent. Run after the stack is settled."
---

# Design System

Settle what the project looks like, write the values where the code can use them, and keep the reasoning where the code cannot express it.

A design system that exists only as prose gets ignored, because nobody can build from adjectives. One that exists only as token values gets violated, because nothing says why red is never a background. Both halves are needed, in different places.

## What this produces

**A token file in the repository.** Colours, type scale, spacing, radii, elevation, state styling. The code reads it, so it is the only place a value lives.

**A design schema in the knowledge base.** The named direction, principles, rules that constrain use, rationale, and a pointer to the token file. No value is repeated here.

**An example page.** A real rendering of the system, used to approve it. Approving a palette from a table of hex codes is guessing; approving a page is judgement.

## Phase 0: What already exists

**Nothing is built yet.** Everything is a choice, but check for a brand outside the code: a brand guide, a logo with defined colours, an existing website, a colour used on invoices. A design system invented next to an existing brand is a second brand nobody asked for.

**Something is already built.** The current look is a fact, read from the code: find the stylesheet, theme file or token definitions and extract what is in use. Expect inconsistency (five greys that should be three, a spacing scale with exceptions, hover states that differ per component). That inconsistency is the finding that makes the system worth writing down.

Say what is in use, say where it contradicts itself, and let the user decide which version wins.

Read the stack decisions too: they determine the token format.

## Phase 1: Settle the direction

Invoke `grill-me` for what is genuinely open; phase 0 answers the rest.

- **The direction itself**, as a name plus a few principles. "Kinetic Precision, high-contrast minimalism, no decorative depth" carries further than hex codes because it decides the cases nobody enumerated.
- **Colour**, from the brand colour if one exists. Then neutrals, the surface hierarchy, and semantic roles: success, warning, danger, information.
- **Where the brand colour must not go.** The most useful colour rule is usually a prohibition, because the failure mode is using it everywhere.
- **Typography**, families and scale, and what distinguishes a heading from a label beyond size.
- **Spacing**, a base unit and the multiples in use, so exceptions become visible.
- **Radius and elevation**, including whether the project expresses depth at all. Deciding against shadows is a decision and needs stating.
- **Interaction states**, focus first: the one every system forgets and accessibility depends on.
- **Dark mode**, whether it exists. Half a dark mode is worse than none.
- **The accessibility floor**, as a checkable target, such as WCAG AA contrast with the ratios named.

Unresolved items stay `TBD` with a note on what would settle them.

## Phase 2: Show it

Build an example page that renders the system in use, and present it before writing anything permanent.

A page with what a real screen has, not a swatch sheet: headings and body at real sizes, buttons in every state including focus and disabled, form fields with a validation error, a card, a table row, a status indicator, a navigation element; in light and dark if dark mode was decided. It exposes combinations that look fine alone and wrong together.

Use the `artifact-design` skill if available so the page can be published and viewed; otherwise write a self-contained HTML file and tell the user where it is. The page carries the proposed token values, so what the user approves is what gets written.

Iterate here: a token changes for free in a preview and costs a sweep once the codebase consumes it.

## Phase 3: Write

Only after the example page is approved.

### The token file, in the repository

Write the values in the shape the stack consumes (utility-first CSS framework, plain custom properties, a theme object, a platform's resource format are different targets); read the stack decisions. A token file in the wrong shape is decoration. Everything else points at this file.

### The design schema, in the knowledge base

Everything the token file cannot say:

- The named direction and its principles
- Why these choices, and what was considered and rejected
- The rules that constrain use, such as where the brand colour may not appear, or which increments are allowed
- Component patterns, described by intent rather than exact values
- The accessibility target and how to check it
- A pointer to the token file for every value

The test for a line: **could the code have told me this?** If yes it belongs in the token file and the document points there.

Token values in prose next to a token file in the code are two truths; the first time they disagree, the reader builds the wrong thing and nothing warns them.

## Running it later

A redesign, rebrand or added dark mode is this skill on a project that already has answers: phase 0 reads the existing tokens, and only what changes goes through the interview. The old value stays documented with what it becomes and until when the code still does it (the "stock with an expiry date" rule from the root `CLAUDE.md`), so a session during the transition is not told a future state as present.

## When called by project-init

Once the token file exists, add the row `design-system` / `tokens` to the root CLAUDE.md section `Project references` pointing at it, and fill the design schema's row in the knowledge base map. Return the direction, the token file location and any open `TBD`, so the area map can decide whether the interface deserves its own instructions and what they point at.

## Before finishing

Update the roadmap in the knowledge base: mark the design system step, note where the token file lives, and set the next action. A half-finished design system stays there as such, with what is missing.
