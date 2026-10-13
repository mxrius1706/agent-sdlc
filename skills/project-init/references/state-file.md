# The session handoff

`.claude/state.md` carries what happened in the last session, and nothing else. A SessionStart hook injects it before the first prompt.

It is committed, not ignored. What was done last session is a fact about the project, and an ignored file is gone after a machine change.

## Handoff vs roadmap

**The roadmap** answers *where are we and what comes next*. It changes when a step completes and lives in the knowledge base (`references/roadmap.md`). **The handoff** answers *what happened last time*. It is overwritten every session. The handoff never says where the project stands in the process; mixing them buries the durable answer under the volatile one.

## Who writes it

`session-recap` at the end of a session, triggered by a hook on farewell phrases. It owns the file's shape and rules; `project-init` installs the hooks that inject and trigger it.
