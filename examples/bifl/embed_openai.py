"""
BIFL fast cloud embedder — OpenAI text-embedding-3-small.

Alternative to embed_bge_m3.py for when you want minutes instead of hours (e.g.
CPU-only Torch). Batched + concurrent embedding via the OpenAI API, writing into
a Chroma collection.

IMPORTANT — different vector space:
  OpenAI text-embedding-3-small = 1536 dims; bge-m3 = 1024 dims. They are NOT
  interchangeable. This writes a NEW collection (default: bifl_openai_3small)
  and re-embeds everything from the master. It does NOT touch bifl_bge_m3.

Auth: reads OPENAI_API_KEY and OPENAI_BASE_URL from the environment (your setup
already has both), so it goes through whatever that base URL is — your relay or
OpenAI directly.

Usage:
    python embed_openai.py \
        --jsonl chunks_all.jsonl \
        --chroma ./04_rag/chroma \
        --collection bifl_openai_3small \
        --concurrency 8 --batch-size 256
"""
from __future__ import annotations

import argparse
import asyncio
from typing import Dict, Iterator, List, Tuple

import orjson
from tqdm import tqdm


def iter_chunks(path: str, id_field: str, text_field: str) -> Iterator[Tuple[str, str, Dict]]:
    text_keys = {text_field, "text", "content", "chunk_text"}
    with open(path, "rb") as f:
        for raw in f:
            raw = raw.strip()
            if not raw:
                continue
            obj = orjson.loads(raw)
            cid = obj.get(id_field) or obj.get("chunk_id") or obj.get("id")
            text = next((obj[k] for k in text_keys if obj.get(k)), None)
            if not cid or not text:
                continue
            meta = {
                k: v
                for k, v in obj.items()
                if k not in text_keys and isinstance(v, (str, int, float, bool))
            }
            yield str(cid), str(text), meta


def existing_ids(collection) -> set:
    return set(collection.get(include=[]).get("ids", []))


async def _embed_batch(client, model, texts, dimensions, sem):
    async with sem:
        kwargs = {"model": model, "input": texts}
        if dimensions:
            kwargs["dimensions"] = dimensions
        resp = await client.embeddings.create(**kwargs)
        # API returns data in input order, but sort by index to be safe.
        data = sorted(resp.data, key=lambda d: d.index)
        return [d.embedding for d in data]


async def main_async(args) -> None:
    import chromadb
    from openai import AsyncOpenAI

    client = AsyncOpenAI(max_retries=5)  # inherits OPENAI_API_KEY / OPENAI_BASE_URL
    chroma = chromadb.PersistentClient(path=args.chroma)
    coll = chroma.get_or_create_collection(
        name=args.collection, metadata={"hnsw:space": "cosine"}
    )
    have = existing_ids(coll)
    print(f"[chroma] {coll.name}: {len(have)} vectors present — these are skipped")
    print(f"[model] {args.model}"
          + (f" @ {args.dimensions} dims" if args.dimensions else " @ 1536 dims"))

    # Build work list (new ids only, deduped within this run).
    ids: List[str] = []
    texts: List[str] = []
    metas: List[Dict] = []
    seen: set = set()
    approx_tokens = 0
    for cid, text, meta in iter_chunks(args.jsonl, args.id_field, args.text_field):
        if cid in have or cid in seen:
            continue
        seen.add(cid)
        ids.append(cid)
        texts.append(text)
        meta["n_chars"] = len(text)
        metas.append(meta)
        approx_tokens += len(text) // 4  # rough token estimate for cost preview
        if args.limit and len(ids) >= args.limit:
            break

    total = len(ids)
    if total == 0:
        print("Nothing to do — collection is already up to date.")
        return
    est_cost = approx_tokens / 1_000_000 * 0.02  # 3-small: $0.02 / 1M tokens
    print(f"[work] {total} new chunks (~{approx_tokens:,} tokens, est ~${est_cost:.2f})")

    bs = args.batch_size
    batches: List[Tuple[List[str], List[str], List[Dict]]] = [
        (ids[i:i + bs], texts[i:i + bs], metas[i:i + bs]) for i in range(0, total, bs)
    ]
    sem = asyncio.Semaphore(args.concurrency)
    pbar = tqdm(total=total, unit="chunk", desc="embedding")

    # Embed a window of batches concurrently, then write them to Chroma
    # sequentially (single-threaded, so no concurrent-write races).
    for w in range(0, len(batches), args.concurrency):
        window = batches[w:w + args.concurrency]
        vec_lists = await asyncio.gather(
            *[_embed_batch(client, args.model, b[1], args.dimensions, sem) for b in window]
        )
        for (bids, btexts, bmetas), vecs in zip(window, vec_lists):
            coll.add(
                ids=bids,
                embeddings=vecs,
                metadatas=bmetas,
                documents=btexts if args.store_documents else None,
            )
            pbar.update(len(bids))
    pbar.close()
    print(f"[done] embedded {total} chunks into {coll.name} (now {len(have) + total} total)")


def main() -> None:
    ap = argparse.ArgumentParser(description="Fast cloud embedder (OpenAI) for BIFL Chroma.")
    ap.add_argument("--jsonl", default="chunks_all.jsonl")
    ap.add_argument("--chroma", default="./04_rag/chroma")
    ap.add_argument("--collection", default="bifl_openai_3small")
    ap.add_argument("--model", default="text-embedding-3-small")
    ap.add_argument("--dimensions", type=int, default=0,
                    help="optional Matryoshka dim reduction, e.g. 1024 (0 = full 1536)")
    ap.add_argument("--batch-size", type=int, default=256, help="inputs per API request")
    ap.add_argument("--concurrency", type=int, default=8, help="concurrent requests")
    ap.add_argument("--id-field", default="chunk_id")
    ap.add_argument("--text-field", default="text")
    ap.add_argument("--store-documents", action="store_true")
    ap.add_argument("--limit", type=int, default=0, help="stop after N new chunks (0 = all)")
    args = ap.parse_args()
    args.dimensions = args.dimensions or None
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
