---
source_id: gh_openai_developers_for_claude
title: openai/openai-developers-for-claude — Claude Code plugin bundling the OpenAI Docs MCP server
category: github_reference
source_urls:
  - https://github.com/openai/openai-developers-for-claude
retrieved_at: 2026-08-15
pinned_commit: 3c5c0debdec2695f657c5f1b99a32df6d23dd0ed
fetch_method: shallow clone (--depth 1 --filter=blob:none), manifests and README read locally
pull_status: fetched
verify: the MCP endpoint is https://developers.openai.com/mcp?source=claude — that host is known to 403 automated fetch, so confirm reachability from wherever you run Claude Code
---

# openai/openai-developers-for-claude

> Provenance: `fetched` 2026-08-15 at `3c5c0de`. Reference only — not vendored here.
> A working fork lives in its own repository; see the note at the bottom.

Claude Code plugin bundling OpenAI developer workflows. Node (`package.json`) with its own
tests (`tests/plugin-structure.test.mjs`, `tests/skill-contracts.test.mjs`).

## Structure

| File | Purpose |
|---|---|
| `.claude-plugin/marketplace.json` | plugin-marketplace metadata |
| `plugins/openai-developers/.claude-plugin/plugin.json` | plugin metadata |
| `plugins/openai-developers/.mcp.json` | bundles the **OpenAI Docs MCP server** |

```json
{"mcpServers": {"openaiDeveloperDocs": {"type": "http",
  "url": "https://developers.openai.com/mcp?source=claude"}}}
```

Six skills: `openai-docs`, `agents-sdk`, `build-chatgpt-app`, `chatgpt-app-submission`,
`openai-api-troubleshooting`, `openai-platform-api-key`.

## Why it is worth having

The Docs MCP server gives an agent authoritative, current OpenAI documentation. That
matters concretely: when the realtime surface was investigated on 2026-08-14,
`platform.openai.com` was egress-blocked from the working sandbox, and the answer had to
be inferred from the SDK's directory layout instead — `resources/realtime/` ships
`client_secrets.py` and no `sessions.py`. The conclusion held, but a docs lookup would
have been direct rather than inferential.

## Not vendored into this repo

It is a tool for working *on* the relay, not part of it — Node tooling, separate tests,
separate release cadence. Kept in its own repository instead.
