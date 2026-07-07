---
source_id: oa_workspace_agents_trigger_runs
source_url: https://developers.openai.com/workspace-agents/trigger-runs
category: workspace_agent_api_trigger
priority: P0
fetched: 2026-07-07
fetch_method: developers.openai.com returns HTTP 403 to automated fetch; reconstructed from the official Cookbook notebook (fetched) + web search of the same docs.
pull_status: fetched
---

# Workspace Agents — Trigger runs (API)

Trigger a **published** Workspace Agent's API channel from your own code
(backend / n8n / scheduled job).

## Endpoint

```
POST https://api.chatgpt.com/v1/workspace_agents/{id}/trigger
```
- `{id}` = the API trigger id from the agent's **API channel**, format `agtch_...`.

## Headers

| Header | Value |
|---|---|
| `Authorization` | `Bearer <WORKSPACE_AGENT_ACCESS_TOKEN>` (NOT an OpenAI Platform API key) |
| `Content-Type` | `application/json` |
| `Idempotency-Key` | stable id for the source event, so retries don't double-fire |

## Request body

```json
{
  "input": "Summarize the customer escalation and recommend a response.",
  "conversation_key": "email_thread_abc"
}
```
- `input` (required) — plain-text message passed to the agent.
- `conversation_key` (optional) — caller-defined stable id to continue the same agent conversation.

## Response

- **`202 Accepted`, no body.** The run is **queued asynchronously**. The API does
  **not** return a run id and the agent's response **cannot** be retrieved
  through the API. Verify output at the agent's configured destination (Slack,
  Drive, etc.), keyed by a request id you put in the input.
- Errors: `401` invalid/expired token · `403` no permission · `404` trigger id
  unknown · `409` agent/API channel not runnable.

## BIFL notes

- Keep the **Workspace Agent access token separate** from `OPENAI_API_KEY`
  (different scope, secret-only).
- Because runs are fire-and-forget (202, no response), design for async: put a
  request id in `input`, then read the result from the destination.
