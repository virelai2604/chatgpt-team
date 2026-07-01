"""
BIFL batched embedder — bge-m3 via SentenceTransformer (Torch).

Drop-in replacement for the slow one-at-a-time Ollama embedding path (Layer 3).
Reads chunks from the master JSONL, embeds with BAAI/bge-m3 in batches, and
writes vectors into the Chroma collection.

Key properties:
  - Device: CUDA if an NVIDIA GPU is available, else CPU (auto-detected).
  - Batched encode: the whole point — turns ~0.29 vec/s (Ollama, one-at-a-time)
    into hundreds/sec on GPU (or a steady CPU batch rate).
  - Resumable & idempotent: skips chunk_ids already present in Chroma, so it
    continues from wherever the previous run stopped (e.g. your 6,336).
  - Uses only libraries already in your pinned stack.

Same model + same normalization as your existing collection (bge-m3, 1024-dim,
cosine), so previously embedded vectors stay compatible — no re-embed needed.

Usage:
    python embed_bge_m3.py \
        --jsonl chunks_all.jsonl \
        --chroma ./04_rag/chroma \
        --collection bifl_bge_m3 \
        --batch-size 64            # omit to auto-pick (64 GPU / 16 CPU)
"""
from __future__ import annotations

import argparse
from typing import Dict, Iterator, List, Tuple

import orjson
from tqdm import tqdm


def detect_device() -> str:
    """Return 'cuda' if an NVIDIA GPU is available to Torch, else 'cpu'."""
    import torch  # imported lazily so --help works without Torch

    return "cuda" if torch.cuda.is_available() else "cpu"


def iter_chunks(path: str, id_field: str, text_field: str) -> Iterator[Tuple[str, str, Dict]]:
    """
    Yield (chunk_id, text, metadata) from a JSONL master file.

    Tolerant of common field names so it works with different chunk schemas.
    Metadata keeps only scalar fields (Chroma requires str/int/float/bool).
    """
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
    """Ids already in the Chroma collection (ids are always returned)."""
    return set(collection.get(include=[]).get("ids", []))


def main() -> None:
    ap = argparse.ArgumentParser(description="Batched bge-m3 embedder for BIFL Chroma.")
    ap.add_argument("--jsonl", default="chunks_all.jsonl")
    ap.add_argument("--chroma", default="./04_rag/chroma")
    ap.add_argument("--collection", default="bifl_bge_m3")
    ap.add_argument("--model", default="BAAI/bge-m3")
    ap.add_argument("--batch-size", type=int, default=0, help="0 = auto (64 GPU / 16 CPU)")
    ap.add_argument("--add-batch", type=int, default=512, help="chunks per Chroma write")
    ap.add_argument("--id-field", default="chunk_id")
    ap.add_argument("--text-field", default="text")
    ap.add_argument("--store-documents", action="store_true",
                    help="also store chunk text in Chroma (larger cache; text is in the master anyway)")
    ap.add_argument("--limit", type=int, default=0, help="stop after N new chunks (0 = all)")
    args = ap.parse_args()

    device = detect_device()
    bs = args.batch_size or (64 if device == "cuda" else 16)
    print(f"[device] {device}  [encode batch] {bs}")

    import chromadb
    from sentence_transformers import SentenceTransformer

    client = chromadb.PersistentClient(path=args.chroma)
    collection = client.get_or_create_collection(
        name=args.collection, metadata={"hnsw:space": "cosine"}
    )
    have = existing_ids(collection)
    print(f"[chroma] {collection.name}: {len(have)} vectors present — these are skipped")

    # Build the work list: only new chunk_ids (deduped within this run too).
    ids: List[str] = []
    texts: List[str] = []
    metas: List[Dict] = []
    seen = set()
    for cid, text, meta in iter_chunks(args.jsonl, args.id_field, args.text_field):
        if cid in have or cid in seen:
            continue
        seen.add(cid)
        ids.append(cid)
        texts.append(text)
        meta["n_chars"] = len(text)  # guarantee non-empty metadata for Chroma
        metas.append(meta)
        if args.limit and len(ids) >= args.limit:
            break

    total = len(ids)
    print(f"[work] {total} new chunks to embed")
    if total == 0:
        print("Nothing to do — Chroma is already up to date.")
        return

    print(f"[model] loading {args.model} on {device} ...")
    model = SentenceTransformer(args.model, device=device)

    buf_ids: List[str] = []
    buf_vecs: List[List[float]] = []
    buf_docs: List[str] = []
    buf_metas: List[Dict] = []

    def flush() -> None:
        if not buf_ids:
            return
        collection.add(
            ids=buf_ids,
            embeddings=buf_vecs,
            documents=buf_docs if args.store_documents else None,
            metadatas=buf_metas,
        )
        buf_ids.clear(); buf_vecs.clear(); buf_docs.clear(); buf_metas.clear()

    for start in tqdm(range(0, total, bs), desc="embedding", unit="batch"):
        sl = slice(start, start + bs)
        vecs = model.encode(
            texts[sl],
            batch_size=bs,
            normalize_embeddings=True,   # cosine space
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        buf_ids.extend(ids[sl])
        buf_vecs.extend(v.tolist() for v in vecs)
        buf_docs.extend(texts[sl])
        buf_metas.extend(metas[sl])
        if len(buf_ids) >= args.add_batch:
            flush()
    flush()

    print(f"[done] embedded {total} chunks into {collection.name} "
          f"(now {len(have) + total} total)")


if __name__ == "__main__":
    main()
