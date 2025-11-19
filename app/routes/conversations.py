"""
conversations.py — /v1/conversations (plus local CSV cache)
────────────────────────────────────────────────────────────
Implements OpenAI Conversations endpoints with an optional local
CSV-based cache for resilience and offline listing.

Aligned with the official Conversations API surface (openai-python 2.8.x):
  • POST /v1/conversations                     → create
  • GET  /v1/conversations/{id}                → retrieve
  • POST /v1/conversations/{id}                → update
  • DELETE /v1/conversations/{id}              → delete
  • POST /v1/conversations/{id}/items          → items.create (wired from /messages)

We expose:
  • GET  /v1/conversations
  • POST /v1/conversations
  • GET  /v1/conversations/{id}
  • POST /v1/conversations/{id}
  • DELETE /v1/conversations/{id}
  • POST /v1/conversations/{id}/messages  (relays to upstream /items + local cache)
"""

import csv
import json
import os
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Optional, Tuple

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from app.utils.logger import relay_log as log

router = APIRouter(prefix="/v1/conversations", tags=["conversations"])

# IMPORTANT:
#  • OPENAI_API_BASE is the root ("https://api.openai.com"), WITHOUT /v1
#  • Paths below explicitly append /v1/conversations...
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_ORG_ID = os.getenv("OPENAI_ORG_ID", "")

RELAY_TIMEOUT = float(os.getenv("RELAY_TIMEOUT", "60"))

# CSV "append-only log" for local cache; respects your no-SQLite preference.
CONVERSATIONS_CSV = os.getenv("CONVERSATIONS_CSV", "data/conversations.csv")

USER_AGENT = os.getenv("RELAY_USER_AGENT", "chatgpt-team-relay/1.0")


# ─────────────────────────────
# Local CSV cache helpers
# ─────────────────────────────

def _csv_path() -> str:
    return CONVERSATIONS_CSV


def _ensure_csv_exists() -> None:
    path = _csv_path()
    directory = os.path.dirname(path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)

    if not os.path.exists(path):
        # Initialize with a simple header row.
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "data", "updated_at"])
        log.info(f"[Conversations] Initialized CSV cache at {path}")


def _append_snapshot(conv_id: str, data: Dict) -> None:
    """
    Append a new snapshot row for a conversation.

    We never update in place; we always append. The latest row for a given
    id (by updated_at) is treated as the current version.
    """
    _ensure_csv_exists()
    path = _csv_path()
    try:
        with open(path, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                conv_id,
                json.dumps(data),
                datetime.now(timezone.utc).isoformat(),
            ])
    except Exception as exc:
        log.warning(f"[Conversations] Failed to append snapshot to CSV: {exc}")


def _iter_rows() -> Iterable[Tuple[str, str, Dict]]:
    """
    Yield (conv_id, updated_at, payload) from the CSV cache.
    """
    path = _csv_path()
    if not os.path.exists(path):
        return []

    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            conv_id = row.get("id")
            updated_at = row.get("updated_at", "") or ""
            raw = row.get("data") or "{}"
            try:
                payload = json.loads(raw)
            except Exception:
                log.warning("[Conversations] Skipping corrupt JSON row in CSV cache")
                continue
            if not conv_id:
                continue
            yield conv_id, updated_at, payload


def save_conversation(conv_id: str, data: Dict) -> None:
    """
    Public helper: append a snapshot for a conversation.
    """
    if not conv_id:
        conv_id = data.get("id") or f"local-{datetime.now(timezone.utc).timestamp()}"
    _append_snapshot(conv_id, data)


def get_conversation(conv_id: str) -> Optional[Dict]:
    """
    Return the latest snapshot for a given conversation id from the CSV cache.
    """
    latest_payload: Optional[Dict] = None
    latest_ts: str = ""

    for cid, ts, payload in _iter_rows():
        if cid != conv_id:
            continue
        # Simple string comparison on ISO timestamps is safe when they are
        # consistently formatted.
        if ts >= latest_ts:
            latest_ts = ts
            latest_payload = payload

    return latest_payload


