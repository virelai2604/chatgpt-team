# Repository Guidelines – ChatGPT Team Relay (Codex Max / Custom Action Focus)

This AGENTS.md applies to the entire `chatgpt-team` repo. The primary goal is to use FastAPI + OpenAI APIs to power private ChatGPT Custom Actions for the owner/team, not to build a generic multi-user chat app.

---

## Baseline + Changes Contract (How you must read repo context)

I will provide you with two generated Markdown artifacts:

1) `chatgpt_baseline.md`
   - Authoritative baseline snapshot of the repo scope that matters.
   - Treat it as the codebase unless overridden by changes.

2) `chatgpt_changes.md`
   - Delta overlay on top of the baseline.
   - May include: change summary, unified diff patch, and full WORKTREE contents of changed files.

Rules:
- If the same file appears in both baseline and changes:
  - The version in `chatgpt_changes.md` is the latest truth.
- If a patch conflicts with embedded changed-file content:
  - Trust the embedded changed-file content and flag the inconsistency.
- Never invent missing files:
  - If a file is not present in baseline scope and not mentioned in changes, ask for the exact path.

Scope that matters long-term:
- repo root: `project-tree.md`, `pyproject.toml` (and optionally root `__init__.py`)
- directories: `app/`, `tests/`, `static/`, `schemas/`
Ignore everything else unless explicitly requested.

---

## Repo, Deployment & Environment

- GitHub (source of truth): https://github.com/virelai2604/chatgpt-team
- Primary deployment (Render): https://chatgpt-team-relay.onrender.com
- Primary workspace (WSL): `/home/user/code/chatgpt-team`
- Hosted relay endpoint (OpenAI-compatible): `https://chatgpt-team-relay.onrender.com/v1`

Runtime:
- Relay implements an OpenAI-compatible REST API.
- Default FastAPI app entrypoint: `app/main.py`.
- Primary routing and action logic lives in `app/routes/` and `app/api/`.
- Data files (SQLite, JSONL, temp artifacts) are under `data/` by convention and are not part of the long-term “action relay” scope unless explicitly needed.

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

3) Local PDF snapshot (tertiary, dated reference):
- `/home/user/code/chatgpt-team/ChatGPT-API_reference_ground_truth-2025-10-29.pdf`
- `\\wsl.localhost\\Ubuntu\\home\\user\\code\\chatgpt-team\\ChatGPT-API_reference_ground_truth-2025-10-29.pdf`

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
