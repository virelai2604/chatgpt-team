# Retrieval-Eval-Only Execution Checklist (from the clean 212 / 550 baseline)

_Run retrieval evaluations **against the existing index** to measure quality._
_**Read-only.** This checklist performs **no rebuild, no re-index, no embedding, and no
database mutation.** It only *queries* the current SQLite/FTS5 + Chroma stores and
records metrics._

> Provenance: written against the accepted baseline recorded in the runbook
> (`212 files / 550 chunks`, `text-embedding-3-large` @ `1024` dims, collection
> `openai_workspace_chunks_3large_1024`). The exact indexer/query commands live in your
> local pipeline (not in this repo), so the command placeholders below are **Not proven**
> against your scripts — fill them with your read-only query entry points.

## 0. Baseline assertions (must all hold BEFORE evaluating)

Read-only integrity checks — if any fails, **stop** and do not proceed:

- [ ] SQLite `PRAGMA integrity_check;` → `ok`
- [ ] SQLite files = `212`, documents = `212`
- [ ] SQLite chunks = `550`
- [ ] FTS5 rows = `550`
- [ ] chunk embeddings = `550`
- [ ] Chroma document count = `212`, Chroma chunk/vector count = `550`
- [ ] No orphaned chunk IDs (SQLite chunk IDs == Chroma vector IDs)

_All of the above are `SELECT`/`PRAGMA`/count operations — no writes._

## 1. Eval set

- [ ] Use the existing retrieval evaluation question set (do not regenerate it here).
- [ ] Each item = `{ query, expected_source_file(s) / expected_chunk_ids, note }`.
- [ ] If no eval set exists yet, author it as a **separate** doc — authoring questions
      is not indexing and does not touch the baseline.

## 2. Run the three retrieval modes (read-only queries)

For each eval query, capture results from:
- [ ] **Keyword (FTS5)** — `<LOCAL_FTS_QUERY_CMD>` (read-only `SELECT` against FTS table)
- [ ] **Semantic (Chroma)** — `<LOCAL_CHROMA_QUERY_CMD>` (similarity search, no upsert)
- [ ] **Hybrid** — `<LOCAL_HYBRID_QUERY_CMD>` (your existing hybrid ranker)

Record top-k (k=5) hits: `rank, source_file, chunk_id, score`.

## 3. Metrics (compute, do not persist into the index)

Per query and aggregate:
- [ ] **Recall@5** — expected source appears in top-5
- [ ] **MRR** — reciprocal rank of first correct hit
- [ ] **Rank-1 hit rate** — expected source is the #1 result
- [ ] latency per query (ms)

Write metrics to a **generated report file** that is **excluded from indexing**
(see `index_exclusion_amendment.md`) — e.g. `retrieval_eval_out/eval_<date>.md`.

## 4. Failure classification (diagnose, don't fix here)

Tag each miss (from the runbook's taxonomy):
- [ ] keyword retrieval miss
- [ ] semantic retrieval miss
- [ ] ranking failure
- [ ] synthesis failure
- [ ] citation / provenance failure

## 5. Exit gate

- [ ] Integrity still `ok`; counts still `212 / 550 / 550 / 550 / 212 / 550`
- [ ] **No rebuild, no re-index, no write to SQLite/Chroma occurred**
- [ ] Rank-1 results did **not regress** vs. the last accepted eval run
- [ ] Report saved to an **excluded** path (not ingested)

## 6. What this checklist deliberately does NOT do

- ✗ rebuild the index
- ✗ re-embed or re-chunk
- ✗ mutate SQLite / FTS5 / Chroma
- ✗ upload anything to hosted OpenAI Vector Stores
- ✗ change the accepted 212/550 baseline

Any of those requires a **separate, explicit authorization** — this is measurement only.
