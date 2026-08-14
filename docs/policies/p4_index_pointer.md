# P4 Index Pointer

Documents the rule for handling the local P4 / OpenAI Workspace retrieval index in
relation to source control.

## Rule

- The **full local index** (SQLite database, Chroma collection, embeddings) lives **only**
  on the local machine. **Do not upload full databases** to GitHub.
- Commit **small derived checkpoints and manifests** instead — enough to reconstruct or
  verify state, never the bulk index itself.

## What to commit

- `reference/manifests/*.json` — source and archive inventory checkpoints.
- `docs/status/*` — dated verification/consistency checkpoints with provenance.

## What NOT to commit

- SQLite/Chroma/DuckDB/Parquet database files.
- Embedding blobs, cache directories, or full vector-store exports.

## Pointer

The authoritative live index is local; this repository holds only the **pointers and
proofs** (manifests + checkpoints) needed to verify and rebuild it under explicit
authorization. Rebuild/re-index is never implied by a documentation change.
