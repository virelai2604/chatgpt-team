---
source_id: gh_openai_evals
title: openai/evals — evaluation framework for LLM systems
category: github_reference
source_urls:
  - https://github.com/openai/evals
retrieved_at: 2026-08-15
pinned_commit: 8eac7a7de5215c907fbddc30efdaf316913eccdd
fetch_method: shallow clone (--depth 1 --filter=blob:none), README read locally
pull_status: fetched
verify: the repo's own README now points to the hosted Evals product first — check whether the dashboard covers the need before adopting the framework
---

# openai/evals

> Provenance: `fetched` 2026-08-15 at `8eac7a7`. Reference only — not vendored.
> Supersedes the "add later" placeholder that was in `_pending_summaries.md`.

Framework and registry for evaluating LLMs and LLM-backed systems. Python
(`pyproject.toml`). Note the README leads with a redirect: evals can now be configured and
run **in the OpenAI Dashboard**, which may be the cheaper path than self-hosting.

## Relevance to this relay

The relay's current gates are structural, not behavioural: ruff, 27 unit tests, and 36
integration tests that assert routes answer and errors propagate. Nothing measures
**output quality**, because a transparent proxy has no opinion about model output.

Where evals would earn their place is if the relay ever gains behaviour of its own —
`/v1/responses/compact` is the obvious candidate, since compaction can silently degrade a
conversation in a way no status code reveals.

Until then this is a pointer, not a dependency.
