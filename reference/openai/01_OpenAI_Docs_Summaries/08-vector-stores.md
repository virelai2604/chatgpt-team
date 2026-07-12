---
source_id: oa_docs_vector_stores
title: Vector Stores
category: openai_docs
source_urls:
  - https://platform.openai.com/docs/api-reference/vector-stores
  - https://github.com/openai/openai-openapi
  - https://github.com/openai/openai-python
fetched: 2026-07-12
fetch_method: curl of raw openai-openapi/master/openapi.yaml (81,040 lines) + WebSearch cross-check
pull_status: fetched
verify: Paths/schemas quoted from openapi.yaml lines 32393-34540 & 46937-73262; SDK surface confirmed via openai-python api.md + local sync_vector_store.py.
---

# Vector Stores

> Provenance: Endpoint paths and request schemas below are quoted directly from the official `openai/openai-openapi` `openapi.yaml` (fetched raw 2026-07-12); Python SDK method names cross-checked against `openai-python` and this repo's `examples/bifl/sync_vector_store.py`.

## What it is
Vector stores are server-managed containers of files that the `file_search` tool (and the Assistants / Responses APIs) query for retrieval-augmented generation. When files are attached, OpenAI chunks and embeds them server-side, so you upload prose (.md/.txt/.pdf) rather than pre-computed vectors. Objects are prefixed `vs_` (stores) and `vsfb_` (file batches).

## Endpoints (from openai-openapi, verified 2026-07-12)
Real paths and `operationId`s as they appear in the spec:

| Method | Path | operationId |
|---|---|---|
| GET  | `/vector_stores` | `listVectorStores` |
| POST | `/vector_stores` | `createVectorStore` |
| GET  | `/vector_stores/{vector_store_id}` | `getVectorStore` |
| POST | `/vector_stores/{vector_store_id}` | `modifyVectorStore` |
| DELETE | `/vector_stores/{vector_store_id}` | `deleteVectorStore` |
| POST | `/vector_stores/{vector_store_id}/file_batches` | `createVectorStoreFileBatch` |
| GET  | `/vector_stores/{vector_store_id}/file_batches/{batch_id}` | `getVectorStoreFileBatch` |
| POST | `/vector_stores/{vector_store_id}/file_batches/{batch_id}/cancel` | `cancelVectorStoreFileBatch` |
| GET  | `/vector_stores/{vector_store_id}/file_batches/{batch_id}/files` | `listFilesInVectorStoreBatch` |
| GET  | `/vector_stores/{vector_store_id}/files` | `listVectorStoreFiles` |
| POST | `/vector_stores/{vector_store_id}/files` | `createVectorStoreFile` |
| GET  | `/vector_stores/{vector_store_id}/files/{file_id}` | `getVectorStoreFile` |
| DELETE | `/vector_stores/{vector_store_id}/files/{file_id}` | `deleteVectorStoreFile` |
| POST | `/vector_stores/{vector_store_id}/files/{file_id}` | `updateVectorStoreFileAttributes` |
| GET  | `/vector_stores/{vector_store_id}/files/{file_id}/content` | `retrieveVectorStoreFileContent` |
| POST | `/vector_stores/{vector_store_id}/search` | `searchVectorStore` |

Base URL is `https://api.openai.com/v1` (spec examples call e.g. `.../v1/vector_stores/vs_abc123`). List endpoints take standard `limit`, `order`, `after`, `before` query params.

## Key params (expires_after, chunking_strategy, file batches)

**`CreateVectorStoreRequest`** (spec ~L46997) — all fields optional:
- `file_ids`: array of File IDs, `maxItems: 500`.
- `name`: string.
- `description`: string.
- `expires_after`: `VectorStoreExpirationAfter`.
- `chunking_strategy`: `oneOf` auto / static (only applies if `file_ids` non-empty; defaults to `auto`).
- `metadata`: `Metadata`.

**`VectorStoreExpirationAfter`** (L73240), `required: [anchor, days]`:
- `anchor`: enum, only `last_active_at`.
- `days`: integer, `minimum: 1`, `maximum: 365`.

