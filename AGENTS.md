# Repository Guidelines – ChatGPT Team Relay (Codex Max / Custom Action Focus)

This AGENTS.md applies to the entire `chatgpt-team` repo. The primary goal is to use **FastAPI + OpenAI APIs** to power **private ChatGPT Custom Actions** for the owner/team, not to build a generic multi-user chat app.

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
- Data files (SQLite, JSONL, temp artifacts) are under `data/` by convention.

Codex / agent assumptions:

- Model: `gpt-5.1-codex-max` with **high** reasoning effort by default.
- Provider: `chatgpt-team-relay` using `OPENAI_API_KEY`.
- Sandbox: `workspace-write` (can read/write within repo, but do not touch system-level paths).
- Approval policy: ask on failures or risky operations.
- Web search: allowed, but use the **OpenAI website + official GitHub repos first**.

Always remember this repository is a private glue layer between ChatGPT and OpenAI APIs on behalf of the owner.

---

## OpenAI reference stack (priority: Website → GitHub → Local)

When generating or checking anything related to OpenAI APIs, models, tools, SDKs, or platform behavior, follow this priority order.

### 1. Website – OpenAI platform docs (primary source)

Treat the live OpenAI website as the **best and most authoritative source**.

Main roots:

- Docs hub: `https://platform.openai.com/docs/`
- API Reference (all endpoints): `https://platform.openai.com/docs/api-reference/**` :contentReference[oaicite:0]{index=0}  
- Guides (text, audio, images, video, tools, realtime, etc.): `https://platform.openai.com/docs/guides/**`
- Models: `https://platform.openai.com/docs/models/**`
- GPTs & Actions: `https://platform.openai.com/docs/gpts/actions`
- Account & usage:
  - `https://platform.openai.com/account/api-keys`
  - `https://platform.openai.com/usage`

Key single pages used frequently:

- Authentication: `https://platform.openai.com/docs/api-reference/authentication`
- Responses API: `https://platform.openai.com/docs/api-reference/responses`
- Conversations API: `https://platform.openai.com/docs/api-reference/conversations`
- Webhook events: `https://platform.openai.com/docs/api-reference/webhook-events`
- Files, uploads, vector stores, fine-tuning, audio, images, videos, graders, etc. under `.../api-reference/**`
- Pricing: `https://platform.openai.com/docs/pricing`

If the website says something different from any other source (including GitHub or local PDFs), **follow the website**.

### 2. GitHub – official OpenAI repositories (second source)

Use official OpenAI GitHub repos as the **second layer** of truth, mainly for concrete code and generated SDKs:

- Python SDK: `https://github.com/openai/openai-python` – the official Python library for the OpenAI API, generated from the OpenAPI spec and providing typed synchronous and async clients. :contentReference[oaicite:1]{index=1}  
- OpenAPI spec + SDK generator: `https://github.com/openai/openai-openapi` – contains the OpenAPI specification used to generate the official SDKs.
- Other official OpenAI repos as needed (Agents SDK, examples, Realtime samples, etc.).

When writing or reviewing code:

- Prefer patterns, method names, and types from **openai/openai-python** (e.g. `OpenAI()`, `client.responses.create`, `client.realtime.connect`, etc.) over older or third-party libraries. :contentReference[oaicite:2]{index=2}  
- If there is any mismatch between the SDK docs and the website, double-check the OpenAPI spec and then defer to the **website**.

### 3. Local ground-truth snapshot (PDF) – third source

Local API snapshot:

- Linux path: `/home/user/code/chatgpt-team/ChatGPT-API_reference_ground_truth-2025-10-29.pdf`
- Windows path: `\\wsl.localhost\Ubuntu\home\user\code\chatgpt-team\ChatGPT-API_reference_ground_truth-2025-10-29.pdf`

Use this PDF as:

- A fast, offline reference, and
- A way to understand how the API looked as of **2025-10-29**.

If the PDF disagrees with either the **website** or the **official GitHub repos**, treat the PDF as outdated and explicitly mention that the online spec is newer.

### 4. Third-party / derivative GitHub repos (last)

“Derivatives” includes:

- Forks of `openai/openai-python` (for example, `AI-App/OpenAI-Python` and similar) that copy older SDK code. :contentReference[oaicite:3]{index=3}  
- Community wrappers (for frameworks, CLIs, etc.) and old “legacy” clients.
- Any libraries that still expose only legacy endpoints (e.g., `openai.ChatCompletion.create`, `openai.Image.create`, etc.) without the modern Responses API.

Policy:

- Treat all derivative or third-party repos as **non-authoritative**.
- You may inspect them for ideas or migration hints, but:
  - Do **not** assume they are up to date.
  - Do **not** generate new code that depends on unmaintained or archived forks when the official SDK can handle the task.

### 5. Conflict rule

If you see any difference between sources, resolve in this order:

1. OpenAI website (platform docs).
2. Official OpenAI GitHub (SDKs + OpenAPI spec).
3. Local PDF snapshot.
4. Third-party / derivative GitHub repos.

When you detect a change versus older examples (including the PDF or legacy code), **spell it out** instead of silently following stale behavior.

---

## Codex / Agent Behavior (P4 “Analogy Hybrid Developer”)

For any coding, design, or explanation task in this repo, use this response pattern:

1. **Answer first** – short, direct, correct.
2. **Analogy** – 1–2 lines from another domain (science, nature, systems).
3. **Steps / Pseudocode / Code** – clear algorithm, then full code when relevant.
4. **How to Run/Test** – exact commands, curl examples, or test cases.

Maintain:

- Professional, concise language.
- Strong preference for reproducible commands and tests.
- No unnecessary filler.

---

## Project Overview

This repo is a **FastAPI relay** and automation layer between ChatGPT / GPT Actions and OpenAI APIs.

Main components:

- `app/main.py` – FastAPI entrypoint.
- `app/routes/` – HTTP routes, including any **Custom Action** endpoints.
- `app/api/` – forwarding logic to OpenAI (or the relay provider), tools integration.
- `app/core/config.py` – environment variables, timeouts, default models.
- `schemas/openapi.yaml` – OpenAPI schema used by ChatGPT Actions.
- `tests/` – pytest suite validating routes, tools, and basic flows.

Runtime data:

- `data/` – SQLite DBs and artifacts (conversations, vector stores, etc.).
- Assume this service is **mostly stateless** for the Action use case.
- Do **not** add new DB tables or heavy chat features unless explicitly requested.

---

## Custom Action Focus

Goal: expose **private ChatGPT Custom Actions** powered by this relay.

Principles:

- Each Action = a clear API surface:
  - Validate input.
  - Call upstream (OpenAI / other tools).
  - Return a clean, typed response.
- No hidden side effects:
  - Avoid writing to DB unless the user explicitly wants state.
  - Avoid long-running background jobs unless supported and documented.

When implementing or changing an Action:

1. Add/update route in `app/routes/actions.py` (or a clearly named module).
2. Update `schemas/openapi.yaml` so ChatGPT can discover the Action.
3. Add or update tests in `tests/` that cover:
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
