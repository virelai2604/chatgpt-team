import os
import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Callable

import requests

try:
    import asyncio
    import websockets  # type: ignore
except ImportError:  # type: ignore
    asyncio = None
    websockets = None  # type: ignore


@dataclass
class E2EContext:
    base_url: str
    api_base: str
    relay_key: str
    test_model: str
    embedding_model: str
    image_model: str
    realtime_model: str

    # Chained IDs
    response_id: Optional[str] = None
    previous_response_id: Optional[str] = None
    conversation_id: Optional[str] = None
    conversation_item_id: Optional[str] = None
    file_id: Optional[str] = None
    upload_id: Optional[str] = None
    vector_store_id: Optional[str] = None
    vector_store_file_id: Optional[str] = None
    vector_store_file_batch_id: Optional[str] = None
    video_id: Optional[str] = None
    video_job_id: Optional[str] = None
    container_id: Optional[str] = None
    chatkit_session_id: Optional[str] = None
    chatkit_thread_id: Optional[str] = None

    # Misc
    debug: bool = False
    headers_cache: Dict[str, str] = field(default_factory=dict)


def log(msg: str) -> None:
    print(msg, flush=True)


def debug(ctx: E2EContext, msg: str) -> None:
    if ctx.debug:
        print(f"[DEBUG] {msg}", flush=True)


def make_headers(
    ctx: E2EContext,
    *,
    json_mode: bool = False,
    extra: Optional[Dict[str, str]] = None,
) -> Dict[str, str]:
    headers: Dict[str, str] = {
        "Authorization": f"Bearer {ctx.relay_key}",
    }
    if json_mode:
        headers["Content-Type"] = "application/json"
    if extra:
        headers.update(extra)
    return headers


def request(
    ctx: E2EContext,
    method: str,
    path: str,
    *,
    base: Optional[str] = None,
    json_body: Any = None,
    stream: bool = False,
    **kwargs: Any,
) -> requests.Response:
    url = (base or ctx.api_base).rstrip("/") + path
    headers = kwargs.pop("headers", {})
    if json_body is not None:
        headers = make_headers(ctx, json_mode=True, extra=headers)
        data = json.dumps(json_body)
        kwargs.setdefault("data", data)
    else:
        headers = make_headers(ctx, extra=headers)

    debug(ctx, f"{method} {url} headers={headers} kwargs={list(kwargs.keys())}")
    resp = requests.request(
        method,
        url,
        headers=headers,
        stream=stream,
        timeout=60,
        **kwargs,
    )
    debug(ctx, f"-> {resp.status_code}")
    return resp


def poll_until(
    ctx: E2EContext,
    description: str,
    method: str,
    path: str,
    *,
    check_fn: Callable[[Dict[str, Any]], bool],
    interval: float = 2.0,
    timeout: float = 60.0,
) -> bool:
    """
    Generic chain-wait helper: repeatedly call an endpoint until check_fn(json) is True
    or timeout is reached. Logs warnings; never raises.
    """
    log(f"Polling {description} at {path} (timeout={int(timeout)}s)...")
    start = time.time()
    while time.time() - start < timeout:
        resp = request(ctx, method, path)
        if resp.status_code != 200:
            log(f"[WARN] {description} poll failed: {resp.status_code} {resp.text}")
            return False
        try:
            data = resp.json()
        except Exception as exc:
            log(f"[WARN] {description} poll JSON error: {exc}")
            return False
        if check_fn(data):
            log(f"{description} completed.")
            return True
        time.sleep(interval)
    log(f"[WARN] {description} poll timed out after {int(timeout)}s")
    return False


# ---------- Core helpers ----------


