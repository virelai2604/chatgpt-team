# relay_client_example.py
from __future__ import annotations

import json
import os
import sys
from typing import Any, Dict, Optional

import requests


def _env(name: str, default: Optional[str] = None) -> str:
    v = os.getenv(name, default)
    if not v:
        raise RuntimeError(f"Missing required env var: {name}")
    return v


def _headers(relay_key: str) -> Dict[str, str]:
    # Your relay supports either X-Relay-Key or Authorization.
    # Choose ONE and keep it consistent with your OpenAPI / GPT Action auth scheme.
    return {
        "X-Relay-Key": relay_key,
        "Content-Type": "application/json",
    }


def get_manifest(base_url: str, relay_key: str) -> Dict[str, Any]:
    r = requests.get(f"{base_url}/manifest", headers=_headers(relay_key), timeout=30)
    r.raise_for_status()
    return r.json()


def create_response(base_url: str, relay_key: str, model: str, user_input: str) -> Dict[str, Any]:
    payload = {
        "model": model,
        "input": user_input,
        "stream": False,  # Actions-safe. SSE streaming is for non-Actions clients.
    }
    r = requests.post(
        f"{base_url}/v1/responses",
        headers=_headers(relay_key),
        data=json.dumps(payload),
        timeout=120,
    )
    r.raise_for_status()
    return r.json()


def main() -> int:
    base_url = _env("RELAY_BASE_URL", "http://localhost:8000").rstrip("/")
    relay_key = _env("RELAY_KEY", "dummy")
    model = os.getenv("RELAY_MODEL", "gpt-5.1")

    manifest = get_manifest(base_url, relay_key)
    print("=== /manifest (truncated) ===")
    # Print just the top-level keys to avoid huge output
    print("keys:", list(manifest.keys()))

    resp = create_response(base_url, relay_key, model, "Say hi in one sentence.")
    print("\n=== /v1/responses ===")
    print(json.dumps(resp, indent=2)[:4000])
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        raise
