# Areas and where instructions live

Read this during phase 3, when deciding which parts of the codebase get their own instructions and in what form.

## Contents

- [How the mechanisms load](#how-the-mechanisms-load)
- [Choosing between them](#choosing-between-them)
- [Candidate areas](#candidate-areas)
- [The test an area has to pass](#the-test-an-area-has-to-pass)

---

## How the mechanisms load

Four mechanisms carry instructions, and they differ in when they enter the context window. That difference is the whole basis for choosing between them.

| Mechanism | Location | Loads |
|---|---|---|
| Root `CLAUDE.md` | `./CLAUDE.md` or `./.claude/CLAUDE.md` | Every session, always |
| Area `CLAUDE.md` | Inside the directory it governs | At launch if started from there, otherwise on demand when a file in that directory is read |
| Rule | `.claude/rules/*.md` | Every session if it has no `paths:` frontmatter, otherwise only when a matching file is touched |
| Skill | `.claude/skills/<name>/SKILL.md` | Only when invoked or when its description matches the request |

**Everything without `paths:` costs context in every session, forever.** A rule that matters for one directory but loads everywhere is pure overhead on every unrelated task.

This has a consequence that catches people moving existing docs into `.claude/rules/`: a document that is **not** path-scoped is cheaper left where it is. A reference file sitting in `.claude/references/`, pointed at from the root file, loads only when something actually sends the session there. Move that same file into `rules/` without `paths:` and it now loads in every session, whether or not the work has anything to do with it. The migration made it more expensive, not less.

So before moving anything into `rules/`, ask what it is scoped by. Scoped by path, it belongs there. Scoped by task type, by phase, or by nothing in particular, it stays a reference that something points at.

**Imports do not save context.** `@path/to/file` in a `CLAUDE.md` is expanded at launch. It organizes files; it does not reduce what is loaded. Only `paths:` scoping and skills do that.

**None of it is enforcement.** All four are context, and the model may not follow them. Anything that must happen without exception belongs in a hook, which runs as a script at a fixed point regardless of what the model decides.

---

## Choosing between them

**Area `CLAUDE.md`** when the rules belong to a directory and should be versioned next to the code they govern. This is the default for a package in a monorepo or a subsystem in a single tree. The people who own that directory maintain its file.

**Path-scoped rule** when the same rule applies to files scattered across the tree, or when the project prefers all conventions collected in one place instead of spread through the directories. A rule scoped to `**/migrations/**` catches migrations wherever they live.

**Skill** when it is a procedure rather than a convention. Conventions are things that are true while working somewhere ("handlers validate input at the boundary"). Procedures are things you do from time to time ("release a version", "add a new integration"). A multi-step procedure in a `CLAUDE.md` costs context in every session and is read in almost none of them.

Skills are not free either, and the way they fail is worth knowing. Every skill's name and description sit in context permanently so the model can pick between them, and that listing has a budget of roughly one percent of the context window. Past it, descriptions get truncated. The skill still exists, it just stops being chosen reliably, and nothing reports this: a skill declared mandatory in a routing table can quietly never fire because the sentence that would have matched the request was cut off. So keep descriptions short and lead with the words a real request would contain, and treat a large pile of installed-but-unused skills as an active cost to the ones you do use, not merely as clutter.

**Hook** when it must happen every time: a type check after an edit, a test run before a commit, a block on writes to a generated directory.

A useful sequence when unsure: if it must happen, hook. If it is a procedure, skill. If it applies only to certain paths, path-scoped rule or an area file. Otherwise root.

---

## Candidate areas

A catalog to think against, not a checklist to fill. Most projects need a handful of these; some need none. What matters is that each area chosen has rules that genuinely do not apply elsewhere.

**Request surface.** HTTP handlers, controllers, resolvers, RPC endpoints. Usually the strongest candidate in any networked application, because a request has a mandatory sequence: authenticate, authorize, validate, do the work, record it, respond. Write the sequence as a numbered list or a code skeleton, not prose.

**Data and schema.** Models, migrations, queries. Rules here are about change safety rather than style: how a schema change is split so a deploy cannot break, what a rollback looks like, which query shapes are forbidden.

**User interface.** Components, views, styling. Two distinct kinds of content: what to build with (tokens, primitives, state handling) and how to decide what to build (which layout for which task). The second is more valuable and more often missing.

**Domain core.** The business rules, where those live separately from delivery mechanisms. Deserves its own file when the domain has invariants that must hold no matter which handler or job touches it.

**Background work.** Jobs, schedulers, queues, workers. Distinct because the failure model is different: nobody is waiting, retries happen, the same message can arrive twice. Idempotency belongs here.

**External integrations.** Clients for third-party services. Distinct because the failures are not yours: timeouts, rate limits, partial outages, and the question of which foreign error becomes which of your own.

**Authentication and authorization.** Often folded into the request surface. Earns a file of its own when the model is non-trivial, such as several identity sources, delegated access, or fine-grained permissions.

**Tests.** Where tests live, what gets mocked and what never does, which fixtures exist. Consider a skill instead if it reads as a procedure rather than a set of standing rules.

**Infrastructure and deployment.** Container definitions, pipelines, infrastructure as code. Also the natural home for environment quirks, the things that cost an hour to rediscover.

**Command line surface.** Argument conventions, exit codes, what goes to stdout versus stderr, output stability. Small but easy to get inconsistent.

**Public library surface.** For anything others depend on: what is public, how versioning works, how a breaking change is handled, how something is deprecated.

**Data and model pipelines.** Transformations, training, evaluation. Distinct because reproducibility is a first-class concern and inputs are versioned alongside code.

**Generated and vendored code.** Rarely a full area, more often a single rule: do not edit, regenerate with this command. Pair it with a `Read` deny rule so the files do not get pulled into context at all.

---

## The test an area has to pass

An area earns its own file when work inside it follows rules that do not apply elsewhere. Data-access rules do not help someone writing a component, and component rules mean nothing in a migration.

Most candidates fail this in a small project, correctly. Two good area files beat six thin ones, because a thin file is one more thing to keep current and one more chance for two files to disagree. Contradictory instructions are worse than missing ones: the model picks one arbitrarily, and nobody can tell which.

Rules that hold everywhere belong in the root file; an area file restating them adds context cost and no information.
