---
name: project-init
description: Set up the Claude Code configuration for a project from scratch - the Obsidian knowledge base, the PRD, and the full instruction layer of root and area CLAUDE.md files, path-scoped rules and hooks. Use this whenever a user starts a new project, says the PRD is done and they want to set the project up, asks to initialize or scaffold their Claude config, wants CLAUDE.md files created, or is standing in an empty repository wondering how to begin. Also use it when a project already has code but no configuration layer worth the name. Do not confuse this with the built-in /init command, which only summarizes an existing codebase into a single file.
---

# Project Init

Build the configuration layer a project needs so that every later session starts informed instead of guessing.

The output is not one file. It is a set of instructions separated by **when they load into the context window**, plus a knowledge base outside the repository. The value comes from putting each statement in exactly one place, and the separation is what makes that possible: a rule that only matters in one corner of the codebase does not have to be paid for in every session.

## The idea in one paragraph

A project has three kinds of truth and they age at different speeds. Product truth (what we build and why) changes rarely and belongs outside the repository, where it is not tied to a branch. Working conventions (how we build here) change with the stack and belong in version control next to the code they govern. Current state (what the code actually does today) is only reliable when read from the code itself, so configuration must never claim it without evidence. Mixing these three is what makes documentation rot. Separating them is the entire point of this skill.

## Order of operations

Do these in order. Each phase depends on the one before it.

0. Knowledge base
1. PRD
2. Stack interview
3. Area map
4. Plan for approval
5. Write

Never skip ahead to writing files. The plan in phase 4 is presented and approved before anything is created.

---

## Phase 0: Knowledge base

This comes first, before the PRD, because the PRD needs somewhere to live that is not the repository.

Product truth in the repo is a trap. It sits on a branch, it gets copied into a second file for convenience, and six months later two versions disagree and nobody knows which one is binding. Keeping it in a vault outside the repo removes the temptation, because there is only ever one copy to read.

**Check for an Obsidian MCP server.** If Obsidian tools are already available, use them and move on.

If not, walk the user through it. Do not assume familiarity, since many people have never added an MCP server. Explain that this connects Claude to a folder of Markdown notes, and that Obsidian itself is optional because the folder works either way.

The simplest server takes a vault path directly and needs no plugin, no API key and no running Obsidian:

```json
{
  "mcpServers": {
    "obsidian": {
      "type": "stdio",
      "command": "obsidian-mcp",
      "args": ["<absolute path to the vault folder>"]
    }
  }
}
```

This goes in the global settings or the project `.mcp.json`. Ask which they prefer: global if they want one vault across projects, project-local if this vault belongs to this project alone. The server has to start before its tools appear, which usually means restarting the session. Say that up front, or they will wonder why nothing works.

A REST-based alternative exists that talks to a running Obsidian instance through a Local REST API plugin and an API key. Only suggest it if the user specifically wants live sync with the Obsidian app. It is more setup and more that can break, and an API key sitting in a config file is a liability worth avoiding when the simple server does the job.

**Create the vault structure.** Once the server answers, lay out the space for this project:

```
<Vault>/
  <Project>/
    PRD.md              product truth, the binding definition
    roadmap.md          where the project stands, initialised with the steps ahead
    specs/
      _index.md         one line per spec with its status
      decisions/        one file per architecture decision
    GLOSSARY.md         domain terms; not created now, the first resolved term creates it
```

Keep it this shallow at the start. Depth earns its way in later. Invented hierarchy only makes things hard to find.

**Copy the roadmap in immediately**, before the product definition exists. The framework ships it filled in at `templates/roadmap.md`, next to this skill: the steps, the skill that performs each one, and the rules that keep it honest. Copy it into the project's space in the knowledge base and adjust only what is project-specific, rather than composing it fresh each time.

It is the file that answers "where are we", and it answers it from the very first session rather than from the day someone remembers to create it. **Read `references/roadmap.md` for how it is meant to be used.**

It starts as the setup process and grows into the build plan. Same document, two stages of a project's life, which is why it exists this early.

### Optional: the status bar

Offered here because this is where the machine-level setup happens, next to the MCP server, rather than interrupting later.

**Three conditions, all of them.** The user works in the terminal, because the status line does not appear in an IDE or on the web. No status line is configured yet - if `statusLine` is already set in the user's settings, skip this **silently**, since it is a per-machine setting and re-offering it in every new project is noise. And the user says yes: this installs a third-party tool from the network, so it is offered, never run unasked.