def get_env_context() -> E2EContext:
    base_url = os.getenv("REST_BASE") or os.getenv("BASE_URL") or "http://127.0.0.1:8000"
    api_base = base_url.rstrip("/") + "/v1"

    relay_key = os.environ.get("RELAY_KEY") or os.environ.get("OPENAI_API_KEY") or ""
    if not relay_key:
        raise SystemExit("Missing RELAY_KEY or OPENAI_API_KEY environment variable")

    test_model = os.getenv("TEST_MODEL", "gpt-5.1-mini")
    embedding_model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    image_model = os.getenv("IMAGE_MODEL", "gpt-image-1")
    realtime_model = (
        os.getenv("REALTIME_MODEL")
        or os.getenv("RELAY_REALTIME_MODEL")
        or "gpt-realtime"
    )

    debug_flag = os.getenv("RELAY_E2E_DEBUG", "").lower() in {"1", "true", "yes"}

    return E2EContext(
        base_url=base_url,
        api_base=api_base,
        relay_key=relay_key,
        test_model=test_model,
        embedding_model=embedding_model,
        image_model=image_model,
        realtime_model=realtime_model,
        debug=debug_flag,
    )


# ---------- Sequential chain helpers ----------


def ensure_conversation(ctx: E2EContext) -> Optional[str]:
    if ctx.conversation_id:
        return ctx.conversation_id

    log("Creating conversation (chain root) ...")
    payload = {
        "title": "relay-e2e-conversation",
        "metadata": {"test": "relay_e2e_raw"},
    }
    resp = request(ctx, "POST", "/conversations", json_body=payload)
    if resp.status_code != 200:
        log(f"[WARN] Failed to create conversation: {resp.status_code} {resp.text}")
        return None
    data = resp.json()
    ctx.conversation_id = data.get("id")
    log(f"Conversation created: {ctx.conversation_id}")
    return ctx.conversation_id


def ensure_file(ctx: E2EContext) -> Optional[str]:
    if ctx.file_id:
        return ctx.file_id

    log("Uploading test file via /files ...")
    files = {
        "file": ("relay-e2e.txt", b"relay e2e content", "text/plain"),
    }
    data = {"purpose": "assistants"}
    resp = requests.post(
        ctx.api_base.rstrip("/") + "/files",
        headers=make_headers(ctx),
        files=files,
        data=data,
        timeout=60,
    )
    if resp.status_code != 200:
        log(f"[WARN] File upload failed: {resp.status_code} {resp.text}")
        return None
    body = resp.json()
    ctx.file_id = body.get("id")
    log(f"File uploaded: {ctx.file_id}")
    return ctx.file_id


def ensure_vector_store(ctx: E2EContext) -> Optional[str]:
    if ctx.vector_store_id:
        return ctx.vector_store_id

    log("Creating vector store ...")
    payload = {
        "name": "relay-e2e-vector-store",
        "metadata": {"test": "relay_e2e_raw"},
    }
    resp = request(ctx, "POST", "/vector_stores", json_body=payload)
    if resp.status_code != 200:
        log(f"[WARN] Failed to create vector store: {resp.status_code} {resp.text}")
        return None
    data = resp.json()
    ctx.vector_store_id = data.get("id")
    log(f"Vector store created: {ctx.vector_store_id}")
    return ctx.vector_store_id


# ---------- Core tests (strict) ----------


def test_health(ctx: E2EContext) -> None:
    log("== Health checks ==")
    # Use the relay-aware request helper so Authorization: Bearer <relay_key>
    # is always sent (RelayAuthMiddleware protects /health and /v1/health).
    for base in (ctx.base_url, ctx.api_base):
        resp = request(ctx, "GET", "/health", base=base)
        url = base.rstrip("/") + "/health"
        if resp.status_code != 200:
            raise AssertionError(
                f"Health check failed for {url}: {resp.status_code} {resp.text}"
            )
        try:
            data = resp.json()
        except Exception:
            raise AssertionError(f"Health check {url} did not return JSON: {resp.text}")
        if data.get("status") != "ok":
            raise AssertionError(f"Health check {url} unexpected body: {data}")
        log(f"Health OK at {url}")


