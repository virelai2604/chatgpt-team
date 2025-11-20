#!/usr/bin/env python
"""
smoke_routes_local.py — Full local route/endpoint smoke test

Targets the local relay only (uvicorn on 127.0.0.1:8080 by default),
and exercises all major route groups:

  - /v1/health
  - /v1/tools
  - /actions/ping, /actions/relay_info
  - /v1/models, /v1/models/{id}
  - /v1/responses
  - /v1/embeddings
  - /v1/files (+ upload / retrieve / content / delete)
  - /v1/vector_stores/** (stores, files, file_batches)
  - /v1/images/generations
  - /v1/videos/**
  - /v1/realtime/sessions
  - /v1/conversations/**

Results are written to logs/smoke_routes_local_YYYYMMDD-HHMMSS.json.
"""

from __future__ import annotations

import json
import os
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, Tuple

import httpx


# ----------------------------------------------------------------------
# Config
# ----------------------------------------------------------------------

BASE_URL = os.getenv("TEST_API_BASE_URL", "http://127.0.0.1:8080").rstrip("/")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TIMEOUT = float(os.getenv("SMOKE_TIMEOUT", "60"))


def _auth_headers() -> Dict[str, str]:
    headers: Dict[str, str] = {
        "Content-Type": "application/json",
    }
    if OPENAI_API_KEY:
        headers["Authorization"] = f"Bearer {OPENAI_API_KEY}"
    return headers


def _clients() -> Tuple[httpx.Client, httpx.Client]:
    """
    Returns:
        (client_json, client_raw)

        client_json: default JSON client with Authorization + Content-Type
        client_raw:  no default headers (for multipart, etc.)
    """
    client_json = httpx.Client(
        base_url=BASE_URL,
        headers=_auth_headers(),
        timeout=TIMEOUT,
    )
    client_raw = httpx.Client(
        base_url=BASE_URL,
        timeout=TIMEOUT,
    )
    return client_json, client_raw


def _is_optional_capability_status(code: int) -> bool:
    """
    Some APIs (videos, realtime, sometimes images or beta endpoints)
    may not be enabled for all accounts. Treat 403/404 from those as
    "skipped" instead of hard failures.
    """
    return code in (401, 403, 404, 501)


# ----------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------

def test_health(client_json: httpx.Client) -> Dict[str, Any]:
    resp = client_json.get("/v1/health")
    resp.raise_for_status()
    data = resp.json()
    assert data.get("object") == "health", data
    assert data.get("status") == "ok", data
    return data


def test_tools(client_json: httpx.Client) -> Dict[str, Any]:
    resp = client_json.get("/v1/tools")
    resp.raise_for_status()
    data = resp.json()
    # Shape may be app-specific; just assert it's JSON.
    return {"status_code": resp.status_code, "keys": list(data.keys())}


def test_actions(client_json: httpx.Client) -> Dict[str, Any]:
    ping = client_json.get("/actions/ping")
    ping.raise_for_status()
    ping_data = ping.json()

    relay_info = client_json.get("/actions/relay_info")
    relay_info.raise_for_status()
    info_data = relay_info.json()

    assert ping_data.get("object") == "action.ping", ping_data
    assert info_data.get("object") == "relay.info", info_data

    return {
        "ping": ping_data,
        "relay_info": {
            "relay_name": info_data.get("relay_name"),
            "environment": info_data.get("environment"),
            "default_model": info_data.get("default_model"),
        },
    }


def test_models(client_json: httpx.Client) -> Dict[str, Any]:
    resp = client_json.get("/v1/models")
    resp.raise_for_status()
    data = resp.json()
    assert isinstance(data.get("data"), list) and data["data"], data
    first_id = data["data"][0].get("id")
    assert first_id, "No model id in first item"

    resp2 = client_json.get(f"/v1/models/{first_id}")
    resp2.raise_for_status()
    data2 = resp2.json()
    assert data2.get("id") == first_id, data2

    return {"count": len(data["data"]), "first_model_id": first_id}


