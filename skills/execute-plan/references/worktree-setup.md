# Worktree setup and removal

Read this when opening or removing a block worktree and the row `execute-plan` / `worktree` in the root CLAUDE.md section `Project references` names no script.

## Making a worktree buildable

A bare `git worktree add` does not bring everything the build needs:

- **Dependencies:** link or share the installed packages from the main checkout rather than installing them again per worktree. On Windows a directory junction; elsewhere a symlink. Some toolchains refuse a linked dependency directory: check once per project, and if so, install in the worktree instead. Record the result in the source of the `worktree` row, so the next phase does not find out again.
- **Environment:** copy the local environment file. It is untracked, so `worktree add` does not bring it.
- **Untracked generated files** the framework needs to type-check, untracked for the same reason.
- **Code generation** (client from a schema, generated types) if the schema changed on the phase branch.

## Removing a worktree

A linked dependency directory means a recursive delete can follow the link and empty the main checkout's dependencies. On Windows that includes `git worktree remove`, which has been seen to follow a junction. Use the teardown script from the `worktree` row; without one, **remove the link itself first** and only then the worktree:

```
cmd //c rmdir "<worktree>
ode_modules"   # Windows junction: removes the link, not its target
rm "<worktree>/node_modules"              # symlink elsewhere: same, never rm -r
git worktree remove <worktree>
```

Check afterwards that the main checkout's dependency directory is still populated.