What it buys is what a session otherwise cannot see about itself: how much of the rate-limit window is used and what that projects to, how full the context is, which model and mode are running, the session cost, and the state of the working tree. Those are the numbers that decide when to hand off, and without them the decision is a guess.

Installation and configuration belong to the `claude-statusbar` skill, which only the user can invoke: when they say yes, ask them to type `/claude-statusbar`. `cs --setup` installs, `cs upgrade` is the only supported upgrade path, and `cs doctor` diagnoses. If the user declines, say nothing further about it.

---

## Phase 1: PRD

If no PRD exists, invoke the `prd` skill, which runs a proper interview through `grill-me` before writing anything. Write the result into the vault.

If a PRD already exists, read it, and check where it lives. A PRD sitting in the repository or in a stray folder gets **moved** into the vault, not copied. Someone may have run `prd` on its own before starting here, which is fine, but leaving the file where it landed while referencing a vault path is how a project ends up with two versions that slowly disagree. Move it, confirm the move with the user, and reference only the new location from then on.

Either way, the repository never holds a copy of the PRD.

The PRD supplies the product section of the configuration and, above all, the non-goals. Non-goals are the sharpest thing in a PRD: they are the only part that tells a future session what not to build, and they belong in the root configuration almost verbatim.

**What the PRD does not supply is the stack.** It says so itself, marking an unspecified stack as `TBD` rather than guessing. Do not read a technology choice out of a product document. That is phase 2.

---

## Phase 2: Stack

Invoke the `stack-decisions` skill. It runs its own interview through `grill-me` and writes one record per settled decision into the knowledge base.

This is deliberately a separate conversation from the PRD, and the danger it avoids is worth naming. A configuration full of confident, specific rules for a stack nobody chose reads exactly like a configuration full of correct rules. It is fiction shaped like documentation, and it will be followed. Only write a technical rule once the technology it belongs to has been confirmed.

What comes back is the set of settled decisions plus the ones left open as `TBD`. Both matter for what follows: phase 3 derives the area map from the settled ones, and every open one becomes a `TBD` in a generated file rather than a guess.

---

## Phase 2b: Design system

Skip this only when the project has no user interface at all. A library or a background service does not need one; anything with screens does, and defining it later means every screen built before it has to be revisited.

Invoke the `design-system` skill. It runs after the stack because the token format depends on it, settles the visual direction, renders an example page to approve by, and writes the values into the codebase with the reasoning into the knowledge base.

What comes back is a token file location, a named direction, and any open `TBD`. Phase 3 needs it: whether the interface deserves its own instructions, and what those instructions point at for values, is decided by whether this ran.

---

## Phase 3: Area map

Areas are not a matter of taste. They follow the structure the stack already has, so derive them from what phase 2 established. In a monorepo that usually means one per package; in a single tree, one per subsystem.

**Read `references/areas.md` before deciding.** It carries the catalogue of areas worth considering, how each mechanism loads into context, and the rule for choosing between them.

The test for every candidate: an area earns its own file when work inside it follows rules that do not apply elsewhere. Applied honestly this rules out most candidates in a small project, which is the correct outcome. A library or a CLI may need no areas at all, only a root file.

Then decide the form for each. Four mechanisms exist and they differ in when they enter the context window, which is the entire basis for the choice:

- **Area `CLAUDE.md`** for conventions belonging to a directory, versioned next to the code
- **Path-scoped rule** in `.claude/rules/` with `paths:` frontmatter, for rules that apply to files scattered across the tree or when conventions are better kept in one place
- **Skill** for a procedure done occasionally rather than a convention that is always in force
- **Hook** for anything that must happen without exception

That last distinction matters more than it looks. Instructions in any of the first three are context, not enforcement, and may not be followed. A hook runs as a script at a fixed point regardless of what the model decides.

---

## Phase 4: Plan for approval

Present the plan before creating anything. These files steer every later session, so the user should see the shape once before it lands.

The plan lists every file with a one-line summary of its contents, the area map with the reason each area exists, every point that will be written as `TBD` together with what would resolve it, and the vault paths that will be referenced.

Then wait for approval.

---

## Phase 5: Write

Create the vault structure first, then the repository files. Everything written here is read by agents: call the Skill tool with "writing-for-agents" before writing.

### Size is a hard constraint, not a preference

Target **under 200 lines per `CLAUDE.md`**. These files load into the context window at the start of every session and compete with the actual work. Past that length adherence drops, and the failure is silent: the model does not announce that it stopped following rule 40, it just stops.

The consequence is counterintuitive. A longer, more thorough configuration is a **worse** one, because the rules that matter get lost among the rules that do not. Being generous here actively harms the project.

