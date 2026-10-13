# Vault and machine setup

Read this in phase 0, when no Obsidian tools are available yet, and for the status bar offer.

## Connecting the vault

Many people have never added an MCP server. Explain that this connects Claude to a folder of Markdown notes, and that Obsidian itself is optional because the folder works either way.

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

This goes in the global settings (one vault across projects) or the project `.mcp.json` (the vault belongs to this project alone); ask which. The server has to start before its tools appear, which usually means restarting the session. Say that up front.

A REST-based alternative talks to a running Obsidian through a Local REST API plugin and an API key. Suggest it only when the user wants live sync with the Obsidian app: it is more setup, more that can break, and an API key in a config file is a liability the simple server avoids.

## Optional: the status bar

Offered in phase 0 because this is where the machine-level setup happens, next to the MCP server.

**Three conditions, all of them.** The user works in the terminal (the status line does not appear in an IDE or on the web). No `statusLine` is set in the user's settings yet; if one is, skip **silently**, since it is a per-machine setting and re-offering it per project is noise. And the user says yes, because this installs a third-party tool from the network.

What it buys is what a session cannot see about itself: rate-limit usage and its projection, context fill, model and mode, session cost, working-tree state. Those numbers decide when to hand off.

Installation belongs to the `claude-statusbar` skill, which only the user can invoke: when they say yes, ask them to type `/claude-statusbar`. If they decline, say nothing further.
