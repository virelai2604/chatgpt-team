---
source_id: workspace_agent_auth
title: Workspace Agent Authentication (access tokens)
category: workspace_agent_auth
source_urls:
  - https://developers.openai.com/workspace-agents/authentication
  - https://developers.openai.com/workspace-agents
  - https://help.openai.com/en/articles/20001143-chatgpt-workspace-agents-for-enterprise-and-business
retrieved_at: 2026-07-16
fetch_method: web search (developers.openai.com returns HTTP 403 to automated fetch; NOT page-snapshotted)
pull_status: web_verified
docs_page_fetched: false
verify: open the source_urls in a browser, confirm the token flow + trigger endpoint, then set pull_status=fetched
---

# Workspace Agent Authentication

> Provenance: `web_verified` (2026-07-16). The official page
> `developers.openai.com/workspace-agents/authentication` returns **HTTP 403** to
> automated fetch, so this is a web-search summary — **not** a page snapshot.
> Open the source_urls in a browser and reconcile before treating any exact
> field/endpoint as durable. Token/scope details are security-sensitive; verify.

## The key distinction (why this exists)

- **Workspace Agent access token** → used to **trigger a published ChatGPT
  workspace agent**. Scoped to Workspace Agents API operations only.
- **Platform API key** (`OPENAI_API_KEY`, `sk-...`) → used for **general OpenAI
  API calls** (`api.openai.com`). NOT interchangeable with the agent token.

Keep them separate: an agent access token is **not** a substitute for the
platform key, and the platform key does **not** trigger workspace agents.

## Prerequisites (workspace admin)

Before a user can create a Workspace Agent access token, a **workspace admin**
must, in **Admin → Permissions & roles**:
1. Enable **Workspace agents**.
2. Turn on **"Allow users to create personal access tokens."**

## Create a token

In ChatGPT:
1. **Admin → Access tokens** → create an access token.
2. Select the **Workspace Agents** scope.
3. Copy the token and **store it in a secrets manager** (never in code/repo).

## Use the token (trigger a run)

Bearer credential against **`api.chatgpt.com`** (note: NOT `api.openai.com`):

```bash
curl https://api.chatgpt.com/v1/workspace_agents/<AGENT_ID>/trigger \
  -H "Authorization: Bearer $AGENT_ACCESS_TOKEN" \
  -H "content-type: application/json" \
  -d '{ ... input per the agent's input schema ... }'
```

- Token scope: **Workspace Agents API operations only**.
- Host: **`api.chatgpt.com`** (workspace agents) — distinct from `api.openai.com`.

## Relevance to this repo (ChatGPT Team Relay / BIFL)

- The relay's `OPENAI_API_KEY` (server-side) and `RELAY_KEY` (client-facing) are
  the **platform** side. A Workspace Agent access token is a **third, separate**
  credential — do not conflate it with either.
- If the relay or a backend triggers a published workspace agent, it must use a
  **Workspace Agent access token** against `api.chatgpt.com`, stored `sync:false`
  in Render (never committed), same discipline as the other secrets.

## Verify / TODO (to promote to `fetched`)

- Open the source_urls in a browser and confirm:
  - exact token-creation path and scope name,
  - the exact trigger endpoint host/path and request/response shape,
  - token lifetime/rotation and revocation behavior,
  - any idempotency / conversation_key semantics on trigger.
- Then set `pull_status: fetched` and `docs_page_fetched: true`.
