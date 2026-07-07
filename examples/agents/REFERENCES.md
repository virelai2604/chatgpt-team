# Agents — Official OpenAI references & coverage

Authoritative sources this agent work is built against, and how each official
concept maps to the examples in this folder.

## Official sources

| Source | What it is | Link |
|---|---|---|
| OpenAI Agents SDK (docs) | The framework guide: define/run agents, tools, handoffs, guardrails | https://developers.openai.com/api/docs/guides/agents |
| Agents SDK (Python API ref) | Python library reference | https://openai.github.io/openai-agents-python/ |
| OpenAI Cookbook — Agents | Worked examples & patterns | https://developers.openai.com/cookbook/topic/agents |
| Function calling guide | How tools/schemas work | https://developers.openai.com/api/docs/guides/function-calling |
| File search / RAG guide | Vector-store grounding | https://developers.openai.com/api/docs/guides/tools-file-search |
| OpenAI Developers — Agents | High-level learn hub | https://developers.openai.com/learn/agents |
| Skills → **Plugins** | `openai/skills` is deprecated; skills now live as **Codex plugins** | https://github.com/openai/plugins |

## Core concepts (official) → our examples

Per the Agents SDK docs, an agent *plans, calls tools, collaborates across
specialists, and keeps state within guardrails.* Coverage here:

| Concept | Official doc | `relay_agent.py` | `agent_pro.py` |
|---|---|---|---|
| Define + run an agent | guides/agents | ✅ | ✅ |
| **Function tools** (auto schema, Pydantic) | function-calling | ✅ `@function_tool` | ✅ |
| **Hosted tools** — file search (RAG) | tools-file-search | — | ✅ `FileSearchTool` |
| **Hosted tools** — web search | guides/agents | — | ✅ `WebSearchTool` |
| **Streaming** results | guides/agents/results | — | ✅ `Runner.run_streamed` |
| **Handoffs** (router → specialists) | guides/agents | ⬜ not yet | ⬜ not yet |
| **Guardrails** (parallel input checks, fail-fast) | guides/agents | ⬜ not yet | ⬜ not yet |
| Sessions / state | guides/agents/running-agents | ⬜ | ⬜ |

## Skills / Plugins note

The old `openai/skills` repo is **deprecated**. "Skills" (folders of
instructions + scripts an agent can discover) are now packaged as **Codex
plugins** under `openai/plugins`: a plugin has `.codex-plugin/plugin.json`, an
optional `.mcp.json`, and a `skills/` folder. This is the current path if you
want to package the M-One tools as a reusable, installable skill for Codex.

## Suggested next steps to fully match the official patterns

1. **Handoffs** — add a router agent that delegates to specialists (e.g.
   `ReviewMiner`, `ComplaintClassifier`, `KnowledgeQA`). Docs: guides/agents
   (handoffs).
2. **Guardrails** — add an input guardrail (e.g. reject non-M-One / unsafe
   requests) that runs in parallel and fails fast. Docs: guides/agents
   (guardrails).
3. **Package as a Codex plugin/skill** — wrap the tools per `openai/plugins`
   structure so the agent's capabilities are reusable across contexts.
