---
source_id: oa_skills_tools
source_url: https://developers.openai.com/api/docs/guides/tools-skills
category: skills
priority: P1
fetched: 2026-07-07
fetch_method: developers.openai.com returns HTTP 403 to automated fetch; NOT snapshotted. Summary from prior knowledge / BIFL plan.
pull_status: summary_only
verify: open source_url in a browser and replace this body; then set pull_status: fetched.
---

# OpenAI API — Skills / Tools (SUMMARY ONLY — verify against source)

> ⚠️ Not a full snapshot. `developers.openai.com` blocked the automated fetch
> (403). Verify against the live page before relying on exact details.

## What it is

Skills are reusable procedures the model can invoke; listed under the API docs
**Tools** section. They package repeatable operating methods so an agent can
"write once, use everywhere."

## Current packaging

The standalone `openai/skills` repo is **deprecated**. Skills are now packaged as
**Codex plugins** (`openai/plugins`): a plugin folder with
`.codex-plugin/plugin.json` and a `skills/` directory of instruction+script
capabilities.

## For BIFL / M-One

To make the M-One tools (`bifl.search`, review-miner, complaint-classifier)
reusable, package them as a Codex plugin skill (see
`github-openai/openai-plugins-repo-summary.md`).

## TODO
Open the source_url in a browser, paste the real content, set `pull_status: fetched`.
