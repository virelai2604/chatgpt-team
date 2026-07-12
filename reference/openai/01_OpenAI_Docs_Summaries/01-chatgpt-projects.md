---
source_id: oa_docs_chatgpt_projects
title: ChatGPT Projects
category: openai_docs
source_urls:
  - https://help.openai.com/en/articles/10169521-projects-in-chatgpt
  - https://openai.com/index/more-ways-to-work-with-your-team/
  - https://x.com/OpenAI/status/1963329936368046111
  - https://chatgpt.com/pricing/
fetched: 2026-07-12
fetch_method: web search (help.openai.com / openai.com / chatgpt.com return 403 to automated fetch here; facts cross-checked via WebSearch)
pull_status: web_verified
verify: Re-check per-plan file caps (Plus shows 20 vs 25 across OpenAI pages), Free availability, and the exact connector list — all are rollout/availability facts and drift often.
---

# ChatGPT Projects

> Provenance: web-verified via WebSearch on 2026-07-12 (OpenAI Help Center, the openai.com "more ways to work with your team" post, and OpenAI's own X announcement). The primary help.openai.com and chatgpt.com pages are 403 to automated fetch here, so wording was confirmed indirectly, not snapshotted. Treat availability and numeric caps as perishable.

## What it is
Projects are workspaces in ChatGPT that keep everything for a long-running effort
in one place: grouped chats ("project chats"), uploaded reference files, and
custom instructions. Conversations started inside a project share context with
that project's files and instructions, so ChatGPT stays on-topic without
re-priming each chat.

## Key facts (verified 2026-07-12)
- **Availability:** Projects are now available to **Free** users as well as paid
  tiers (rolled out from ~Sept 2025). One OpenAI page states "all free and paid
  subscription types globally." Some third-party plan tables instead say "Go and
  above" — reconcile at source before relying on the Free claim. (verify at source)
- **Per-project file uploads** (per OpenAI's X announcement, 2025):
  **Free = 5**, **Plus = 25**, **Pro / Business / Enterprise = 40** files per project.
  Note: OpenAI's own pages have disagreed on the Plus cap (20 vs 25); the
  Projects help page shows 25. (verify at source)
- **Sharing:** Business, Enterprise, and Edu users can **share a project with
  teammates** (shared workspace / collaboration). Consumer tiers (Free/Plus/Pro)
  are single-user projects.
- **Customization:** projects support custom **colors and icons**.
- **Project-only memory** is an opt-in control (see below).
- **Connectors** can surface external sources inside projects (see below).

## How it works (files, instructions, memory, project chats, connectors)
- **Files:** upload reference files that persist at the project level and are
  available to every chat in the project (subject to the per-plan caps above).
- **Instructions:** per-project custom instructions steer tone/scope for all
  chats in that project.
- **Memory:** projects have built-in memory across the project's chats and files.
  When creating a project, users can enable **project-only memory**: with it on,
  ChatGPT uses other conversations *in that project* for context but will **not**
  pull in saved memories from outside the project, and will **not** carry
  anything from the project into chats outside it. This isolates project context.
- **Project chats:** chats created inside a project inherit that project's files,
  instructions, and (project) memory; they are grouped under the project.
- **Connectors:** connectors let ChatGPT pull from external sources for more
  relevant answers. The set referenced in OpenAI's team post includes
  **Gmail, Google Calendar, Microsoft Outlook, Microsoft Teams, SharePoint,
  GitHub, Dropbox, and Box** (enabled via Settings → Connectors; some are
  chat-search vs deep-research scoped, and availability varies by plan/admin).
  Exact connector-in-project support per tier is a moving target. (verify at source)

## Relevance to this repo (ChatGPT Team Relay / BIFL)
Mostly a consumer/Business product surface rather than an API, but two points
matter for a Team-context repo:
- **Project sharing is a Business/Enterprise/Edu capability** — relevant if the
  relay ever mirrors or references shared team projects.
- **Project-only memory** and **connectors** define what context a project chat
  can see; useful as background when reasoning about data boundaries. There is no
  public REST API for Projects documented here — this is a ChatGPT app feature,
  not a platform.openai.com endpoint. Treat as N/A for direct API integration
  unless a Projects API is later confirmed at source.

## Verify / TODO
- Confirm whether **Free** truly includes Projects vs "Go and above" — sources
  conflict. (help.openai.com Projects article; chatgpt.com/pricing)
- Confirm the **Plus per-project file cap** (20 vs 25).
- Confirm the **current connector list** and which connectors work *inside
  projects* (vs global chat) per plan/admin settings.
- Confirm iOS/Android parity and any Team-specific project sharing behavior.
- All above are availability/rollout/connector facts — re-check live before use.
