#!/usr/bin/env python
"""
Smoke test for ChatGPT Team Relay (Render or local).

This script:
- Hits /v1/health over raw HTTP.
- Uses the OpenAI Python SDK (2.8.x+) pointed at the relay
  to exercise models, responses, files, embeddings, images,
  videos, and realtime sessions.

Environment variables:
- TEST_API_BASE_URL  : relay base URL (e.g. https://chatgpt-team-relay.onrender.com)
- TEST_OPENAI_API_KEY: any non-empty string; relay uses its own real key server-side.
- DEFAULT_MODEL      : model name used for responses/embeddings, default: gpt-4o-mini
"""

import os
import sys
import tempfile
from typing import Any, List

import httpx
from openai import OpenAI
from openai.types import Model

# --------------------------------------------------------------------------------------
# Config
# --------------------------------------------------------------------------------------

BASE_URL = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:8000")
TEST_API_KEY = os.environ.get("TEST_OPENAI_API_KEY", "dummy-key")
DEFAULT_MODEL = os.environ.get("DEFAULT_MODEL", "gpt-4o-mini")

HEALTH_URL = f"{BASE_URL}/v1/health"
MODELS_URL = f"{BASE_URL}/v1/models"

# SDK client configured to talk to the relay instead of api.openai.com directly
client = OpenAI(
    base_url=f"{BASE_URL}/v1",
    api_key=TEST_API_KEY,
)


# --------------------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------------------

def print_header(title: str) -> None:
    print(f"\n[{title}]".ljust(80, "="))


def safe_model_id(first: Any) -> str:
    """
    Extract a model id from either:
    - openai.types.Model instance (SDK 2.x)
    - dict returned from raw JSON
    Without triggering TypeError like: 'Model' object is not subscriptable.
    """
    # Preferred: attribute on SDK object
    if hasattr(first, "id"):
        return getattr(first, "id")

    # Fallback: dict-like
    if isinstance(first, dict) and "id" in first:
        return first["id"]

    raise TypeError(f"Cannot extract model id from object of type {type(first)}")


# --------------------------------------------------------------------------------------
# Individual tests
# --------------------------------------------------------------------------------------

def test_health_http() -> None:
    print_header("health via HTTP")
    with httpx.Client(timeout=10.0) as hclient:
        resp = hclient.get(HEALTH_URL)
        print(f"GET {HEALTH_URL} -> {resp.status_code}")
        resp.raise_for_status()
        print(resp.json())


def test_models() -> str:
    print_header("models list + retrieve via SDK")

    # List via SDK (proxied by relay)
    page = client.models.list()
    # page.data is List[Model]; iteration also yields Model objects
    models: List[Model] = list(page.data)

    if not models:
        raise RuntimeError("models.list() returned no models")

    first = models[0]
    model_id = safe_model_id(first)

    print(f"First model id: {model_id}")

    # Retrieve by id
    retrieved = client.models.retrieve(model_id)
    print(f"Retrieved model: {retrieved.id}")

    return model_id


def test_responses(model_id: str) -> None:
    print_header("responses.create via SDK")

    resp = client.responses.create(
        model=model_id or DEFAULT_MODEL,
        input="Say hello from the smoke test running through the relay.",
    )
    # SDK object; access fields directly
    print(f"response.id = {resp.id}")
    print(f"response.status = {resp.status}")
    first_msg = resp.output[0]
    text_piece = first_msg.content[0].text if first_msg.content else ""
    print(f"first message text: {text_piece!r}")


def test_files() -> None:
    print_header("files upload + list via SDK")

    # Create a small temp file
    with tempfile.NamedTemporaryFile("w+b", delete=False) as tmp:
        tmp.write(b"hello from smoke test\n")
        tmp.flush()
        tmp_name = tmp.name

    # Upload for assistants or user_data; either is fine for passthrough
    with open(tmp_name, "rb") as f:
        uploaded = client.files.create(
            file=f,
            purpose="assistants",
        )

    print(f"Uploaded file id: {uploaded.id}, filename: {uploaded.filename}")

    # List files
    listed = client.files.list()
    print(f"Total files: {len(listed.data)}")
    if listed.data:
        f0 = listed.data[0]
        print(f"First file from list: id={f0.id}, filename={f0.filename}")


def test_embeddings(model_id: str) -> None:
    print_header("embeddings.create via SDK")

    emb = client.embeddings.create(
        model="text-embedding-3-small",  # keep explicit and cheap
        input="Smoke test embedding through relay.",
    )
    vector = emb.data[0].embedding
    print(f"embedding length: {len(vector)}")


def test_images() -> None:
    print_header("images.generate via SDK")

    img = client.images.generate(
        model="gpt-image-1",
        prompt="A simple line drawing of a relay baton being passed between two robots.",
        size="512x512",
        n=1,
    )
    # The SDK returns base64 JSON or URLs depending on the model; we just check structure.
    print(f"images.generated: {len(img.data)}")
    print(f"first image keys: {list(img.data[0].dict().keys())}")


def test_videos() -> None:
    print_header("videos.generate via SDK")

    vid = client.videos.generate(
        model="gpt-video-1",
        prompt="A quick animated clip of a digital packet travelling through servers.",
    )
    # Again, just confirm we got an object back.
    print(f"video.id: {vid.id}")
    print(f"video.status: {getattr(vid, 'status', 'unknown')}")


def test_realtime_sessions() -> None:
    print_header("realtime.sessions.create via SDK")

    session = client.realtime.sessions.create(
        model=DEFAULT_MODEL,
    )
    print(f"realtime session id: {session.id}")


# --------------------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------------------

def main() -> None:
    print("=== ChatGPT Team Relay smoke test ===")
    print(f"BASE_URL      : {BASE_URL}")
    print(f"DEFAULT_MODEL : {DEFAULT_MODEL}")

    failures = []

    try:
        test_health_http()
    except Exception as e:
        failures.append(("health", e))

    model_id = ""
    try:
        model_id = test_models()
    except Exception as e:
        failures.append(("models", e))

    if model_id:
        try:
            test_responses(model_id)
        except Exception as e:
            failures.append(("responses", e))

    try:
        test_files()
    except Exception as e:
        failures.append(("files", e))

    try:
        test_embeddings(model_id or DEFAULT_MODEL)
    except Exception as e:
        failures.append(("embeddings", e))

    try:
        test_images()
    except Exception as e:
        failures.append(("images", e))

    try:
        test_videos()
    except Exception as e:
        failures.append(("videos", e))

    try:
        test_realtime_sessions()
    except Exception as e:
        failures.append(("realtime", e))

    if failures:
        print_header("FAILURES")
        for name, err in failures:
            print(f"- {name}: {repr(err)}")
        sys.exit(1)

    print_header("ALL GOOD")
    print("All smoke tests passed.")


if __name__ == "__main__":
    main()
