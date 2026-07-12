---
source_id: oa_docs_responses_api
title: Responses API
category: openai_docs
source_urls:
  - https://platform.openai.com/docs/api-reference/responses
  - https://platform.openai.com/docs/guides/responses
  - https://github.com/openai/openai-openapi
fetched: 2026-07-12
fetch_method: curl of openai-openapi openapi.yaml (raw.githubusercontent.com, master) — extracted POST /responses -> CreateResponse (allOf CreateModelResponseProperties + ResponseProperties + inline), Response, and ResponseStreamEvent schemas; current models/tools web-searched (platform.openai.com is 403-blocked).
pull_status: fetched
verify: curl -sS https://raw.githubusercontent.com/openai/openai-openapi/master/openapi.yaml | grep -nE '^  /responses'
---

# Responses API

> Provenance: Request/response fields below are quoted from the openai-openapi spec (`openapi.yaml`, `info.version: 2.3.0`) fetched 2026-07-12 — the `POST /responses` operation (`operationId: createResponse`) with body `$ref CreateResponse` and 200 `$ref Response`; current model names and built-in-tool status are web-verified since platform.openai.com returns 403 to automated fetches.

## What it is (vs Chat Completions)
The Responses API (`POST /v1/responses`) is OpenAI's recommended agentic primitive for new projects. Versus Chat Completions it: (a) takes a single flexible `input` (string or typed item list) instead of a `messages` array; (b) keeps server-side conversation state via `store` + `previous_response_id` (or `conversation`), so you don't resend history; (c) exposes OpenAI-hosted **built-in tools** (web search, file search, code interpreter, image generation, computer use, MCP) in the same call; and (d) returns a structured `output` array of typed items (messages, reasoning, tool calls) plus an SDK-only `output_text` convenience string. Chat Completions (`/chat/completions`) remains fully supported for compatibility.

## Endpoint & key request fields (from openai-openapi, verified 2026-07-12)
`POST /responses` body = `CreateResponse`, an `allOf` of `CreateModelResponseProperties`, `ResponseProperties`, plus inline fields. Real field names from the spec:

Core input / model:
- `model` — model ID (`$ref ModelIdsResponses`), e.g. `gpt-4o`, `o3`, GPT-5 family.
- `input` — string or array of input items (`$ref InputParam`); text, images, file, and prior items.
- `instructions` — system/developer message; **not** carried over across `previous_response_id` turns.

State / storage:
- `store` (bool, default `true`) — persist response for later retrieval.
- `previous_response_id` — chain multi-turn; mutually exclusive with `conversation`.
- `conversation` (`$ref ConversationParam`) — attach to a stateful conversation object.
- `metadata` (`$ref Metadata`), `prompt` (`$ref Prompt`, reusable prompt template).

Tools:
- `tools` (`$ref ToolsArray`) — array of built-in / MCP / custom function tools.
- `tool_choice` (`$ref ToolChoiceParam`), `parallel_tool_calls` (bool, default `true`), `max_tool_calls` (int).

Generation controls:
- `max_output_tokens` (int, min 16 — includes reasoning tokens), `temperature` (0–2), `top_p`, `top_logprobs` (0–20).
- `reasoning` (`$ref Reasoning`; `effort` + `summary` = `auto|concise|detailed`) — **gpt-5 and o-series only**.
- `text` (`$ref ResponseTextParam`, structured-output/format), `truncation` (`auto|disabled`, default `disabled`).
- `background` (bool, default `false`), `service_tier`, `prompt_cache_key`, `prompt_cache_retention` (`in_memory|24h`), `safety_identifier`, `user` (deprecated).
- `context_management` (array, `$ref ContextManagementParam`).

Streaming / output selection:
- `stream` (bool, default `false`) — SSE.
- `stream_options` (`$ref ResponseStreamOptions`).
- `include` (array of `IncludeEnum`) — extra output data, e.g. `web_search_call.action.sources`, `code_interpreter_call.outputs`, `file_search_call.results`, `message.output_text.logprobs`, `reasoning.encrypted_content`, `message.input_image.image_url`, `computer_call_output.output.image_url`.

Related subpaths in spec: `/responses/{response_id}` (GET/DELETE), `/responses/{response_id}/cancel`, `/responses/{response_id}/input_items`, `/responses/input_tokens`, `/responses/compact`.

