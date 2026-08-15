---
source_id: gh_openai_sites
title: openai/sites — tooling for sites hosted by OpenAI
category: github_reference
source_urls:
  - https://github.com/openai/sites
  - https://developers.openai.com/codex
retrieved_at: 2026-08-15
pinned_commit: 9d3c7dd5e24ddd9058f5242a835c08b72b3f1069
fetch_method: shallow clone (--depth 1 --filter=blob:none), README read locally
pull_status: fetched
verify: confirm against developers.openai.com before treating Sites as an option for anything user-facing
---

# openai/sites

> Provenance: `fetched` 2026-08-15 at `9d3c7dd`. Reference only — not vendored.
> Promotes the note previously filed under `_pending_summaries.md` #9 into its own
> provenance-stamped file.

JavaScript/TypeScript tooling for building and packaging **sites hosted by OpenAI**.
Small repo (~684 KB cloned), `package.json`-based.

## The reason this file exists is a constraint, not a capability

**`ai.lafiel.me` must stay a live backend — not a static Site.**

Sites are for public/demo/status pages. They are the wrong home for anything that:

- holds or forwards credentials (the relay's whole purpose is keeping `OPENAI_API_KEY`
  server-side while callers present a `RELAY_KEY`),
- needs request-time logic (auth middleware, upstream forwarding, SSE streaming),
- serves ChatGPT Actions, which require a real `servers` URL that answers POSTs.

If a status or landing page is ever wanted, a Site is a reasonable place for *that page*
— hosted separately, never replacing the Render service.
