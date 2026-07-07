---
source_id: oa_apps_sdk_build_mcp_server
source_url: https://developers.openai.com/apps-sdk/build/mcp-server
category: apps_sdk_mcp
priority: P0
fetched: 2026-07-07
fetch_method: developers.openai.com returns HTTP 403 to automated fetch; NOT snapshotted. This is a summary of known concepts pending a manual pull.
pull_status: summary_only
verify: Open the source_url in a browser and replace this file with the real content.
---

# Apps SDK — Build an MCP server (SUMMARY ONLY — verify against source)

> ⚠️ Not a full snapshot. `developers.openai.com` blocked the automated fetch
> (403). The points below are from prior knowledge / your own BIFL plan and MUST
> be verified against the live page before relying on exact field names.

## What it is

An **MCP server** exposes your tools + optional UI to ChatGPT as an "app".
For BIFL this is the `ai.lafiel.me` bridge exposing `bifl.health`, `bifl.search`,
`bifl.fetch`.

## Tool definition (MCP)

Each tool declares:
- `name`, `title`, `description`
- `inputSchema` (JSON Schema; `additionalProperties: false`)
- `annotations` — **required** safety hints: `readOnlyHint`, `openWorldHint`,
  `destructiveHint` (missing/null hints are treated as validation errors)
- `_meta.ui` — optional UI binding: `resourceUri`, `visibility`
  (`["model","app"]` or `["app"]`), and `csp`
  (`connectDomains`, `resourceDomains`)

## First-milestone tools (read-only)

`bifl.health`, `bifl.search`, `bifl.fetch` → `readOnlyHint: true`,
`visibility: ["model","app"]`. Add write tools (app-only) only after audit
logging exists.

## Do-not

- No secrets in `content`, `structuredContent`, `_meta`, or widget state.
- Custom MCP apps must be connected/published through workspace controls
  (developer mode alone does not expose new actions).

## TODO to make this a real snapshot

Open `https://developers.openai.com/apps-sdk/build/mcp-server` in a browser,
copy the page, and replace this file's body. Then set `pull_status: fetched`.
