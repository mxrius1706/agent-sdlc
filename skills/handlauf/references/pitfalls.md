# Pitfalls

Every item here has cost somebody a run, and each holds for any project driven through a browser.

The expensive traps are usually specific to one project: a particular auth broker, build cache or container. Those live in the project, in the source of the `handlauf` / `pitfalls` row of the root CLAUDE.md section `Project references`, one line each: the symptom, then what to do about it. A trap found during a run goes there before the report is written, or the next run pays for it again. Without the row, the report proposes the file (for example `.claude/references/handlauf-pitfalls.md`) and the row, with the trap as its first line. A trap that holds for every project belongs in the list below, through a change to the toolkit.

## Generic

- **A print dialog blocks browser control.** A page that calls `window.print()` itself hangs the extension. Before opening a print view, set `window.print = () => { document.title = 'PRINT-CALLED ' + document.title; };` through `javascript_tool` in exactly that tab, then click. If printing opens a new tab, do the same there immediately, before the page finishes loading, or load the print view directly by URL. The real PDF is checked by the user.
- **Never trigger browser dialogs.** `alert`, `confirm` and `prompt` block everything. Check the code first for buttons that might call `confirm()` (delete, discard); when in doubt set `window.confirm = () => true` and note that in the report. Run injection probes without `alert`.
- **The renderer freezes during screenshots** (a CDP timeout). Switch to `get_page_text` or `javascript_tool` reading `innerText` instead of more screenshots; after two failures, reload the tab.
- **The session expires.** Token renewal fails occasionally, usually visible as a redirect to the login page. Do not count it as a finding against the surface being checked: ask the user to sign in again, continue at the same inventory row, and note it once under the environment section of the report.
- **A production build poisons the dev cache.** A production build written into the framework's build directory while the dev server runs can turn API routes into HTML 404s, which then looks like the application is broken everywhere. The start script checks for it; if the pattern appears mid-run, stop and ask the user.
- **Run against the main checkout, never a worktree.** Build tooling frequently refuses the linked dependency directory inside a worktree, and the dev port and database belong to the main checkout anyway.
- **Monitor filters.** Structured loggers print one object over several lines, with the level on one line and the message on the next, which is why the watch script emits context lines. Too many messages stop a monitor automatically; tighten the filter rather than switching it off.
- **Two accounts, one browser.** The user often tests along in the same browser. Before any role case, verify who is actually signed in, and never attribute a finding to an account that was not the one checked.
- **The dev server belongs to the user.** Do not stop or restart it without asking, unless it was started for this run in this session.
- **Read the database, do not write it.** Reading is for verifying that a save really landed. Writing or deleting only after asking.

