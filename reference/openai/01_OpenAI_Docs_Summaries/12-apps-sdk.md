---
source_id: oa_docs_apps_sdk
title: Apps SDK
category: openai_docs
source_urls:
  - https://developers.openai.com/apps-sdk
  - https://developers.openai.com/apps-sdk/reference
  - https://developers.openai.com/apps-sdk/build/mcp-server
  - https://developers.openai.com/apps-sdk/deploy/submission
  - https://github.com/openai/openai-apps-sdk-examples
fetched: 2026-07-12
fetch_method: examples repo README fetched via GitHub (github.com + raw.githubusercontent.com); developers.openai.com/apps-sdk is 403 to automated fetch here, so its content was cross-checked via WebSearch snippets only (not snapshotted)
pull_status: web_verified
verify: Confirm exact _meta key spelling on developers.openai.com/apps-sdk/reference (openai/* prefixed keys vs ui.* keys) — search surfaced BOTH conventions; do not treat any single field name as authoritative until read at source.
---

# Apps SDK

> Provenance: the official examples repo README (github.com/openai/openai-apps-sdk-examples) was fetched and quoted; the developers.openai.com/apps-sdk docs pages are 403 to automated fetch here, so their specifics were verified via WebSearch snippets, not direct capture.

## What it is (MCP Apps in ChatGPT)
The Apps SDK lets developers build apps that surface **inside ChatGPT**. Each app
is backed by a **Model Context Protocol (MCP) server** that exposes tools the
model can call; tool responses can carry extra metadata — including inline HTML —
that ChatGPT uses to render rich **UI components ("widgets")** in an iframe. Per
the examples repo, it "provides example UI components to be used with the Apps
SDK, as well as example MCP servers that expose a collection of components as
tools." Apps are discoverable in an in-ChatGPT **App Directory**
(chatgpt.com/apps or the tools menu) once published.

## MCP server + tools (name/description/inputSchema/annotations)
An MCP server "defines tools, provides optional server instructions, enforces
auth, returns data, and points each tool to a UI bundle." Tools are advertised
with **JSON Schema contracts** (`inputSchema`) and optional **annotations** —
hints to ChatGPT about tool behavior, e.g. `readOnlyHint`, `destructiveHint`,
`openWorldHint` (standard MCP tool annotations). The three core MCP capabilities
exercised: **list tools**, **call tools** (with model-selected arguments), and
**return widgets** via metadata.

Official example MCP servers in the repo (exact folder names):
- `pizzaz_server_node/` and `pizzaz_server_python/` — list, carousel, and map views
- `solar-system_server_python/` — 3D solar-system viewer widget
- `kitchen_sink_server_node/` and `kitchen_sink_server_python/` — full `window.openai` surface
- `shopping_cart_python/` — `widgetSessionId` state sync
- `authenticated_server_python/` — OAuth-authenticated tool calls
- `mcp_app_basics_node/` — MCP fundamentals
- `src/` (widget source) + `assets/` (built HTML/JS/CSS bundles); build via `pnpm run build`, serve via `pnpm run serve` (localhost:4444, CORS). MIT license.

## UI widgets & _meta (visibility, csp) — VERIFY field names
Widgets render in a sandboxed iframe and talk to the host over a JSON-RPC-over-
postMessage bridge ("Skybridge"). Search surfaced TWO naming conventions for the
`_meta` keys — DO NOT treat either as final without reading the reference page:

- **OpenAI-prefixed keys** (surfaced from reference snippets, "verify at source"):
  - `_meta["openai/outputTemplate"]` — links a tool to its UI template
  - `_meta["openai/widgetDescription"]`
  - `_meta["openai/widgetCSP"]` — CSP for the widget sandbox
  - `_meta["openai/widgetPrefersBorder"]`
  - Widget resource served with **`mimeType: "text/html+skybridge"`**
- **ui.* keys** (MCP Apps standard, surfaced from docs/3rd-party snippets):
  - `_meta.ui.resourceUri` — points to the UI template (`ui://…`)
  - `_meta.ui.csp` — connect/resource/frame domain allowlists for the sandbox
    (e.g. `connectDomains`, `resourceDomains`, `frameDomains`)
- `_meta["widgetSessionId"]` — keeps widget state synced across turns (shopping_cart example)

Widget-facing `window.openai` surface (from README, verbatim set): `toolInput`,
`toolOutput`, `displayMode`, `theme`, `widgetState`; host APIs `setWidgetState`,
`callTool`, `requestDisplayMode`, `openExternal`, `sendFollowUpMessage`.

> Caution: the task's shorthand "`_meta.ui` visibility & csp" and the reference's
> "`openai/*`" keys may be two names for the same thing OR two layers. Confirm the
> exact spelling + visibility control field at developers.openai.com/apps-sdk/reference.

## Publishing (workspace controls, not dev mode alone)
- **Developer Mode**: build and test your app privately / within your workspace.
  Working in Developer Mode is the precondition, not the published state.
- **Submission**: apps are submitted **as plugins** through a plugin submission
  portal — sign in at platform.openai.com and go to the apps/plugin submission
  page. OpenAI reviews submissions.
- **Publish**: after approval, publish from the OpenAI platform dashboard; you
  MUST publish for the app to be listed in the in-ChatGPT **App Directory**.
- So: dev-mode connect ≠ published. Private/workspace use stays in dev mode;
  public listing requires review + explicit publish.
  (Sources: developers.openai.com/apps-sdk/deploy, .../deploy/submission,
  .../app-submission-guidelines; openai.com "Developers can now submit apps".)

## Relevance to this repo (ai.lafiel.me as MCP server; bifl.health/search/fetch as tools)
- **ai.lafiel.me** would be the deployed **MCP server** (HTTPS endpoint) that
  ChatGPT connects to — the same role as the example `*_server_*` folders.
- **bifl.health `search` and `fetch`** map to **MCP tools**: each declared with
  `name`, `description`, `inputSchema` (JSON Schema), and `annotations`
  (`search`/`fetch` are read-only ⇒ set `readOnlyHint: true`, likely
  `openWorldHint: true` since they hit external data).
- If either tool returns a widget, attach a widget resource
  (`mimeType: text/html+skybridge`) and reference it via the tool's `_meta`
  template key; set the widget CSP to allow only the domains bifl.health calls.
- For private/workspace use, connect via Developer Mode; for a public listing,
  go through plugin submission + publish — not dev-mode connect alone.

## Verify / TODO
- [ ] Read developers.openai.com/apps-sdk/reference directly (currently 403 here)
      to lock the exact `_meta` key spelling and the **visibility** control field
      name — search returned both `openai/*` and `ui.*` conventions.
- [ ] Confirm the full annotations list and any Apps-SDK-specific annotation keys
      beyond standard MCP (`readOnlyHint`/`destructiveHint`/`openWorldHint`).
- [ ] Confirm current submission/publish flow wording (platform.openai.com portal;
      review criteria) at .../apps-sdk/deploy/submission — availability/UX drifts.
- [ ] Pin the examples repo commit/tag when relied on for code (folder set above
      confirmed 2026-07-12).
