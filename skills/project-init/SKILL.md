---
name: project-init
description: "Initialize a project's Claude Code configuration: Obsidian knowledge base, PRD, root and area CLAUDE.md files, path-scoped rules, hooks. Use when starting a new project, when the PRD is done and setup is next, in an empty repo, or when code exists without a config layer. Not the built-in /init."
---

# Project Init

Build the configuration layer a project needs so that every later session starts informed instead of guessing.

The output is a set of instructions separated by **when they load into the context window**, plus a knowledge base outside the repository. The separation lets each statement live in exactly one place: a rule that matters in one corner of the codebase is not paid for in every session.

## The idea in one paragraph

A project has three kinds of truth that age at different speeds. Product truth (what we build and why) changes rarely and belongs outside the repository, where no branch ties it down. Working conventions (how we build here) change with the stack and belong in version control next to the code they govern. Current state (what the code does today) is reliable only when read from the code, so configuration claims it only with evidence. Mixing the three is what makes documentation rot.

## Order of operations

Each phase depends on the one before it: 0 Knowledge base, 1 PRD, 2 Stack (2b Design system), 3 Area map, 4 Plan for approval, 5 Write. Files are created only after the plan in phase 4 is approved.

---

## Phase 0: Knowledge base

First, because the PRD needs somewhere to live that is not the repository. Product truth in the repo sits on a branch and gets copied into a second file for convenience, and six months later two versions disagree with no way to tell which is binding. A vault outside the repo leaves only one copy to read.

**Check for an Obsidian MCP server.** If its tools are available, use them. If not, read `references/vault-setup.md` and walk the user through connecting one. The same file holds the optional status bar offer; make it here, next to the machine-level setup.

**Create the vault structure:**

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

Keep it this shallow; depth earns its way in later.

**Copy the roadmap in immediately**, before the product definition exists. It ships filled in at `templates/roadmap.md`: the steps, the skill that performs each one, and the rules that keep it honest. Copy it into the project's space and adjust only what is project-specific. It answers "where are we" from the first session, starting as the setup process and growing into the build plan. **Read `references/roadmap.md` for how it is used.**

---

## Phase 1: PRD

If no PRD exists, invoke the `prd` skill (it interviews through `grill-me` before writing) and write the result into the vault.

If one exists, check where it lives. A PRD in the repository or a stray folder is **moved** into the vault, not copied, confirmed with the user, and referenced only at the new location from then on. The repository never holds a copy.

The PRD supplies the product section of the configuration and, above all, the non-goals: the only part that tells a future session what not to build, which belong in the root configuration almost verbatim.

The PRD does not supply the stack; it marks an unspecified stack `TBD`. That is phase 2.

---

## Phase 2: Stack

Invoke the `stack-decisions` skill. It interviews through `grill-me` and writes one record per settled decision into the knowledge base.

It is a separate conversation from the PRD because a configuration full of confident rules for a stack nobody chose is fiction shaped like documentation, and it will be followed. Technical rules are written only once their technology is confirmed.

What comes back: settled decisions, from which phase 3 derives the area map, and open ones, each of which becomes a `TBD` in a generated file.

## Phase 2b: Design system

Skip only when the project has no user interface. Anything with screens needs it, because defining it later means revisiting every screen built before.

Invoke the `design-system` skill. It runs after the stack because the token format depends on it. What comes back is a token file location, a named direction and any open `TBD`; phase 3 uses them to decide whether the interface gets its own instructions and what they point at for values.

---

## Phase 3: Area map

Areas follow the structure the stack already has: one per package in a monorepo, one per subsystem in a single tree. **Read `references/areas.md` before deciding.** It holds the catalogue of candidate areas, how each of the four mechanisms (area `CLAUDE.md`, path-scoped rule, skill, hook) loads, and the rule for choosing between them.

An area earns its own file when work inside it follows rules that do not apply elsewhere. Applied honestly this rules out most candidates in a small project; a library or CLI may need only a root file.

---

## Phase 4: Plan for approval

These files steer every later session, so the user sees their shape once before it lands. The plan lists every file with a one-line summary, the area map with the reason each area exists, every point that will be written as `TBD` with what would resolve it, and the vault paths that will be referenced. Then wait for approval.

---

## Phase 5: Write

Vault structure first, then the repository files. Call the Skill tool with "writing-for-agents" before writing, since everything written here is read by agents.

### Size is a hard constraint

