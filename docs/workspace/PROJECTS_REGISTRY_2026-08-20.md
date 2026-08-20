# ChatGPT Projects Registry — 2026-08-20 Refresh

## Projects Root

`D:\ChatgptDATAB\DB Chatgpt\Projects`

## Current Interpretation

This registry supersedes the 2026-07-14 assumption that `chatgpt-team` must exist as a local clone under `OpenAI_Workspace_Project\repo\chatgpt-team`.

Current user-provided PowerShell evidence on 2026-08-20 proves:

- `D:\ChatgptDATAB\DB Chatgpt\Projects\OpenAI_Workspace_Project` exists.
- `D:\ChatgptDATAB\DB Chatgpt\Projects\OpenAI_Workspace_Project\repo\chatgpt-team` does **not** exist.
- GitHub remote `https://github.com/virelai2604/chatgpt-team` remains the implementation authority.

## Active Local Projects

| Project | Path | Role | Status |
|---|---|---|---|
| `_root_registry` | `D:\ChatgptDATAB\DB Chatgpt\Projects\_root_registry` | Root project registry / project-split metadata | Active |
| `OpenAI_Workspace_Project` | `D:\ChatgptDATAB\DB Chatgpt\Projects\OpenAI_Workspace_Project` | Central OpenAI Workspace control plane: OpenAI Platform, ChatGPT Project setup, P4 working references, Agent Skills, connector planning, local BIFL/RAG, runbooks, continuity, GitHub remote coordination | Active |
| `OpenClaw_Project` | `D:\ChatgptDATAB\DB Chatgpt\Projects\OpenClaw_Project` | OpenClaw / AgentOS / BIFL source archive, selected source, scripts, reports, summaries, manifests, and continuity | Active |
| `P4_Runtime_Project` | `D:\ChatgptDATAB\DB Chatgpt\Projects\P4_Runtime_Project` | Previously planned root-level P4 runtime shell | Not present in current root listing / superseded by pointer-based P4 handling |

## External Sources

| Source | Location | Project Owner | Rule |
|---|---|---|---|
| GitHub repo | `https://github.com/virelai2604/chatgpt-team` | `OpenAI_Workspace_Project` | Remote implementation authority. No local clone required unless explicitly recreated. |
| Expected old local repo path | `D:\ChatgptDATAB\DB Chatgpt\Projects\OpenAI_Workspace_Project\repo\chatgpt-team` | `OpenAI_Workspace_Project` | Superseded / currently absent. Do not claim local checkout exists. |
| P4 resource vault | `E:\p4_v257_resources` | `OpenAI_Workspace_Project` / P4 pointer layer | Pointer + selected exports only. Do not copy full vault. |
| P4 SQLite index | `E:\p4_v257_resources\07_index\p4_index.sqlite` | P4 pointer layer | Do not copy full database. Export only selected schema/table/query results when needed. |
| OpenClaw source archive | `Y:\openclaw` | `OpenClaw_Project` | Promote selected active source/scripts/reports/summaries/manifests only. |
| WSL execution engine | `~/knowledge_bifl` | OpenAI Workspace execution | Execute tools only. Windows remains durable write target. |

## GitHub Policy

The user currently uses GitHub as the implementation source for `chatgpt-team`.

Allowed in GitHub:

- lightweight Markdown documentation;
- project registries;
- source-location manifests;
- runbooks;
- policy files;
- compact summaries;
- source registers;
- skills ledgers;
- checkpoint summaries;
- small scripts that contain no secrets.

Do not put in GitHub:

- API keys;
- passwords;
- cookies;
- private tokens;
- `.env` files;
- credential logs;
- SQLite databases;
- SQLite WAL/SHM files;
- raw ChromaDB folders;
- DuckDB databases unless explicitly needed;
- Ollama / HuggingFace / Whisper model files;
- raw full archive dumps;
- noisy generated eval outputs unless intentionally stored as evidence outside active retrieval.

## Database Policy

Use per-project DB hubs and pointer manifests.

Do not upload or duplicate:

- SQLite databases;
- SQLite WAL/SHM files;
- raw ChromaDB folders;
- DuckDB database files unless explicitly needed;
- model files;
- `.env` files;
- API keys;
- tokens;
- cookies;
- credential logs.

## Current Status

- [Done] Projects root exists.
- [Done] `OpenAI_Workspace_Project` exists.
- [Done] `OpenClaw_Project` exists.
- [Done] Root registry files exist.
- [Done] GitHub remote repo is the implementation authority.
- [Done] Expected old local repo path was checked and is absent.
- [Done] Project Core refresh applied on 2026-08-20.
- [Done] OpenClaw remains separate from OpenAI Workspace.
- [Done] P4 SQLite remains do-not-copy.
- [Done] Heavy DB/vector/model/credential upload exclusions remain active.
- [Not done] Local clone of `chatgpt-team` under the old expected path.
- [Not proven] Production deployment equals GitHub `main`.
- [Done] Committed this refreshed registry to GitHub (`docs/workspace/`, on `main`).
- [Not done] Clean up selected `.bak_*` files after review.
