---
source_id: oa_docs_platform_overview
title: OpenAI Platform
category: openai_docs
source_urls:
  - https://platform.openai.com/docs
  - https://github.com/openai/openai-openapi
fetched: 2026-07-12
fetch_method: Fetched openai-openapi openapi.yaml (raw.githubusercontent.com, master) and grepped top-level paths + servers + securitySchemes; SDK versions and prose web-searched (platform.openai.com is 403-blocked).
pull_status: fetched
verify: curl -sS https://raw.githubusercontent.com/openai/openai-openapi/master/openapi.yaml | grep -E '^  /' | sort -u
---

# OpenAI Platform

> Provenance: Endpoint families below are derived from the openai-openapi spec (`openapi.yaml`, `info.version: 2.3.0`, `servers[0].url: https://api.openai.com/v1`) fetched 2026-07-12; SDK versions and high-level framing were web-verified since platform.openai.com returns 403 to automated fetches.

## What it is
The OpenAI Platform (platform.openai.com) is the developer surface for OpenAI's models: a REST API served from a single base URL (`https://api.openai.com/v1`), plus official SDKs, dashboard, keys/projects, usage/billing, and reference docs. All model calls are HTTPS requests authenticated with a bearer API key. The spec advertises the **Responses API** as the recommended primitive for new projects (unified, agentic, built-in tools), with **Chat Completions** still fully supported for compatibility.

## Endpoint families (from openai-openapi, verified 2026-07-12)
Derived from the ~130 top-level paths in `openapi.yaml`. Grouped by family (leading `/v1` base omitted; the spec lists paths without the version prefix but serves them under `https://api.openai.com/v1`):

- **Responses** — `/responses`, `/responses/{id}`, `/responses/{id}/cancel`, `/responses/{id}/input_items`, `/responses/input_tokens`, `/responses/compact`. The recommended agentic primitive.
- **Chat Completions** — `/chat/completions`, `/chat/completions/{id}`, `/chat/completions/{id}/messages`. Legacy text **Completions** at `/completions`.
- **Conversations** (stateful) — `/conversations`, `/conversations/{id}`, `/conversations/{id}/items`, `.../items/{item_id}`.
- **Embeddings** — `/embeddings`.
- **Images** — `/images/generations`, `/images/edits`, `/images/variations`.
- **Audio** — `/audio/speech`, `/audio/transcriptions`, `/audio/translations`, `/audio/voices`, `/audio/voice_consents`.
- **Realtime** — `/realtime/sessions`, `/realtime/client_secrets`, `/realtime/transcription_sessions`, `/realtime/translations/client_secrets`, `/realtime/calls` (+ accept/hangup/refer/reject). Low-latency voice over WebRTC/WebSocket/SIP.
- **Video** (newer) — `/videos`, `/videos/edits`, `/videos/extensions`, `/videos/remix`, `/videos/characters`, `/videos/{id}/content`.
- **Batch** — `/batches`, `/batches/{id}`, `/batches/{id}/cancel`.
- **Files** — `/files`, `/files/{id}`, `/files/{id}/content`; large uploads via `/uploads` (+ parts/complete/cancel).
- **Vector Stores** — `/vector_stores`, `/vector_stores/{id}`, `.../files`, `.../file_batches`, `.../search`.
- **Fine-tuning** — `/fine_tuning/jobs` (+ cancel/pause/resume/events/checkpoints), `/fine_tuning/checkpoints/.../permissions`, `/fine_tuning/alpha/graders/{run,validate}`.
- **Evals** — `/evals`, `/evals/{id}`, `/evals/{id}/runs`, `.../runs/{run_id}/output_items`.
- **Moderations** — `/moderations`.
- **Models** — `/models`, `/models/{model}`.
- **Assistants (beta)** — `/assistants`, `/threads`, `/threads/{id}/messages`, `/threads/{id}/runs` (+ steps/submit_tool_outputs). Legacy; superseded by Responses/Conversations.
- **Containers** (Code Interpreter) — `/containers`, `.../files`, `.../files/{id}/content`.
- **Skills** — `/skills`, `/skills/{id}` (+ versions/content).
- **ChatKit** — `/chatkit/sessions`, `/chatkit/threads`, `.../items`.
- **Administration** (admin key) — `/organization/*` (projects, users, groups, roles, invites, api_keys, admin_api_keys, service_accounts, rate_limits, certificates, usage/*, costs, audit_logs) and `/projects/{id}/*`.

Note: The `/organization/*` and admin endpoints authenticate with an **Admin API key** (`AdminApiKeyAuth`), distinct from the standard project key.

## SDKs & auth (base_url, Authorization: Bearer, projects/keys)
- **Base URL**: `https://api.openai.com/v1` (single `servers` entry in the spec).
- **Auth**: HTTP bearer. Every request sends `Authorization: Bearer <API_KEY>`. Spec `securitySchemes`: `ApiKeyAuth` (type http, scheme bearer) for normal endpoints; `AdminApiKeyAuth` for org/admin endpoints. Keys are scoped to a **project** within an **organization**; optional `OpenAI-Organization` / `OpenAI-Project` headers select context.
- **Python SDK** (`openai` on PyPI) — official; latest **2.45.0** (2026-07-09). Sync + async clients, typed params/responses, configurable `base_url` and `api_key`.
- **Node/TypeScript SDK** (`openai` on npm) — official; latest **6.46.0** (mid-July 2026). Same configurability (`baseURL`, `apiKey`).
- Both SDKs default to the base URL above and read `OPENAI_API_KEY` from the environment; `base_url`/`baseURL` is overridable, which is what makes OpenAI-compatible relays work.

## Relevance to this repo (the relay is an OpenAI-compatible passthrough to /v1)
This repo's relay presents an **OpenAI-compatible** surface: clients point their SDK's `base_url`/`baseURL` at the relay instead of `https://api.openai.com/v1`, keep the `Authorization: Bearer` header, and call the same paths (primarily `/chat/completions`, `/responses`, `/embeddings`, `/models`). Because the SDKs treat the base URL as a plain prefix and the auth model is a single bearer header, a passthrough only needs to preserve path shape, headers, and streaming semantics — no SDK changes on the client side. Families the relay does not proxy (Realtime, Batch, org admin, fine-tuning) simply fall through or are unsupported; verify against the relay's actual route table.

## Verify / TODO
- Re-run the `curl | grep '^  /'` verify command to refresh the path list; spec `info.version` was **2.3.0** on 2026-07-12.
- platform.openai.com and developers.openai.com are 403 to automated fetch — human-verify prose (Responses-vs-Chat-Completions recommendation, key/project model) in a browser if exact wording matters.
- SDK versions move fast; confirm `openai` (PyPI) and `openai` (npm) current releases at publish time.
- Confirm which endpoint families this repo's relay actually forwards vs. rejects (route table not audited here).
