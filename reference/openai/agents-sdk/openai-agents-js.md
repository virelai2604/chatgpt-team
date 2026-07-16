---
source_id: gh_openai_agents_js
title: openai/openai-agents-js (Agents SDK for JS/TS)
category: agents_sdk_js
source_urls:
  - https://github.com/openai/openai-agents-js
  - https://raw.githubusercontent.com/openai/openai-agents-js/main/README.md
  - https://openai.github.io/openai-agents-js/
retrieved_at: 2026-07-16
fetch_method: WebFetch of the repo README on raw.githubusercontent.com (GitHub is fetchable)
pull_status: fetched
verify: version moves; check npm (@openai/agents) / package.json for the current release before pinning
---

# openai/openai-agents-js — Agents SDK (JS / TS)

> Provenance: `fetched` (2026-07-16) from the repo README (GitHub raw is fetchable).
> The JS/TS counterpart of `openai-agents-python`.

## What it is

A lightweight framework for building **multi-agent workflows** in JavaScript/
TypeScript. Works with OpenAI APIs and other providers.

## Install & runtime

```bash
npm install @openai/agents zod
```
- **Node.js 22+** (also **Deno** and **Bun**).
- **Experimental Cloudflare Workers** support (with `nodejs_compat`).
- Version moves fast — check npm / `package.json` for the current release before pinning.

## Core primitives

| Primitive | Purpose |
|---|---|
| **Agent** | LLM configured with instructions, tools, guardrails, handoffs |
| **Sandbox Agents** (beta) | Agent + filesystem workspace for longer-running work |
| **Realtime Agents** | Low-latency **voice** agents (tools, guardrails, conversation history) |
| **`run()`** | Execute an agent workflow |
| **Tools** | Actions agents can take — functions, **MCP**, hosted tools |
| **Handoffs / agents-as-tools** | Delegate tasks to other agents |
| **Guardrails** | Input/output safety validation |
| **Sessions** | Automatic conversation-history management |
| **Tracing** | Built-in run tracking/debugging |

(Same primitive set as the Python SDK — Agent/Runner/tools/handoffs/guardrails/
sessions/tracing — so patterns port across the two.)

## Minimal example

```js
import { Agent, run } from '@openai/agents';

const agent = new Agent({
  name: 'Assistant',
  instructions: 'You are a helpful assistant.',
});
const result = await run(agent, 'Write a haiku about recursion in programming.');
console.log(result.finalOutput);
```

## Relevance to this repo (ChatGPT Team Relay / BIFL)

- The **Node/TS** path for agents on the relay side (Render/Cloudflare/n8n),
  parallel to the Python examples (`examples/agents/*`).
- `FileSearchTool`-style hosted tools + MCP tools can point at the relay's
  `bifl.search`/`fetch`.
- **Custom `base_url`** (to route through `ai.lafiel.me/v1`) is **not** shown in the
  README — configure a custom OpenAI client / default client in code; confirm the
  exact API against the docs site before wiring.

## Verify / TODO

- Confirm current version + the custom-client/`base_url` API from
  `openai.github.io/openai-agents-js` when implementing.