def test_models(ctx: E2EContext) -> None:
    log("== Models list ==")
    resp = request(ctx, "GET", "/models")
    if resp.status_code != 200:
        raise AssertionError(f"/models failed: {resp.status_code} {resp.text}")
    body = resp.json()
    if body.get("object") != "list":
        raise AssertionError(f"/models unexpected object: {body.get('object')}")
    log(f"/models OK, {len(body.get('data', []))} models")


def _extract_responses_text(data: Dict[str, Any]) -> str:
    text_out = ""
    output = data.get("output") or data.get("choices")
    if isinstance(output, list):
        # New Responses output structure
        for item in output:
            if isinstance(item, dict):
                for part in item.get("content", []):
                    if isinstance(part, dict) and part.get("type") in {
                        "output_text",
                        "output_text_delta",
                    }:
                        txt = part.get("text") or part.get("delta") or ""
                        text_out += txt
    if not text_out and "choices" in data:
        # Chat Completions fallback
        try:
            text_out = data["choices"][0]["message"]["content"]
        except Exception:
            pass
    return text_out


def test_responses_chain(ctx: E2EContext) -> None:
    log("== Responses create + retrieve + chain ==")
    payload = {
        "model": ctx.test_model,
        "input": "Say exactly: relay-http-chain-ok",
        "store": True,
        "metadata": {"test": "relay_e2e_raw"},
    }
    resp = request(ctx, "POST", "/responses", json_body=payload)
    if resp.status_code != 200:
        raise AssertionError(f"/responses create failed: {resp.status_code} {resp.text}")
    data = resp.json()
    ctx.response_id = data.get("id")
    ctx.conversation_id = data.get("conversation") or ctx.conversation_id
    log(f"Response created: {ctx.response_id}, conversation: {ctx.conversation_id}")

    text_out = _extract_responses_text(data)
    if "relay-http-chain-ok" not in text_out:
        raise AssertionError(f"/responses create did not echo marker; got: {text_out!r}")

    # Retrieve by id
    if ctx.response_id:
        resp2 = request(ctx, "GET", f"/responses/{ctx.response_id}")
        if resp2.status_code != 200:
            raise AssertionError(f"/responses retrieve failed: {resp2.status_code} {resp2.text}")
        log("/responses retrieve OK")

        # List items (best effort)
        resp3 = request(ctx, "GET", f"/responses/{ctx.response_id}/items")
        if resp3.status_code == 200:
            log("/responses list-items OK")
        else:
            log(f"[WARN] /responses list-items failed: {resp3.status_code} {resp3.text}")

        # Input token counts (best effort)
        resp4 = request(ctx, "GET", f"/responses/{ctx.response_id}/input_token_counts")
        if resp4.status_code == 200:
            log("/responses input_token_counts OK")
        else:
            log(f"[WARN] /responses input_token_counts failed: {resp4.status_code} {resp4.text}")

    # Chain using previous_response_id if supported
    if ctx.response_id:
        log("Chaining second response using previous_response_id ...")
        payload2 = {
            "model": ctx.test_model,
            "input": "Answer with exactly: relay-http-chain-followup-ok",
            "previous_response_id": ctx.response_id,
        }
        resp5 = request(ctx, "POST", "/responses", json_body=payload2)
        if resp5.status_code == 200:
            data2 = resp5.json()
            ctx.previous_response_id = data2.get("id")
            text2 = _extract_responses_text(data2)
            if "relay-http-chain-followup-ok" in text2:
                log("Chained /responses previous_response_id OK")
            else:
                log(f"[WARN] Chained response missing marker: {text2!r}")
        else:
            log(f"[WARN] /responses chained create failed: {resp5.status_code} {resp5.text}")


