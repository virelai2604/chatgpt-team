# Index Exclusion Policy — Amendment: generated retrieval-eval / readiness artifacts

_Amendment to the canonical local `openai_workspace_index_exclusion_policy.md`._
_Purpose: keep a **narrow, directory-scoped** set of **generated** retrieval-eval and
readiness outputs out of the local index — **without** suppressing canonical evidence
reports the policy deliberately keeps indexable._
_Status: **documentation-only**. Applying this does **not** rebuild or re-index anything —
it takes effect on the **next explicitly-authorized** ingest. Removes nothing already indexed._

> Provenance: revised per review to reconcile with the **actual** canonical policy.
> The prior draft used broad filename globs (`reports/**`, `report_*.md`, `*_score*.json`,
> `*_readiness*.md`, `*_retrieval_eval*.md`) that would have suppressed legitimate canonical
> evidence and future authored source documents. Those broad patterns are **removed**.

## Principle

**Exclude by exact project-relative directory + name, never by bare filename token.**
A pattern like `report_*.md` or `reports/**` is too broad — it catches canonical evidence.
Every exclusion below is anchored to a specific directory.

## MUST STAY INDEXABLE (canonical evidence — do NOT exclude)

These are authoritative and must remain retrievable:

- `openai_workspace_index_init_report.*`
- `openai_workspace_chunk_index_report.*`
- the hybrid **smoke-test** report
- `07_Continuity/` continuity + state artifacts (checkpoints, registries, closures) that
  the canonical policy already treats as evidence
- any authored source doc under `01_OpenAI_Docs_Summaries/`, `06_Runbooks/`, `reference/`

## ADD these narrow, directory-scoped exclusions (generated eval/readiness outputs only)

```gitignore
# Generated retrieval-eval outputs (scoped to the eval/reports dirs only)
05_BIFL_RAG/reports/openai_workspace_retrieval_eval_report_*.json
05_BIFL_RAG/reports/openai_workspace_retrieval_eval_report_*.md
05_BIFL_RAG/evals/openai_workspace_retrieval_eval_set_*.jsonl
05_BIFL_RAG/retrieval_eval_out/**

# Generated readiness snapshots (scoped to Continuity, exact stem)
07_Continuity/openai_workspace_docs_readiness_*.md

# Per-run eval working dirs (scoped, generated per run)
07_Continuity/openai_workspace_eval_run_*/**
```

> Adjust the directory prefixes to match your tree if they differ — the **rule** is:
> anchor to a directory, name the exact generated stem. Do not globally exclude
> `reports/**`, `report_*.md`, `*_score*.json`, `*_readiness*.md`, or `*_retrieval_eval*`
> without a directory boundary.

## Explicitly NOT excluded (guard against over-broad matching)

- ✗ `reports/**` (would hit canonical index-init / chunk-index / smoke-test reports)
- ✗ `report_*.md` (too broad — future authored reports)
- ✗ `*_score*.json` (could hit authored scoring configs)
- ✗ `*_readiness*.md` without the `07_Continuity/openai_workspace_docs_readiness_` anchor
- ✗ `*_retrieval_eval*` without the `05_BIFL_RAG/` directory anchor

## Interaction with the baseline

- Prevents **future** contamination only; removes nothing already indexed.
- The active baseline remains **212 files / 212 documents / 550 chunks / 550 FTS rows /
  550 embeddings**, unchanged. Any removal of an already-indexed generated artifact is a
  **separately-authorized re-index**, not part of this amendment.

## Adoption checklist

- [ ] Diff these anchored patterns against the canonical exclusion policy (dedupe).
- [ ] Confirm each directory prefix matches your actual tree (`05_BIFL_RAG/reports`, etc.).
- [ ] Confirm none of the MUST-STAY-INDEXABLE files match an exclusion.
- [ ] Commit the amended policy **without** running the indexer.
- [ ] Leave the 212/550 baseline untouched until a rebuild is explicitly authorized.