For every line, apply the test: **would removing this cause a mistake?** If not, cut it.

What earns its place: commands that cannot be guessed, conventions that differ from the language or framework default, environment quirks, decisions specific to this project, non-obvious behaviour that has already bitten someone.

What does not: anything derivable by reading the code, standard conventions the model already knows, file-by-file descriptions of the tree, dependency lists, API documentation that should be a link, and self-evident advice like "write clean code".

Notes for human maintainers can go in block-level HTML comments. Those are stripped before the file reaches the context window, so they are free.

### Root CLAUDE.md

Sections in this order. Omit any that has nothing true to say, because an empty section invites someone to fill it with plausible noise later.

**Working agreement.** How the user wants to be worked with: execute or propose, when to ask, how much scope to take on. Take this from the user's own habits rather than inventing house rules.

**Product.** From the PRD: what this is, who it is for, and the non-goals. Then a pointer to the PRD in the vault for anything deeper. Two or three sentences, not a summary of the whole document. Duplicating the PRD here creates exactly the second version this structure exists to prevent.

**Stack.** From phase 2. Each entry names the technology plus the one thing this project does differently from its default.

**Architecture rules.** The invariants: what must always hold, what must never happen. Derive them from the constraints in the PRD and the decisions from phase 2. Each rule states the rule and then why it exists. A rule without a reason gets discarded by the first person who finds it inconvenient.

**Security baseline.** Where authentication is checked, where input is validated, what gets logged, how secrets are handled.

**Testing requirements.** What must have tests, what coverage is expected, where tests live.

**Definition of done.** A checklist someone can actually work through: compiles, lint clean, tests green, new logic covered, no unexplained escape hatches.

**Scope discipline.** Solve the task that was asked. No improvements to neighbouring code. Ask when scope is unclear instead of guessing.

**File conventions.** A table of path patterns with one real example each. Add one line: judgement rules for reviews live in `CODING_STANDARDS.md` in the repo, which `retro` creates when it is needed. Do not create it empty, and do not put those rules in this file: they are read by reviewers, not by every session.

**Language.** Which language for code and comments, which for user-facing text, which for documentation and commits.

**Knowledge base map.** A table from question type to vault location: product questions to the PRD, decisions to `specs/decisions/`, domain terms to `GLOSSARY.md`, technical detail to the relevant spec. The glossary row is written as `TBD` until the file exists, since it is created lazily with the first resolved term. This table is what stops a later session from creating a local copy of something that already exists in the vault.

**Where the project stands.** Name the roadmap explicitly as the single place that answers it, with its path, and state the obligation that goes with it: **it is updated whenever a step completes, by whoever completed it.** Both halves are needed. Without the pointer a session has no reason to look and will ask instead. Without the obligation the file becomes a diary of the first week that everything afterwards quietly contradicts.

This is one of the few places where a short instruction earns its permanent context cost, because it is read at the start of every session and decides whether the session begins informed or guessing.

**Phrase routing.** One table mapping what the user says to the skill that should run, plus the one rule that binds those skills to the roadmap's order. The only routing table in the project. See below.

### Area CLAUDE.md

One per area from phase 3. Each opens with a single line on what the area covers, then its rules, then a short list of anti-patterns specific to it. Anti-patterns earn their space: they catch the plausible-but-wrong move that general rules miss.

Where an area has a mandatory sequence, such as a fixed order of steps in a request handler or a procedure for schema changes, write it as a numbered sequence or a code skeleton rather than prose. Sequences get followed when they look like sequences.

### .claude/rules/

Detail that applies to some paths but not others goes here, one topic per file, with `paths:` frontmatter naming the globs it covers:

```markdown
---
paths:
  - "src/api/**/*.ts"
---

# API rules

- Validate at the boundary before anything reaches the database
- Errors use the shared response shape
```

The frontmatter is what makes this worth doing. A rule with `paths:` enters the context window only when a matching file is touched. A rule without it loads in every session, exactly like the root file, and should therefore be held to the same test.

Rules also suit anything that applies across scattered paths, where an area file would have to be duplicated: migrations wherever they live, generated files wherever they sit.

Create one only when there is real content for it. An empty rule file is a promise that will not be kept.

### The handoff file and the hooks

Everything above spans far more than one session. The product interview, the stack, the design system, the component map and then one spec per component is weeks of work, and each session starts with an empty context window.

Two files carry across that gap, and they answer different questions. The **roadmap** in the knowledge base says where the project stands and what comes next. `.claude/state.md` says what happened in the last session. **Read `references/roadmap.md` and `references/state-file.md`;** the division between them is the point and collapsing it destroys both.