def list_conversations_local(limit: int = 50) -> List[Dict]:
    """
    Return up to `limit` conversation payloads, ordered by latest updated_at desc.
    """
    by_id: Dict[str, Tuple[str, Dict]] = {}

    for cid, ts, payload in _iter_rows():
        prev = by_id.get(cid)
        if prev is None or ts >= prev[0]:
            by_id[cid] = (ts, payload)

    sorted_items = sorted(
        by_id.items(),
        key=lambda kv: kv[1][0],  # updated_at
        reverse=True,
    )

    return [entry[1][1] for entry in sorted_items[:limit]]


# ─────────────────────────────
# Upstream helpers
# ─────────────────────────────

def build_headers() -> Dict[str, str]:
    """
    Build headers for upstream OpenAI /v1/conversations calls.

    Conversations API does not require an Assistants beta header;
    we just send standard auth + org.
    """
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY is not configured")

    headers: Dict[str, str] = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "User-Agent": USER_AGENT,
        "Content-Type": "application/json",
    }
    if OPENAI_ORG_ID:
        headers["OpenAI-Organization"] = OPENAI_ORG_ID
    return headers


def conversations_base_url() -> str:
    # https://api.openai.com + /v1/conversations
    return f"{OPENAI_API_BASE.rstrip('/')}/v1/conversations"


# ─────────────────────────────
# Routes
# ─────────────────────────────

@router.get("")
async def list_conversations():
    """
    GET /v1/conversations

    Primary: proxy to OpenAI Conversations list.
    Fallback: use local CSV cache.
    """
    headers = build_headers()
    url = conversations_base_url()

    async with httpx.AsyncClient(timeout=RELAY_TIMEOUT) as client:
        try:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200:
                return JSONResponse(resp.json(), status_code=200)
        except httpx.RequestError as e:
            log.warning(f"[Conversations] Online list failed: {e}, using local cache.")

    return JSONResponse(
        {"object": "list", "data": list_conversations_local()},
        status_code=200,
    )


@router.get("/{conv_id}")
async def retrieve_conversation(conv_id: str):
    """
    GET /v1/conversations/{id}
    """
    headers = build_headers()
    url = f"{conversations_base_url()}/{conv_id}"

    async with httpx.AsyncClient(timeout=RELAY_TIMEOUT) as client:
        try:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                save_conversation(conv_id, data)
                return JSONResponse(data, status_code=resp.status_code)
        except httpx.RequestError as e:
            log.warning(f"[Conversations] Online retrieve failed: {e}, falling back.")

    local = get_conversation(conv_id)
    if local:
        return JSONResponse(local, status_code=200)
    return JSONResponse({"error": "Conversation not found"}, status_code=404)


@router.post("")
async def create_conversation(request: Request):
    """
    POST /v1/conversations
    """
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON body"}, status_code=400)

    headers = build_headers()
    url = conversations_base_url()

    async with httpx.AsyncClient(timeout=RELAY_TIMEOUT) as client:
        try:
            resp = await client.post(url, headers=headers, json=body)
            if resp.status_code in (200, 201):
                data = resp.json()
                conv_id = data.get(
                    "id",
                    f"local-{datetime.now(timezone.utc).timestamp()}",
                )
                save_conversation(conv_id, data)
                return JSONResponse(data, status_code=resp.status_code)
        except httpx.RequestError as e:
            log.warning(f"[Conversations] Online create failed: {e}, saving locally.")

    conv_id = f"local-{datetime.now(timezone.utc).timestamp()}"
    data = {
        "id": conv_id,
        "title": body.get("title", "Untitled"),
        "messages": body.get("messages", []),
        "created": datetime.now(timezone.utc).isoformat(),
    }
    save_conversation(conv_id, data)
    return JSONResponse(data, status_code=201)


