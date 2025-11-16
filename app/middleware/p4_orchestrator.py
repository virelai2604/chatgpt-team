# app/middleware/p4_orchestrator.py

import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.forward_openai import forward_openai_request

logger = logging.getLogger("uvicorn")


class P4OrchestratorMiddleware(BaseHTTPMiddleware):
    """
    P4OrchestratorMiddleware
    ────────────────────────
    Central policy router for the ChatGPT-Team relay.

    It decides, for each incoming HTTP request:

      • Should this be handled LOCALLY by FastAPI routes (your "value-add" surfaces)?
      • Or should this be FORWARDED to the upstream OpenAI API as a transparent proxy?

    Design (aligned with the current OpenAI REST API & SDKs):

    1) Local priority endpoints — "relay focus"
       These are the endpoints where the relay is expected to add long-term value:
       logging, auth, org-level policy, orchestration, or custom plumbing.

       They are *excluded* from upstream forwarding and must be implemented by
       FastAPI routes under app/api or app/routes:

         • /v1/tools
         • /v1/responses
         • /v1/conversations/**
         • /v1/files/**
         • /v1/vector_stores/**
         • /v1/embeddings
         • /v1/images/**
         • /v1/videos/**
         • /v1/realtime/**
         • /v1/health, /schemas, /actions

    2) Compat / passthrough endpoints — "SDK parity"
       Everything else under /v1/* is forwarded unchanged to OpenAI, preserving
       full compatibility with the official REST surface and SDKs. This includes,
       but is not limited to:

         • /v1/chat/completions
         • /v1/assistants/**
         • /v1/threads/**, /v1/runs/**, /v1/messages/**
         • /v1/moderations
         • /v1/fine_tuning/jobs/**
         • /v1/evals/**
         • /v1/batches/**
         • /v1/models   (you also have an optional local /v1/models router)
         • Any future /v1/* not explicitly claimed as local priority.
    """

    async def dispatch(self, request: Request, call_next):
        path = request.url.path or ""
        method = request.method

        # ------------------------------------------------------------
        # 1. Paths that are ALWAYS handled locally
        # ------------------------------------------------------------
        is_meta_local = (
            path.startswith("/v1/tools")      # local tools registry
            or path.startswith("/v1/health")  # relay healthcheck
            or path.startswith("/schemas")    # OpenAPI schema for ChatGPT Actions
            or path.startswith("/actions")    # custom ChatGPT Actions APIs
        )

        # Relay focus: where the relay adds value beyond vanilla OpenAI
        is_relay_focus = (
            path.startswith("/v1/responses")
            or path.startswith("/v1/conversations")
            or path.startswith("/v1/files")
            or path.startswith("/v1/vector_stores")
            or path.startswith("/v1/embeddings")
            or path.startswith("/v1/images")
            or path.startswith("/v1/videos")
            or path.startswith("/v1/realtime")
        )

        # Guard: avoid accidental double-prefixing like /v1/v1/responses
        has_double_prefix = path.startswith("/v1/v1/")

        excluded_from_forward = is_meta_local or is_relay_focus or has_double_prefix

        # ------------------------------------------------------------
        # 2. Forward or handle locally
        # ------------------------------------------------------------
        if path.startswith("/v1/") and not excluded_from_forward:
            # Compat / passthrough surface: let OpenAI handle it directly.
            logger.info(f"[P4] Forwarding upstream (compat): {method} {path}")
            return await forward_openai_request(request)

        # Everything else (non-/v1 or explicitly excluded) is handled locally.
        logger.info(f"[P4] Handling locally: {method} {path}")
        response = await call_next(request)
        return response
