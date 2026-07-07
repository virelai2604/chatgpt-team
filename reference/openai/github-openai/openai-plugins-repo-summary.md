---
source_id: gh_openai_plugins
source_url: https://github.com/openai/plugins
category: codex_plugins_skills
priority: P0
fetched: 2026-07-07
fetch_method: WebFetch of the GitHub repo README (github is reachable).
pull_status: fetched
note: Current replacement for the deprecated openai/skills repo.
---

# openai/plugins — repo summary

Curated collection of **Codex plugin** examples. This is the **current** path for
packaging reusable agent capabilities (replaces the deprecated `openai/skills`).

## Plugin layout

Each plugin lives in `plugins/<name>/`:

```
plugins/<name>/
  .codex-plugin/plugin.json   # REQUIRED — the plugin manifest
  skills/                     # optional — skill definitions (folders of instructions/scripts)
  .app.json                   # optional — app configuration
  .mcp.json                   # optional — MCP server settings
  agents/                     # optional — plugin-level agent definitions
  commands/                   # optional — command specs
  hooks.json                  # optional — event hooks
  assets/                     # optional — supporting resources
```

- Marketplace config: `.agents/plugins/marketplace.json`
  (and `.agents/plugins/api_marketplace.json` for authenticated users).

## Example plugins referenced

`figma`, `notion`, `build-ios-apps`, `build-macos-apps`, `build-web-apps`, `expo`.

## For BIFL / M-One

To package the M-One tools (e.g. `bifl.search`, review-miner, complaint
classifier) as a reusable skill for Codex, mirror this structure: a
`plugins/bifl/` folder with `.codex-plugin/plugin.json` + a `skills/` folder of
instruction+script capabilities, and (optionally) `.mcp.json` pointing at the
`ai.lafiel.me` MCP bridge.
