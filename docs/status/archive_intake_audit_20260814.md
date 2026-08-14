# Archive Intake Audit — 2026-08-14

**Archive:** `ChatGPT-PR_#34_Merge_Review-2026-08-14-…-2026-08-13T23-06-29.zip`
**Target repo:** `virelai2604/chatgpt-team` (`main` @ `dee39c3` / PR #56 at commit time)
**Nature:** Read-only intake audit. No index, database, or source mutation performed.

## Intake result

| Check | Result |
|---|---|
| ZIP integrity / extraction safety | Passed — 23 members, no absolute or `..` traversal paths |
| Member count | 23 files (18 `.md`, 3 `.json`, 2 `.csv`) |
| Canonical Memory Verifier | Invalid — no `bundle.json`; not a canonical-memory bundle |
| Included manifests | Stale — `manifest.json` = 33 entries, `archive_members.json` = 35 entries; neither matches the 23 actual members |
| Duplicate content | 5 exact `(1)` duplicate pairs present |
| Raw conversation exports | 8 `ChatGPT-*` transcripts (Originals, 3× PR#34 Merge Review, 2× Project Root and Tracks, Enable-OpenAI-Docs-MCP) |
| Secret/token pattern scan | 14 / 23 files match `api_key`/`secret`/`password`/`DASHSCOPE`/`sk-…` patterns (chiefly the raw exports) |
| Current RAG/Chroma health | Not claimed — the archive labels live RAG/Chroma/sync/deploy state as *not proven* |

## Disposition

- **Not added to the repository:** the ZIP itself, all raw `ChatGPT-*` exports, the stale `manifest.json` / `archive_members.json` / `manifest (7).csv`, `hash_report_20260814.csv`, and all `(1)` duplicates. Raw personal conversation exports plus secret-pattern hits must not enter a public repository, and stale manifests must not masquerade as a current inventory.
- **Added instead (this branch):** authored-fresh historical status checkpoints, policy documents, and freshly regenerated manifests — none copied verbatim from the archive.

## Provenance note

This records the **intake of a historical archive**. It makes **no claim** about current retrieval, database, or deployment health. Every metric carried forward from the archive is **historical** and retains its original date and source.