def test_responses_stream_sse(ctx: E2EContext) -> None:
    log("== Responses streaming (SSE) ==")
    payload = {
        "model": ctx.test_model,
        "input": "Say exactly: relay-stream-ok",
        "stream": True,
    }
    headers = make_headers(ctx, json_mode=True, extra={"Accept": "text/event-stream"})
    url = ctx.api_base.rstrip("/") + "/responses"
    resp = requests.post(
        url,
        headers=headers,
        data=json.dumps(payload),
        stream=True,
        timeout=60,
    )
    if resp.status_code != 200:
        raise AssertionError(f"/responses stream failed: {resp.status_code} {resp.text}")

    full_text = ""
    for raw in resp.iter_lines(decode_unicode=True):
        if not raw:
            continue
        if raw.startswith("data:"):
            line = raw[len("data:") :].strip()
            if line == "[DONE]":
                break
            try:
                evt = json.loads(line)
            except Exception:
                continue
            evt_type = evt.get("type") or ""
            if evt_type == "response.output_text.delta":
                full_text += evt.get("delta") or ""
            elif evt_type == "response.output_text.done":
                full_text += (evt.get("text") or "").strip()
    if "relay-stream-ok" not in full_text:
        raise AssertionError(f"/responses SSE missing marker: {full_text!r}")
    log("Responses SSE OK")


def test_embeddings(ctx: E2EContext) -> None:
    log("== Embeddings ==")
    payload = {
        "model": ctx.embedding_model,
        "input": "relay embedding test",
    }
    resp = request(ctx, "POST", "/embeddings", json_body=payload)
    if resp.status_code != 200:
        raise AssertionError(f"/embeddings failed: {resp.status_code} {resp.text}")
    body = resp.json()
    embedding = None
    if isinstance(body.get("data"), list) and body["data"]:
        embedding = body["data"][0].get("embedding")
    elif "embedding" in body:
        embedding = body.get("embedding")
    if not isinstance(embedding, list) or not embedding:
        raise AssertionError("/embeddings returned empty embedding")
    log("/embeddings OK")


# ---------- Best-effort tests (do not fail core run) ----------


def test_conversations_chain(ctx: E2EContext) -> None:
    log("== Conversations (best-effort) ==")
    conv_id = ensure_conversation(ctx)
    if not conv_id:
        return

    # Retrieve
    resp = request(ctx, "GET", f"/conversations/{conv_id}")
    if resp.status_code == 200:
        log("/conversations retrieve OK")
    else:
        log(f"[WARN] /conversations retrieve failed: {resp.status_code} {resp.text}")

    # List items
    resp2 = request(ctx, "GET", f"/conversations/{conv_id}/items")
    if resp2.status_code == 200:
        items = resp2.json().get("data", [])
        log(f"/conversations list-items OK, {len(items)} items")
        if items:
            ctx.conversation_item_id = items[0].get("id")
    else:
        log(f"[WARN] /conversations list-items failed: {resp2.status_code} {resp2.text}")

    # Create item referencing previous_response_id in input text (chain by ID)
    payload = {
        "type": "message",
        "role": "user",
        "content": [
            {
                "type": "input_text",
                "text": f"Conversation chain check. Previous response id: {ctx.response_id}",
            }
        ],
    }
    resp3 = request(ctx, "POST", f"/conversations/{conv_id}/items", json_body=payload)
    if resp3.status_code == 200:
        data3 = resp3.json()
        ctx.conversation_item_id = data3.get("id") or ctx.conversation_item_id
        log("/conversations create-item OK")
    else:
        log(f"[WARN] /conversations create-item failed: {resp3.status_code} {resp3.text}")

    # Fetch item if we have an id
    if ctx.conversation_item_id:
        resp4 = request(ctx, "GET", f"/conversations/{conv_id}/items/{ctx.conversation_item_id}")
        if resp4.status_code == 200:
            log("/conversations retrieve-item OK")
        else:
            log(f"[WARN] /conversations retrieve-item failed: {resp4.status_code} {resp4.text}")


