---
source_id: oa_apps_sdk_mcp_apps
source_url: https://developers.openai.com/apps-sdk/mcp-apps-in-chatgpt
category: chatgpt_apps
priority: P0
fetched: 2026-07-07
fetch_method: developers.openai.com returns HTTP 403 to automated fetch; NOT snapshotted. Summary from prior knowledge / BIFL plan.
pull_status: summary_only
verify: open source_url in a browser and replace this body; then set pull_status: fetched.
---

# Apps SDK — MCP Apps in ChatGPT (SUMMARY ONLY — verify against source)

> ⚠️ Not a full snapshot. `developers.openai.com` blocked the automated fetch
> (403). Verify against the live page before relying on exact field names.

## What it defines

The ChatGPT **app / MCP surface**: how an MCP server + optional UI show up inside
ChatGPT. The docs navigation covers: MCP Apps in ChatGPT, MCP Server, UX
principles, UI guidelines, auth, state, deploy, test, submit.

## Key concepts

- **Tools** are declared on the MCP server (`name`, `description`, `inputSchema`,
  `annotations`).
- **UI components** can invoke tools via `tools/call`.
- `_meta.ui.visibility` restricts a tool to `["model","app"]` or `["app"]`.
- `_meta.ui.csp` declares allowed `connectDomains` / `resourceDomains`.
- Custom MCP apps must be **connected/published through workspace controls**;
  developer mode alone does not expose new actions.

## For BIFL

`ai.lafiel.me` is the MCP server; `bifl.health/search/fetch` are the tools. An
optional widget (`ui://widget/bifl-dashboard.html`) can call them via `tools/call`.

## TODO
Open the source_url in a browser, paste the real content, set `pull_status: fetched`.
