# tests/test_models_files_vectorstores_sdk.py
#
# SDK-level integration tests that hit a *running* ChatGPT Team Relay
# using the official OpenAI Python client.
#
# IMPORTANT:
#   • These tests are true integrations; they should only run when:
#       - RUN_SDK_RELAY_TESTS=1
#       - A relay is running at RELAY_BASE_URL (or the default http://127.0.0.1:8080)
#   • In all other cases, they are skipped so the stubbed test suite can
#     run without any real network access.

import io
import os

import pytest
from openai import OpenAI

# ---------------------------------------------------------------------------
# Environment gating
# ---------------------------------------------------------------------------

RUN_SDK_RELAY_TESTS = os.getenv("RUN_SDK_RELAY_TESTS") == "1"

skip_if_not_relay = pytest.mark.skipif(
    not RUN_SDK_RELAY_TESTS,
    reason=(
        "SDK integration tests require RUN_SDK_RELAY_TESTS=1 "
        "and a running ChatGPT Team Relay (RELAY_BASE_URL or http://127.0.0.1:8080)."
    ),
)

# Default model aliases (override via env if desired)
TEST_MODEL = os.getenv("TEST_MODEL", "gpt-4o-mini")
TEST_EMBEDDING_MODEL = os.getenv("TEST_EMBEDDING_MODEL", "text-embedding-3-small")


def get_relay_client() -> OpenAI:
    """
    Build an OpenAI client pointing at the ChatGPT Team Relay.

    The relay itself is responsible for forwarding to https://api.openai.com.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY must be set in the environment for integration tests.")

    relay_base = os.getenv("RELAY_BASE_URL", "http://127.0.0.1:8080")
    # NOTE: for these SDK tests we include /v1 here so the SDK talks to the
    # relay's OpenAI-compatible base path.
    base_url = f"{relay_base.rstrip('/')}/v1"

    return OpenAI(
        api_key=api_key,
        base_url=base_url,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@skip_if_not_relay
@pytest.mark.integration
def test_models_list_via_relay():
    """
    Ensure /v1/models works end-to-end via the relay.

    This should return at least one model and no HTTP errors.
    """
    client = get_relay_client()

    resp = client.models.list()
    assert resp.data, "models.list returned empty data"

    first = resp.data[0]
    model_id = getattr(first, "id", None)
    assert isinstance(model_id, str) and model_id, "First model has no id"


@skip_if_not_relay
@pytest.mark.integration
def test_files_lifecycle_via_relay():
    """
    Full small lifecycle:
    - create a tiny text file
    - list files and ensure it's present
    - delete it
    """
    client = get_relay_client()

    # 1) Create file
    content = b"Hello from SDK relay file test."
    file_bytes = io.BytesIO(content)

    created = client.files.create(
        file=("relay_test.txt", file_bytes),
        purpose="user_data",
    )

    file_id = getattr(created, "id", None)
    assert isinstance(file_id, str) and file_id, "files.create did not return an id"

    # 2) List files and verify presence
    listed = client.files.list()
    ids = [getattr(f, "id", None) for f in listed.data]
    assert file_id in ids, "Uploaded file id not found in files.list"

    # 3) Delete file (cleanup)
    deleted = client.files.delete(file_id)
    deleted_id = getattr(deleted, "id", None)
    assert deleted_id == file_id or getattr(deleted, "deleted", True), \
        "files.delete did not indicate success"


@skip_if_not_relay
@pytest.mark.integration
def test_vector_store_create_retrieve_delete_via_relay():
    """
    Smoke test for /v1/vector_stores via the Python SDK & relay.

    - Create a small vector store
    - Retrieve it
    - Delete it
    """
    client = get_relay_client()

    # 1) Create vector store
    vs = client.vector_stores.create(name="pytest-relay-store")
    store_id = getattr(vs, "id", None)
    assert isinstance(store_id, str) and store_id, "vector_stores.create returned no id"

    # 2) Retrieve
    vs_get = client.vector_stores.retrieve(store_id)
    assert getattr(vs_get, "id", None) == store_id, "retrieve returned different id"

    # 3) Delete
    vs_del = client.vector_stores.delete(store_id)
    vs_del_id = getattr(vs_del, "id", None)
    assert vs_del_id == store_id or getattr(vs_del, "deleted", True), \
        "vector_stores.delete did not indicate success"
