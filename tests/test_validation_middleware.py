import json
from typing import Any, Dict

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from app.middleware.validation import SchemaValidationMiddleware


def _dummy_app() -> FastAPI:
    app = FastAPI()

    @app.post("/echo")
    async def echo(request: Request) -> JSONResponse:
        body = await request.body()
        return JSONResponse({"echo_raw": body.decode("utf-8")})

    return app


def _build_client() -> TestClient:
    app = _dummy_app()
    app.add_middleware(SchemaValidationMiddleware)
    return TestClient(app)


def _post(client: TestClient, body: Any, content_type: str = "application/json"):
    return client.post(
        "/echo",
        data=body,
        headers={"Content-Type": content_type},
    )


def test_valid_json_passes_validation() -> None:
    client = _build_client()

    payload = {"foo": "bar"}
    resp = _post(client, json.dumps(payload))
    assert resp.status_code == 200
    data = resp.json()
    assert json.loads(data["echo_raw"]) == payload


def test_invalid_json_returns_400() -> None:
    client = _build_client()

    invalid_json = '{"foo": "bar"'  # missing closing }
    resp = _post(client, invalid_json)
    assert resp.status_code == 400

    data = resp.json()
    assert data["error"]["code"] == "invalid_json"
    assert "JSON decode error" in data["error"]["message"]


def test_multipart_form_is_allowed() -> None:
    client = _build_client()

    resp = client.post(
        "/echo",
        files={"file": ("test.txt", b"hello", "text/plain")},
    )
    # The middleware should not block multipart/form-data
    assert resp.status_code == 200
    data = resp.json()
    assert "hello" in data["echo_raw"]


def test_non_json_non_multipart_is_allowed_but_logged() -> None:
    client = _build_client()

    # For example, text/plain body
    resp = _post(client, "plain text body", content_type="text/plain")
    # Middleware doesn't enforce JSON here; it just lets it through.
    assert resp.status_code == 200
    data = resp.json()
    assert data["echo_raw"] == "plain text body"
