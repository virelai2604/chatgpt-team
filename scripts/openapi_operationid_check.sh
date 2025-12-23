#!/usr/bin/env bash
set -euo pipefail

RELAY_BASE_URL="${RELAY_BASE_URL:-${RELAY_BASE:-http://localhost:8000}}"

python3 - <<'PY'
import json
import os
import sys
import urllib.request

base = (os.environ.get("RELAY_BASE_URL") or os.environ.get("RELAY_BASE") or "http://localhost:8000").rstrip("/")
url = base + "/openapi.json"

with urllib.request.urlopen(url) as resp:
    spec = json.loads(resp.read().decode("utf-8"))

paths = spec.get("paths", {})
seen = {}
dupes = {}

for path, ops in paths.items():
    if not isinstance(ops, dict):
        continue
    for method, meta in ops.items():
        if method.lower() not in {"get","post","put","patch","delete","options","head"}:
            continue
        if not isinstance(meta, dict):
            continue
        op_id = meta.get("operationId")
        if not op_id:
            continue
        if op_id in seen:
            dupes.setdefault(op_id, []).append((method.upper(), path))
        else:
            seen[op_id] = (method.upper(), path)

if dupes:
    print("ERROR: duplicate operationId values detected:")
    for op_id in sorted(dupes):
        first = seen[op_id]
        all_occ = [first] + dupes[op_id]
        print(f"  - {op_id}:")
        for m, p in all_occ:
            print(f"      {m} {p}")
    sys.exit(1)

print("OK: no duplicate operationId values")
PY
