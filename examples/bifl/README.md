# BIFL indexing — fast batched embedders

Two ways to replace the slow Ollama embedding path (Layer 3, ~0.29 vec/s /
~15-day ETA). Pick by whether you have a GPU:

| Script | Model | Speed | When |
|---|---|---|---|
| `embed_openai.py` | OpenAI `text-embedding-3-small` (1536-dim) | **minutes, ~$2–3** | **Fastest** — best on CPU-only boxes; uses cloud |
| `embed_bge_m3.py` | `bge-m3` (1024-dim) via SentenceTransformer | minutes (GPU) / hours (CPU) | Fully offline; keeps your existing bge-m3 vectors |

> ⚠️ They use **different vector spaces** (1536 vs 1024) and therefore
> **separate Chroma collections** — never mix them. `embed_openai.py` writes a
> new collection and re-embeds all chunks; it does not reuse the bge-m3 vectors.

## `embed_openai.py` — the fastest method (recommended for CPU-only Torch)

Batched + concurrent OpenAI API calls. Reads `OPENAI_API_KEY` / `OPENAI_BASE_URL`
from your environment (so it goes through your relay or OpenAI directly).

```bash
python embed_openai.py \
    --jsonl chunks_all.jsonl \
    --chroma ./04_rag/chroma \
    --collection bifl_openai_3small \
    --concurrency 8 --batch-size 256
```

- Prints an estimated cost before running.
- **Resumable:** skips ids already in `bifl_openai_3small`.
- Speed knobs: raise `--concurrency` (e.g. 12–16) when hitting OpenAI directly;
  keep it ~8 if routing through the relay (Starter instance). Rate-limit 429s are
  retried automatically.
- `--dimensions 1024` optionally shrinks vectors (Matryoshka) for a smaller cache.

Do a timed `--limit 5000` run first to confirm throughput and cost, then run full.

---

## `embed_bge_m3.py` — offline path (same model, different runner)

`embed_bge_m3.py` embeds the **same** `bge-m3` model as your current setup, but
**batched** through `SentenceTransformer` + Torch, which is what turns days into
hours (or minutes on a GPU).

## Why this is faster (same model, different runner)

| | Old path | This script |
|---|---|---|
| Runner | Ollama (one chunk at a time) | SentenceTransformer (batched) |
| Rate | ~0.29 vec/s → ~15 days | hundreds/sec (GPU) / steady batch (CPU) |
| Model | bge-m3 (1024-dim, cosine) | **same** bge-m3 (1024-dim, cosine) |
| Vectors | — | **compatible** — existing ones are kept |

Because the model and normalization are identical, your already-embedded vectors
stay valid. The script **resumes**: it skips chunk_ids already in Chroma.

## Device

Auto-detects: **CUDA if an NVIDIA GPU is present, else CPU** (`torch.cuda.is_available()`).
No config needed. On CPU it defaults to a smaller encode batch (16); on GPU, 64.

## Requirements

Only libraries already in your pinned stack: `sentence-transformers`, `torch`,
`chromadb`, `tqdm`, `orjson`. Nothing new to install.

## Run

```bash
python embed_bge_m3.py \
    --jsonl   chunks_all.jsonl \
    --chroma  ./04_rag/chroma \
    --collection bifl_bge_m3
```

Common options:
- `--batch-size 64` — override the encode batch (default: 64 GPU / 16 CPU).
- `--limit 5000` — embed only the next N new chunks (good for a timed test).
- `--store-documents` — also store chunk text in Chroma (bigger cache; the text
  already lives in your master JSONL, so off by default).
- `--id-field` / `--text-field` — match your JSONL schema (defaults: `chunk_id`,
  `text`; it also falls back to `id`/`content`/`chunk_text`).

### First, a timed sanity check

```bash
python embed_bge_m3.py --jsonl chunks_all.jsonl --chroma ./04_rag/chroma \
    --collection bifl_bge_m3 --limit 2000
```

Time that, multiply out to your total remaining chunks, and you'll see the new
ETA (should be hours, not days). Then run again without `--limit` to finish.

## How it fits the pipeline

```
Layer 1 master (chunks_all.jsonl)  →  [this script, batched]  →  Layer 3 Chroma (bifl_bge_m3)
```

It reads from your durable source of truth and writes only into the rebuildable
Chroma cache — consistent with your "Chroma is NOT the master" rule. Safe to
re-run anytime; it only embeds what's missing.

> Tip: you can stop the old Ollama embedding process (PID 33396) once this run is
> underway — same collection, same vectors, just far faster.
