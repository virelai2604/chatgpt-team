# Projects Split Checkpoint — 2026-08-20 Refresh

## Purpose

Refresh the 2026-07-14 project split after the user confirmed that the old local `chatgpt-team` path is absent and that GitHub is used as the implementation authority.

## Completed / Current

- [Done] `D:\ChatgptDATAB\DB Chatgpt\Projects` is the Projects root.
- [Done] `OpenAI_Workspace_Project` remains the canonical owner for OpenAI Workspace work.
- [Done] `OpenClaw_Project` remains a separate OpenClaw / AgentOS / BIFL archive and continuity project.
- [Done] Root registry files exist at the Projects root.
- [Done] Project Core files were refreshed on 2026-08-20.
- [Done] `source_location_manifest_2026-08-20.md` was written under `OpenAI_Workspace_Project\00_Project_Admin`.
- [Done] GitHub remote `https://github.com/virelai2604/chatgpt-team` is the implementation authority.
- [Done] Old expected local repo path was tested and returned `False`.
- [Done] The local clone path `OpenAI_Workspace_Project\repo\chatgpt-team` must no longer be claimed as present.
- [Done] P4 full vault remains pointer/export only.
- [Done] P4 SQLite remains do-not-copy.
- [Done] OpenClaw remains separate and must not receive a duplicate `chatgpt-team` clone.
- [Done] Heavy DB/vector/model/credential upload restrictions remain active.

## Current Project Ownership

| Project / Layer | Owns | Status |
|---|---|---|
| `OpenAI_Workspace_Project` | OpenAI Platform setup, ChatGPT Project setup, P4 working references, Agent Skills, connectors, local BIFL/RAG, runbooks, continuity, GitHub remote coordination | Active |
| GitHub `virelai2604/chatgpt-team` | Implementation authority for the relay/repository | Active remote authority |
| `OpenClaw_Project` | OpenClaw / AgentOS / BIFL source archive, scripts, reports, summaries, manifests, continuity | Active local archive project |
| External P4 vault | Full P4 resources and P4 SQLite | External pointer only |
| `P4_Runtime_Project` root shell | Earlier planned separate root project | Not present in current root listing / superseded unless recreated later |

## Superseded From 2026-07-14

- [Superseded] Claim that the actual local `chatgpt-team` path is present under `OpenAI_Workspace_Project\repo\chatgpt-team`.
- [Superseded] Requirement that a local clone must exist for normal project operation.
- [Superseded] Treating `P4_Runtime_Project` as a visible current root project if it is absent from the latest root listing.
- [Superseded] Any instruction that duplicates `chatgpt-team` into `OpenClaw_Project`.
- [Superseded] Any implied permission to copy full P4 vault or P4 SQLite.
- [Superseded] Any implied permission to index raw OpenClaw archives.

## Not Done

- [Not done] Local clone of `chatgpt-team` under the old expected path.
- [Done] Committed refreshed registry/checkpoint files to GitHub (`docs/workspace/`, on `main`).
- [Not done] Verify production deployment equals GitHub `main`.
- [Not done] Refresh official OpenAI summaries from live official sources.
- [Not done] Run new hosted File Search pilot.
- [Not done] Run new retrieval eval from this checkpoint.
- [Not done] Clean selected `.bak_*` files after review.

## Not Proven

- [Not proven] Production deployment equals GitHub `main`.
- [Not proven] Any local clone exists somewhere else.
- [Not proven] OpenAI Library connector scope.

## Rules

- Do not copy `E:\p4_v257_resources` wholesale.
- Do not copy `p4_index.sqlite`.
- Do not duplicate `chatgpt-team` into `OpenClaw_Project`.
- Do not store secrets, `.env` files, API keys, tokens, cookies, or credential logs.
- Do not upload SQLite databases, SQLite WAL/SHM files, raw ChromaDB folders, DuckDB databases, or model files.
- Do not rebuild, re-index, mutate SQLite, mutate Chroma, deploy, or change credentials from this registry refresh.

## GitHub Storage Decision

Lightweight project-governance data like this file can be stored in both:

1. the local Windows project mirror, and
2. the GitHub repository,

provided it contains no secrets and no heavy database/vector/model artifacts.

GitHub destination (committed on `main`):

```text
docs/workspace/PROJECTS_REGISTRY_2026-08-20.md
docs/workspace/PROJECTS_SPLIT_CHECKPOINT_2026-08-20.md
docs/workspace/openclaw/README.md
docs/workspace/openclaw/PROJECTS_SPLIT_CHECKPOINT_2026-08-20.md
```

## Next Actions

1. Replace root registry/checkpoint files locally after review.
2. Replace OpenClaw README/checkpoint files locally after review.
3. Delete selected `.bak_*` files only after confirming the refreshed active files are correct.
4. Decide whether to upload these lightweight governance docs to GitHub.
5. If GitHub upload is chosen, create a docs-only PR; do not add raw archives or databases.
