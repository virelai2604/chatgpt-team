---
source_id: gh_openai_codex_action
title: openai/codex-action — run Codex from a GitHub Actions workflow
category: github_reference
source_urls:
  - https://github.com/openai/codex-action
retrieved_at: 2026-08-15
pinned_commit: c385816875cc2fc8e033ed9d1cba96f8c331210e
fetch_method: shallow clone (--depth 1 --filter=blob:none), README read locally
pull_status: fetched
verify: third-party actions are rejected at startup unless allow-listed for this repo — see the note in .github/workflows/ci.yml about gitleaks
---

# openai/codex-action

> Provenance: `fetched` 2026-08-15 at `c385816`. Reference only — not vendored.

GitHub Action that runs `codex exec` inside a workflow while constraining what Codex can
reach. It installs the Codex CLI and configures it behind a **secure proxy to the Responses
API**, so the job never holds a broad-scope key.

## Relevance to this relay

This repo's CI already runs four jobs (gitleaks, ruff, pytest, and a manual live-OpenAI
integration job). Codex-action would be additive, not a replacement.

**Adoption blocker worth knowing first:** `.github/workflows/ci.yml` documents that
third-party Marketplace actions are *rejected at startup* for this repo unless allow-listed
— which is why gitleaks is installed as a plain binary in a `run:` step rather than via its
official action. Any adoption of `codex-action` hits the same gate.
