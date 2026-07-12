---
source_id: oa_docs_embeddings
title: Embeddings
category: openai_docs
source_urls:
  - https://platform.openai.com/docs/guides/embeddings
  - https://github.com/openai/openai-openapi
  - https://github.com/openai/openai-cookbook
fetched: 2026-07-12
fetch_method: Fetched openai-openapi openapi.yaml (raw.githubusercontent.com, master) for the /embeddings path + CreateEmbeddingRequest params; model names, dimensions, pricing, and the Matryoshka/dimensions behavior web-searched (platform.openai.com guide is 403-blocked to automated fetches).
pull_status: web_verified
verify: curl -sS https://raw.githubusercontent.com/openai/openai-openapi/master/openapi.yaml | grep -nA2 'CreateEmbeddingRequest'  # then re-check pricing on the OpenAI pricing page (perishable)
---

# Embeddings

> Provenance: The endpoint shape and params below come from the openai-openapi spec (`openapi.yaml`, master) fetched 2026-07-12; model names, dimensions, and pricing were web-verified the same day because the platform.openai.com embeddings guide returns 403 to automated fetches. Pricing is perishable — re-confirm before quoting.

## What it is
Embeddings turn text into a dense floating-point vector that captures semantic meaning: inputs whose vectors are close (cosine / dot-product) are semantically similar. They power semantic search, retrieval-augmented generation (RAG), clustering, classification, recommendations, deduplication, and anomaly detection. A single POST to `/v1/embeddings` returns one vector per input string. Cost is charged on **input tokens only** — embeddings have no output-token charge.

## Models, dimensions, pricing (verified 2026-07-12 via web search)

| Model | Default dims | `dimensions` range (Matryoshka) | Price /1M input tokens | Batch API /1M | Notes |
|---|---|---|---|---|---|
| `text-embedding-3-small` | 1536 | 256 – 1536 | ~$0.02 | ~$0.01 | Best default; ~5x cheaper than ada-002 and higher MTEB |
| `text-embedding-3-large` | 3072 | 256 – 3072 | ~$0.13 | ~$0.065 | Highest quality; largest vectors |
| `text-embedding-ada-002` | 1536 | (fixed, no `dimensions` support) | ~$0.10 | ~$0.05 | **Legacy** — worse cost/quality than 3-small; avoid for new work |

- `dimensions` is only honored by the **text-embedding-3** family; ada-002 is fixed at 1536.
- Confirmed: 3-small = 1536 dims @ ~$0.02/1M, 3-large = 3072 dims @ ~$0.13/1M, ada-002 legacy @ ~$0.10/1M. Prices are perishable — verify on the live pricing page.

## Endpoint & params (from openai-openapi: model, input, dimensions, encoding_format)
`POST /v1/embeddings` — operationId `createEmbedding`, request body `CreateEmbeddingRequest`.

| Param | Type | Req? | Meaning |
|---|---|---|---|
| `model` | string | required | Model id, e.g. `text-embedding-3-small`. |
| `input` | string \| string[] \| int[] \| int[][] | required | Text (or pre-tokenized token arrays) to embed. Pass an **array** to embed a batch in one call. |
| `dimensions` | integer | optional | Truncate output vector to this many dims (text-embedding-3 only). |
| `encoding_format` | string | optional | `"float"` (default) or `"base64"`. base64 shrinks the wire payload (~4x) — handy over the network. |
| `user` | string | optional | Opaque end-user id for abuse monitoring. |

Response: `{ "object": "list", "data": [ { "object": "embedding", "index": N, "embedding": [...] }, ... ], "model": "...", "usage": { "prompt_tokens": N, "total_tokens": N } }`. Data is returned per-input; sort by `index` to be safe.

## The `dimensions` param (Matryoshka shortening)
The text-embedding-3 models are trained with **Matryoshka Representation Learning (MRL)**: information is packed coarse-to-fine, so a prefix of the vector is itself a usable embedding. Passing `dimensions` (e.g. `1024` on 3-large, which is 3072 by default) returns a shortened vector — you trade a little accuracy for much smaller storage and faster search, **without retraining**. OpenAI's published MTEB numbers show `text-embedding-3-large` @ 256 dims still beats `ada-002` @ 1536 dims. Shortened vectors should be **L2-normalized** before use if you need unit vectors, since truncation changes the norm. Vectors of different dims (or different models) live in **different spaces** and are not comparable.

## Relevance to this repo (examples/bifl embedders; /v1/embeddings passthrough is the relay's real-upstream test)
- **`examples/bifl/embed_openai.py`** — the fast cloud embedder for the BIFL RAG index. Uses `AsyncOpenAI().embeddings.create(model="text-embedding-3-small", input=batch)` with batching + a concurrency semaphore, writing 1536-dim vectors into a Chroma collection (`bifl_openai_3small`). It exposes `--dimensions` for optional Matryoshka shrinking and prints an estimated cost using the confirmed `$0.02/1M` rate. It reads `OPENAI_API_KEY` / `OPENAI_BASE_URL`, so it can run through the relay or hit OpenAI directly. Its sibling `embed_bge_m3.py` uses a **1024-dim** local model — a different vector space, hence a separate collection (never mix).
- **`app/routes/embeddings.py`** — `POST /v1/embeddings` route; hands the raw JSON body to `forward_embeddings_create()` in `app/api/forward_openai.py`, which builds outbound headers and forwards to the real upstream (`build_upstream_url("/v1/embeddings")`). This is a **passthrough**, so it doubles as the relay's real-upstream sanity check: `tests/test_local_e2e.py::test_embeddings_basic` posts `text-embedding-3-small` and asserts the OpenAI response shape (`{"object":"list","data":[...]}`, non-empty `data`). If real forwarding is broken, this is the test that catches it.

## Verify / TODO
- Re-check all three prices on the live OpenAI pricing page before quoting — pricing is perishable; batch discounts (~50%) may change.
- Confirm exact `dimensions` min/max per model against the guide when platform.openai.com is reachable (spec lists the param but not the numeric bounds; the 256 floor and per-model ceilings are web-sourced).
- Spec fetch of `openapi.yaml` truncated the enum for `encoding_format`; `float`/`base64` are web-confirmed. Re-grep the spec to lock the exact enum + defaults if needed.
