from __future__ import annotations

from fastapi import APIRouter, Request, Response

from app.api.forward_openai import forward_openai_request

router = APIRouter(tags=["responses"])


#
# /v1/responses — thin proxy to upstream OpenAI-compatible API
# The behavior is intentionally simple:
#   - All endpoints delegate to forward_openai_request(...)
#   - For "pure local" tests, httpx.AsyncClient is stubbed in conftest.py,
#     so these become echo-style "test_proxy" responses.
#   - For httpx_mock-based forwarding tests, forward_openai_request uses
#     real httpx.AsyncClient, which pytest-httpx intercepts.
#


@router.post("/v1/responses")
async def create_response(request: Request) -> Response:
    """
    POST /v1/responses

    tests/test_responses_and_conversations.py expects:
      - HTTP 200
      - JSON with:
          object == "test_proxy"
          echo_path == "/v1/responses"
          echo_method == "POST"
      - forward_spy["json"] == payload (via stubbed AsyncClient)
    """
    return await forward_openai_request(request)


@router.get("/v1/responses")
async def list_responses(request: Request) -> Response:
    """
    GET /v1/responses

    Expected by tests to behave as a simple proxy (status + body passthrough).
    """
    return await forward_openai_request(request)


@router.get("/v1/responses/{response_id}")
async def retrieve_response(response_id: str, request: Request) -> Response:
    """
    GET /v1/responses/{response_id}

    Local path:  /v1/responses/{id}
    Upstream path: /v1/responses/{id}  (via forward_openai_request)
    """
    # forward_openai_request infers the upstream path from request.url.path
    # and rewrites /v1/... → /v1/... using _normalize_upstream_path internally.
    return await forward_openai_request(request)


@router.post("/v1/responses/{response_id}/cancel")
async def cancel_response(response_id: str, request: Request) -> Response:
    """
    POST /v1/responses/{response_id}/cancel

    tests/test_responses_and_conversations.py expects:
      - HTTP 200
      - JSON with:
          object == "test_proxy"
          echo_path == f"/v1/responses/{response_id}/cancel"
          echo_method == "POST"
    """
    return await forward_openai_request(request)
