# Index Exclusion Policy — Amendment: generated readiness / eval artifacts

_Amendment to the local `openai_workspace_index_exclusion_policy.md`._
_Purpose: keep **generated** readiness/eval/report artifacts out of the local
retrieval index so they never contaminate the clean **212 / 550** baseline._
_Status: **documentation-only**. Applying this amendment does **not** rebuild or
re-index anything — it takes effect on the **next explicitly-authorized** ingest._

> Provenance note: this amendment is written against the exclusion-policy *pattern*
> described in the project runbook. It has **not** been diffed against your actual
> local `openai_workspace_index_exclusion_policy.md` (that file is not in this repo),
> so reconcile the exact rule syntax with your indexer before adopting. Marked
> **Not proven** until you confirm it matches your policy format.

## Why

Readiness reports, eval outputs, and run summaries are **generated derivatives**, not
source knowledge. Indexing them:
- inflates chunk counts and breaks the accepted `212 files / 550 chunks` baseline;
- pollutes retrieval with stale, self-referential text (evals about the corpus rank
  above the corpus);
- creates non-deterministic re-index drift (reports change every run).

## Add these exclusion patterns

Append to the exclusion policy's ignore list (glob-style; adapt to your matcher):

```gitignore
# --- generated readiness / eval / report artifacts (do NOT index) ---
*_readiness*.md
*_readiness*.json
*readiness_report*.*
*_eval_report*.*
*_eval_results*.*
*evals_output*/**
eval_runs/**
*.eval.json
*.eval.jsonl
*.results.json
*.results.jsonl
*_run_summary*.md
*_score*.json
report_*.md
reports/**
# retrieval-eval working outputs
retrieval_eval_out/**
*_retrieval_eval*.json
*_retrieval_eval*.md
```

## Keep indexable (do NOT exclude)

These are **source** knowledge and must remain indexed:
- `reference/openai/**` distilled snapshots (the docs track output);
- `06_Runbooks/**` runbooks (excluding any generated report subfolder);
- curated architecture/decision docs with provenance.

## Interaction with the baseline

- This amendment **prevents future contamination**; it does **not** remove anything
  already indexed. If a generated artifact was previously indexed, its removal is a
  **separately-authorized re-index**, not part of this amendment.
- Until a rebuild is authorized, the active baseline remains **212 / 550**, unchanged.

## Adoption checklist

- [ ] Diff these patterns against the existing local exclusion policy (dedupe overlaps).
- [ ] Confirm the glob syntax matches your indexer's matcher.
- [ ] Commit the amended policy **without** running the indexer.
- [ ] Leave the 212/550 baseline untouched until a rebuild is explicitly authorized.