def test_files_and_vector_store_chain(ctx: E2EContext) -> None:
    log("== Files + Vector Stores (best-effort) ==")
    file_id = ensure_file(ctx)
    vs_id = ensure_vector_store(ctx)
    if not vs_id:
        return

    # Attach file to vector store via file_batches if supported
    if file_id:
        payload = {
            "file_ids": [file_id],
        }
        resp = request(
            ctx,
            "POST",
            f"/vector_stores/{vs_id}/file_batches",
            json_body=payload,
        )
        if resp.status_code == 200:
            body = resp.json()
            ctx.vector_store_file_batch_id = body.get("id") or ctx.vector_store_file_batch_id
            log("/vector_stores file_batches create OK")

            # Poll batch status if possible
            batch_id = ctx.vector_store_file_batch_id
            if batch_id:
                def _check_batch(d: Dict[str, Any]) -> bool:
                    status = d.get("status") or d.get("state")
                    return status in {"completed", "succeeded", "failed", "cancelled"}

                poll_until(
                    ctx,
                    "vector_store file_batch",
                    "GET",
                    f"/vector_stores/{vs_id}/file_batches/{batch_id}",
                    check_fn=_check_batch,
                    interval=2.0,
                    timeout=60.0,
                )
        else:
            log(f"[WARN] /vector_stores file_batches create failed: {resp.status_code} {resp.text}")

    # List vector stores
    resp2 = request(ctx, "GET", "/vector_stores")
    if resp2.status_code == 200:
        body2 = resp2.json()
        log(f"/vector_stores list OK, {len(body2.get('data', []))} stores")
    else:
        log(f"[WARN] /vector_stores list failed: {resp2.status_code} {resp2.text}")

    # List files for this vector store
    files_list: Optional[Dict[str, Any]] = None
    if vs_id:
        resp3 = request(ctx, "GET", f"/vector_stores/{vs_id}/files")
        if resp3.status_code == 200:
            files_list = resp3.json()
            log(f"/vector_stores files list OK, {len(files_list.get('data', []))} files")
        else:
            log(f"[WARN] /vector_stores files list failed: {resp3.status_code} {resp3.text}")

    # Retrieve and download first file in store, if any
    if vs_id and files_list and isinstance(files_list.get("data"), list) and files_list["data"]:
        first_file = files_list["data"][0]
        vs_file_id = first_file.get("id")
        ctx.vector_store_file_id = vs_file_id or ctx.vector_store_file_id
        if vs_file_id:
            resp4 = request(ctx, "GET", f"/vector_stores/{vs_id}/files/{vs_file_id}")
            if resp4.status_code == 200:
                log("/vector_stores files retrieve OK")
            else:
                log(f"[WARN] /vector_stores files retrieve failed: {resp4.status_code} {resp4.text}")

            resp5 = request(ctx, "GET", f"/vector_stores/{vs_id}/files/{vs_file_id}/content")
            if resp5.status_code == 200:
                log("/vector_stores files content OK")
            else:
                log(f"[WARN] /vector_stores files content failed: {resp5.status_code} {resp5.text}")


def test_uploads_best_effort(ctx: E2EContext) -> None:
    log("== Uploads (best-effort) ==")

    # Try listing uploads if supported
    resp_list = request(ctx, "GET", "/uploads")
    if resp_list.status_code == 200:
        try:
            body = resp_list.json()
            uploads = body.get("data", [])
            log(f"/uploads list OK, {len(uploads)} uploads")
        except Exception as exc:
            log(f"[WARN] /uploads list JSON error: {exc}")
    else:
        log(f"[WARN] /uploads list failed or unsupported: {resp_list.status_code} {resp_list.text}")

    # Try creating an upload in the simplest possible way
    payload = {
        "filename": "relay-e2e-upload.txt",
        "purpose": "assistants",
    }
    resp_create = request(ctx, "POST", "/uploads", json_body=payload)
    if resp_create.status_code in (200, 201):
        try:
            body_c = resp_create.json()
            ctx.upload_id = body_c.get("id") or ctx.upload_id
            log(f"/uploads create OK, upload_id={ctx.upload_id}")
        except Exception as exc:
            log(f"[WARN] /uploads create JSON error: {exc}")
    else:
        log(f"[WARN] /uploads create failed or unsupported: {resp_create.status_code} {resp_create.text}")


