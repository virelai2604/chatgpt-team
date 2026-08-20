---
source_id: oa_docs_prompt_caching
title: Prompt Caching
category: openai_docs
source_urls:
  - https://developers.openai.com/api/docs/guides/prompt-caching
  - https://platform.openai.com/docs/guides/prompt-caching
  - https://openai.com/index/api-prompt-caching/
  - https://github.com/openai/openai-openapi
  - https://raw.githubusercontent.com/openai/openai-openapi/master/openapi.yaml
fetched: 2026-08-20
fetch_method: openai-openapi openapi.yaml (raw.githubusercontent.com, master, info.version 2.3.0) fetched via curl — extracted the `prompt_cache_key` request property and the `usage.input_tokens_details.cached_tokens` / `input_cached_tokens` usage fields. Discount %, retention window, and rate guidance are web-searched (developers.openai.com / platform.openai.com return 403 to automated fetch).
pull_status: web_verified
verify: curl -sS https://raw.githubusercontent.com/openai/openai-openapi/master/openapi.yaml | grep -n 'prompt_cache_key'
---

# Prompt Caching

> Provenance: the `prompt_cache_key` param and `cached_tokens` usage fields are
> quoted from the openai-openapi spec (`openapi.yaml`, `info.version: 2.3.0`,
> fetched 2026-08-20). Pricing/discount and retention are **web-verified** —
> the doc guide host 403s automated fetch, and these numbers drift, so
> reconcile against the live pricing page before relying on them.

## What it is

Prompt caching reuses the computation for a **prompt prefix** the model has seen
recently, so repeated leading context (system prompt, tool definitions, long
static documents) is billed cheaper and returns faster. It is **automatic** — no
opt-in flag — and applies on both Chat Completions and the Responses API. Caching
engages once the prompt is long enough (historically **≥ 1024 tokens**, then in
increments); shorter prompts are never cached. Creating a cache entry carries **no
extra fee**.

## What you pay / save

- Cache **hits** bill the cached portion of the input at a reduced rate. The
  discount was originally **50%** off cached input tokens and is **larger on newer
  models** (reported up to ~90%). Verify the exact rate per model on the live
  pricing page.
- Only **input** tokens cache. Output tokens are never cached.
- Usage reports the hit: on the Responses API,
  `usage.input_tokens_details.cached_tokens`; billing detail objects also expose
  `input_cached_tokens` / `input_uncached_tokens`.

## `prompt_cache_key` (request field)

From the spec: an optional string (`anyOf: string | null`).

> "Used by OpenAI to cache responses for similar requests to optimize your cache
> hit rates. Replaces the `user` field."

- Route requests that share a large common prefix to the **same** key so they
  land on the same cache. Pair with `safety_identifier` (the two together replace
  the deprecated `user` field).
- Keep per-key traffic modest (guidance seen: **~15 requests/minute** per key) —
  hit rates fall as a single key is fanned across too many machines.

## How to structure prompts for cache hits

- Put **static** content first (system instructions, tool schemas, long reference
  text) and **variable** content (the user's turn) last — caching matches a
  **prefix**, so any change near the front invalidates the rest.
- Retention is ephemeral (minutes of inactivity) by default; the window was
  **extended up to ~24h** on the newest models (change noted around late May
  2026). Do not assume a specific TTL — treat cache as best-effort.

## Relation to other features

Independent of, and composable with, server-side conversation state
(`previous_response_id` / `conversation`) and **compaction** (see
`17-compaction.md`): compaction shrinks *how many* tokens you send; prompt
caching cuts the *cost/latency* of the tokens you do send.
