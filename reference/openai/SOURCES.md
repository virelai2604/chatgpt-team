# OpenAI Reference Catalog — pull priority

Durable index of official OpenAI sources to reference for the BIFL / Workspace
Agent / Apps-SDK / MCP project. This is a **catalog**, not vendored repos:
libraries are pinned via pip; docs/examples are referenced by URL; only specific
files are pulled into `reference/openai/` when offline durability is needed.

Machine-readable companion: `sources.json`.

## Top 10 docs to pull first

| Rank | Source | Purpose | DB category | URL |
|---:|---|---|---|---|
| 1 | Workspace Agents — Trigger runs | Canonical API trigger behavior for published Workspace Agents | `workspace_agent_api_trigger` | https://developers.openai.com/workspace-agents/trigger-runs |
| 2 | Workspace Agent API trigger (Cookbook) | Working API example for triggering agents from code | `workspace_agent_cookbook` | https://github.com/openai/openai-cookbook/blob/main/examples/chatgpt/workspace_agents/workspace-agents-api-trigger.ipynb |
| 3 | Workspace Agent access token / auth | Separate token from OPENAI_API_KEY; trigger-only scope | `workspace_agent_auth` | https://developers.openai.com/workspace-agents/authentication |
| 4 | Apps SDK — Build MCP server | Build the ai.lafiel.me MCP/API bridge + ChatGPT app tools | `apps_sdk_mcp` | https://developers.openai.com/apps-sdk/build/mcp-server |
| 5 | Apps SDK — MCP Apps in ChatGPT | Defines the ChatGPT app / MCP surface (UI, auth, state, deploy) | `chatgpt_apps` | https://developers.openai.com/apps-sdk/mcp-apps-in-chatgpt |
| 6 | OpenAI API — Skills (Tools) | Skill behavior and tool layer | `skills` | https://developers.openai.com/api/docs/guides/tools-skills |
| 7 | OpenAI — File Search | Hosted retrieval / Vector Store pattern for distilled knowledge | `file_search_vector_store` | https://developers.openai.com/api/docs/guides/tools-file-search |
| 8 | OpenAI Agents SDK | Agent workflow design, orchestration, results/state, evals | `agents_sdk` | https://developers.openai.com/api/docs/guides/agents |
| 9 | Codex / ChatGPT Sites | Public/demo/status pages only — never secret storage | `codex_sites` | https://developers.openai.com/codex |
| 10 | Codex Plugins / Build plugins | Current plugin examples (skills repo is deprecated) | `codex_plugins_skills` | https://github.com/openai/plugins |

## GitHub repos to reference (do NOT vendor whole)

| Rank | Repo | Why | Priority | How to use |
|---:|---|---|---|---|
| 1 | openai/openai-cookbook | Official examples & guides | P0 | Link; pull specific notebooks only |
| 2 | openai/plugins | Current Codex plugin examples (`.codex-plugin/plugin.json` + `skills/`) | P0 | Reference structure to package your tools |
| 3 | openai/skills | **Deprecated** — historical skill patterns; points to openai/plugins | P1 | Reference only; use plugins instead |
| 4 | openai/openai-node | JS/TS SDK (Render/Cloudflare/n8n) | P1 | `npm i openai` when needed |
| 5 | openai/openai-python | **Python SDK** (WSL scripts, embeddings, file search) | P1 | `pip install openai` (pinned 2.44) |
| 6 | openai/openai-openapi | API schema source for endpoint modeling | P2 | Reference for the relay's OpenAPI |
| 7 | openai/evals | Evaluation patterns / regression gates | P2 | Add later for quality gates |

## Rules (how to "pull" each type)

- **SDKs** (`openai-python`, `openai-node`) → pin in requirements / package.json. Never clone into the repo.
- **Docs** (developers.openai.com) → reference by URL. Optionally save a specific page to `reference/openai/<name>.md` with the fetch date.
- **Cookbook notebooks** → pull only the 3–5 you use into `reference/openai/cookbook/`, pinned to a commit.
- **Plugin/skill structure** → copy the `plugin.json` layout as a template; don't vendor the catalog.

> Status flags from the source list: `openai-python`, `openai-openapi`, `evals`
> were marked "not proven fetched" — treat as reference links until a specific
> file is actually pulled and checksummed here.
