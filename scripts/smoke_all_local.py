#!/usr/bin/env python
import json
import os
import time
from pathlib import Path
from typing import Any, Dict

import httpx
from openai import OpenAI  # openai-python 2.x

def get_env(name: str, default: str | None = None) -> str:
    val = os.getenv(name, default)
    if val is None:
        raise RuntimeError(f"Required env var {name} is not set")
    return val

def make_http_client(base_url: str) -> httpx.Client:
    api_key = get_env("OPENAI_API_KEY")
    headers = {
        "Authorization": f"Bearer {api_key}",
    }
    return httpx.Client(base_url=base_url, headers=headers, timeout=120.0)

def test_health(base_url: str) -> Dict[str, Any]:
    with make_http_client(base_url) as client:
        r = client.get("/v1/health")
        r.raise_for_status()
        data = r.json()
        assert data.get("object") == "health", data
        assert data.get("status") == "ok", data
        return data

def test_models(client: OpenAI) -> Dict[str, Any]:
    models = client.models.list()
    assert models.data, "No models returned"
    first = models.data[0]
    model_id = getattr(first, "id", None)
    if model_id is None and isinstance(first, dict):
        model_id = first.get("id")
    if not model_id:
        raise TypeError(f"Cannot extract id from model: {type(first)}")
    return {"first_model_id": model_id}

def test_responses(client: OpenAI, model: str) -> Dict[str, Any]:
    resp = client.responses.create(
        model=model,
        input="Say hello from the ChatGPT Team Relay (Python smoke test).",
    )
    # Basic shape checks against Responses API spec
    # https://platform.openai.com/docs/api-reference/responses 
    assert getattr(resp, "id", None), resp
    output = getattr(resp, "output", None) or []
    assert output, resp
    first = output[0]
    content = getattr(first, "content", None) or []
    assert content, resp
    first_piece = content[0]
    # handle attr or dict
    piece_type = getattr(first_piece, "type", None) or (
        isinstance(first_piece, dict) and first_piece.get("type")
    )
    text = getattr(first_piece, "text", None) or (
        isinstance(first_piece, dict) and first_piece.get("text")
    )
    assert piece_type in {"output_text", "output_message", "message"}, resp
    assert text, resp
    return {"id": resp.id, "first_type": piece_type, "first_text_prefix": str(text)[:80]}

def test_embeddings(client: OpenAI, model: str) -> Dict[str, Any]:
    emb = client.embeddings.create(
        model=model,
        input="Embedding test via Python smoke.",
    )
    # https://platform.openai.com/docs/api-reference/embeddings 
    assert emb.data, emb
    first = emb.data[0]
    embedding = getattr(first, "embedding", None) or (
        isinstance(first, dict) and first.get("embedding")
    )
    assert isinstance(embedding, list) and embedding, emb
    return {"embedding_dim": len(embedding)}

def test_files(base_url: str) -> Dict[str, Any]:
    api_key = get_env("OPENAI_API_KEY")
    tmp_path = Path("tmp_smoke_file.txt")
    tmp_path.write_text("relay smoke file\n", encoding="utf-8")

    with httpx.Client(base_url=base_url, timeout=120.0) as client:
        # upload
        files = {
            "file": (tmp_path.name, tmp_path.read_bytes(), "text/plain"),
        }
        data = {"purpose": "assistants"}
        r = client.post(
            "/v1/files",
            headers={"Authorization": f"Bearer {api_key}"},
            files=files,
            data=data,
        )
        r.raise_for_status()
        file_obj = r.json()
        file_id = file_obj.get("id")

        # list
        r_list = client.get(
            "/v1/files",
            headers={"Authorization": f"Bearer {api_key}"},
        )
        r_list.raise_for_status()
        files_list = r_list.json().get("data", [])

    return {"uploaded_file_id": file_id, "files_count": len(files_list)}

def main() -> None:
    base = os.getenv("TEST_API_BASE_URL", os.getenv("RELAY_LOCAL_BASE", "http://127.0.0.1:8080"))
    api_key = get_env("OPENAI_API_KEY")
    test_model = os.getenv("TEST_MODEL", "gpt-4.1-mini")
    test_emb_model = os.getenv("TEST_EMBEDDING_MODEL", "text-embedding-3-small")

    print(f"[smoke_all] Using base URL: {base}")
    client = OpenAI(
        api_key=api_key,
        base_url=base,
    )

    ok = True
    results: Dict[str, Any] = {"base_url": base}

    try:
        results["health"] = test_health(base)
        print("[smoke_all] /v1/health OK")
    except Exception as exc:
        ok = False
        results["health_error"] = repr(exc)
        print(f"[smoke_all] /v1/health ERROR: {exc!r}")

    try:
        results["models"] = test_models(client)
        print("[smoke_all] /v1/models OK:", results["models"])
    except Exception as exc:
        ok = False
        results["models_error"] = repr(exc)
        print(f"[smoke_all] /v1/models ERROR: {exc!r}")

    try:
        results["responses"] = test_responses(client, test_model)
        print("[smoke_all] /v1/responses OK")
    except Exception as exc:
        ok = False
        results["responses_error"] = repr(exc)
        print(f"[smoke_all] /v1/responses ERROR: {exc!r}")

    try:
        results["embeddings"] = test_embeddings(client, test_emb_model)
        print("[smoke_all] /v1/embeddings OK")
    except Exception as exc:
        ok = False
        results["embeddings_error"] = repr(exc)
        print(f"[smoke_all] /v1/embeddings ERROR: {exc!r}")

    try:
        results["files"] = test_files(base)
        print("[smoke_all] /v1/files OK")
    except Exception as exc:
        ok = False
        results["files_error"] = repr(exc)
        print(f"[smoke_all] /v1/files ERROR: {exc!r}")

    # save log
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    ts = time.strftime("%Y%m%d-%H%M%S")
    out_path = logs_dir / f"smoke_all_{ts}.json"
    out_path.write_text(json.dumps(results, indent=2), encoding="utf-8")

    print(f"[smoke_all] Results logged to {out_path}")
    status = "PASS" if ok else "FAIL"
    print(f"[smoke_all] STATUS: {status}")

if __name__ == "__main__":
    main()