def test_images_and_stream(ctx: E2EContext) -> None:
    log("== Images (sync + stream best-effort) ==")
    # Basic generations: try /images/generations first, fall back to /images
    payload = {
        "model": ctx.image_model,
        "prompt": f"Minimalist icon with text 'relay-img-{int(time.time())}'",
        "size": "512x512",
        "response_format": "b64_json",
    }

    def _try_images(path: str) -> Optional[Dict[str, Any]]:
        resp = request(ctx, "POST", path, json_body=payload)
        if resp.status_code == 200:
            try:
                return resp.json()
            except Exception as exc:
                log(f"[WARN] {path} JSON parse error: {exc}")
        else:
            log(f"[WARN] {path} failed: {resp.status_code} {resp.text}")
        return None

    data = _try_images("/images/generations")
    if not data:
        data = _try_images("/images")

    if data:
        if isinstance(data.get("data"), list) and data["data"]:
            if data["data"][0].get("b64_json") or data["data"][0].get("url"):
                log("Image generation OK")
            else:
                log("[WARN] Image generation missing b64_json/url")
        else:
            log("[WARN] Image generation: unexpected data shape")

    # Image streaming endpoint (if relay/OpenAI supports it)
    payload_stream = {
        "model": ctx.image_model,
        "prompt": f"Streaming image test chained with response_id={ctx.response_id}",
    }
    headers = make_headers(ctx, json_mode=True, extra={"Accept": "text/event-stream"})
    url = ctx.api_base.rstrip("/") + "/image-stream"
    try:
        resp2 = requests.post(
            url,
            headers=headers,
            data=json.dumps(payload_stream),
            stream=True,
            timeout=60,
        )
    except Exception as exc:
        log(f"[WARN] /image-stream request error: {exc}")
        return

    if resp2.status_code != 200:
        log(f"[WARN] /image-stream failed: {resp2.status_code} {resp2.text}")
        return

    chunks = 0
    for raw in resp2.iter_lines(decode_unicode=True):
        if not raw:
            continue
        if raw.startswith("data:"):
            line = raw[len("data:") :].strip()
            if line == "[DONE]":
                break
            chunks += 1
    if chunks > 0:
        log(f"/image-stream OK, received {chunks} chunks")
    else:
        log("[WARN] /image-stream returned no chunks")


def test_moderations_best_effort(ctx: E2EContext) -> None:
    log("== Moderations (best-effort) ==")
    payload = {
        "model": "omni-moderation-latest",
        "input": "Relay moderation benign text.",
    }
    resp = request(ctx, "POST", "/moderations", json_body=payload)
    if resp.status_code == 200:
        log("/moderations OK")
    else:
        log(f"[WARN] /moderations failed: {resp.status_code} {resp.text}")


def test_batch_list_best_effort(ctx: E2EContext) -> None:
    log("== Batch list (best-effort) ==")
    resp = request(ctx, "GET", "/batches")
    if resp.status_code == 200:
        body = resp.json()
        log(f"/batches list OK, {len(body.get('data', []))} batches")
    else:
        log(f"[WARN] /batches list failed: {resp.status_code} {resp.text}")


def test_tools_and_actions_best_effort(ctx: E2EContext) -> None:
    log("== Tools + Actions (best-effort) ==")

    # /v1/tools
    resp_tools = request(ctx, "GET", "/tools")
    if resp_tools.status_code == 200:
        try:
            tools = resp_tools.json().get("tools") or resp_tools.json()
            log(f"/tools OK ({len(tools) if isinstance(tools, list) else 'object'})")
        except Exception as exc:
            log(f"[WARN] /tools JSON error: {exc}")
    else:
        log(f"[WARN] /tools failed: {resp_tools.status_code} {resp_tools.text}")

    # /v1/actions/ping
    resp_ping = request(ctx, "GET", "/actions/ping")
    if resp_ping.status_code == 200:
        log("/actions/ping OK")
    else:
        log(f"[WARN] /actions/ping failed: {resp_ping.status_code} {resp_ping.text}")

    # /v1/actions/relay_info
    resp_info = request(ctx, "GET", "/actions/relay_info")
    if resp_info.status_code == 200:
        log("/actions/relay_info OK")
    else:
        log(f"[WARN] /actions/relay_info failed: {resp_info.status_code} {resp_info.text}")


