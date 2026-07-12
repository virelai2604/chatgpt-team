---
source_id: oa_docs_agents_sdk
title: Agents SDK
category: openai_docs
source_urls:
  - https://github.com/openai/openai-agents-python
  - https://raw.githubusercontent.com/openai/openai-agents-python/main/README.md
  - https://openai.github.io/openai-agents-python
  - https://pypi.org/project/openai-agents/
  - https://developers.openai.com
fetched: 2026-07-12
fetch_method: curl raw README.md + src/agents/__init__.py, tool.py, run.py from main branch; PyPI JSON API for version
pull_status: fetched
verify: pip install openai-agents==0.18.2 then `python -c "import agents; print([n for n in ('Agent','Runner','function_tool','FileSearchTool','WebSearchTool','handoff','Session') ])"` — all import from the top-level `agents` package
---

# Agents SDK

> Provenance: Fetched the live `main` README plus `src/agents/__init__.py`, `tool.py`, and `run.py` on 2026-07-12; primitives below are quoted from that source, not memory. Current PyPI release confirmed as 0.18.2 (requires Python >=3.10).

## What it is
The OpenAI Agents SDK is a lightweight, provider-agnostic Python framework for building single- and multi-agent workflows. Per the README it supports the OpenAI Responses and Chat Completions APIs "as well as 100+ other LLMs." Install with `pip install openai-agents` (optional groups: `[voice]`, `[redis]`; `uv add openai-agents` also works). A JS/TS sibling lives at `openai/openai-agents-js`.

- Package name: `openai-agents` (import as `agents`)
- Version confirmed 2026-07-12: **0.18.2** (PyPI); `requires_python >=3.10`
- Note: this repo's `examples/agents/requirements.txt` currently pins `openai-agents>=0.17,<0.18` — older than the 0.18.2 release; bump if you want the newest surface.

## Core primitives (from openai-agents-python, verified 2026-07-12)
All of the following are exported from the top-level `agents` package (`src/agents/__init__.py`):

- **`Agent`** (and `AgentBase`) — an LLM configured with `name`, `instructions`, `tools`, `guardrails`, `handoffs`, `model`.
- **`Runner`** — exposes the three run modes confirmed in `run.py`:
  - `Runner.run(agent, input)` — async coroutine
  - `Runner.run_sync(agent, input)` — blocking wrapper
  - `Runner.run_streamed(agent, input)` — returns `RunResultStreaming` for token/event streaming
  - Results: `RunResult`, `RunResultStreaming`; config via `RunConfig`.
- **`function_tool`** — decorator that turns a Python function into a tool.
- **`handoff`** / `handoffs=` — delegate to another agent (`from .handoffs import handoff`, `Handoff`, etc.).
- **Guardrails** — `input_guardrail`, `output_guardrail` decorators; plus tool-level `tool_input_guardrail` / `tool_output_guardrail`.
- **Sessions / memory** — `Session`, `SessionABC`, `SessionSettings`, `SQLiteSession` (lazy import), `OpenAIConversationsSession`, `OpenAIResponsesCompactionSession`. Automatic conversation-history management across runs.
- **Tracing** — built-in; spans include `agent_span`, `guardrail_span`, `handoff_span`, etc. (`from .tracing import ...`).
- **Lifecycle hooks** — `AgentHooks`, `RunHooks`, `RunContextWrapper`.
- **Realtime** — `RealtimeAgent` / `RealtimeRunner` (README shows a `gpt-realtime-2.1` voice example).
- **Sandbox** — `SandboxAgent` with `Manifest` / `SandboxRunConfig` for long-horizon file/command work (newer surface in 0.18.x).

## Minimal example (from README)
```python
from agents import Agent, Runner

agent = Agent(name="Assistant", instructions="You are a helpful assistant")

result = Runner.run_sync(agent, "Write a haiku about recursion in programming.")
print(result.final_output)
```
Set `OPENAI_API_KEY` before running. (README also shows async `Runner.run(...)`, a `SandboxAgent` example, and a `RealtimeAgent` WebSocket example.)

## Hosted tools (FileSearchTool, WebSearchTool) — confirmed
Both are exported from `agents` and defined in `src/agents/tool.py`:

- **`FileSearchTool`** — confirmed field `vector_store_ids: list[str]` (required), plus optional `max_num_results: int | None = None`. Runs OpenAI-hosted file/vector-store retrieval.
  ```python
  from agents import FileSearchTool
  FileSearchTool(vector_store_ids=["vs_abc123"], max_num_results=5)
  ```
- **`WebSearchTool`** — confirmed optional field `user_location: UserLocation | None = None`. Hosted web search.
- Other hosted tools present in the same module: `CodeInterpreterTool`, `ComputerTool`, `ImageGenerationTool`. MCP tools are also supported.

## Relevance to this repo (examples/agents/relay_agent.py, agent_pro.py; point base_url at ai.lafiel.me/v1)
- **`examples/agents/relay_agent.py`** — minimal agent using `Agent`, `Runner`, `function_tool`. It routes through the relay by calling `set_default_openai_client(AsyncOpenAI(base_url=os.getenv("RELAY_BASE_URL", "https://ai.lafiel.me/v1"), api_key=relay_key))` plus `set_tracing_disabled`. This is the correct pattern for pointing the SDK at `ai.lafiel.me/v1`: build an `AsyncOpenAI` client with the relay `base_url` and register it as the default. Falls back to direct OpenAI if `RELAY_KEY` is unset.
- **`examples/agents/agent_pro.py`** — upgraded example importing `Agent, FileSearchTool, Runner, WebSearchTool, function_tool`; demonstrates hosted tools + streaming via `Runner.run_streamed`.
- **`examples/agents/agent_server.py`** — wraps an `Agent` behind an HTTP server (`Runner.run` per request), same relay flow.
- Action item: `examples/agents/requirements.txt` pins `>=0.17,<0.18`; the SDK is now 0.18.2. The `set_default_openai_client` + `base_url` mechanism remains valid, so the relay integration does not depend on the pin — but the sandbox/realtime primitives above require 0.18.x.

## Verify / TODO
- Re-fetch README + `src/agents/__init__.py` on the next research pass to catch new exports; primitives here are pinned to `main` as of 2026-07-12.
- `https://developers.openai.com` was BLOCKED (403) — not used as a source; canonical docs are `openai.github.io/openai-agents-python` and the GitHub repo.
- Confirm the relay (`ai.lafiel.me/v1`) forwards the Responses API endpoints that hosted tools (`FileSearchTool`, `WebSearchTool`, `CodeInterpreterTool`) require, not just Chat Completions.
- Consider bumping the local `requirements.txt` pin to `openai-agents>=0.18,<0.19` if sandbox/realtime features are wanted.
