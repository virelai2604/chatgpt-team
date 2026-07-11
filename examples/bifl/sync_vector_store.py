"""
Create (or reuse) an OpenAI Vector Store from distilled BIFL knowledge and print
the BIFL_VECTOR_STORE_ID to set in Render.

This is the piece that turns on /v1/bifl/search, /v1/bifl/fetch, and the
agent_pro.py FileSearchTool RAG path.

Upload DISTILLED knowledge (summaries, milestones, top-issue digests, reference
packs) — NOT all 380K raw chunks. File Search chunks + embeds server-side, so
prose files (.md / .txt / .pdf) work best.

Auth: reads OPENAI_API_KEY / OPENAI_BASE_URL from the environment.

Run:
    pip install "openai>=2.44,<3.0"
    export OPENAI_API_KEY="sk-..."             # your real key
    python sync_vector_store.py --name bifl_distilled \
        --files ./_exports/distilled_knowledge.md ./_markdown/*.md

Then paste the printed line into Render → Environment:
    BIFL_VECTOR_STORE_ID=vs_...
"""
from __future__ import annotations

import argparse
import glob
import os
import sys
from typing import List

from openai import OpenAI


def _expand(patterns: List[str]) -> List[str]:
    paths: List[str] = []
    for pat in patterns:
        matched = glob.glob(pat)
        paths.extend(matched if matched else ([pat] if os.path.isfile(pat) else []))
    # de-dupe, keep only real files
    seen, out = set(), []
    for p in paths:
        ap = os.path.abspath(p)
        if os.path.isfile(ap) and ap not in seen:
            seen.add(ap)
            out.append(ap)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="Create an OpenAI Vector Store from distilled knowledge.")
    ap.add_argument("--files", nargs="+", required=True,
                    help="files or globs of distilled docs (.md/.txt/.pdf/.jsonl)")
    ap.add_argument("--name", default="bifl_distilled", help="vector store name")
    ap.add_argument("--vector-store-id", default="",
                    help="reuse an existing vector store id instead of creating one")
    args = ap.parse_args()

    files = _expand(args.files)
    if not files:
        print("No files matched. Check --files paths/globs.", file=sys.stderr)
        raise SystemExit(1)
    print(f"[files] {len(files)} to upload")
    for f in files[:10]:
        print(f"   - {f}")
    if len(files) > 10:
        print(f"   … and {len(files) - 10} more")

    client = OpenAI()  # OPENAI_API_KEY / OPENAI_BASE_URL from env

    if args.vector_store_id:
        vs_id = args.vector_store_id
        print(f"[vector_store] reusing {vs_id}")
    else:
        vs = client.vector_stores.create(name=args.name)
        vs_id = vs.id
        print(f"[vector_store] created {vs_id} (name={args.name})")

    streams = [open(p, "rb") for p in files]
    try:
        batch = client.vector_stores.file_batches.upload_and_poll(
            vector_store_id=vs_id, files=streams
        )
    finally:
        for s in streams:
            s.close()

    print(f"[batch] status={batch.status}  counts={batch.file_counts}")
    if batch.status != "completed":
        print("WARNING: batch did not complete; check failed file_counts above.", file=sys.stderr)

    print("\n=== SET THIS IN RENDER (Environment tab) ===")
    print(f"BIFL_VECTOR_STORE_ID={vs_id}")
    print("\nAfter saving in Render (redeploys), test:")
    print('  curl https://ai.lafiel.me/v1/bifl/search -H "Authorization: Bearer <RELAY_KEY>" '
          '-H "content-type: application/json" -d \'{"query":"tire sealant complaints","limit":5}\'')


if __name__ == "__main__":
    main()
