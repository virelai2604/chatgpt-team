# chatgpt-team-relay

A stable, minimal-risk OpenAI relay focused on **ChatGPT Actions compatibility** with a **BIFL (buy-it-for-life)** maintenance posture.

## Why this exists

This relay is designed to:

- Support **ChatGPT Actions** with an **Actions-safe OpenAPI subset**
- Provide a **strictly guarded proxy** (`/v1/proxy`) for allowlisted JSON endpoints
- Implement **Actions-friendly wrappers** for endpoints Actions cannot call directly (multipart, binary, colon paths)
- Enforce long-term safety via a **coverage guardrail**: every endpoint must be classified as one of:
  - Actions wrapper
  - Proxy-allowlisted
  - Explicitly excluded

## API surfaces (intentional separation)

### 1) Canonical APIs (`/v1/*`)
These are the primary relay endpoints mirroring OpenAI-style paths (where safe).

Examples:
- `/v1/responses`
- `/v1/embeddings`
- `/v1/images/*`
- `/v1/videos/*` (canonical forwarding; some paths require wrappers for Actions)

### 2) Actions-safe wrappers (`/v1/actions/*`)
Actions cannot reliably call multipart or binary endpoints; wrappers convert JSON (often base64) into upstream-compatible requests.

Examples:
- `/v1/actions/files/upload` (JSON → multipart for `/v1/files`)
- `/v1/actions/uploads/*` (resumable upload wrappers)
- `/v1/actions/images/edits`, `/v1/actions/images/variations` (JSON wrapper surfaces)
- `/v1/actions/videos` + `/v1/actions/videos/generations` + `/v1/actions/videos/{video_id}/remix`
- `/v1/actions/responses/stream` (SSE wrapper)

### 3) Guarded proxy (`/v1/proxy`)
Generic relay endpoint that forwards allowlisted upstream paths only.

- Regex-based allowlist + normalization
- Explicit blocks for:
  - `:` paths (e.g. `/v1/responses:stream`)
  - `/content` binary downloads
  - multipart endpoints (e.g. `/v1/files`, `/v1/videos`)

### 4) OpenAPI outputs
- Full schema: `GET /openapi.json`
- Actions subset: `GET /openapi.actions.json`

The Actions schema is **curated** (subset) to expose only Actions-safe endpoints.

## Key guardrails (BIFL rules)

- Do not expose binary `/content` endpoints to Actions.
- Do not expose multipart endpoints directly to Actions.
- Do not expose wildcard `{path}` routers in Actions OpenAPI.
- The proxy allowlist must remain conservative.
- Every new endpoint must be assigned to exactly one policy bucket:
  - Actions wrapper
  - Proxy allowlisted
  - Explicitly excluded  
  Otherwise the coverage report must fail.

## Quickstart

### Requirements
- Python 3.11+ recommended
- `uvicorn`, `fastapi`, and project dependencies installed

### Run locally

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000