def test_videos_best_effort(ctx: E2EContext) -> None:
    log("== Videos (best-effort) ==")
    payload = {
        "model": "sora-2",
        "prompt": "Short abstract pattern for relay e2e video test.",
        "seconds": "4",
    }
    resp = request(ctx, "POST", "/videos", json_body=payload)
    if resp.status_code == 200:
        try:
            data = resp.json()
        except Exception as exc:
            log(f"[WARN] /videos create JSON error: {exc}")
            return
        ctx.video_id = data.get("id") or data.get("video_id") or ctx.video_id
        log(f"/videos create OK, video_id={ctx.video_id}, status={data.get('status')}")
    elif resp.status_code == 403:
        log(f"[WARN] /videos forbidden (likely no Sora access): {resp.text}")
        return
    else:
        log(f"[WARN] /videos create failed or unsupported: {resp.status_code} {resp.text}")
        return

    if ctx.video_id:
        resp2 = request(ctx, "GET", f"/videos/{ctx.video_id}")
        if resp2.status_code == 200:
            try:
                data2 = resp2.json()
                log(f"/videos retrieve OK, status={data2.get('status')}")
            except Exception as exc:
                log(f"[WARN] /videos retrieve JSON error: {exc}")
        else:
            log(f"[WARN] /videos retrieve failed: {resp2.status_code} {resp2.text}")


def test_containers_best_effort(ctx: E2EContext) -> None:
    log("== Containers (best-effort) ==")
    payload = {
        "name": "relay-e2e-container",
        "metadata": {"test": "relay_e2e_raw"},
    }
    resp = request(ctx, "POST", "/containers", json_body=payload)
    if resp.status_code == 200:
        try:
            data = resp.json()
            ctx.container_id = data.get("id") or ctx.container_id
            log(f"/containers create OK, container_id={ctx.container_id}")
        except Exception as exc:
            log(f"[WARN] /containers create JSON error: {exc}")
            return
    else:
        log(f"[WARN] /containers create failed or unsupported: {resp.status_code} {resp.text}")
        return

    # List containers
    resp2 = request(ctx, "GET", "/containers")
    if resp2.status_code == 200:
        try:
            body2 = resp2.json()
            log(f"/containers list OK, {len(body2.get('data', []))} containers")
        except Exception as exc:
            log(f"[WARN] /containers list JSON error: {exc}")
    else:
        log(f"[WARN] /containers list failed: {resp2.status_code} {resp2.text}")

    # Retrieve container
    if ctx.container_id:
        resp3 = request(ctx, "GET", f"/containers/{ctx.container_id}")
        if resp3.status_code == 200:
            log("/containers retrieve OK")
        else:
            log(f"[WARN] /containers retrieve failed: {resp3.status_code} {resp3.text}")

        # List files in container (may be empty)
        resp4 = request(ctx, "GET", f"/containers/{ctx.container_id}/files")
        if resp4.status_code == 200:
            try:
                body4 = resp4.json()
                log(f"/containers files list OK, {len(body4.get('data', []))} files")
            except Exception as exc:
                log(f"[WARN] /containers files list JSON error: {exc}")
        else:
            log(f"[WARN] /containers files list failed: {resp4.status_code} {resp4.text}")


