#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import pathlib
import sys


# 1x1 transparent PNG, stable and tiny.
_TINY_PNG_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNgYAAAAAMAASsJTYQAAAAASUVORK5CYII="
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create a tiny deterministic PNG (1x1) for relay multipart tests."
    )
    parser.add_argument(
        "--out",
        default="input.png",
        help="Output path (default: ./input.png)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite output file if it already exists",
    )
    args = parser.parse_args()

    out_path = pathlib.Path(args.out)

    if out_path.exists() and not args.force:
        print(
            f"Refusing to overwrite existing file: {out_path} (use --force)",
            file=sys.stderr,
        )
        return 2

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(base64.b64decode(_TINY_PNG_B64))
    print(f"Wrote: {out_path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