The hooks are what make this reliable. An instruction asking the model to read a file first is a request; injected content is simply there. The framework ships three, all copied to `.claude/hooks/` and registered:

- `session-state.py` on SessionStart, which injects **both** the roadmap and the handoff, and tells the session to open by naming where things stand and offering the next step rather than waiting to be asked
- `session-recap-trigger.py` on UserPromptSubmit, which forces the handoff to be written when someone says goodbye
- `post-edit-check.py` on PostToolUse with matcher `Edit|Write|MultiEdit`, which runs the fast checks from `.claude/checks.json` after every edit and returns a failure with exit code 2, so the error is seen while the edit is still fresh. Write `.claude/checks.json` from the check commands `stack-decisions` settled, as `{"commands": [...], "timeout_s": 60}`: only fast, deterministic checks such as the type check and lint of the touched files, never the test suite. Without settled commands, write no file; the hook then does nothing, and `retro` reports the missing guardrail.

The roadmap lives in the knowledge base, outside the repository, so the hook cannot guess its path. Write it into `.claude/roadmap-path`, one line, when installing the hook. You know the path because you created the structure in phase 0. Without it the hook still works and injects only the handoff, which is the quiet failure worth avoiding.

A phrase hook fires on every prompt, so its patterns have to be unambiguous. The test for one: could this sentence be said mid-work without meaning what the hook assumes? If yes, it does not belong in the list. A hook triggering on everyday words fires constantly, is almost always wrong, and devalues the skill it forces, because that skill then runs whether or not it was wanted.

As the last act of writing, bring the roadmap up to date: every step that has actually run marked done, and a concrete next action spelled out. Not a phase name, an action, naming which document comes first and why.

### CLAUDE.local.md

Anything personal to one developer, such as a sandbox URL or preferred test data, belongs in `CLAUDE.local.md` at the project root, added to `.gitignore`. Keeping it out of the shared file prevents one person's setup from becoming everyone's instruction.

### Three ways a written file fails silently

Each of these produces a file that looks correct in an editor and does nothing.

**Unquoted YAML that contains a colon.** In frontmatter, a `: ` inside an unquoted value ends the scalar, and the rest of the line is read as a new mapping key. The whole block then fails to parse, and a block that fails to parse does not degrade gracefully: every field is dropped, so a skill loses its name and description and a rule loses its `paths:`. Descriptions are where this bites, because a natural sentence reaches for a colon. Quote any value containing a colon, or rewrite the sentence without one, and parse the block after writing rather than assuming.

**A byte order mark before the frontmatter.** On Windows many editors and some write paths prepend a BOM. A file starting with those three bytes and then `---` no longer has frontmatter as far as the parser is concerned, so a rule's `paths:` never applies and a skill loses its name, description and every other field. Write these files without a BOM, and when editing an existing one, check whether it had one before you prepend anything.

**A pointer to something that is not there.** Every path a generated file names, whether a vault note, a reference document, an MCP tool or a source file, is a claim that can be wrong the moment it is written and gets wronger as things move. Nothing validates it, and the failure is quiet: the session looks, finds nothing, and carries on with less than it should have.

So verify each one as you write it. Read the directory the path points into rather than trusting the name. For an MCP tool, check that a tool by that exact name exists on the server that is actually running, not on the one the config was written for; two servers can carry the same configured name while only one is live, and their tool names differ. A pointer you could not confirm goes in as `TBD` with a note, never as a plausible guess.

### Two rules that hold across every generated file

**One truth, one place.** No statement appears in two files. Where a second file needs it, it links. Two copies of a rule will disagree eventually, and then the work follows the wrong one. When a fact would fit in several places, put it in the most specific one and link from the others.

**Stock with an expiry date.** When something exists but is on its way out, say so in the document that describes it: what runs today, what replaces it, which decision settled that, and what may no longer be built on it. Documentation that describes a doomed system as though it were the target quietly teaches the wrong thing to every session that reads it.

### Routing

Path routing needs no table. A rule with `paths:` frontmatter is loaded by the tooling when a matching file is touched, without the model having to remember to consult anything. Write the globs; do not restate them as a table somewhere.

**Phrase routing** does need writing down: a table in the root file mapping what the user actually says to the skill that should run. Use the phrases they really use, in every language they work in. This is the only routing table, and it lives in the root file alone. Routing kept in two places drifts apart, and then the wrong one gets followed.

Give it a third column: where the skill sits in the roadmap. Two columns answer *which skill*; the third is what makes the next rule cheap to obey, because it is what gets looked up. Skills of the per-phase ritual have no step number - they repeat every phase - so they carry their position in the ritual instead.