## Response object & streaming events (from spec)
`Response` (200) = `allOf ModelResponseProperties + ResponseProperties + object`. Key fields: `id`, `object` (const `response`), `created_at`, `status` (`completed|failed|in_progress|cancelled|queued|incomplete`), `error` (`$ref ResponseError`), `incomplete_details.reason` (`max_output_tokens|content_filter`), `output` (array of `OutputItem`), `output_text` (SDK-only aggregate string), `usage` (`$ref ResponseUsage`), `parallel_tool_calls`, `conversation`, `max_output_tokens`. `required: [id, object, created_at, error, ...]`.

Streaming (`stream: true`) emits `text/event-stream` of `ResponseStreamEvent`. Lifecycle events from the spec: `response.created`, `response.in_progress`, `response.completed`, `response.failed`, `response.incomplete`, `response.queued`. Incremental/item events include `response.output_item.added` / `.done`, `response.content_part.added` / `.done`, `response.output_text.delta` / `.done`, `response.output_text.annotation.added`, `response.refusal.delta` / `.done`, `response.reasoning_text.delta` / `.done`, `response.reasoning_summary_text.delta` / `.done`, `response.reasoning_summary_part.added` / `.done`, `response.function_call_arguments.delta` / `.done`, and per-tool progress events (`response.web_search_call.*`, `response.file_search_call.*`, `response.code_interpreter_call.*`, `response.image_generation_call.*`, `response.mcp_call.*`, `response.mcp_list_tools.*`, `response.custom_tool_call_input.*`, `response.output_audio.*` / `response.output_audio_transcript.*`). Each event carries a `sequence_number`.

## Built-in tools usable via Responses (web_search, file_search, etc. — verify)
`ToolsArray.items` is `$ref Tool`, a `oneOf` discriminated on `type`. Built-in / hosted tool `type` values in the spec: `web_search` (also versioned alias `web_search_2025_08_26`; legacy `web_search_preview`), `file_search`, `code_interpreter`, `image_generation`, `computer_use_preview`, `local_shell`, `mcp` (custom MCP servers + connectors like Google Drive/SharePoint), plus custom `function` and `custom` tools. Spec also lists newer entries: `apply_patch`, `function_shell`, `namespace`, `tool_search`. Web-verified (Jul 2026): the `web_search` tool is GA on GPT-5 family; per OpenAI docs `tool_search` requires gpt-5.4+, and the web_search tool exposes a `return_token_budget` option for high-effort research. Treat exact per-model tool availability as web-verified, not spec-guaranteed.

## Relevance to this repo (relay passthrough; /v1/responses)
This repo (chatgpt-team relay) implements `/v1/responses` at `app/routes/responses.py` — an `APIRouter(prefix="/v1", tags=["responses"])` that forwards to OpenAI via `app.api.forward_openai.forward_openai_request` / `forward_openai_method_path`. It supports an `x-relay-disable-tools` request header and can inject a tools manifest (`settings.TOOLS_MANIFEST`) into the passthrough. Because it is a relay, the field names above are the contract the relay must preserve untouched (especially `stream`, `tools`, `store`, `previous_response_id`, `input`, `instructions`, and the SSE event shapes). The repo's local mirror is `schemas/openapi.yaml`; siblings: `app/routes/conversations.py` (stateful state) and `app/api/sse.py` (stream relaying).

## Verify / TODO
- Re-run: `curl -sS https://raw.githubusercontent.com/openai/openai-openapi/master/openapi.yaml | grep -nE '^  /responses'` and re-extract `CreateResponse` / `Response` / `ResponseStreamEvent` when `info.version` moves past `2.3.0`.
- Web-verify current model IDs supported by `/responses` (GPT-5.x family shifts monthly; platform.openai.com/docs/models is 403 to fetch — use WebSearch).
- Confirm newer tool types (`apply_patch`, `function_shell`, `namespace`, `tool_search`) against live API before relaying them.
- Not fully expanded here: `InputParam`, `OutputItem`, `ResponseTextParam`, `ToolChoiceParam`, `ResponseUsage` sub-schemas — drill in if the relay needs field-level validation.