def test_responses(client_json: httpx.Client) -> Dict[str, Any]:
    model = os.getenv("TEST_MODEL", "gpt-4.1-mini")
    payload = {
        "model": model,
        "input": "Say hello from smoke_routes_local (Responses).",
        "store": False,
    }
    resp = client_json.post("/v1/responses", json=payload)
    resp.raise_for_status()
    data = resp.json()
    return {
        "id": data.get("id"),
        "model": data.get("model"),
    }


def test_embeddings(client_json: httpx.Client) -> Dict[str, Any]:
    model = os.getenv("TEST_EMBEDDING_MODEL", "text-embedding-3-small")
    payload = {
        "model": model,
        "input": "Embedding smoke test via relay.",
    }
    resp = client_json.post("/v1/embeddings", json=payload)
    resp.raise_for_status()
    data = resp.json()
    assert data.get("data"), data
    dim = len(data["data"][0].get("embedding", []))
    return {"model": model, "dim": dim}


def test_files_and_vector_store(client_json: httpx.Client, client_raw: httpx.Client) -> Dict[str, Any]:
    results: Dict[str, Any] = {}

    # 1) List files
    resp_list = client_json.get("/v1/files")
    resp_list.raise_for_status()
    results["files_initial"] = len(resp_list.json().get("data", []))

    # 2) Upload a small text file via multipart/form-data
    with tempfile.NamedTemporaryFile("w+b", delete=False) as tmp:
        tmp.write(b"hello from smoke_routes_local\n")
        tmp.flush()
        tmp_name = tmp.name

    with open(tmp_name, "rb") as f:
        files = {
            "file": ("smoke_routes_local.txt", f, "text/plain"),
        }
        data = {"purpose": "assistants"}
        resp_upload = client_raw.post(
            "/v1/files",
            data=data,
            files=files,
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
        )

    resp_upload.raise_for_status()
    uploaded = resp_upload.json()
    file_id = uploaded.get("id")
    assert file_id, uploaded
    results["uploaded_file_id"] = file_id

    # 3) Retrieve metadata
    resp_meta = client_json.get(f"/v1/files/{file_id}")
    resp_meta.raise_for_status()
    meta = resp_meta.json()
    assert meta.get("id") == file_id

    # 4) Download content
    resp_content = client_json.get(f"/v1/files/{file_id}/content")
    resp_content.raise_for_status()
    # Not parsing; just ensure not empty.
    results["file_content_len"] = len(resp_content.content)

    # 5) Create vector store and attach file
    vs_payload = {
        "name": "smoke_routes_local_vs",
        "file_ids": [file_id],
    }
    resp_vs = client_json.post("/v1/vector_stores", json=vs_payload)
    resp_vs.raise_for_status()
    vs = resp_vs.json()
    vs_id = vs.get("id")
    assert vs_id, vs
    results["vector_store_id"] = vs_id

    # 6) List vector stores
    resp_vs_list = client_json.get("/v1/vector_stores")
    resp_vs_list.raise_for_status()
    vs_list = resp_vs_list.json()
    results["vector_stores_count"] = len(vs_list.get("data", []))

    # 7) File batches: create, retrieve, cancel
    batch_payload = {
        "file_ids": [file_id],
    }
    resp_batch = client_json.post(
        f"/v1/vector_stores/{vs_id}/file_batches",
        json=batch_payload,
    )
    resp_batch.raise_for_status()
    batch = resp_batch.json()
    batch_id = batch.get("id")
    results["file_batch_id"] = batch_id

    resp_batch_get = client_json.get(
        f"/v1/vector_stores/{vs_id}/file_batches/{batch_id}"
    )
    resp_batch_get.raise_for_status()

    # Cancel batch (DELETE)
    resp_batch_cancel = client_json.delete(
        f"/v1/vector_stores/{vs_id}/file_batches/{batch_id}"
    )
    resp_batch_cancel.raise_for_status()

    # 8) Delete vector store
    resp_vs_del = client_json.delete(f"/v1/vector_stores/{vs_id}")
    resp_vs_del.raise_for_status()
    del_payload = resp_vs_del.json()
    results["vector_store_deleted"] = del_payload.get("deleted", False)

    # 9) Delete file
    resp_del = client_json.delete(f"/v1/files/{file_id}")
    resp_del.raise_for_status()
    del_data = resp_del.json()
    results["file_deleted"] = del_data.get("deleted", False)

    return results


