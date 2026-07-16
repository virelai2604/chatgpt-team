---
source_id: workspace_agent_auth
title: Workspace Agent Authentication (access tokens)
category: workspace_agent_auth
source_urls:
  - https://developers.openai.com/workspace-agents/authentication
  - https://developers.openai.com/workspace-agents
  - https://help.openai.com/en/articles/20001143-chatgpt-workspace-agents-for-enterprise-and-business
retrieved_at: 2026-07-16
fetch_method: Official page content provided verbatim via user browser 2026-07-16 (developers.openai.com returns HTTP 403 to automated fetch; content is the live page, not a web-search reconstruction)
pull_status: fetched
docs_page_fetched: true
verify: page-accurate as of 2026-07-16; token rotation/lifetime and idempotency/conversation_key are NOT on this page (see TODO)
---

# Workspace Agent Authentication

> Provenance: `fetched` (2026-07-16) — content is the **live official page**,
> supplied via browser because `developers.openai.com/.../authentication` 403s
> automated fetch. Verbatim specifics below.

## What it is

Workspace Agents API calls authenticate with **Workspace Agent access tokens**.
These tokens are **provisioned from the ChatGPT admin access-token flow** and are
**scoped for workspace use**.

## Provision a token

Prerequisite (workspace admin, in **Admin → Permissions & roles**): enable
**Workspace agents** and turn on **"Allow users to create personal access tokens."**

1. In ChatGPT, open **Admin → Access tokens**.
2. Create an access token and select the **Workspace Agents** scope.
3. Copy the token and **store it in your secrets manager**.

## Use the token (trigger a run)

Bearer credential on **`api.chatgpt.com`** (verbatim from the page):

```bash
curl https://api.chatgpt.com/v1/workspace_agents/agtch_complaints_123/trigger \
  -H "Authorization: Bearer $AGENT_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"input":"Summarize the newest escalation."}'
```

- Endpoint: `POST https://api.chatgpt.com/v1/workspace_agents/<AGENT_ID>/trigger`
  (agent id form e.g. `agtch_complaints_123`).
- Body: `{"input": "..."}`.

## What this token can access

Workspace Agent access tokens are **scoped to Workspace Agents API operations only**.

## Key distinction (agent token vs API key)

- **Workspace Agent access token** → trigger published workspace agents on
  `api.chatgpt.com`. Scoped to Workspace Agents ops only.
- **Platform API key** (`OPENAI_API_KEY`, `sk-...`) → general OpenAI API on
  `api.openai.com`. **Not interchangeable** with the agent token.

## Relevance to this repo (ChatGPT Team Relay / BIFL)

A Workspace Agent access token is a **third credential**, separate from the relay's
`OPENAI_API_KEY` (server-side) and `RELAY_KEY` (client-facing). If the relay/backend
triggers a published workspace agent, it uses the **agent token** against
`api.chatgpt.com`, stored `sync:false` in Render (never committed).

## Related (documented on the Trigger page, not here)

`conversation_key`, the `Idempotency-Key` header, the `202 Accepted` response, and
the `401/403/404/409` error codes live on the **Trigger workspace agent runs** page
→ see `workspace-agents/workspace-agent-trigger-runs.md`.

## Verify / TODO (genuinely not on either page)

- Token **lifetime / rotation / revocation** behavior (this auth page does not state it).
