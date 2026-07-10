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
- Sites are for **public/demo/status pages only** — never secret storage.
- `ai.lafiel.me` must stay a live backend, NOT a static Site.

## Repos (P1–P2) — reference, do not vendor

- **openai/openai-node** — official JS/TS SDK (`npm i openai`); use for
  Render/Cloudflare/n8n integrations. `https://github.com/openai/openai-node`
- **openai/openai-cookbook** — examples/notebooks (link; pull specific ones).
  `https://github.com/openai/openai-cookbook`
- **openai/openai-openapi** — the API's OpenAPI source; reference for modeling
  the relay's own schema. `https://github.com/openai/openai-openapi`
- **openai/evals** — evaluation framework for quality/regression gates; add
  later. `https://github.com/openai/evals`
