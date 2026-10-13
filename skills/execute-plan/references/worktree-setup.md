# Worktree setup and removal

Read this when opening or removing a block worktree without a project bootstrap or teardown script.

## Making a worktree buildable

A bare `git worktree add` does not bring everything the build needs:

- **Dependencies:** link or share the installed packages from the main checkout rather than installing them again per worktree. On Windows a directory junction; elsewhere a symlink. Some toolchains refuse a linked dependency directory: check once per project, and if so, install in the worktree instead.
- **Environment:** copy the local environment file. It is untracked, so `worktree add` does not bring it.
- **Untracked generated files** the framework needs to type-check, untracked for the same reason.
- **Code generation** (client from a schema, generated types) if the schema changed on the phase branch.

## Removing a worktree

A linked dependency directory means a naive recursive delete can follow the link and empty the main checkout. Use `git worktree remove`, or the project's teardown script.