@router.post("/{conv_id}")
async def update_conversation(conv_id: str, request: Request):
    """
    POST /v1/conversations/{id} — update

    Mirrors client.conversations.update(conversation_id, **params).
    """
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON body"}, status_code=400)

    headers = build_headers()
    url = f"{conversations_base_url()}/{conv_id}"

    async with httpx.AsyncClient(timeout=RELAY_TIMEOUT) as client:
        try:
            resp = await client.post(url, headers=headers, json=body)
            if resp.status_code == 200:
                data = resp.json()
                save_conversation(conv_id, data)
                return JSONResponse(data, status_code=resp.status_code)
            else:
                log.warning(
                    f"[Conversations] Upstream update non-200 ({resp.status_code}), "
                    "falling back to local update."
                )
        except httpx.RequestError as e:
            log.warning(f"[Conversations] Online update failed: {e}, local-only update.")

    # Local fallback: merge into existing conversation or create a stub.
    existing = get_conversation(conv_id) or {"id": conv_id}
    if isinstance(body, dict):
        existing.update(body)
    existing.setdefault("updated", datetime.now(timezone.utc).isoformat())
    save_conversation(conv_id, existing)
    return JSONResponse(existing, status_code=200)


@router.delete("/{conv_id}")
async def delete_conversation(conv_id: str):
    """
    DELETE /v1/conversations/{id}
    """
    headers = build_headers()
    url = f"{conversations_base_url()}/{conv_id}"

    async with httpx.AsyncClient(timeout=RELAY_TIMEOUT) as client:
        try:
            resp = await client.delete(url, headers=headers)
            if resp.status_code in (200, 204):
                try:
                    payload = resp.json()
                except Exception:
                    payload = {"id": conv_id, "deleted": True}
                # Record a tombstone locally
                tombstone = {
                    "id": conv_id,
                    "deleted": True,
                    "deleted_at": datetime.now(timezone.utc).isoformat(),
                }
                save_conversation(conv_id, tombstone)
                return JSONResponse(payload, status_code=resp.status_code)
        except httpx.RequestError as e:
            log.warning(
                f"[Conversations] Online delete failed: {e}, marking tombstone locally."
            )

    # Offline tombstone if upstream fails completely
    tombstone = {
        "id": conv_id,
        "deleted": True,
        "deleted_at": datetime.now(timezone.utc).isoformat(),
    }
    save_conversation(conv_id, tombstone)
    return JSONResponse(tombstone, status_code=200)


@router.post("/{conv_id}/messages")
async def append_message(conv_id: str, request: Request):
    """
    POST /v1/conversations/{id}/messages

    Locally we keep the route name `/messages` for compatibility with the
    existing OpenAPI spec, but upstream we call the official Items API:
      POST /v1/conversations/{id}/items
    """
    try:
        msg = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON body"}, status_code=400)

    headers = build_headers()
    # Align with Items API upstream while keeping local route path `/messages`.
    url = f"{conversations_base_url()}/{conv_id}/items"

    async with httpx.AsyncClient(timeout=RELAY_TIMEOUT) as client:
        try:
            resp = await client.post(url, headers=headers, json=msg)
            if resp.status_code in (200, 201):
                data = resp.json()
                existing = get_conversation(conv_id) or {
                    "id": conv_id,
                    "messages": [],
                    "created": datetime.now(timezone.utc).isoformat(),
                }
                messages = existing.get("messages", [])
                messages.append(msg)
                existing["messages"] = messages
                save_conversation(conv_id, existing)
                return JSONResponse(data, status_code=resp.status_code)
        except httpx.RequestError as e:
            log.warning(f"[Conversations] Online append failed: {e}, local only.")

    # Pure local append fallback
    existing = get_conversation(conv_id) or {
        "id": conv_id,
        "messages": [],
        "created": datetime.now(timezone.utc).isoformat(),
    }
    messages = existing.get("messages", [])
    messages.append(msg)
    existing["messages"] = messages
    save_conversation(conv_id, existing)
    return JSONResponse(existing, status_code=200)
