# tests/test_actions_request_bodies.py
"""Every Actions-exposed write operation must declare a request body.

Why this exists
---------------
The relay's write routes read the raw request body rather than declaring a
pydantic model, because it is a transparent proxy. That left nine operations in
`/openapi.actions.json` with no `requestBody` at all — including
`POST /v1/responses`, the endpoint `ai-plugin.json` tells models to prefer.

ChatGPT Actions builds the request from the schema. An operation with no
declared body gets called with no body, so those calls could only ever fail
upstream with a missing-parameter error, and nothing in the relay would show
why.

Schemas now come from `app/api/action_schemas.py`, derived from OpenAI's own
`api_reference/openapi.transformed.yml`. These tests pin that every write op
either declares a body or is one of the genuinely body-less cancel endpoints.
"""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from app.main import app

pytestmark = pytest.mark.unit

# POST endpoints that legitimately take no body: they act on the resource named
# in the path and have nothing else to say.
BODYLESS = {
    "POST /v1/actions/uploads/{upload_id}/cancel",
    "POST /v1/responses/{response_id}/cancel",
}


def _actions_doc() -> dict:
    with TestClient(app, base_url="https://ai.lafiel.me") as client:
        return client.get("/openapi.actions.json").json()


def _write_ops(doc: dict) -> list[tuple[str, dict]]:
    out = []
    for path, ops in doc.get("paths", {}).items():
        for method, op in ops.items():
            if method.lower() in {"post", "put", "patch"}:
                out.append((f"{method.upper()} {path}", op))
    return out


def test_every_actions_write_op_declares_a_request_body() -> None:
    ops = _write_ops(_actions_doc())
    assert ops, "Actions document exposes no write operations — did the filter break?"

    missing = sorted(name for name, op in ops if "requestBody" not in op and name not in BODYLESS)
    assert not missing, (
        "these operations are advertised to ChatGPT with no request body schema, "
        f"so the model cannot construct a call: {missing}"
    )


def test_the_primary_chat_endpoint_documents_model_and_input() -> None:
    """ai-plugin.json points models at /v1/responses; it must be callable."""
    doc = _actions_doc()
    schema = doc["paths"]["/v1/responses"]["post"]["requestBody"]["content"]["application/json"]["schema"]
    props = schema.get("properties", {})

    for field in ("model", "input"):
        assert field in props, f"/v1/responses must document `{field}` or the model cannot send one"

    # The relay does not validate bodies, so the schema must not imply it does.
    assert schema.get("additionalProperties") is True, (
        "the relay forwards unknown parameters untouched; the schema must say so, "
        "or callers will drop parameters OpenAI actually supports"
    )


def test_required_fields_match_the_official_spec() -> None:
    """`required` is load-bearing: it is what stops the model omitting a field."""
    doc = _actions_doc()

    embeddings = doc["paths"]["/v1/embeddings"]["post"]["requestBody"]["content"]["application/json"]["schema"]
    assert set(embeddings["required"]) == {"model", "input"}, "per CreateEmbeddingRequest"

    images = doc["paths"]["/v1/images/generations"]["post"]["requestBody"]["content"]["application/json"]["schema"]
    assert images["required"] == ["prompt"], "per CreateImageRequest"


def test_actions_document_stays_small_enough_to_import() -> None:
    """Inlining the upstream schemas verbatim would have made this unusable.

    Resolving CreateResponse's $ref graph pulls in 203 component schemas, ~141 KB
    for one operation. ChatGPT parses the whole document on import, so the
    compact hand-derived subsets are the point, not a shortcut.
    """
    size_kb = len(json.dumps(_actions_doc())) / 1024
    assert size_kb < 100, f"Actions document has grown to {size_kb:.0f} KB — did a full schema get inlined?"


def test_deprecated_sora_video_routes_are_not_advertised_to_chatgpt() -> None:
    """Sora shuts down in September; models must not be pointed at it.

    openai/openai-python@721cb1cd stamps `deprecated: true` on the video paths.
    The routes stay served for direct callers until the shutdown -- this only
    asserts they are absent from the Actions subset, not that they are gone.
    """
    doc = _actions_doc()
    advertised = sorted(p for p in doc.get("paths", {}) if "video" in p)
    assert not advertised, (
        f"deprecated Sora video paths are advertised to ChatGPT: {advertised}. "
        "Remove 'videos_actions' from actions_openapi_groups in _build_manifest()."
    )

    # ...but they must still be served, or this removed capability instead of an ad.
    with TestClient(app) as client:
        served = set(client.get("/openapi.json").json()["paths"])
    assert "/v1/videos" in served, "video routes should still work for direct callers"
