# Repository Guidelines – ChatGPT Team Relay (Codex Max / Custom Action Focus)

This AGENTS.md applies to the entire `chatgpt-team` repo. The primary goal is to use FastAPI + OpenAI APIs to power private ChatGPT Custom Actions for the owner/team, not to build a generic multi-user chat app.

---

## How you must read repo context

Read the working tree directly. It is the only source of truth.

This repo previously shipped two generated snapshots — `chatgpt_baseline.md` and
`chatgpt_changes.md` — that agents were told to treat as the codebase. Both were
pinned at merge-base `f267274` and had drifted badly: the baseline still showed
`extra_headers` for the realtime websocket connect, a form that raises `TypeError`
against the pinned `websockets>=15` (see
`reference/openai/01_OpenAI_Docs_Summaries/14-realtime.md`). They have been removed,
along with `chatgpt_sync.sh` and `generate_tree.py` which produced them.

Rules:
- Read files from the tree; never rely on a snapshot of them.
- Never invent missing files. If a path you need does not exist, ask for it.

Scope that matters long-term:
- repo root: `pyproject.toml`, `render.yaml`, `OPENAI_REFERENCES.md`
- directories: `app/`, `tests/`, `static/`, `schemas/`
- runnable examples (NOT part of the relay app): `examples/agents/`, `examples/bifl/`, `examples/mone/`
- OpenAI reference catalog: `reference/openai/` (`SOURCES.md`, `sources.json`, `openai-reference-manifest.jsonl`, snapshots)
Ignore everything else unless explicitly requested.

---

## Repo, Deployment & Environment

- GitHub (source of truth): https://github.com/virelai2604/chatgpt-team
- Primary deployment (Render, auto-deploy on push to `main`): https://chatgpt-team-relay.onrender.com
- Public URL (custom domain, use this to call the relay): https://ai.lafiel.me
- Hosted relay endpoint (OpenAI-compatible): `https://ai.lafiel.me/v1`
- Local workspace path varies (Windows: `...\Agent\Openclaw\chatgpt-team`; WSL/cloud: `/home/user/chatgpt-team`) — the GitHub repo is the source of truth.

Runtime:
- Python 3.12+ ; dependencies pinned in `pyproject.toml` (fastapi, uvicorn, httpx, openai 2.x, pydantic 2.x). OpenAI SDK is used only for the `OpenAIError` type; forwarding is transparent httpx pass-through.
- Relay implements an OpenAI-compatible REST API. Default FastAPI entrypoint: `app/main.py`.
- Primary routing/action logic lives in `app/routes/` and `app/api/`.
- Data files (SQLite, JSONL, temp artifacts) under `data/` are not part of the long-term "action relay" scope unless explicitly needed.

Current endpoint surface (as of 2026-07):
- OpenAI SDK parity: `/v1/chat/completions`, `/v1/embeddings`, `/v1/responses`, `/v1/models`, `/v1/images/*`, `/v1/files`, `/v1/batches`, `/v1/vector_stores`.
- BIFL retriever (read-only): `/v1/bifl/health`, `/v1/bifl/search`, `/v1/bifl/fetch` (search needs `BIFL_VECTOR_STORE_ID`).
- Actions-safe OpenAPI subset served at `/openapi.actions.json` (for Custom GPT import).
- Health at `/v1/health`. Auth is relay-key based (`RELAY_KEY`); the real `OPENAI_API_KEY` stays server-side.

Assumptions:
- This repository is a private glue layer between ChatGPT and OpenAI APIs on behalf of the owner.
- Prefer small, auditable changes; avoid adding heavy “chat app” features unless explicitly requested.

---

## OpenAI reference stack (priority: Website → GitHub → Local)

When generating or checking anything related to OpenAI APIs, models, tools, SDKs, or platform behavior, follow this priority order:

1) OpenAI platform docs (primary):
- https://platform.openai.com/docs/
- API reference: https://platform.openai.com/docs/api-reference/
- GPTs & Actions: https://platform.openai.com/docs/gpts/actions

2) Official OpenAI GitHub repos (secondary):
- Python SDK: https://github.com/openai/openai-python
- OpenAPI spec: https://github.com/openai/openai-openapi

3) In-repo reference catalog (tertiary, provenance-stamped, preferred over the PDF):
- `reference/openai/SOURCES.md` + `sources.json` — top-20 sources (docs + repos).
- `reference/openai/openai-reference-manifest.jsonl` — accession ledger (`pull_status`: `fetched` vs `summary_only`).
- Snapshots under `reference/openai/{workspace-agents,cookbook,apps-sdk,file-search,agents-sdk,tools-skills,github-openai}/`.
- Older PDF (dated, lowest priority): `ChatGPT-API_reference_ground_truth-2025-10-29.pdf` at repo root.
- Note: `summary_only` snapshots are NOT authoritative — `developers.openai.com` blocks automated fetch; verify against the live URL before relying on exact fields.

Conflict rule:
1) Website
2) Official GitHub
3) Local PDF
4) Third-party repos

If you detect changes versus older examples, spell it out explicitly instead of silently following stale behavior.

---

## Codex / Agent Behavior (P4 “Analogy Hybrid Developer”)

For any coding, design, or explanation task in this repo, use this response pattern:

1) Answer first — short, direct, correct.
2) Analogy — 1–2 lines from another domain (systems, science, nature).
3) Steps / Pseudocode / Code — clear algorithm, then full code when relevant.
4) How to Run/Test — exact commands, curl examples, or test cases.

Maintain:
- Professional, concise language.
- Strong preference for reproducible commands and tests.
- No filler.

---

## Project Overview

This repo is a FastAPI relay and automation layer between ChatGPT / GPT Actions and OpenAI APIs.

Main components:
- `app/main.py` — FastAPI entrypoint.
- `app/routes/` — HTTP routes, including Custom Action endpoints.
- `app/api/` — forwarding logic to OpenAI (or the relay provider), tools integration.
- `app/core/config.py` — environment variables, timeouts, default models.
- `schemas/openapi.yaml` — OpenAPI schema used by ChatGPT Actions.
- `tests/` — pytest suite validating routes, tools, and basic flows.

---

## Custom Action Focus

Goal: expose private ChatGPT Custom Actions powered by this relay.

Principles:
- Each Action = a clear API surface:
  - Validate input.
  - Call upstream (OpenAI / other tools).
  - Return a clean, typed response.
- No hidden side effects:
  - Avoid writing to DB unless explicitly requested.
  - Avoid long-running background jobs unless supported and documented.

When implementing or changing an Action:
1) Add/update route in `app/routes/actions.py` (or a clearly named module).
2) Update `schemas/openapi.yaml` so ChatGPT can discover the Action.
3) Add/update tests in `tests/` that cover:
   - Happy path.
   - Common error cases.
   - Basic schema/contract checks.

---

## Dev Environment & Commands (WSL)

Typical setup:

```bash
cd ~/code/chatgpt-team
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