def test_images(client_json: httpx.Client) -> Dict[str, Any]:
    model = os.getenv("TEST_IMAGE_MODEL", "gpt-image-1")
    payload = {
        "model": model,
        "prompt": "Simple black-and-white checkmark icon.",
        "size": "512x512",
    }
    resp = client_json.post("/v1/images/generations", json=payload)
    if _is_optional_capability_status(resp.status_code):
        return {
            "skipped": True,
            "status_code": resp.status_code,
            "reason": "Images API not enabled for this key",
        }
    resp.raise_for_status()
    data = resp.json()
    return {
        "status_code": resp.status_code,
        "keys": list(data.keys()),
    }


def test_videos(client_json: httpx.Client) -> Dict[str, Any]:
    model = os.getenv("TEST_VIDEO_MODEL", "sora-2")
    payload = {
        "model": model,
        "prompt": "A red ball bouncing on a white floor.",
        "seconds": 2,
    }
    resp = client_json.post("/v1/videos", json=payload)
    if _is_optional_capability_status(resp.status_code):
        return {
            "skipped": True,
            "status_code": resp.status_code,
            "reason": "Video API not enabled for this key",
        }
    resp.raise_for_status()
    data = resp.json()
    return {
        "status_code": resp.status_code,
        "video_id": data.get("id"),
    }


def test_realtime(client_json: httpx.Client) -> Dict[str, Any]:
    model = os.getenv("TEST_REALTIME_MODEL", "gpt-4.1-realtime")
    payload = {"model": model}
    resp = client_json.post("/v1/realtime/sessions", json=payload)
    if _is_optional_capability_status(resp.status_code):
        return {
            "skipped": True,
            "status_code": resp.status_code,
            "reason": "Realtime API not enabled for this key",
        }
    resp.raise_for_status()
    data = resp.json()
    return {
        "status_code": resp.status_code,
        "session_id": data.get("id"),
    }


def test_conversations(client_json: httpx.Client) -> Dict[str, Any]:
    results: Dict[str, Any] = {}

    # 1) Create conversation (will proxy upstream and/or hit local CSV cache)
    create_payload = {
        "title": "smoke_routes_local conversation",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": "Hello from smoke test."}
                ],
            }
        ],
    }
    resp_create = client_json.post("/v1/conversations", json=create_payload)
    resp_create.raise_for_status()
    created = resp_create.json()
    conv_id = created.get("id")
    assert conv_id, created
    results["conversation_id"] = conv_id

    # 2) List conversations (may be upstream or local CSV list)
    resp_list = client_json.get("/v1/conversations")
    resp_list.raise_for_status()
    results["list_status_code"] = resp_list.status_code

    # 3) Retrieve conversation
    resp_get = client_json.get(f"/v1/conversations/{conv_id}")
    resp_get.raise_for_status()
    retrieved = resp_get.json()
    results["retrieve_title"] = retrieved.get("title")

    # 4) Update conversation
    update_payload = {"title": "smoke_routes_local conversation (updated)"}
    resp_update = client_json.post(f"/v1/conversations/{conv_id}", json=update_payload)
    resp_update.raise_for_status()
    updated = resp_update.json()
    results["updated_title"] = updated.get("title")

    # 5) Append message
    msg_payload = {
        "role": "user",
        "content": [{"type": "input_text", "text": "Second message."}],
    }
    resp_msg = client_json.post(
        f"/v1/conversations/{conv_id}/messages", json=msg_payload
    )
    resp_msg.raise_for_status()
    results["append_message_status"] = resp_msg.status_code

    # 6) Delete conversation (creates local tombstone if upstream fails)
    resp_del = client_json.delete(f"/v1/conversations/{conv_id}")
    resp_del.raise_for_status()
    del_data = resp_del.json()
    results["deleted_flag"] = del_data.get("deleted", True)

    return results


# ----------------------------------------------------------------------
# Runner
# ----------------------------------------------------------------------

