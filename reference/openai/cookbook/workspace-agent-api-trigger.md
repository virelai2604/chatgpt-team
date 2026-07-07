---
source_id: oa_cookbook_workspace_agent_api_trigger
source_url: https://developers.openai.com/cookbook/examples/chatgpt/workspace_agents/workspace-agents-api-trigger
source_raw: https://raw.githubusercontent.com/openai/openai-cookbook/main/examples/chatgpt/workspace_agents/workspace-agents-api-trigger.ipynb
category: workspace_agent_cookbook
priority: P0
fetched: 2026-07-07
fetch_method: WebFetch of the raw .ipynb on GitHub (github is reachable).
pull_status: fetched
---

# Cookbook — Trigger a Workspace Agent from the API

Concrete example for triggering a Workspace Agent from a backend / automation
(stdlib only, no SDK needed).

## Core request (from the notebook)

```python
import json, urllib.request

API_BASE = "https://api.chatgpt.com/v1"

def trigger_workspace_agent(trigger_id: str, access_token: str,
                            payload: dict, idempotency_key: str) -> dict:
    url = f"{API_BASE}/workspace_agents/{trigger_id}/trigger"
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url, data=body, method="POST",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Idempotency-Key": idempotency_key,
        },
    )
    # ... urlopen(request) -> expect HTTP 202 Accepted, empty body
```

## Payload

```python
payload = {
    "input": "Summarize the customer escalation and recommend a response.",
    "conversation_key": "email_thread_abc",   # optional
}
```

## Key facts

- `trigger_id` is the `agtch_...` API-channel id.
- `access_token` is the **Workspace Agent access token**, not `OPENAI_API_KEY`.
- Success = **202 Accepted, no body** (async queue). No run id is returned; read
  results from the agent's configured output destination.
- Reuse the same `Idempotency-Key` to safely retry the same source event.

## For M-One / BIFL

Use this from n8n or a Render/WSL script to kick the `BIFL Index Reengineer`
Workspace Agent on a schedule or on an event (e.g. new marketplace reviews).
