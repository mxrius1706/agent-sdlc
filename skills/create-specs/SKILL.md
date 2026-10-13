---
name: create-specs
description: "Break a planned product into components, laid out as a connected graph of specs: index, placeholders with declared boundaries, writing order. Use after product definition and stack are settled and before any single spec, when asked how to cut a system or where a boundary runs, or when specs exist but nothing relates them."
---

# Create Specs

Cut the product into components, and connect them.

The cutting is the smaller half. A list of components is a filing system, and filing systems do not stop two documents from specifying the same field differently. What prevents that is every component stating what it does **not** cover and naming who does. Then the specs form a graph that can be navigated and checked instead of a pile that slowly contradicts itself.

This skill lays out the graph; each spec is written later, one at a time (`write-spec`), against this map.

## What this produces

- **A spec index**: every planned component with its responsibility in one sentence, the components it depends on, and its status. It is the map and is updated whenever a spec is written or a component added.
- **One placeholder per component**, at its final path, with frontmatter and declared boundaries only, marked unmistakably as not yet written.
- **A writing order**, derived from the dependencies.

## Phase 0: Read the foundation

The product definition, the stack decisions and, with an interface, the design system. Components derive from them, so a half-read product definition yields components that do not match what is built. Read existing code too: components that already exist are facts, and a decomposition that ignores them describes a different system than the one on disk.

## Phase 1: Structural layers

Start from this set, then **remove what this project does not have**:

- **architecture** - how the system is put together, deployment shape, security posture, tenancy
- **data** - the entities, their relationships, the invariants that must hold
- **api** - the contracts other things call
- **ui** - the screens, if there are any
- **integrations** - external systems, one per system
- **decisions** - one document per architectural decision, kept separate because decisions outlive the documents that cite them

A project with no external systems gets no integrations layer (an empty folder invites someone to fill it); a library has no ui. The set is a proposal, not a template to complete.

## Phase 2: Product domains

These come from the product definition and differ per project. Look for two things.

**The nouns the product is about**: the things users create, find, change and talk about. A domain usually forms around a noun with its own lifecycle.

**The flows.** A path that runs end to end through the system and that someone would describe as one thing usually earns a document even though it touches everything. It explains how the pieces fit; without it every reader reassembles the story from the parts.

A domain is real when it has vocabulary of its own and rules that make no sense outside it. A "utilities" domain has neither, so that name always signals a bad cut.

## Phase 3: Settle the boundaries

This phase matters most, and it is a conversation, not a derivation.

Invoke `grill-me`. For each pair of components that could plausibly own the same thing, ask the user which one owns it and what the other says instead. The answer becomes a line in the losing component's boundary list.

Ask where a reasonable person could answer either way: does the state machine own the permission to make a transition, or the permissions component? Does the entity document define the validation rules, or the contract that receives them? No answer is universally right, so decide once and write it down.

**Every component gets an explicit not-covered list**, a required section, each entry naming the component that owns it instead. This makes the graph navigable and stops the same rule being written twice.

**A boundary is a link in both directions.** If A says the model belongs to B, B is now responsible for the model, and that expectation is real before B is written. Record it, so the later component honours the assumption or knowingly breaks it.

## Phase 4: Writing order

Write what everything else points at first. The entity model usually leads: contracts, flows and screens all reference fields, and a contract specified before the fields exist invents fields that turn out wrong. Then the domain logic using the entities, then the contracts exposing it, then the interface consuming them.

Where two components genuinely depend on each other, say so. Write the more stable one first and mark the other as expected to correct it.

This is the writing order only. The build order, which follows what delivers value first, is derived later by `plan-build`.

## Phase 5: Write

**The index** is the entry point and stays current: a spec written without its index entry updated is a component nobody can find.

**A placeholder per component**, at the path it will keep, with only frontmatter and the phase 3 boundaries:

*Create them at the correct path now.* In a linked knowledge base, following a link to a missing document creates it wherever the tool guesses. Pre-created placeholders make every planned link resolve to the right place from day one.

*Make them unmistakably unwritten*: a status field and a body sentence saying so. The next step reads neighbouring specs to learn what has been assumed, so a placeholder that reads like a thin specification contributes assumptions nobody made. Neither a person skimming nor a later pass reading in bulk may confuse the two.

Links use the full path the knowledge base resolves unambiguously.

## Boundaries of this skill

**Requirements belong in the component's own document**, written against the code. One written into the map is a requirement nobody reviews.

**Components exist for substance.** If one domain has an overview and another does not need one, that is fine; filling a matrix produces empty documents. If a component's boundary list is longer than its responsibility, it is a paragraph moved out of another component.

For an interface, the screens are their own step (`plan-pages`), a product conversation held after the components stand.

## Before finishing

Update the roadmap in the knowledge base: mark the component map done, record how many specs are planned, and set the next action to the **first document in the writing order, with the reason**. "Start with the entity model, everything else references it" tells the next session where to begin and why; "Write specs" tells it nothing.
