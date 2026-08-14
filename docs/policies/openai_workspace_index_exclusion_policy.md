# Index Exclusion Policy — OpenAI Workspace

Prevents retrieval pollution by keeping generated and raw noise **out of the retrieval
index** and out of ChatGPT Project Sources.

## Exclude from indexing

- Raw chat exports: `ChatGPT-*.md`, `ChatGPT-*.jsonl`, `*.tavern.jsonl`, full conversation dumps.
- Duplicate raw exports and `(1)`/`(2)` copy variants.
- Generated eval output and eval-result reports (e.g. `*_retrieval_eval_results_*`).
- Backups and temporaries: `.bak_*`, `*.before_*`, `__pycache__/`, `*.pyc`.
- Full database and cache directories: SQLite, Chroma, DuckDB, Parquet, caches.
- Large raw ZIP bundles.

## Keep indexable

- Distilled/curated docs, runbooks, and policies.
- Small verification checkpoints and manifests.
- Curated reference maps under `reference/`.

## Rule of thumb

If a file is **raw, generated, duplicated, or a full database**, exclude it. If it is
**distilled, authored, small, and provenance-labeled**, it may be indexed. Anchor
exclusions to a directory/pattern; do not exclude authored evidence by a bare keyword.