**Chunking strategy** — `ChunkingStrategyRequestParam` is `oneOf`:
- `AutoChunkingStrategyRequestParam` (L39902): `{ "type": "auto" }`. Default; the spec states it "currently uses a `max_chunk_size_tokens` of `800` and `chunk_overlap_tokens` of `400`."
- `StaticChunkingStrategyRequestParam` (L71256): `{ "type": "static", "static": {...} }`. Inner `StaticChunkingStrategy` requires both:
  - `max_chunk_size_tokens`: integer, `minimum: 100`, `maximum: 4096`, default `800`.
  - `chunk_overlap_tokens`: integer, default `400`; "must not exceed half of `max_chunk_size_tokens`."

**`CreateVectorStoreFileBatchRequest`** (L46937): supply either `file_ids` (array, `minItems: 1`, `maxItems: 2000`) OR `files` (array of `{file_id, chunking_strategy?, attributes?}`, mutually exclusive with `file_ids`), plus optional batch-level `chunking_strategy` and `attributes`. Spec note: batches "reduce per-vector-store write request pressure" and are "recommended for multi-file ingestion."

**`UpdateVectorStoreRequest`** (modify, L72183): `name` (nullable), `expires_after` (nullable), `metadata`.

## Python SDK usage (client.vector_stores.* — confirm)
Confirmed via `openai-python` `api.md` and this repo's working script. Namespace is `client.vector_stores` (openai>=1.21 flattened it off the old `client.beta`):
```python
from openai import OpenAI
client = OpenAI()

vs = client.vector_stores.create(name="bifl_distilled")   # -> vs.id "vs_..."

batch = client.vector_stores.file_batches.upload_and_poll( # helper: upload + attach + poll
    vector_store_id=vs.id, files=[open(p, "rb") for p in paths]
)
# batch.status ("completed"/...), batch.file_counts
```
Related helpers on `client.vector_stores.file_batches`: `create()`, `create_and_poll()`, `retrieve()`, `cancel()`, `poll()`, `list_files()`. `upload_and_poll` is a convenience wrapper (uploads Files, then calls the `file_batches` create + poll loop).

## Relevance to this repo (sync_vector_store.py creates one; prints BIFL_VECTOR_STORE_ID)
`examples/bifl/sync_vector_store.py` is the exact ingestion path:
- `client.vector_stores.create(name=args.name)` → captures `vs.id` (line 74-76).
- `client.vector_stores.file_batches.upload_and_poll(vector_store_id=vs_id, files=streams)` uploads distilled `.md` knowledge (line 80-82).
- Prints `BIFL_VECTOR_STORE_ID=vs_...` to paste into Render env (line 92). That env var turns on `/v1/bifl/search`, `/v1/bifl/fetch`, and the `agent_pro.py` `FileSearchTool` RAG path.
- App-side route lives at `app/routes/vector_stores.py`; local cache at `data/vector_stores/vectors.db`.
- Doc string pins `openai>=2.44,<3.0` and reads `OPENAI_API_KEY` / `OPENAI_BASE_URL` from env.

## Verify / TODO
- Spec caps `file_ids` per store-create at 500 and file_batches at 2000; the older SDK helper docs sometimes cite 500 per batch — treat the spec's 2000 as authoritative but test large batches before relying on it.
- `expires_after.anchor` currently only supports `last_active_at`; no absolute-timestamp expiry.
- Vector store search (`POST /vector_stores/{id}/search`) exists in the spec but is not used by `sync_vector_store.py` (the repo queries via `file_search`/BIFL routes instead) — confirm whether direct search is wired anywhere.
- `platform.openai.com` / `developers.openai.com` were not fetchable (403); prose confirmations came from WebSearch of the OpenAI community + `openai-python` GitHub. Re-verify field defaults against live docs when access is restored.

Sources: [openai-openapi openapi.yaml](https://github.com/openai/openai-openapi), [openai-python api.md](https://github.com/openai/openai-python/blob/main/api.md), [OpenAI Retrieval guide](https://platform.openai.com/docs/guides/retrieval)
