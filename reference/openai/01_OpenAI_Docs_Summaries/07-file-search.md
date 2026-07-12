---
source_id: oa_docs_file_search
title: File Search
category: openai_docs
source_urls:
  - https://platform.openai.com/docs/guides/tools-file-search
  - https://github.com/openai/openai-openapi
  - https://github.com/openai/openai-cookbook
fetched: 2026-07-12
fetch_method: openapi.yaml (openai-openapi master) fetched via raw.githubusercontent + grep for exact schemas; cookbook File_Search_Responses.ipynb + oai_docs/tool-file-search.txt fetched; platform.openai.com guide is 403-blocked, so its prose was web-verified only.
pull_status: fetched
verify: In an account with an API key, run POST /v1/vector_stores/{id}/search and confirm the response is object=vector_store.search_results.page with data[].content[].text; separately confirm a .jsonl upload to a vector store is rejected.
---

# File Search

> Provenance: Field names and shapes below are transcribed from `openai/openai-openapi` `openapi.yaml` (master, fetched 2026-07-12); the supported-file-type and chunking prose is cross-checked against the cookbook doc mirror `oai_docs/tool-file-search.txt` and July-2026 web search, since the platform.openai.com guide blocks automated fetch.

## What it is
File Search is a **hosted (server-side) RAG tool**. You upload files, add them to a **Vector Store**, and OpenAI automatically parses, chunks, embeds, and indexes them. At query time the model retrieves relevant chunks via hybrid semantic + keyword search — you write no retrieval, chunking, or embedding code. It is exposed two ways: as a built-in tool in the **Responses API**, in the legacy **Assistants API**, and as a raw **Vector Store search endpoint** (`POST /v1/vector_stores/{id}/search`). Assistants API is deprecated (shutdown 2026-08-26); new work should use the Responses API + Vector Stores.

## How to use it

### Responses API tool (verified shape — schema `FileSearchTool`)
Required fields are `type` and `vector_store_ids`; the rest are optional.
```python
r = client.responses.create(
    model="gpt-5.1",
    input="What are the top tire-sealant complaints?",
    tools=[{
        "type": "file_search",          # required, const
        "vector_store_ids": ["vs_123"], # required (array of vector store IDs)
        "max_num_results": 5,           # optional, 1..50
        "ranking_options": {            # optional
            "ranker": "auto",           # RankerVersionType
            "score_threshold": 0.0,     # 0..1
        },
        "filters": {                    # optional: ComparisonFilter | CompoundFilter over file attributes
            "type": "eq", "key": "category", "value": "reviews"
        },
    }],
)
print(r.output_text)
```
The model emits a `file_search_call` output item (schema `FileSearchToolCall`): `id`, `type="file_search_call"`, `status` (`in_progress` | `searching` | `completed` | `incomplete` | `failed`), `queries` (array of the search strings it ran), and `results[]` with `{file_id, text, filename, attributes, score}` (`score` 0..1). Include `"include": ["file_search_call.results"]` on the request to get the results array populated in the response.

### Assistants API (legacy — schema `AssistantToolsFileSearch`)
Tool object is `{"type":"file_search","file_search":{"max_num_results":20,"ranking_options":{...}}}`, and the vector store is attached separately via `tool_resources.file_search.vector_store_ids` (max **1** vector store per assistant/thread). Default `max_num_results` is 20 for `gpt-4*`, 5 for `gpt-3.5-turbo`.

### Raw Vector Store search (schema `VectorStoreSearchRequest`)
This is what this repo's relay calls directly. `POST /v1/vector_stores/{vs}/search`:
```json
{"query": "…", "max_num_results": 10, "rewrite_query": false,
 "filters": {…}, "ranking_options": {"ranker": "auto", "score_threshold": 0}}
```
`query` may be a string or array of strings; `max_num_results` default 10 (1..50); `ranking_options.ranker` enum is `none | auto | default-2024-11-15`. Response is `object="vector_store.search_results.page"` with `data[]` of `VectorStoreSearchResultItem`: `{file_id, filename, score (0..1), attributes, content:[{type:"text", text}]}` — note `content` is an **array of content objects**, not a bare string.

## Supported files, chunking, citations
- **Chunking (server-side, auto):** default `max_chunk_size_tokens = 800`, `chunk_overlap_tokens = 400` (schema `AutoChunkingStrategyRequestParam`). Overridable via a `static` chunking strategy at file-add time: `max_chunk_size_tokens` 100..4096, `chunk_overlap_tokens` must be ≤ half of `max_chunk_size_tokens`. Embeddings use `text-embedding-3-large` (256 dims per the docs mirror).
- **Supported file types:** `.pdf .txt .md .json .docx .doc .html .pptx` plus source-code extensions (`.py .js .ts .java .cpp .c .cs .rb .php .sh .css .tex`). Files are added with `purpose="assistants"` (a.k.a. `user_data`).
- **GOTCHA — `.jsonl` and `.csv`:** the file-search doc's supported-extensions table does **not** include `.jsonl`, and the known-limitations section lists `.csv`/`.jsonl` (structured formats) as **not yet supported** for vector-store retrieval; community reports (2025–2026) confirm CSV/XLSX uploads to vector stores erroring. General model file-input docs muddy this by listing CSV elsewhere, so **do not assume `.jsonl` works** — for this repo, upload distilled knowledge as `.md`/`.json`/`.txt`, not `.jsonl`. Verify against your account before relying on it.
- **Citations:** In Responses output, cited passages appear as message annotations of type `file_citation` carrying `file_id` (and filename/index) so you can surface source attributions.
- **Scale note:** Vector stores created from **Nov 2025** onward raised the per-store file cap to 100,000,000 (was 10,000).

## Relevance to this repo
- `app/routes/bifl.py` `POST /v1/bifl/search` proxies straight to `{base}/v1/vector_stores/{vs}/search` with `{"query", "max_num_results": limit}` and reads back `data[].{file_id, filename, score, content}` — exactly the `VectorStoreSearchResultsPage` / `VectorStoreSearchResultItem` shape above. (One caveat: the route stores `content` as-is, which is the array-of-`{type,text}` objects, not a flat string.)
- `examples/agents/agent_pro.py` builds `FileSearchTool(vector_store_ids=[vs], max_num_results=5)` from the Agents SDK — the SDK wrapper for the same Responses `file_search` tool.
- Both light up only when **`BIFL_VECTOR_STORE_ID`** (a `vs_...` id) is set; `bifl_health` reports `vector_store_configured` and `/search` degrades gracefully with a note when it's unset.
- To populate it: upload distilled BIFL knowledge (as `.md`/`.json`, per the gotcha), create a vector store, add files (auto chunk+embed), then export `BIFL_VECTOR_STORE_ID=vs_...`. See `examples/bifl/sync_vector_store.py`.

## Verify / TODO
- Confirm current supported-extension list against a live account — the `.jsonl`/`.csv` status is the highest-risk item; the platform.openai.com guide (403-blocked here) is the authoritative source, verify there.
- Confirm whether `content` in `/v1/bifl/search` output should be flattened to `content[].text` for downstream consumers rather than passed as the raw array.
- Confirm the default embedding model/dimension (`text-embedding-3-large` @ 256) is still current in July 2026 — it comes from the doc mirror, not the openapi schema.