| Was der Nutzer sagt | Skill | Fahrplan |
|---|---|---|
| „Komponenten schneiden", „Specs anlegen" | `create-specs` | Schritt 6 |
| „Schreib die Spec für X", „X spezifizieren" | `write-spec` | Schritt 7 |
| „Lass uns Phase 4 bauen", „den Plan abarbeiten" | `execute-plan` | Ritual, nach Freigabe |
| „Klick das mal durch", „sieht das gut aus" | `handlauf` | Ritual, Gate |
| „Was können wir besser machen", „das passiert uns schon wieder" | `retro` | Ritual, nach den Reviews |
| „Das ist kaputt", „geht nicht", „warum passiert X" | `diagnosing-bugs` | Jederzeit, ohne Voraussetzung |
| „Wo ist der Code verknotet", „Architektur aufräumen" | `/improve-codebase-architecture` vorschlagen | Jederzeit, nur per Hand |

A skill that only the user can invoke still earns a row when its phrase does not name it; the row then means *suggest the command to the user*, because no skill and no model can start it.

**Which skills earn a row.** Not all of them, or the table becomes a directory nobody reads. The test: **a skill earns a row when the natural way of asking for it does not contain its name.** "Write the PRD" names its skill and needs no row. "Does this actually work?" is `handlauf`, and without a row it is reachable only through the skill's own description - which is the layer this table exists to reinforce in the first place.

Two things follow from that test, and both are easy to miss. The skills of the **per-phase ritual** earn rows as much as the setup ones, and are forgotten more often: a setup skill runs once, while the ritual runs on every phase for the life of the project. And the test keeps the table correct as the toolkit changes, which a fixed list of skills would not - the installed skills are the truth about what exists, and a list copied into this file starts drifting the first time one is added.

Where a phrase must always trigger its skill, a `UserPromptSubmit` hook can enforce it. The table then documents what the hook does rather than hoping the model reads it.

**Order is the part that fails in practice**, and the table alone does not fix it. A phrase table answers which skill a sentence means. It says nothing about whether that skill's turn has come, and a skill that runs three steps early produces a document resting on things nobody has decided yet. It also fails quietly, because the output looks like the output.

So one rule goes into the root file next to the table, and the wording matters more than its length:

> Bevor ein Skill aus diesem Ablauf läuft, wird seine Zeile im Fahrplan gelesen. Steht die Voraussetzung dort noch offen, wird der Skill **nicht** ausgeführt: der fehlende Schritt wird benannt und angeboten. Das gilt auch, wenn nach dem Ergebnis gefragt wird statt nach dem Schritt — „schreib die Spec für X" ist ein Aufruf von Schritt 7. Bei den Skills des Rituals ist die Voraussetzung ihre Stelle im Ritual statt eine Schrittnummer: `handlauf` läuft nach dem Bauen, nicht während.

Four things make that hold rather than decorate the file.

**It is a pointer, not a second copy of the order.** The order lives in the roadmap's `Setzt voraus` column and nowhere else, so the two cannot disagree. A root file that restates the sequence has created the exact drift this structure exists to prevent.

**The roadmap is injected**, by the SessionStart hook, so the lookup costs nothing and has no excuse. A rule requiring a file to be opened first is a rule with a way out.

**It names the fallback.** A rule that only forbids is one a session argues itself past when the user sounds like they are in a hurry. Naming what to do instead — say which step is missing, offer it — leaves nothing to improvise.

**It covers the phrasing the failure actually arrives in.** Nobody asks for step 7 by name; they ask for the spec for X. Without that clause the rule reads as applying only to requests that name a step, which is the half that never causes the problem.

The same hook that injects the roadmap repeats this rule in its instruction, so it holds even in a session that never reaches the root file.

---

## Working with an existing codebase

When the project already has code, one rule overrides everything above: claims about the current state come from the code, not from the user's description and not from a specification.

Read before writing. Check the real paths, the real function names, the real field names. Where the user's account and the code disagree, the code wins, and the disagreement is worth mentioning, because it usually means something moved and nobody updated their mental model.

Specifications describe intent, and intent is usually ahead of reality. Writing intent into configuration as though it were fact produces rules that refer to things nobody built.

## When done

Report the files created, every `TBD` together with what would resolve it, and the areas deliberately left without a file.

Then say plainly that this is a scaffold and not truth. Its accuracy about the code is at its lowest right now, because there is barely any code yet. It becomes true through use: by being corrected when it turns out wrong, and by having what gets learned written back into it.
