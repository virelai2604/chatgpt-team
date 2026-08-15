---
source_id: gh_openai_cli
title: openai/openai-cli — official CLI for the OpenAI REST API
category: github_reference
source_urls:
  - https://github.com/openai/openai-cli
retrieved_at: 2026-08-15
pinned_commit: 3023717289fdafce3e13f06fe613fac592391d2a
fetch_method: shallow clone (--depth 1 --filter=blob:none), README read locally
pull_status: fetched
verify: release-please manages versions; check the latest tag rather than the README badge
---

# openai/openai-cli

> Provenance: `fetched` 2026-08-15 at `3023717`. Reference only — not vendored.

Official command-line client for the OpenAI REST API. Written in **Go** (`go.mod`);
installable via Homebrew (`brew install openai/tools/openai`) or `go install`.

## Relevance to this relay

Potentially useful as a **manual probe**, since the relay is OpenAI-API-compatible: point
the CLI's base URL at `https://ai.lafiel.me/v1` with the relay key and it should behave
like the real API. That is a cheaper smoke test than writing curl by hand.

Caveat before relying on it: the relay authenticates with `X-Relay-Key` (falling back to
`Authorization: Bearer`), so the CLI's auth handling has to line up with
`app/middleware/relay_auth.py`. Verify rather than assume — this has not been tried.
