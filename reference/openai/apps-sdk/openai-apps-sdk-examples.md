---
source_id: gh_openai_apps_sdk_examples
title: openai/openai-apps-sdk-examples (repo reference)
category: apps_sdk_examples
source_urls:
  - https://github.com/openai/openai-apps-sdk-examples
  - https://raw.githubusercontent.com/openai/openai-apps-sdk-examples/main/README.md
retrieved_at: 2026-07-16
fetch_method: WebFetch of the repo README on raw.githubusercontent.com (GitHub is fetchable)
pull_status: fetched
verify: repo evolves; re-pull README + example list when building an MCP app
---

# openai/openai-apps-sdk-examples

> Provenance: `fetched` (2026-07-16) from the repo README (GitHub raw is fetchable).
> Official example **MCP servers + UI widgets** for building ChatGPT apps.

## What it is

A gallery of **UI components + MCP servers** showing how to build ChatGPT **apps**:
combine the Model Context Protocol with rich widget interfaces.

## Example servers

| Server | Language | Demonstrates |
|---|---|---|
| **Pizzaz** | Node.js, Python | Multiple UI views (list, carousel, map), interactive checkout; uses the official Apps SDK UI library |
| **Kitchen Sink Lite** | Node.js, Python | Full `window.openai` API surface, state management, tool chaining |
| **Solar System** | Python | 3D interactive widget rendering |
| **Shopping Cart** | Python | `widgetSessionId` to keep state across multiple tool calls |
| **Authenticated** | Python | OAuth / multi-level authentication patterns |

## The three MCP capabilities an app needs

1. **List tools** — advertise supported tools with JSON-Schema contracts.
2. **Call tools** — execute actions when the model invokes them.
3. **Return widgets** — embed UI via `_meta.ui.resourceUri` metadata.

## Structure

```
src/                            # widget source
assets/                         # built HTML/JS/CSS bundles (versioned)
<server>_server_<node|python>/  # MCP server implementations
build-all.mts                   # Vite build orchestrator
```

## Run

```bash
# widgets
pnpm install && pnpm run build          # -> versioned bundles in assets/
pnpm run serve                          # http://localhost:4444 (CORS)

# a Python server example
python -m venv .venv && source .venv/bin/activate
pip install -r <server>/requirements.txt
uvicorn <server>.main:app --port 8000
```

## Gotchas worth knowing

- **State sync:** `_meta["widgetSessionId"]` keeps widget state synced across turns.
- **DNS-rebinding protection (Python, when tunneling):**
  `MCP_ALLOWED_HOSTS`, `MCP_ALLOWED_ORIGINS` must be set.
- **Chrome 142+:** disable the `local-network-access` flag (`chrome://flags/`) for local dev.
- **Deploy:** set `BASE_URL` / `API_BASE_URL` so widgets load assets + build fully-qualified API URLs.

## Relevance to this repo (ChatGPT Team Relay / BIFL)

This is the concrete template for turning `ai.lafiel.me` into a **ChatGPT app**:
expose `bifl.search`/`fetch` as MCP tools, and (optionally) a widget that renders
results, returned via `_meta.ui.resourceUri`. Use a Python server example
(`uvicorn <server>.main:app`) as the starting shape, matching the relay's stack.

## Verify / TODO

- When building, re-pull the README + the specific example's source for exact
  `window.openai` / `_meta` field names (they evolve).
