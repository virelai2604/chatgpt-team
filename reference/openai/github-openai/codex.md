---
source_id: gh_openai_codex
title: openai/codex — Codex CLI coding agent
category: github_reference
source_urls:
  - https://github.com/openai/codex
retrieved_at: 2026-08-15
pinned_commit: 22bf16a37ed45006c0226541874abd7449c29911
fetch_method: shallow clone (--depth 1 --filter=blob:none), README read locally
pull_status: fetched
verify: moves fast; check the release notes before pinning a version in any workflow
---

# openai/codex

> Provenance: `fetched` 2026-08-15 at `22bf16a`. Reference only — not vendored.

Codex CLI: a coding agent from OpenAI that runs **locally on your machine**. Predominantly
Rust (~46 MB of `.rs` in the clone) with a `package.json` wrapper for npm distribution.

## What it is not

It is **not an API surface**, and nothing in it belongs in the relay. Worth stating plainly
because the name collides with the ChatGPT "Codex" product and with `codex-action`, and
because it is by far the largest of the cloned repos.

## Relevance to this relay

Indirect: it is a tool that might be used *on* this repo, not by it. The one concrete hook
is `codex exec`, which `openai/codex-action` wraps for CI — see `codex-action.md`.
