# Database / Storage Role Map

Separates the roles of each storage layer in the OpenAI Workspace Project so agents know
which artifact is authoritative for what.

| Layer | Role | Committed to GitHub? |
|---|---|---|
| **Raw files** (chat exports, ZIPs) | Original evidence / warehouse input | No — distill first |
| **Manifests** (`reference/manifests/*.json`) | Machine-readable source/archive inventory checkpoints | Yes — small, derived |
| **SQLite** | Primary document/chunk index + FTS5 keyword search | No — local index only |
| **Chroma** | Vector store for semantic retrieval | No — local index only |
| **DuckDB** | Analytical/columnar queries over derived tables | No — local only |
| **Parquet** | Columnar bulk storage of derived records | No — local only |
| **ChatGPT Project Sources** | Curated, high-signal documents the model retrieves over | Managed in the ChatGPT UI, not this repo |

## Rules

1. **GitHub = source control**; **Windows mirror = durable outputs**; **WSL = execution**; **databases = local indexes**.
2. Store **derived manifests/checkpoints**, never full database files, in the repository.
3. Keep raw exports and databases out of retrieval Project Sources to avoid pollution
   (see `openai_workspace_index_exclusion_policy.md`).
