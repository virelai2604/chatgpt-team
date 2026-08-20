# OpenClaw Project

## Purpose

Local project mirror for OpenClaw / AgentOS / BIFL workflow evidence, selected source, scripts, reports, architecture notes, summaries, manifests, and continuity.

## External source

`Y:\openclaw`

## Ownership

`OpenClaw_Project` owns OpenClaw / AgentOS / BIFL source and continuity material only.

It does **not** own:

- the `chatgpt-team` GitHub implementation repository;
- the OpenAI Workspace relay;
- Render deployment;
- OpenAI Platform credentials;
- P4 SQLite;
- active OpenAI Workspace RAG indexes.

## Current rule

Do not blindly copy archive folders.

Promote only selected active source, scripts, reports, summaries, manifests, and reviewed continuity files.

Keep raw ZIP exports, raw JSON, raw JSONL, full chat exports, and large generated outputs as archive artifacts unless exact reconstruction is required.

## GitHub rule

Lightweight OpenClaw documentation can be copied to GitHub if useful, but raw archives and heavy evidence should stay local.

Allowed for GitHub:

- README;
- compact summary;
- manifest;
- source-selection policy;
- checkpoint summary;
- no-secret scripts.

Not allowed for GitHub:

- raw ZIP archives;
- raw JSON / JSONL exports unless deliberately reviewed and small;
- SQLite databases;
- ChromaDB folders;
- DuckDB files;
- model files;
- `.env`;
- API keys;
- tokens;
- cookies;
- credential logs.

## Indexing rule

Do not build an OpenClaw semantic index or promote OpenClaw sources into ChatGPT Project Sources until selected durable OpenClaw-specific sources are reviewed and explicitly authorized.

Current OpenClaw index state: not authorized.
