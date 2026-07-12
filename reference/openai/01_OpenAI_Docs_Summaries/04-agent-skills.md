---
source_id: oa_docs_agent_skills
title: Agent Skills
category: openai_docs
source_urls:
  - https://github.com/openai/plugins
  - https://github.com/openai/skills
  - https://developers.openai.com/codex/skills
fetched: 2026-07-12
fetch_method: WebFetch of raw.githubusercontent.com/openai/plugins (README, a real plugin.json, a real SKILL.md, and the plugin-json-spec.md) + the GitHub git-tree API; WebFetch of github.com/openai/skills for its deprecation notice. developers.openai.com is 403-blocked, so its skills guide is corroborated via WebSearch only.
pull_status: fetched
verify: Open https://github.com/openai/plugins and https://developers.openai.com/codex/skills to confirm the plugin.json field set and SKILL.md frontmatter keys, which are still moving month to month.
---

# Agent Skills

> Provenance: Compiled 2026-07-12 by directly fetching the `openai/plugins` repo (README, `plugins/notion/.codex-plugin/plugin.json`, `plugins/airtable/skills/airtable-overview/SKILL.md`, and `.agents/skills/plugin-creator/references/plugin-json-spec.md`) plus the repo git-tree, and confirming the `openai/skills` deprecation notice from its own README; the developers.openai.com skills guide could not be fetched (403) and is reflected only where WebSearch corroborated it.

## What it is
A "skill" is OpenAI's authoring format for a reusable, model-invoked workflow for Codex (available in the ChatGPT desktop app, Codex CLI, and the IDE extension). Each skill is a folder with a required `SKILL.md` (YAML frontmatter + markdown instructions) plus optional bundled resources. Codex is shown each skill's name, description, and file path up front, and loads the full `SKILL.md` only when it decides to use the skill — an implicit match against the description, or an explicit invocation (`/skills`, or `$` to mention a skill). Skills are the *authoring* unit; **plugins are the installable distribution unit** that bundles one or more skills (and optionally an app/MCP integration) for others to install. (Skill-loading/invocation mechanics per WebSearch of the developers.openai.com Codex skills guide; verify at source.)

## Current packaging (openai/plugins — Codex plugins)
Per the fetched `openai/plugins` README, plugins live under `plugins/<name>/` with:
- **Required:** a `.codex-plugin/plugin.json` manifest
- **Optional companion surfaces:** a `skills/` directory, `.app.json`, `.mcp.json`, plugin-level `agents/`, `commands/`, `hooks.json`, `assets/`, and other supporting files

A skill is therefore no longer a standalone repo artifact — it ships *inside* a plugin's `skills/` directory, wired up by the manifest's `skills` field.

**`plugin.json` fields** (quoted from `.agents/skills/plugin-creator/references/plugin-json-spec.md`):
- Required: `name` — "Plugin identifier (kebab-case, no spaces). Required if `plugin.json` is provided"
- Optional: `version`, `description`, `author` (name/email/url object), `homepage`, `repository`, `license`, `keywords`, `skills` ("Relative path to skill directories/files"), `hooks`, `mcpServers`, `apps`, `interface` (UX metadata object: displayName, shortDescription, longDescription, etc.)
- Spec note: "skills, hooks, and mcpServers are supplemented on top of default component discovery; they do not replace defaults."

**Real manifest excerpt** (`plugins/notion/.codex-plugin/plugin.json`, fetched verbatim):
```json
{
  "name": "notion",
  "version": "0.1.5",
  "description": "Notion workflows for implementation planning, research synthesis, meeting preparation, and knowledge capture.",
  "author": { "name": "OpenAI", "email": "support@openai.com", "url": "https://openai.com/" },
  "license": "MIT",
  "skills": "./skills/",
  "apps": "./.app.json",
  "mcpServers": "./.mcp.json",
  "interface": { "displayName": "Notion", "category": "Productivity", "capabilities": ["Interactive","Read","Write"] }
}
```

**Real `SKILL.md` frontmatter** (`plugins/airtable/skills/airtable-overview/SKILL.md`, fetched verbatim):
```yaml
---
name: airtable-overview
description: Explains what Airtable is and how data is structured — bases, tables, fields, records, views, automations, and interfaces. Use when you need context about the Airtable data model.
license: MIT
metadata:
  version: '1.0.0'
  author: airtable
---
```
So the observed per-skill frontmatter keys are `name`, `description`, `license`, and a `metadata` map (`version`, `author`). Directory convention: `plugins/<name>/skills/<skill-name>/SKILL.md`, with skills grouped under a plugin's `skills/` folder. (WebSearch additionally reports optional `scripts/`, `references/`, `assets/` folders and an `agents/openai.yaml` for UI metadata; not verified against a fetched skill here — verify at source.)

## Deprecation note (openai/skills)
The standalone `openai/skills` repo is **deprecated**. Its own README states: "This repository is deprecated. For current Codex skill and plugin examples, use the OpenAI Plugins repository," pointing to https://github.com/openai/plugins and the developers.openai.com "Build plugins" guide. Skills are now authored and shipped **as plugins**, not from a separate skills catalog. (Confirmed by fetching github.com/openai/skills directly on 2026-07-12.)

## Relevance to this repo (packaging bifl.search / M-One tools as a skill)
This repo already has candidate skill payloads:
- `examples/bifl/` — batched embedder scripts (`embed_openai.py`, `embed_bge_m3.py`) that replace a slow Ollama path for BIFL indexing/search.
- `examples/mone/` — self-contained M-One business tools (e.g. `review_miner.py`) built on the official `openai-python` SDK.

To surface these inside Codex, wrap each as a skill folder (`SKILL.md` with `name` + `description` + `license`, plus a `scripts/`-style layout holding the existing Python), then bundle them under one plugin: `plugins/<name>/.codex-plugin/plugin.json` with `"skills": "./skills/"` and the two skill folders beneath it. The `description` line is load-bearing — it is all Codex sees before choosing the skill, so it should name the trigger ("Use when embedding BIFL chunks / mining M-One reviews…"). Distribute the plugin (not a bare skill) since these are reusable and there is more than one.

## Verify / TODO
- [ ] Fetch the developers.openai.com Codex skills + Build-plugins guides (currently 403 here) to confirm the authoritative SKILL.md frontmatter key list and whether `agents/openai.yaml`, `scripts/`, `references/`, `assets/` are required or optional.
- [ ] Confirm the `plugin.json` required/optional split against the live `plugin-json-spec.md` before publishing a manifest.
- [ ] Decide plugin `name` + marketplace entry (`.agents/plugins/marketplace.json` in openai/plugins) if these skills are ever meant to be installable outside this repo.
- [ ] Re-check the `openai/skills` deprecation status periodically — deprecated repos sometimes get fully archived/removed.