Target **under 200 lines per `CLAUDE.md`**. These files load at the start of every session and compete with the work; past that length adherence drops silently, since the model does not announce that it stopped following rule 40. A thorough configuration is a worse one, because the rules that matter get lost among those that do not.

Test for every line: **would removing this cause a mistake?** If not, cut it.

Earns its place: commands that cannot be guessed, conventions that differ from the framework default, environment quirks, project-specific decisions, non-obvious behaviour that has already bitten someone. Does not: anything derivable from the code, standard conventions, file-by-file tree descriptions, dependency lists, API documentation that should be a link, self-evident advice.

Notes for human maintainers go in block-level HTML comments, which are stripped before the file reaches the context window.

### Root CLAUDE.md

Sections in this order. Omit any with nothing true to say; an empty section invites plausible noise later.

**Working agreement.** How the user wants to be worked with: execute or propose, when to ask, how much scope. Taken from the user's own habits.

**Product.** From the PRD: what it is, who it is for, the non-goals, then a pointer to the PRD in the vault. Two or three sentences; a PRD summary here is the second version this structure prevents.

**Stack.** From phase 2. Each entry names the technology plus the one thing this project does differently from its default.

**Architecture rules.** The invariants, derived from the PRD constraints and the phase 2 decisions. Each states the rule and why; a rule without a reason is discarded by the first person it inconveniences.

**Security baseline.** Where authentication is checked, where input is validated, what gets logged, how secrets are handled.

**Testing requirements.** What must have tests, expected coverage, where tests live.

**Definition of done.** A checklist someone can work through: compiles, lint clean, tests green, new logic covered, no unexplained escape hatches.

**Scope discipline.** Solve the task asked, leave neighbouring code alone, ask when scope is unclear.

**Two rules over everything.** Both rules from "Two rules that hold across every generated file" below, written out in full in the documentation language: "one truth, one place" and "stock with an expiry date" with its four parts. They bind every later session, not only this setup, and other skills (`stack-decisions`, `design-system`, `config-sync`) point here for them.

**File conventions.** A table of path patterns with one real example each, plus one line: judgement rules for reviews live in `CODING_STANDARDS.md` in the repo, which `retro` creates when needed (not created empty, not duplicated here, since reviewers read it rather than every session).

**Language.** Which language for code and comments, user-facing text, documentation and commits.

**Knowledge base map.** A table from question type to vault location: product questions to the PRD, the spec index to `specs/_index.md`, decisions to `specs/decisions/`, domain terms to `GLOSSARY.md`, the design schema and the page plans where `design-system` and `plan-pages` put them, technical detail to the relevant spec. A row whose target does not exist yet reads `TBD`; the skill that creates the target fills it in. It stops a later session from creating a local copy of something the vault already holds.

**Project references.** The interface between the global skills and this project. Its heading is always exactly `## Project references`, in English whatever the documentation language, because skills look it up by that name. It is a table `Skill | Topic | Source`: when a skill needs something specific to this project (a script, a command, a value, a file of project traps), its text names a row here, and the row points at the source in the project, usually a file under `.claude/references/`. A row may name several skills that share one source. Write only rows whose source exists; the skill that creates a source adds its row. Without any row, leave the section out.

The section carries one rule along, in a sentence under its heading: **no project copies of global skills.** A folder under `.claude/skills/` with the name of a global skill hides the global one and cuts the project off from every toolkit update. Project knowledge a skill needs goes into a row plus its source; a skill of the project's own, under its own name, is fine.

**Where the project stands.** Name the roadmap as the single place that answers it, with its path, and state the obligation: **it is updated whenever a step completes, by whoever completed it.** The pointer gives a session a reason to look; the obligation keeps the file from becoming a diary of the first week. A short instruction earns its permanent context cost here, because it decides whether a session begins informed or guessing.

**Phrase routing.** The phrase table plus the roadmap precondition rule. **Read `references/routing.md`** for the table, which skills earn a row, and the rule's exact wording (German, written into the root file as given).

### Area CLAUDE.md

One per area from phase 3. Each opens with one line on what the area covers, then its rules, then a short list of anti-patterns specific to it; they catch the plausible-but-wrong move general rules miss. A mandatory sequence (request handler steps, schema change procedure) is written as a numbered sequence or code skeleton, since sequences get followed when they look like sequences.

### .claude/rules/

Detail that applies to some paths, one topic per file, with `paths:` frontmatter:

```markdown
---
paths:
  - "src/api/**/*.ts"
---

# API rules

- Validate at the boundary before anything reaches the database
- Errors use the shared response shape
```

