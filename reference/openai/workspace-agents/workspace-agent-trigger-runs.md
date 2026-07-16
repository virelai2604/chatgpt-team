---
source_id: oa_workspace_agents_trigger_runs
source_url: https://developers.openai.com/workspace-agents/trigger-runs
category: workspace_agent_api_trigger
priority: P0
fetched: 2026-07-16
fetch_method: Official page content provided verbatim via user browser 2026-07-16 (developers.openai.com returns HTTP 403 to automated fetch; content is the live page, superseding the 2026-07-07 cookbook reconstruction)
pull_status: fetched
docs_page_fetched: true
verify: page-accurate as of 2026-07-16; "retrieve agent responses" marked coming soon on the page
---

# Trigger Workspace Agent Runs

> Provenance: `fetched` (2026-07-16) — content is the **live official page**,
> supplied via browser because `developers.openai.com` 403s automated fetch.
> Supersedes the 2026-07-07 cookbook-reconstructed version.

## What it is

Programmatically trigger a **published** ChatGPT workspace agent via API — for
workflows where an **external system** needs to trigger an agent outside the
ChatGPT UI (and the third-party triggers offered).

## Endpoint

```
POST https://api.chatgpt.com/v1/workspace_agents/{id}/trigger
```

- `{id}` = the **stable public API trigger identifier** for the published API
  channel, in `agtch_XXX` format.

## Authentication

Bearer **Workspace Agent access token** (see `workspace-agent-authentication.md`):

```
Authorization: Bearer $AGENT_ACCESS_TOKEN
```

## Request body

```json
{
  "conversation_key": "email_thread_abc",
  "input": "Summarize the customer escalation and recommend a response."
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `input` | string | **Yes** | Message text passed to the agent as trigger input. |
| `conversation_key` | string | No | Caller-defined stable id to **continue the same agent conversation** across multiple trigger events. |

**Idempotency:** send an optional **`Idempotency-Key`** header to safely retry the
same event. Reuse the same key **only** when retrying the same event — a repeat
request with the same key returns the **original accepted outcome** instead of
enqueueing a second trigger.

## Response

- **`202 Accepted`**, **no response body**.
- The event is **durably queued**.
- **No public run ID** is returned, and the **agent response cannot currently be
  retrieved through the API** ("coming soon").

## Example

```bash
curl -i https://api.chatgpt.com/v1/workspace_agents/agtch_complaints_123/trigger \
  -X POST \
  -H "Authorization: Bearer $AGENT_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_key": "email_thread_abc",
    "input": "Summarize the newest escalation and recommend next steps."
  }'
# -> HTTP/1.1 202 Accepted
```

## Errors

| Status | When returned |
|---|---|
| `401 Unauthorized` | Bearer credential missing, expired, revoked, or invalid. |
| `403 Forbidden` | Token valid but not permitted to trigger the requested agent. |
| `404 Not Found` | `id` does not exist or is not visible to the caller's workspace. |
| `409 Conflict` | Channel/agent is not in a runnable state. |

## Relevance to this repo (ChatGPT Team Relay / BIFL)

If the relay/backend triggers a published workspace agent, it `POST`s to
`api.chatgpt.com/.../{id}/trigger` with a **Workspace Agent access token** (a
credential separate from `OPENAI_API_KEY`/`RELAY_KEY`). The agent `id` and token
belong in **env / Render `sync:false`** — never in code or the repo. The call is
fire-and-forget (`202`, no retrievable response yet), so don't block on a result.

## Verify / TODO

- Re-check when "retrieve agent responses" ships (currently "coming soon").
