import binascii
import os
import struct
import zlib
from typing import Dict

import pytest
import requests

RELAY_BASE_URL = os.getenv("RELAY_BASE_URL", "http://localhost:8000").rstrip("/")
RELAY_TOKEN = os.getenv("RELAY_TOKEN", "")
DEFAULT_TIMEOUT_S = 20


def _auth_headers() -> Dict[str, str]:
    if not RELAY_TOKEN:
        pytest.skip("RELAY_TOKEN not set")
    return {"Authorization": f"Bearer {RELAY_TOKEN}"}


def _skip_if_no_real_key() -> None:
    # Integration tests tolerate 4xx from upstream but should not run
    # without a real OpenAI key behind the relay.
    if not os.getenv("INTEGRATION_OPENAI_API_KEY"):
        pytest.skip("INTEGRATION_OPENAI_API_KEY not set")


def _make_rgba_png_bytes(width: int, height: int, rgba=(0, 0, 0, 0)) -> bytes:
    """
    Create a minimal, valid RGBA PNG using only the standard library.
    Avoids committing binary fixtures and avoids pillow dependency.
    """
    r, g, b, a = rgba

    # Each row: filter byte (0) + width * RGBA bytes
    row = bytes([0]) + bytes([r, g, b, a]) * width
    raw = row * height
    compressed = zlib.compress(raw)

    def _chunk(chunk_type: bytes, data: bytes) -> bytes:
        crc = binascii.crc32(chunk_type + data) & 0xFFFFFFFF
        return struct.pack("!I", len(data)) + chunk_type + data + struct.pack("!I", crc)

    # IHDR: width, height, bit depth=8, color type=6 (RGBA), compression=0, filter=0, interlace=0
    ihdr = struct.pack("!IIBBBBB", width, height, 8, 6, 0, 0, 0)

    return (
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", ihdr)
        + _chunk(b"IDAT", compressed)
        + _chunk(b"IEND", b"")
    )


def test_openapi_has_images_variations_path() -> None:
    r = requests.get(f"{RELAY_BASE_URL}/openapi.json", timeout=DEFAULT_TIMEOUT_S)
    assert r.status_code == 200
    paths = r.json().get("paths", {})
    assert "/v1/images/variations" in paths, "missing /v1/images/variations in OpenAPI schema"


def test_images_variations_wiring_no_5xx(tmp_path) -> None:
    _skip_if_no_real_key()

    img_path = tmp_path / "input.png"
    img_path.write_bytes(_make_rgba_png_bytes(256, 256))

    # Use an intentionally invalid model to avoid billable generations while still
    # exercising multipart wiring end-to-end.
    data = {"model": "__invalid_model__", "n": "1", "size": "256x256"}
    files = {"image": ("input.png", img_path.read_bytes(), "image/png")}

    r = requests.post(
        f"{RELAY_BASE_URL}/v1/images/variations",
        headers=_auth_headers(),
        data=data,
        files=files,
        timeout=DEFAULT_TIMEOUT_S,
    )
    assert r.status_code < 500, r.text
