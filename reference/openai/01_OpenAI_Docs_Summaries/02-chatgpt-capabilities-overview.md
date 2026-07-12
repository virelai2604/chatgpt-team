---
source_id: oa_docs_chatgpt_capabilities
title: ChatGPT Capabilities Overview
category: openai_docs
source_urls:
  - https://openai.com/chatgpt
  - https://help.openai.com
fetched: 2026-07-12
fetch_method: WebSearch only. Direct WebFetch of openai.com / help.openai.com is blocked (403), so this summary is built from OpenAI Help Center article titles/snippets surfaced in search plus third-party corroboration.
pull_status: web_verified
verify: Open each linked help.openai.com article and the in-product Plans page (chatgpt.com/pricing) to confirm exact plan gating, limits, and model names — these change monthly.
---

# ChatGPT Capabilities Overview

> Provenance: Compiled 2026-07-12 from OpenAI Help Center articles located via WebSearch (openai.com and help.openai.com cannot be fetched directly from this environment) plus third-party pricing/feature roundups; plan-tier and model-name specifics that rest only on third-party sources are flagged "verify at source".

## What it is
ChatGPT is OpenAI's consumer/enterprise assistant product (web + mobile + desktop apps) — distinct from the OpenAI API. It bundles a chat model with a growing set of built-in tools (web search, research, canvas, voice, tasks, an autonomous agent, connectors, custom GPTs, image and video generation, and memory). Feature access is gated by subscription tier: Free, Go, Plus, Pro, Business, and Enterprise (plus Edu). NOTE: the plan historically called "ChatGPT Team" appears to have been rebranded to "ChatGPT Business" — verify at source before relying on either name.

## Capabilities (verified 2026-07-12)
Each row lists a capability, what it does, and a plan/availability note. Plan gating is the fastest-changing part of this doc — treat every "plan" cell as provisional and confirm in-product.

| Capability | What it does | Plan / availability note |
| --- | --- | --- |
| Web search / browsing | Single-shot web lookups with cited answers inside a normal chat. | Broadly available incl. Free; verify at source. |
| Deep research | Multi-step research agent: issues many sequential queries, reads dozens of pages, returns a structured cited report (minutes-long runs). Can be scoped to trusted sites / connected via MCP. | Plus and up; monthly session caps scale by tier (Pro much higher). Verify caps at source. Ref: openai.com/index/introducing-deep-research |
| Canvas | Side-by-side collaborative document/code editing surface. | Plus and up (per third-party); verify at source. |
| Voice / Advanced Voice | Real-time spoken conversation with interruption. Third-party sources report Advanced Voice was rebranded/replaced by a full-duplex "Live" / "GPT-Live" experience in July 2026 (mini model on Free, full model on paid). | Some voice on Free (short daily preview); higher limits on paid. Model names + "Live" rebrand are third-party — verify at help.openai.com/en/articles/8400625 |
| Scheduled tasks | Proactive/recurring tasks: reminders, daily briefings, monitoring for changes and notifying you. Runs at most once/hour; pauses if chat is deleted. Replaced the earlier "Pulse" feature. | Plus, Pro, Business, Enterprise (and Go). Active-task caps differ by tier. Ref: help.openai.com/en/articles/10291617 |
| Agent mode ("ChatGPT agent") | Autonomous agent that browses websites, operates a virtual computer/browser, fills forms, and executes multi-step workflows, combining browsing + deep research + action. | Plus, Pro, Business (via composer tools). Verify at source. Ref: help.openai.com/en/articles/11752874 |
| Connectors | Link external apps / MCP servers to bring in context and take actions (e.g., Drive, calendar, internal tools). | Business advertises 60+ connectors; availability varies by tier/admin. Verify at source. |
| Custom GPTs / GPT Store | Build and share configured assistants (instructions, conversation starters, uploaded knowledge, tool capabilities). GPTs run stateless — no saved memory / custom instructions carried between chats. | Building GPTs on Plus and up; using GPTs broadly available. Ref: help.openai.com/en/articles/8554407 |
| Image generation | In-chat image creation/editing ("ChatGPT Images", built on 4o-era image gen) as the default generator. | Free, Plus, Pro, Business; Enterprise/Edu rollout followed. Ref: help.openai.com/en/articles/11084440 |
| Video generation (Sora) | Text/image-to-video generation; a higher-quality "Pro" model tier exists. | Sora 2 broadly available with limits; Sora 2 Pro on Pro tier. Ref: openai.com/index/sora-2 |
| Memory | Persists user facts/preferences across chats to personalize responses (does not apply inside GPTs). | Paid tiers get longer/expanded memory; verify at source. |
| Projects | Group chats, files, and instructions into a persistent workspace. | Plus and up (per third-party); verify at source. |
| Codex (coding agent) | Software-engineering agent for multi-file coding tasks. | Plus, Business and up; verify at source. |

## Notable recent changes
- Scheduled tasks launched broadly and gained a dedicated hub (mid-2026), replacing "Pulse." Ref: help.openai.com/en/articles/10291617
- Deep research can now (Feb 2026, per third-party) connect to MCP/apps and restrict searches to trusted sites.
- Voice: third-party reporting says Advanced Voice was replaced by a full-duplex "Live" / "GPT-Live" model in July 2026 — NOT yet confirmed here from an official page; verify at help.openai.com/en/articles/8400625.
- Model/pricing churn: third-party roundups cite a "GPT-5.6" flagship and multiple paid tiers (Go/Plus/Pro at various prices). These specific model names and prices are UNVERIFIED against an official page and must be confirmed at chatgpt.com/pricing before use. Do not quote them as fact.

## Relevance to this repo
This repo concerns the ChatGPT *product* and, by its name ("chatgpt-team"), the Team/Business plan surface — which is a different thing from the OpenAI *API relay*. Capabilities here (agent mode, canvas, connectors, GPTs, scheduled tasks, in-app image/video, memory) are ChatGPT app features and are generally NOT exposed as API endpoints; conversely, API models/features are not automatically present in ChatGPT. Keep product-plan gating separate from API model availability when reasoning about what "the relay" can do. Also confirm whether this repo's "Team" plan maps to the current "Business" plan (apparent rebrand) before assuming feature parity.

## Verify / TODO
- Confirm current plan lineup and prices at chatgpt.com/pricing (Free / Go / Plus / Pro / Business / Enterprise / Edu) — third-party numbers here are unverified.
- Confirm exact plan gating + limits for: deep research sessions, scheduled-task counts, agent mode, canvas, voice, connectors, Projects, Codex.
- Confirm the "Advanced Voice → Live/GPT-Live" rebrand and the current flagship model name against an official OpenAI page (help center / release notes at help.openai.com/en/articles/6825453).
- Confirm whether "ChatGPT Team" is now "ChatGPT Business" and what that means for this repo.
- Re-fetch help.openai.com articles directly if/when the 403 block is lifted, to replace third-party corroboration with primary text.
