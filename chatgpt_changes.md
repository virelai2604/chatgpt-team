# ChatGPT Sync
Repo: chatgpt-team
Base: origin/main
Base commit (merge-base): 7a82803fe44fd5fe56936c36bdc6f9a6e6b6c89b
Dirs: app tests static schemas src scripts/src
Root files: project-tree.md pyproject.toml chatgpt_sync.sh AGENTS.md __init__.py generate_tree.py
Mode: changes
Generated: 2026-01-01T06:52:40+07:00

## CHANGE SUMMARY (since 7a82803fe44fd5fe56936c36bdc6f9a6e6b6c89b, includes worktree)

```
M	app/routes/actions.py
```

## PATCH (since 7a82803fe44fd5fe56936c36bdc6f9a6e6b6c89b, includes worktree)

```diff
diff --git a/app/routes/actions.py b/app/routes/actions.py
index 6b120e5..91ce87d 100755
--- a/app/routes/actions.py
+++ b/app/routes/actions.py
@@ -161,9 +161,9 @@ async def system_info() -> JSONResponse:
         "environment": settings.ENVIRONMENT,
         "openai_api_base": settings.OPENAI_API_BASE,
         "default_model": settings.DEFAULT_MODEL,
-        "org_id": settings.OPENAI_ORG_ID,
-        "project_id": settings.OPENAI_PROJECT_ID,
-        "openai_beta": settings.OPENAI_BETA,
+        "openai_organization": settings.OPENAI_ORGANIZATION,
+        "openai_project": settings.OPENAI_PROJECT,
+        "openai_assistants_beta": settings.OPENAI_ASSISTANTS_BETA,
         "openai_realtime_beta": settings.OPENAI_REALTIME_BETA,
         "relay_auth_enabled": settings.RELAY_AUTH_ENABLED,
         "relay_auth_key_set": bool(settings.RELAY_KEY),
```

## CURRENT CONTENT OF CHANGED FILES (WORKTREE)

## FILE: app/routes/actions.py @ WORKTREE
```
# app/routes/actions.py

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.core.config import settings

router = APIRouter(tags=["actions"])


def _ping_payload() -> dict:
    """
    Canonical payload for ping-style endpoints.

    Tests assert at least:
      - data["status"] == "ok"            (for /actions/ping)
      - data["source"] == "chatgpt-team-relay"
      - data["app_mode"] non-empty
      - data["environment"] non-empty     (for /v1/actions/ping)
    """
    return {
        "source": "chatgpt-team-relay",
        "status": "ok",
        "app_mode": settings.APP_MODE,
        "environment": settings.ENVIRONMENT,
    }


def _relay_info_payloads() -> tuple[dict, dict]:
    """
    Build both the nested and flat relay-info payloads.

    Nested shape (for /v1/actions/relay_info):

        {
          "type": "relay.info",
          "relay": {
            "name": <relay_name>,
            "app_mode": <app_mode>,
            "environment": <environment>,
          },
          "upstream": {
            "base_url": <openai_base_url>,
            "default_model": <default_model>,
          },
        }

    Flat shape (for /actions/relay_info):

        {
          "relay_name": <relay_name>,
          "environment": <environment>,
          "app_mode": <app_mode>,
          "base_openai_api": <openai_base_url>,
        }

    The tests only assert that the relevant keys exist and are non-empty.
    """
    relay_name = settings.RELAY_NAME or "chatgpt-team-relay"
    app_mode = settings.APP_MODE
    environment = settings.ENVIRONMENT
    base_url = settings.OPENAI_API_BASE
    default_model = settings.DEFAULT_MODEL

    nested = {
        "type": "relay.info",
        "relay": {
            "name": relay_name,
            "app_mode": app_mode,
            "environment": environment,
        },
        "upstream": {
            "base_url": base_url,
            "default_model": default_model,
        },
    }

    flat = {
        "relay_name": relay_name,
        "environment": environment,
        "app_mode": app_mode,
        "base_openai_api": base_url,
    }

    return nested, flat


# ----- ping -----

@router.get("/actions/ping", summary="Simple local ping for tools/tests")
async def actions_ping_root() -> dict:
    """
    Simple ping at /actions/ping.

    tests/test_tools_and_actions_routes.py only checks that:
      - response.status_code == 200
      - response.json()["status"] == "ok"
    Extra fields are allowed.
    """
    return _ping_payload()


@router.get("/v1/actions/ping", summary="Local ping used by orchestrator tests")
async def actions_ping_v1() -> dict:
    """
    Ping under /v1/actions/ping.

    tests/test_actions_and_orchestrator.py requires:
      - status code 200
      - JSON contains non-empty source/status/app_mode/environment
    """
    return _ping_payload()


# ----- relay_info -----

@router.get("/actions/relay_info", summary="Flat relay info for tools")
async def actions_relay_info_root() -> dict:
    """
    Flat relay info at /actions/relay_info.

    tests/test_tools_and_actions_routes.py asserts:
      - data["relay_name"]
      - data["environment"]
      - data["app_mode"]
      - data["base_openai_api"]
    """
    _nested, flat = _relay_info_payloads()
    return flat


@router.get("/v1/actions/relay_info", summary="Structured relay info for orchestrator")
async def actions_relay_info_v1() -> dict:
    """
    Structured relay info at /v1/actions/relay_info.

    tests/test_actions_and_orchestrator.py asserts that:
      - data["type"] == "relay.info"
      - data["relay"]["name"] is non-empty
      - data["relay"]["app_mode"] is non-empty
      - data["relay"]["environment"] is non-empty
      - data["upstream"]["base_url"] is non-empty
      - data["upstream"]["default_model"] is non-empty
    """
    nested, _flat = _relay_info_payloads()
    return nested


@router.get("/actions/system/info", summary="Relay system info", include_in_schema=False)
async def system_info() -> JSONResponse:
    """
    Basic config info for debugging.

    NOTE: Not part of the official relay API; keep it local.
    """
    payload = {
        "relay_name": settings.RELAY_NAME,
        "app_mode": settings.APP_MODE,
        "environment": settings.ENVIRONMENT,
        "openai_api_base": settings.OPENAI_API_BASE,
        "default_model": settings.DEFAULT_MODEL,
        "openai_organization": settings.OPENAI_ORGANIZATION,
        "openai_project": settings.OPENAI_PROJECT,
        "openai_assistants_beta": settings.OPENAI_ASSISTANTS_BETA,
        "openai_realtime_beta": settings.OPENAI_REALTIME_BETA,
        "relay_auth_enabled": settings.RELAY_AUTH_ENABLED,
        "relay_auth_key_set": bool(settings.RELAY_KEY),
    }
    return JSONResponse(payload)
```

