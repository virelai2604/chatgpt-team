---
source_id: oa_agents_sdk
source_url: https://developers.openai.com/api/docs/guides/agents
source_ref: https://openai.github.io/openai-agents-python/
category: agents_sdk
priority: P0
fetched: 2026-07-07
fetch_method: developers.openai.com and openai.github.io 403 automated fetch; reconstructed from web search + the installed openai-agents 0.17.7 API (introspected locally).
pull_status: fetched
---

# Agents SDK (Python)

An agent plans, calls tools, can hand off to specialists, and keeps state within
guardrails.

## Primitives

| Primitive | Purpose |
|---|---|
| `Agent` | name, instructions, model, tools, (handoffs, guardrails) |
| `@function_tool` | turn a Python function into a tool (auto JSON schema + Pydantic) |
| `FileSearchTool` / `WebSearchTool` | hosted tools (RAG / web) |
| `Runner.run` / `run_sync` / `run_streamed` | execute the agent loop |
| `handoff` | router agent delegates to specialists |
| guardrails | parallel input/output validation, fail-fast |
| sessions | persist state across turns |

## Minimal

```python
from agents import Agent, Runner, function_tool

@function_tool
def multiply(a: float, b: float) -> float:
    "Multiply two numbers."
    return a * b

agent = Agent(name="Assistant", instructions="Be helpful.", tools=[multiply])
print(Runner.run_sync(agent, "6 times 7?").final_output)
```

## Streaming

```python
result = Runner.run_streamed(agent, "…")
async for e in result.stream_events():
    if e.type == "raw_response_event" and hasattr(e.data, "delta"):
        print(e.data.delta, end="")
```

## In this repo

`examples/agents/relay_agent.py` (minimal) and `agent_pro.py` (FileSearchTool +
WebSearchTool + streaming) implement these. Handoffs/guardrails deferred
(personal project). Install: `pip install openai-agents` (0.17.x).
