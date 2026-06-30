# Agents example — build agents on top of your relay

This is a minimal [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/)
agent that routes its model calls **through your relay** instead of straight to
OpenAI.

```
your agent  ──►  relay (ai.lafiel.me)  ──►  OpenAI
            RELAY_KEY              OPENAI_API_KEY (server-side only)
```

## Why route an agent through the relay?

- **Your OpenAI key stays server-side.** The agent only holds `RELAY_KEY`, which
  you can rotate or revoke without touching your OpenAI key.
- **One control point.** Model defaults, auth, logging, and rate limits live in
  the relay, shared by every agent/app you build.
- **It gives the relay a real consumer** — which is the whole point of having
  deployed it.

The Agents SDK talks to the OpenAI **Responses API**, which the relay already
proxies at `/v1/responses`, so no relay changes are needed.

## Run it

```bash
pip install -r requirements.txt

# Option A — through your relay (recommended)
export RELAY_BASE_URL="https://ai.lafiel.me/v1"   # your relay's /v1 base
export RELAY_KEY="your-relay-key"                 # the key the relay checks
export AGENT_MODEL="gpt-4o-mini"                  # any model your relay allows
python relay_agent.py "What is 23 * 19, and is the result prime?"

# Option B — straight to OpenAI (no relay)
export OPENAI_API_KEY="sk-..."
python relay_agent.py "Multiply 6 and 7"
```

Expected: the agent calls the `multiply` and `is_prime` tools rather than doing
the math itself, then answers in one line.

## What's in `relay_agent.py`

- Two `@function_tool`s (`multiply`, `is_prime`) — these are the agent's
  "actions". Add your own functions here and list them in `tools=[...]`.
- `set_default_openai_client(AsyncOpenAI(base_url=..., api_key=RELAY_KEY))` —
  the one line that makes the SDK route through your relay.
- `Runner.run(agent, prompt)` — runs the agent loop (model ⇄ tools) to a final
  answer.

## Where to take it next

- **More tools:** wrap any Python function with `@function_tool` (web lookups,
  DB queries, calling other relay endpoints like images or files).
- **Multiple agents:** the SDK supports handoffs between specialized agents and
  guardrails — see the official docs.
- **Expose it:** wrap `Runner.run` in a small FastAPI route if you want the
  agent reachable over HTTP too.