def test_chatkit_best_effort(ctx: E2EContext) -> None:
    log("== ChatKit (best-effort) ==")

    # Try simple GET endpoints first to see if anything is wired up
    for path in ("/chatkit/sessions", "/chatkit/threads", "/chatkit"):
        resp = request(ctx, "GET", path)
        if resp.status_code == 200:
            log(f"{path} OK")
            break
        else:
            log(f"[WARN] {path} failed or unsupported: {resp.status_code} {resp.text}")

    # Try creating a session, if supported
    payload = {"metadata": {"test": "relay_e2e_raw"}}
    resp_create = request(ctx, "POST", "/chatkit/sessions", json_body=payload)
    if resp_create.status_code == 200:
        try:
            data = resp_create.json()
            session = data.get("session") or data
            ctx.chatkit_session_id = (
                session.get("id")
                or session.get("session_id")
                or ctx.chatkit_session_id
            )
            log(f"/chatkit/sessions create OK, session_id={ctx.chatkit_session_id}")
        except Exception as exc:
            log(f"[WARN] /chatkit/sessions create JSON error: {exc}")
    else:
        log(f"[WARN] /chatkit/sessions create failed or unsupported: {resp_create.status_code} {resp_create.text}")


def test_realtime_session_ws(ctx: E2EContext) -> None:
    log("== Realtime session WebSocket (best-effort) ==")
    if asyncio is None or websockets is None:
        log("[WARN] websockets or asyncio not available; skipping realtime WS test")
        return

    payload = {
        "model": ctx.realtime_model,
    }
    resp = request(ctx, "POST", "/realtime/sessions", json_body=payload)
    if resp.status_code != 200:
        log(f"[WARN] /realtime/sessions failed: {resp.status_code} {resp.text}")
        return
    data = resp.json()

    ws_url = (
        data.get("ws_url")
        or data.get("url")
        or (data.get("session") or {}).get("ws_url")
        or (data.get("session") or {}).get("url")
    )
    client_secret = (
        data.get("client_secret")
        or (data.get("session") or {}).get("client_secret")
    )
    if isinstance(client_secret, dict):
        client_secret = client_secret.get("value") or client_secret.get("secret")

    if not ws_url or not client_secret:
        log(f"[WARN] Missing ws_url or client_secret in realtime session payload: {data}")
        return

    async def _roundtrip() -> bool:
        async with websockets.connect(
            ws_url,
            extra_headers={"Authorization": f"Bearer {client_secret}"},
            max_size=16 * 1024 * 1024,
        ) as ws:
            event = {
                "type": "input_text",
                "text": "Say exactly: relay-ws-ok",
            }
            await ws.send(json.dumps(event))
            collected = ""
            start = time.time()
            while time.time() - start < 20:
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=5.0)
                except asyncio.TimeoutError:
                    break
                try:
                    evt = json.loads(msg)
                except Exception:
                    continue
                evt_type = evt.get("type")
                if evt_type == "response.output_text.delta":
                    collected += evt.get("delta") or ""
                elif evt_type == "response.output_text.done":
                    collected += (evt.get("text") or "").strip()
                elif evt_type and evt_type.startswith("response.completed"):
                    break
            return "relay-ws-ok" in collected

    try:
        ok = asyncio.run(_roundtrip())
    except Exception as exc:
        log(f"[WARN] Realtime WS error: {exc}")
        return

    if ok:
        log("Realtime WebSocket roundtrip OK")
    else:
        log("[WARN] Realtime WebSocket did not echo marker")


def main() -> int:
    ctx = get_env_context()
    log(f"Relay E2E RAW (sequential chain) against {ctx.api_base} using model={ctx.test_model}")

    # Core strict tests
    test_health(ctx)
    test_models(ctx)
    test_responses_chain(ctx)
    test_responses_stream_sse(ctx)
    test_embeddings(ctx)

    log("CORE TESTS PASSED (health + models + responses + SSE + embeddings).")

    # Best-effort tests (do not fail the run)
    test_conversations_chain(ctx)
    test_files_and_vector_store_chain(ctx)
    test_uploads_best_effort(ctx)
    test_images_and_stream(ctx)
    test_moderations_best_effort(ctx)
    test_batch_list_best_effort(ctx)
    test_tools_and_actions_best_effort(ctx)
    test_videos_best_effort(ctx)
    test_containers_best_effort(ctx)
    test_chatkit_best_effort(ctx)
    test_realtime_session_ws(ctx)

    log("E2E RAW (sequential chain) completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
