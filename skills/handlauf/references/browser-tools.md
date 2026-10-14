# Browser tools

The walkthrough runs with whichever browser tools the session has. Two families are supported; the steps in SKILL.md name the purpose, this table names the tool.

- **Claude in Chrome** (`mcp__claude-in-chrome__*`): the extension in the user's Chrome, on the machine where Claude Code runs.
- **Chrome DevTools** (`mcp__chrome-devtools__*`): the `chrome-devtools-mcp` server attached to a running Chrome (`--browser-url`). Typical when Claude Code runs on another machine than the one the user sits at: the Chrome window opens on the user's screen, so logins, MFA and anything else that needs the user happen right there.

Both available: prefer the one whose browser the user is looking at.

| Purpose | Claude in Chrome | Chrome DevTools |
|---|---|---|
| Load the tools | one `ToolSearch` for the names below | same |
| Own tab | `tabs_create_mcp` | `new_page` (url required; keep its `pageId` for every later call) |
| Go to a URL, back, reload | `navigate` | `navigate_page` (`type`: url, back, forward, reload) |
| Fixed window size | `resize_window` | `resize_page` |
| Screenshot to look at | `computer` (screenshot) | `take_screenshot` without `filePath` |
| Zoom into an area | `computer` (zoom) | `take_screenshot` with the element's `uid` |
| Screenshot for the report | save the screenshot | `take_screenshot` with `filePath` (saved on the machine running Claude Code) |
| Page structure, find elements | `read_page`, `find` | `take_snapshot` (gives the `uid`s) |
| Page text | `get_page_text` | `take_snapshot`, or `evaluate_script` with `() => document.body.innerText` |
| Click, type, keys | `computer`, `form_input` | `click`, `fill`, `fill_form`, `type_text`, `press_key` (by `uid`) |
| Run JavaScript in the page | `javascript_tool` | `evaluate_script` |
| Console | `read_console_messages` with `pattern` | `list_console_messages`, filter by `types` (error, warn) |
| Network | `read_network_requests`, called once before the action | `list_network_requests` (records from the last navigation on, no arming needed), details with `get_network_request` |
| Dark mode | the app's own switch | the app's own switch, or `emulate` with `colorScheme: dark` |
| Narrow viewport | `resize_window` 390 x 844 | `resize_page` 390 x 844, or `emulate` with a `viewport` |
| Browser dialog appeared | blocks the extension, avoid at all costs | `handle_dialog`; still avoid triggering one |
| Close the own tab | `tabs_close_mcp` | `close_page` |

**Chrome DevTools, remote setup:** the MCP server connects to `http://127.0.0.1:9222`. When that fails, the user's Chrome for Claude is not running or the port is not forwarded; say so and ask, do not fall back to starting a browser of your own (it would open where nobody sees it, and logins would fail).
