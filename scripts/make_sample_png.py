#!/usr/bin/env python3
"""
Create a deterministic RGBA PNG using only the Python standard library.

Default output: ./input.png
Default size: 256x256 (square), fully transparent

Why this exists:
- curl multipart tests (images/variations) require a real file path.
- We avoid external deps (Pillow) to keep the repo low-maintenance.
"""

from __future__ import annotations

import argparse
import os
import struct
import zlib
from dataclasses import dataclass
from pathlib import Path
from typing import Tuple


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


@dataclass(frozen=True)
class RGBA:
    r: int
    g: int
    b: int
    a: int

    def to_bytes(self) -> bytes:
        for v in (self.r, self.g, self.b, self.a):
            if not (0 <= v <= 255):
                raise ValueError(f"RGBA values must be 0..255; got {self!r}")
        return bytes([self.r, self.g, self.b, self.a])


def _chunk(chunk_type: bytes, data: bytes) -> bytes:
    """
    PNG chunk format:
      length (4 bytes, big-endian) + type (4 bytes) + data + crc (4 bytes)
    CRC is computed over type+data.
    """
    if len(chunk_type) != 4:
        raise ValueError("chunk_type must be 4 bytes (e.g., b'IHDR')")
    length = struct.pack(">I", len(data))
    crc = zlib.crc32(chunk_type)
    crc = zlib.crc32(data, crc)
    crc_bytes = struct.pack(">I", crc & 0xFFFFFFFF)
    return length + chunk_type + data + crc_bytes


def make_png_rgba_square(size: int, color: RGBA) -> bytes:
    """
    Create a PNG (color type 6 = RGBA, bit depth 8) of size x size.

    Image data uses filter type 0 on each scanline:
      scanline = b'\\x00' + (pixel_bytes * width)
    """
    if size <= 0:
        raise ValueError("size must be > 0")

    width = height = size

    # IHDR: width, height, bit_depth=8, color_type=6 (RGBA),
    # compression=0, filter=0, interlace=0
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)

    px = color.to_bytes()
    row = px * width  # width * 4 bytes
    raw = b"".join(b"\x00" + row for _ in range(height))  # add filter byte per row

    compressed = zlib.compress(raw, level=9)

    png = bytearray()
    png += PNG_SIGNATURE
    png += _chunk(b"IHDR", ihdr)
    png += _chunk(b"IDAT", compressed)
    png += _chunk(b"IEND", b"")
    return bytes(png)


def parse_rgba_hex(s: str) -> RGBA:
    """
    Accept:
      - RRGGBB  (assumes AA=FF)
      - RRGGBBAA
    """
    s = s.strip().lstrip("#")
    if len(s) == 6:
        r = int(s[0:2], 16)
        g = int(s[2:4], 16)
        b = int(s[4:6], 16)
        a = 255
        return RGBA(r, g, b, a)
    if len(s) == 8:
        r = int(s[0:2], 16)
        g = int(s[2:4], 16)
        b = int(s[4:6], 16)
        a = int(s[6:8], 16)
        return RGBA(r, g, b, a)
    raise ValueError("color must be RRGGBB or RRGGBBAA (optionally prefixed with #)")


def main() -> int:
    p = argparse.ArgumentParser(description="Generate a deterministic PNG for curl multipart testing.")
    p.add_argument("--out", default="input.png", help="Output PNG path (default: input.png)")
    p.add_argument("--size", type=int, default=256, help="Square image size (default: 256)")
    p.add_argument(
        "--color",
        default="00000000",
        help="RGBA hex as RRGGBB or RRGGBBAA (default: 00000000 transparent)",
    )
    p.add_argument("--force", action="store_true", help="Overwrite if the file exists")
    args = p.parse_args()

    out_path = Path(args.out).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if out_path.exists() and not args.force:
        print(f"Refusing to overwrite existing file: {out_path} (use --force)")
        return 2

    color = parse_rgba_hex(args.color)
    png_bytes = make_png_rgba_square(args.size, color)

    tmp_path = out_path.with_suffix(out_path.suffix + ".tmp")
    tmp_path.write_bytes(png_bytes)
    os.replace(tmp_path, out_path)

    print(f"Wrote: {out_path} ({args.size}x{args.size}, {len(png_bytes)} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
