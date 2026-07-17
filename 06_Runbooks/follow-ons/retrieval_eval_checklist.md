# Retrieval-Eval Execution Checklist (read-only, from the clean 212/550 baseline)

_Runs the **existing** hybrid retrieval eval against the **frozen** index to confirm
health and ranking. **Read-only:** no rebuild, no re-index, no embedding, no DB mutation._
_This does **not** replace the accepted prior evaluation — it re-runs and re-scores it._

> Revised per review to use the **real** local workflow, not placeholders, and to preserve
> the existing per-item status model (Done / Not done / Not proven).

## Fixed inputs (the real artifacts — do not regenerate)

- **Query entry point (read-only):** `06_Runbooks/scripts/query_openai_workspace_hybrid.py`
  (invocation pattern is in `openai_workspace_hybrid_retrieval_runbook.md`).
- **Eval set:** `.../07_Continuity/openai_workspace_recurring_retrieval_eval_set_2026-07-16.jsonl`
  (keys per row include `eval_id`, `query`, **`expected_rank_1_source`**, `expected_checks`,
  `baseline_evidence`, `cadence`, `notes`).
- **Fixed run dir (WSL):** `.../07_Continuity/openai_workspace_eval_run_<DATE>/`
  with `<eval_id>_report.txt` per query + a results CSV.

## Accepted prior evaluation — carry these statuses forward

Do **not** overwrite these with a fresh generic run; **carry them forward**:

| Aspect | Status |
|---|---|
| Operational retrieval health (integrity, fts/semantic/merged > 0) | **10/10 Done** |
| Accepted ranking outcomes | **7 Done** |
| Two expected sources absent from the frozen index | **Not proven** (absence from frozen index — **not** a retrieval failure) |
| **OW-RAG-EVAL-010 authority-ranking** | **Not done — UNRESOLVED GATE** |

> **OW-RAG-EVAL-010 is the open authority-ranking gate.** It must stay flagged **Not done**
> until explicitly resolved; a green health run does **not** clear it.

## 0. Baseline assertions (read-only — must hold before scoring)

- [ ] SQLite `PRAGMA integrity_check;` → `ok`
- [ ] files = `212`, documents = `212`
- [ ] chunks = `550`, FTS rows = `550`, embeddings = `550`
- [ ] Chroma documents = `212`, Chroma vectors = `550`
- [ ] no orphaned chunk IDs (SQLite chunk IDs == Chroma vector IDs)

All `PRAGMA`/`SELECT`/count — no writes.

## 1. Run the eval (read-only queries)

For each row in the eval set, invoke the hybrid query entry point (read-only) and
capture its `<eval_id>_report.txt`:

```bash
# parameterized; adjust flags to the script's actual signature (see the runbook)
python3 "06_Runbooks/scripts/query_openai_workspace_hybrid.py" \
    --query "<row.query>" \
    --top-k 10 \
    --report-out ".../openai_workspace_eval_run_<DATE>/<eval_id>_report.txt"
```

The script performs retrieval only. It must not upsert, re-embed, or write to the index.

## 2. Score (read the reports — do NOT re-query)

> **Known scorer bug to avoid:** score against the eval key **`expected_rank_1_source`**,
> NOT a key named `expected`. A prior scorer read `expected` (absent) → every row came back
> empty and defaulted to **Not proven** (a false negative) even though the reports showed
> correct rank-1. Read the correct key and parse each report's `rank: 1` → `source:` line.

Per `eval_id`, compute:
- [ ] `sqlite_integrity_check == ok` (from report)
- [ ] rank-1 `source:` in the report **== `expected_rank_1_source`** (normalize `\`↔`/`, case)
- [ ] rank-1 source is **not** a generated eval/readiness artifact (see exclusion amendment)
- [ ] classify: **Done** (rank-1 match + checks pass) / **Not done** (gate unresolved, e.g.
      OW-RAG-EVAL-010) / **Not proven** (expected source absent from the frozen index, or
      report unparseable)

## 3. Distinguish failure classes (do not conflate)

- **"expected source absent from frozen index"** → **Not proven**, *not* a retrieval failure.
  The retriever can't rank a document that isn't indexed. Note it; do not fix by re-indexing
  here (re-index is separately authorized).
- **genuine ranking miss** (source is indexed but out-ranked) → the actionable case.
- classify misses: keyword miss / semantic miss / ranking failure / synthesis / citation.

## 4. Exit gate

- [ ] Integrity `ok`; counts still `212 / 212 / 550 / 550 / 550` (+ Chroma `212 / 550`)
- [ ] **No rebuild, no re-index, no write to SQLite/Chroma occurred**
- [ ] Operational health preserved (10/10)
- [ ] **OW-RAG-EVAL-010 still carried as Not done** until explicitly resolved
- [ ] Report(s) written to an **excluded** path (see `index_exclusion_amendment.md`)

## 5. Deliberately NOT done here

- ✗ rebuild / re-index / re-embed / re-chunk
- ✗ mutate SQLite / FTS5 / Chroma
- ✗ upload to hosted OpenAI Vector Stores
- ✗ replace the accepted prior evaluation with a generic Recall@5/MRR run
- ✗ change the accepted 212/550 baseline

Any of those requires a **separate, explicit authorization** — this is measurement only.
