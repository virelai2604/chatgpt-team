---
source_id: oa_docs_tools_connectors
title: Tools and Connectors
category: openai_docs
source_urls:
  - https://platform.openai.com/docs/guides/tools
  - https://platform.openai.com/docs/guides/tools-connectors-mcp
  - https://github.com/openai/openai-openapi
  - https://raw.githubusercontent.com/openai/openai-openapi/master/openapi.yaml
fetched: 2026-07-12
fetch_method: Fetched openai-openapi/master/openapi.yaml (2.8 MB, 81040 lines) via curl and grepped the `Tool` discriminator + tool schemas directly. Doc guide pages (platform.openai.com/docs, developers.openai.com) are 403-blocked, so their contents were web-searched (OpenAI announcement blog, TechCrunch, OpenAI Help Center) rather than fetched.
pull_status: web_verified
verify: Re-run `curl -s https://raw.githubusercontent.com/openai/openai-openapi/master/openapi.yaml | grep -nE "Tool:|connector_id" -A3` and confirm the `Tool` oneOf members and connector_id enum still match this table.
---

# Tools and Connectors

> Provenance: Tool `type` strings and connector IDs are quoted verbatim from the machine-readable OpenAPI spec (openai-openapi repo, `master`); the human-facing framing ("what it does") comes from web-searched OpenAI announcement/help pages because the `/docs/guides` pages are 403-blocked to this environment.

## What it is

The **Responses API** runs an agentic loop in which the model can call one or more **built-in (hosted) tools**, custom **function** tools, and **remote MCP servers** within a single API request. Tools are passed in the request `tools:` array; each entry is discriminated by a `type` string. Separately, **ChatGPT product connectors** are data-source integrations surfaced inside the ChatGPT app (and Deep Research), which OpenAI has partially mirrored into the API as MCP **connectors** addressed by `connector_id`. The two surfaces overlap in branding but are configured differently.

## Built-in API tools (verified 2026-07-12)

Quoted from the `Tool` discriminator (`oneOf`) and each tool schema's `type` enum in `openapi.yaml`. The `Tool` union members are: FunctionTool, FileSearchTool, ComputerTool, ComputerUsePreviewTool, WebSearchTool, MCPTool, CodeInterpreterTool, ImageGenTool, LocalShellToolParam, FunctionShellToolParam, CustomToolParam, NamespaceToolParam, ToolSearchToolParam, WebSearchPreviewTool, ApplyPatchToolParam.

| tool `type` string | what it does | notes |
|---|---|---|
| `web_search` (also `web_search_2025_08_26`) | Includes live internet data in the response. | Current web search tool; dated variant is a pinned version. |
| `web_search_preview` (also `web_search_preview_2025_03_11`) | Earlier/preview web search tool. | Both `web_search` and `web_search_preview` variants exist in the current spec. |
| `file_search` | Makes contents of uploaded files (vector stores) queryable for retrieval. | Requires `vector_store_ids`; ties into the Vector Stores API. |
| `code_interpreter` | Model writes and runs Python in a sandboxed container. | Requires a `container` field. |
| `computer` / `computer_use_preview` | Computer-use / browser-and-desktop control tool. | `computer_use_preview` requires `environment`, `display_width`, `display_height`. `ToolChoiceTypes` also lists `computer_use`. |
| `image_generation` | In-loop image generation/editing (model `gpt-image-1`), supports streaming previews and multi-turn edits. | — |
| `mcp` | Calls tools hosted on a remote MCP server (or an OpenAI connector). | See next section for fields. |
| `local_shell` | Local shell tool. | Hosted tool param. |
| `shell` (FunctionShellToolParam) | "Shell tool" variant. | `type: shell`. |
| `custom` | Custom (free-form) tool. | Also has a `custom` tool-choice. |
| `namespace` | Namespaces a set of tools. | `NamespaceToolParam`. |
| `tool_search` | Lets the model discover/load deferred tool definitions at runtime. | "Tool search tool"; matches the "tool search" feature noted in docs. |
| `apply_patch` | Apply-patch tool (edit files via patches). | `ApplyPatchToolParam`. |
| `function` | Developer-defined custom function calling. | Standard function tool. |

