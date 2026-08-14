# Write Target Policy

Defines **where durable project outputs are written** for the OpenAI Workspace Project.

## Targets and their roles

| Target | Role | What goes here |
|---|---|---|
| **GitHub (`virelai2604/chatgpt-team`)** | Durable source control / recovery source | Distilled docs, runbooks, policies, small manifests, verification checkpoints. The authoritative recovery source. |
| **Windows project mirror** | Durable local outputs | Full generated artifacts, reports, and working copies kept off GitHub. |
| **WSL** | Execution environment | Runs indexing/query/eval scripts; not a durable store. |
| **Local databases (SQLite / Chroma / DuckDB)** | Local indexes | Live retrieval state; never committed to GitHub. |

## Rules

1. **Commit proof, policy, manifests, and runbooks** to GitHub — small, high-signal, self-contained.
2. **Never commit** raw ZIP bundles, raw chat exports, full databases, Chroma/cache folders, secrets, or generated eval noise. When a raw artifact matters, commit a **manifest or checksum-backed checkpoint** instead.
3. Durable *outputs* (large generated files) go to the Windows mirror, **not** GitHub.
4. Treat GitHub as the **control room**, not the storage warehouse.
