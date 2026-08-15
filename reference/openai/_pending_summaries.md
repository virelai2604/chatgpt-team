---
category: mixed
priority: P1-P2
fetched: 2026-07-07
fetch_method: developers.openai.com 403s automated fetch; these are SUMMARIES pending a manual browser pull. GitHub repos summarized from known structure.
pull_status: summary_only
verify: open each source_url in a browser and split into full snapshots when needed.
---

# Pending reference summaries (verify against source)

> ⚠️ Not full snapshots. Grouped here to record the remaining top-20 items with
> honest `summary_only` status. Promote any to its own `fetched` file when pulled
> in a browser.

## #3 — Workspace Agent access token / auth
`https://developers.openai.com/workspace-agents/authentication`
- A **Workspace Agent access token** is scoped ONLY to Workspace Agent API
  operations (triggering runs). Keep it **separate from `OPENAI_API_KEY`**.
- Use a **service account** for agent-owned accounts; least privilege.

> #5 (MCP Apps in ChatGPT) and #6 (Skills/Tools) now have dedicated snapshots:
> `apps-sdk/mcp-apps-in-chatgpt.md` and `tools-skills/openai-tools-skills.md`.

## #9 — Codex / ChatGPT Sites
`https://developers.openai.com/codex`
> Promoted 2026-08-15 to `github-openai/openai-sites.md` (`fetched`, pinned at
> `9d3c7dd`), which carries the constraint in full: Sites are for public/demo/status
> pages only, and `ai.lafiel.me` must stay a live backend, never a static Site.

## Repos (P1–P2) — reference, do not vendor

Most of this list has been promoted to its own `fetched` file. Remaining:

- **openai/openai-openapi** — the API's OpenAPI source; reference for modeling
  the relay's own schema. `https://github.com/openai/openai-openapi`
  (Note: `api_reference/openapi.transformed.yml` inside `openai/openai-python`
  already carries the same content and is what `app/api/action_schemas.py` was
  derived from — check whether a separate pull is still worth it.)

> Promoted on 2026-08-15, all `pull_status: fetched` from local shallow clones:
> `openai-node` → `node-sdk/openai-node.md` (already fetched 2026-07-16),
> `openai-cookbook` → `cookbook/openai-cookbook-selected.md`,
> `evals` → `github-openai/evals.md`,
> plus `chatgpt-retrieval-plugin`, `tiktoken`, `codex`, `codex-action`,
> `openai-cli`, `sites`, and the two `openai-developers-for-*` bundles under
> `github-openai/`.
