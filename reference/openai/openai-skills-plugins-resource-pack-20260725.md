---
source_id: openai_skills_plugins_resource_pack
category: skills_plugins_index
priority: P1
generated: 2026-07-25
reconciled: 2026-08-15
fetch_method: openai/plugins skill paths verified via raw.githubusercontent.com (2026-08-15); developers.openai.com portal links NOT machine-verified (403 to automated fetch).
note: Distilled + status-corrected version of a user-supplied resource pack. Pointer-only; nothing vendored.
---

# OpenAI Skills & Plugins — Resource Pack (reconciled)

Curated, fetchable pointers for OpenAI Skills/Plugins, the Agents SDK, and the
Agent Skills open standard. **Pointer-only** — no upstream trees are vendored.

This is a distilled version of a resource pack authored **2026-07-25**. Its
material has been reconciled against the current source state on **2026-08-15**;
where the original pack conflicted with the sources, the sources win (see the
status banner below).

## ⚠️ Status reconciliation — `openai/skills` is deprecated

The original pack's headline decision ("`openai/skills` is the current official
Agent Skills catalog … do not treat plugins as a replacement") is **superseded**.
The `openai/skills` README states verbatim (re-confirmed 2026-08-15, HEAD
`49f948faa9258a0c61caceaf225e179651397431`):

> "This repository is deprecated. For current Codex skill and plugin examples,
> use the OpenAI Plugins repository."

**Consequence:** author and ship skills **as Codex plugins** via
[`openai/plugins`](https://github.com/openai/plugins). Do **not** fetch or rely
on `raw.githubusercontent.com/openai/skills/...` paths as a current source —
they resolve only as frozen history of a deprecated repo. This matches the
repo's existing coverage:

- `reference/openai/01_OpenAI_Docs_Summaries/04-agent-skills.md` (deprecation, verbatim)
- `reference/openai/github-openai/openai-plugins-repo-summary.md` (plugin layout)
- `reference/openai/tools-skills/openai-tools-skills.md` (Skills/Tools guide)

## Current canonical source — `openai/plugins`

| Resource | Human link | Raw / fetchable |
|---|---|---|
| Plugins repository (README) | https://github.com/openai/plugins | https://raw.githubusercontent.com/openai/plugins/main/README.md |
| `openai-developers` plugin | https://github.com/openai/plugins/tree/main/plugins/openai-developers | — |

Provenance pin: `openai/plugins` HEAD `11c74d6ba24d3a6d48f54a194cd00ef3beea18f9`
(recorded in `reference/manifests/openai_upstream_pins_20260815.json`).

### High-value `openai-developers` plugin skills

All five paths verified to resolve on 2026-08-15. Keep available for
project-specific invocation; do not blanket-activate.

| Skill | Raw / fetchable link | Use |
|---|---|---|
| `agents-sdk` | https://raw.githubusercontent.com/openai/plugins/main/plugins/openai-developers/skills/agents-sdk/SKILL.md | Build, run, deploy, evaluate Agents SDK apps from Codex |
| `build-chatgpt-app` | https://raw.githubusercontent.com/openai/plugins/main/plugins/openai-developers/skills/build-chatgpt-app/SKILL.md | Build ChatGPT Apps (MCP server + widget/tool UI) |
| `chatgpt-app-submission` | https://raw.githubusercontent.com/openai/plugins/main/plugins/openai-developers/skills/chatgpt-app-submission/SKILL.md | Generate/review `chatgpt-app-submission.json`, tool hints, tests |
| `openai-api-troubleshooting` | https://raw.githubusercontent.com/openai/plugins/main/plugins/openai-developers/skills/openai-api-troubleshooting/SKILL.md | Classify OpenAI API failures and route to the fix |
| `openai-platform-api-key` | https://raw.githubusercontent.com/openai/plugins/main/plugins/openai-developers/skills/openai-platform-api-key/SKILL.md | Create/configure/use OpenAI API credentials safely |

Other plugin examples worth studying as architecture references (not
auto-installing): `figma`, `notion`, `build-web-apps`, `build-ios-apps`,
`build-macos-apps`, `expo`, `google-slides`, `remotion`, `netlify`.

## Agents SDK — canonical docs

Portal links below were **not** machine-verified (docs host 403s automated
fetch); treat as canonical URLs to open in a browser. Distilled SDK summaries
already live in `reference/openai/agents-sdk/`.

| Resource | Link |
|---|---|
| Agents SDK docs (home) | https://openai.github.io/openai-agents-python/ |
| Quickstart | https://openai.github.io/openai-agents-python/quickstart/ |
| Tools | https://openai.github.io/openai-agents-python/tools/ |
| Running agents | https://openai.github.io/openai-agents-python/running_agents/ |
| Models | https://openai.github.io/openai-agents-python/models/ |
| Usage accounting | https://openai.github.io/openai-agents-python/usage/ |
| Source repo | https://github.com/openai/openai-agents-python |

**Decision rule:** Responses API directly when you want to own the tool loop and
lifecycle; Agents SDK for managed turns, guardrails, handoffs, sessions,
tracing; **skills** (packaged as plugins) for reusable procedures; **MCP
server/connector** for live external data or actions.

## Agent Skills open standard

| Resource | Link |
|---|---|
| Standard overview | https://agentskills.io/ |
| Specification (frontmatter, layout, progressive disclosure) | https://agentskills.io/specification |
| GitHub org | https://github.com/agentskills |

## User's related GitHub forks — presence only (sync UNVERIFIED)

Listed in the source pack under the account `virelai2604`. Recorded here as
pointers only. These are **not** in this session's repo scope, were **not**
inspected, and their sync against upstream is **not** verified — do not treat any
as a source of truth without confirming fork ancestry and diffing against
upstream first.

- Working sources: `agent-skills`, `codex-plugins`, `chatgpt-team`, `chatgpt-exporter-BIFL`, `openai-cookbook`, `openai-agents-python`, `codex`, `evals`
- SDK/use-case refs: `openai-python`, `openai-node`, `openai-responses-starter-app`, `openai-structured-outputs-samples`, `openai-realtime-agents`, `whisper`, `tiktoken`, `model_spec`
- Historical / migration-review: `openai-assistants-quickstart`, `chatgpt-retrieval-plugin` (historical retrieval architecture — not a current default), `openai-quickstart-node`, `gpt-5-coding-examples`

## Skill install / inspection gate

Before activating any externally-sourced skill or plugin (in addition to the
repo's `docs/policies/` write-target and index-exclusion rules):

1. Record source URL, commit SHA, date, and SHA-256; preserve the original.
2. Read `SKILL.md` and every executable script it references.
3. Enumerate shell commands, network calls, MCP servers, installs, and write paths.
4. Check plugin manifest (`.codex-plugin/plugin.json`) / `agents/openai.yaml` deps + triggers.
5. Review the license.
6. Test in a disposable directory or container; activate only when output matches the stated contract.
7. Check trigger-name overlap with already-active skills.
8. Keep private paths, business data, and secrets out of any public package.