def main() -> None:
    results: Dict[str, Any] = {
        "base_url": BASE_URL,
    }
    ok = True

    print(f"[smoke_routes_local] Using base URL: {BASE_URL}")

    client_json, client_raw = _clients()

    try:
        results["health"] = test_health(client_json)
        print("[smoke_routes_local] /v1/health OK")
    except Exception as exc:
        ok = False
        results["health_error"] = repr(exc)
        print(f"[smoke_routes_local] /v1/health ERROR: {exc!r}")

    try:
        results["tools"] = test_tools(client_json)
        print("[smoke_routes_local] /v1/tools OK")
    except Exception as exc:
        ok = False
        results["tools_error"] = repr(exc)
        print(f"[smoke_routes_local] /v1/tools ERROR: {exc!r}")

    try:
        results["actions"] = test_actions(client_json)
        print("[smoke_routes_local] /actions/* OK")
    except Exception as exc:
        ok = False
        results["actions_error"] = repr(exc)
        print(f"[smoke_routes_local] /actions/* ERROR: {exc!r}")

    try:
        results["models"] = test_models(client_json)
        print("[smoke_routes_local] /v1/models OK")
    except Exception as exc:
        ok = False
        results["models_error"] = repr(exc)
        print(f"[smoke_routes_local] /v1/models ERROR: {exc!r}")

    try:
        results["responses"] = test_responses(client_json)
        print("[smoke_routes_local] /v1/responses OK")
    except Exception as exc:
        ok = False
        results["responses_error"] = repr(exc)
        print(f"[smoke_routes_local] /v1/responses ERROR: {exc!r}")

    try:
        results["embeddings"] = test_embeddings(client_json)
        print("[smoke_routes_local] /v1/embeddings OK")
    except Exception as exc:
        ok = False
        results["embeddings_error"] = repr(exc)
        print(f"[smoke_routes_local] /v1/embeddings ERROR: {exc!r}")

    try:
        results["files_and_vector_store"] = test_files_and_vector_store(
            client_json, client_raw
        )
        print("[smoke_routes_local] /v1/files + /v1/vector_stores OK")
    except Exception as exc:
        ok = False
        results["files_and_vector_store_error"] = repr(exc)
        print(f"[smoke_routes_local] /v1/files + /v1/vector_stores ERROR: {exc!r}")

    try:
        results["images"] = test_images(client_json)
        if results["images"].get("skipped"):
            print("[smoke_routes_local] /v1/images/* SKIPPED:", results["images"])
        else:
            print("[smoke_routes_local] /v1/images/* OK")
    except Exception as exc:
        ok = False
        results["images_error"] = repr(exc)
        print(f"[smoke_routes_local] /v1/images/* ERROR: {exc!r}")

    try:
        results["videos"] = test_videos(client_json)
        if results["videos"].get("skipped"):
            print("[smoke_routes_local] /v1/videos/* SKIPPED:", results["videos"])
        else:
            print("[smoke_routes_local] /v1/videos/* OK")
    except Exception as exc:
        ok = False
        results["videos_error"] = repr(exc)
        print(f"[smoke_routes_local] /v1/videos/* ERROR: {exc!r}")

    try:
        results["realtime"] = test_realtime(client_json)
        if results["realtime"].get("skipped"):
            print("[smoke_routes_local] /v1/realtime/sessions SKIPPED:", results["realtime"])
        else:
            print("[smoke_routes_local] /v1/realtime/sessions OK")
    except Exception as exc:
        ok = False
        results["realtime_error"] = repr(exc)
        print(f"[smoke_routes_local] /v1/realtime/sessions ERROR: {exc!r}")

    try:
        results["conversations"] = test_conversations(client_json)
        print("[smoke_routes_local] /v1/conversations/* OK")
    except Exception as exc:
        ok = False
        results["conversations_error"] = repr(exc)
        print(f"[smoke_routes_local] /v1/conversations/* ERROR: {exc!r}")

    # Close clients
    client_json.close()
    client_raw.close()

    # Write log
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    ts = time.strftime("%Y%m%d-%H%M%S")
    out_path = logs_dir / f"smoke_routes_local_{ts}.json"
    out_path.write_text(json.dumps(results, indent=2), encoding="utf-8")

    status = "PASS" if ok else "FAIL"
    print(f"[smoke_routes_local] STATUS: {status}")
    print(f"[smoke_routes_local] Results logged to {out_path}")


if __name__ == "__main__":
    main()