A rule with `paths:` enters the context only when a matching file is touched; one without loads every session and meets the root file's test. Rules also suit anything across scattered paths, such as migrations or generated files. Create one only with real content.

### The handoff file and the hooks

The work spans far more than one session, and each starts with an empty context window. Two files carry across that gap: the **roadmap** (knowledge base) says where the project stands and what comes next, `.claude/state.md` says what happened last session. **Read `references/roadmap.md` and `references/state-file.md`;** collapsing the division destroys both.

An instruction to read a file first is a request; injected content is simply there. The framework ships three hooks, copied to `.claude/hooks/` and registered:

- `session-state.py` on SessionStart: injects **both** the roadmap and the handoff, and tells the session to open by naming where things stand and offering the next step
- `session-recap-trigger.py` on UserPromptSubmit: forces the handoff to be written on a farewell
- `post-edit-check.py` on PostToolUse, matcher `Edit|Write|MultiEdit`: runs the fast checks from `.claude/checks.json` after every edit and returns failures with exit code 2, so the error is seen while the edit is fresh. Write `.claude/checks.json` from the commands `stack-decisions` settled, as `{"commands": [...], "timeout_s": 60}`: fast, deterministic checks such as a type check, never the test suite. A command containing `{file}` runs once per edit with the edited file's path in its place (e.g. `npx eslint --quiet {file}`), which is how "lint the touched file" works. **Run each command once before writing the file.** One that cannot run yet (no `package.json`, no `tsconfig` in a greenfield project) stays out and is noted as `TBD` in the roadmap's step 5; otherwise every later edit, including the spec work, fails on a toolchain that does not exist yet. Without runnable commands write no file; the hook then does nothing and `retro` reports the missing guardrail.

The roadmap sits outside the repository, so write its path, one line, into `.claude/roadmap-path` when installing the hook. Without it the hook injects only the handoff, a quiet failure.

A phrase hook fires on every prompt, so its patterns must be unambiguous. Test: could this sentence be said mid-work without meaning what the hook assumes? If yes, it stays out; a hook on everyday words fires constantly and devalues the skill it forces.

As the last act of writing, bring the roadmap up to date: every step that has run marked done, and a concrete next action naming which document comes first and why.

### CLAUDE.local.md

Anything personal to one developer (sandbox URL, preferred test data) goes in `CLAUDE.local.md` at the project root, added to `.gitignore`.

### Three ways a written file fails silently

Each produces a file that looks correct in an editor and does nothing.

**Unquoted YAML containing a colon.** A `: ` inside an unquoted frontmatter value ends the scalar, the block fails to parse, and every field is dropped: a skill loses name and description, a rule loses `paths:`. Descriptions are where this bites. Quote any value containing a colon or rewrite the sentence, and parse the block after writing.

**A byte order mark before the frontmatter.** On Windows, editors and some write paths prepend a BOM, after which `---` is no longer frontmatter to the parser. Write these files without a BOM, and check an existing file for one before prepending anything.

**A pointer to something that is not there.** Every path a generated file names (vault note, reference document, MCP tool, source file) can be wrong the moment it is written, and nothing validates it. Verify each as you write: read the directory the path points into rather than trusting the name. For an MCP tool, per `config-sync` the name must exist on the server that is actually running. A pointer you could not confirm goes in as `TBD` with a note.

### Two rules that hold across every generated file

**One truth, one place.** No statement appears in two files; where a second file needs it, it links. Two copies of a rule disagree eventually and the work follows the wrong one. When a fact fits several places, put it in the most specific one.

**Stock with an expiry date.** When something exists but is on its way out, say so in the document that describes it: what runs today, what replaces it, which decision settled that, and what may no longer be built on it. A doomed system described as the target teaches the wrong thing to every session that reads it.

---

## Working with an existing codebase

Claims about the current state come from the code, not from the user's description or a specification. Read before writing; check real paths, function names and field names. Where the user's account and the code disagree, the code wins and the disagreement is worth mentioning, since it usually means something moved and nobody updated their mental model. Specifications describe intent, which runs ahead of reality; written into configuration as fact, it produces rules about things nobody built.

## When done

Report the files created, every `TBD` with what would resolve it, and the areas deliberately left without a file.

Then say plainly that this is a scaffold and not truth. Its accuracy about the code is at its lowest now, because there is barely any code yet. It becomes true through use: corrected when wrong, with what gets learned written back into it.