`ToolChoiceTypes` (hosted-tool forcing) enumerates: `file_search`, `web_search_preview`, `computer`, `computer_use_preview`, `computer_use`, `web_search_preview_2025_03_11`, `image_generation`, `code_interpreter`.

## Remote MCP / connectors

The `mcp` tool (schema `MCPTool`, `type: mcp`) connects OpenAI models to any MCP server. Key fields (from spec):

- `server_label` — label for the MCP server.
- `server_url` — URL of a remote MCP server. **One of `server_url` or `connector_id` must be provided.**
- `connector_id` — selects an **OpenAI-maintained service connector** ("like those available in ChatGPT") instead of a self-hosted server. Enum (verbatim):
  - `connector_dropbox` (Dropbox)
  - `connector_gmail` (Gmail)
  - `connector_googlecalendar` (Google Calendar)
  - `connector_googledrive` (Google Drive)
  - `connector_microsoftteams` (Microsoft Teams)
  - `connector_outlookcalendar` (Outlook Calendar)
  - `connector_outlookemail` (Outlook Email)
  - `connector_sharepoint` (SharePoint)
- `authorization` — OAuth access token; your app runs the OAuth flow and passes the token here.
- (also present) `require_approval`, `allowed_tools`, `server_label`.

So an API "connector" is just an `mcp` tool where you pass `connector_id` + `authorization` instead of `server_url` — no server hosting required. Note the API `connector_id` enum does **not** include GitHub or Box (those appear on the ChatGPT product side; see below), so honesty caveat: the API-side connector list is narrower than the ChatGPT connector catalog.

## ChatGPT product connectors vs API tools (distinction)

- **ChatGPT product connectors** are data-source integrations inside the ChatGPT app / Deep Research: Google Drive, Dropbox, SharePoint, Box, GitHub, Gmail, Google Calendar, Microsoft/Outlook, etc. (per OpenAI Help Center release notes and TechCrunch, Jun 2025). They are enabled/governed by workspace admins (Business/Enterprise/Edu) and consumed by an end user chatting — not by developer code. GitHub and Box appear here.
- **API built-in tools** (`web_search`, `file_search`, `code_interpreter`, `image_generation`, `computer_use_preview`, `mcp`, …) are configured per-request in the Responses API `tools:` array by a developer.
- **API connectors** (`mcp` + `connector_id`) are the bridge: a subset of the ChatGPT connector catalog exposed to the API as OpenAI-hosted MCP wrappers, authorized with a caller-supplied OAuth token. Overlapping brand, different plumbing: ChatGPT connectors = admin-toggled product feature; API connectors = code-level `mcp` tool entries.

## Relevance to this repo (relay + agent examples)

- `examples/agents/relay_agent.py` and `agent_server.py` route through the relay at `https://ai.lafiel.me/v1` (OpenAI-compatible base URL; see `AGENTS.md` lines 40-41). Honesty caveat: those two examples wire **custom function tools** (`multiply`, `is_prime` via the Agents SDK `@function_tool`), **not** built-in `file_search`/`web_search`. The relay is an OpenAI-compatible proxy, not itself described in code as an MCP server.
- Actual `file_search`/vector-store usage in this repo lives in `examples/bifl/sync_vector_store.py` and `app/routes/bifl.py`, with reference notes in `reference/openai/file-search/openai-file-search.md` — that is where the `file_search` built-in tool + Vector Stores API are exercised.
- If this repo later exposes `ai.lafiel.me` as an MCP endpoint, it would be consumed via the `mcp` tool with `server_url: https://ai.lafiel.me/...` (not a `connector_id`, since only the 8 enumerated OpenAI connectors are valid there).

## Verify / TODO

- Confirm whether `web_search` vs `web_search_preview` are both still accepted at request time (spec keeps both; docs pages are 403-blocked here — verify against a live 200 doc pull when unblocked).
- Watch the `connector_id` enum for additions (GitHub/Box are ChatGPT-side today; may land in the API list later).
- `platform.openai.com/docs/guides/tools` and `/docs/guides/tools-connectors-mcp` were NOT fetched (403) — re-pull for exact prose and any tools not surfaced by the spec grep.
- Re-check the `Tool` oneOf on each spec refresh; newer members (`tool_search`, `namespace`, `apply_patch`, `shell`) were absent from older tool lists and may still be evolving.
