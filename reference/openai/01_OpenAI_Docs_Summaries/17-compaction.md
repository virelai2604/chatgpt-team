---
source_id: oa_docs_compaction
title: Compaction
category: openai_docs
source_urls:
  - https://developers.openai.com/api/docs/guides/compaction
  - https://developers.openai.com/api/docs/guides/conversation-state
  - https://developers.openai.com/api/reference/resources/responses/methods/compact
  - https://github.com/openai/openai-openapi
  - https://raw.githubusercontent.com/openai/openai-openapi/master/openapi.yaml
fetched: 2026-08-20
fetch_method: openai-openapi openapi.yaml (raw.githubusercontent.com, master, info.version 2.3.0) fetched via curl — extracted the `POST /responses/compact` operation (operationId `Compactconversation`, body `BetaCompactResponseMethodPublicBody`, 200 `CompactResource`) and its example. The two usage modes (server-side threshold vs standalone) and the continuation pattern are web-verified (developers.openai.com is 403-blocked to automated fetch).
pull_status: web_verified
verify: curl -sS https://raw.githubusercontent.com/openai/openai-openapi/master/openapi.yaml | grep -n '/responses/compact'
---

# Compaction

> Provenance: the `POST /responses/compact` operation is quoted from the
> openai-openapi spec (`openapi.yaml`, `info.version: 2.3.0`, fetched
> 2026-08-20). Behavioural detail (server-side threshold mode, continuation
> pattern, ZDR note) is **web-verified** — the guide host 403s automated fetch.

## What it is

Compaction shrinks the context of a **long-running Responses conversation**.
Instead of resending the full turn history each request, the API produces a
**compaction item** that carries forward the key prior state and reasoning in
**fewer tokens**. It is the token-reduction layer for balancing quality vs cost
vs latency as a conversation grows.

## Two modes

**1. Server-side (automatic).** On a normal `POST /responses` create call, set
`context_management` with a `compact_threshold`. When the rendered token count
crosses the threshold, the server compacts automatically — **no separate call**.

**2. Standalone endpoint (explicit).** `POST /v1/responses/compact`
(operationId `Compactconversation`) compacts on demand and returns a compacted
response object (`CompactResource`). Request body (`BetaCompactResponseMethodPublicBody`)
takes the same shape as a response create — `model`, `input` (string or input-item
list), `previous_response_id`, `instructions`. Spec example:

```bash
curl -X POST https://api.openai.com/v1/responses/compact \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -d '{ "model": "gpt-5.1-codex-max", "input": [ ...prior items... ] }'
```

(The request schema is currently a **Beta** variant — treat the exact field set
as subject to change and re-check the API reference.)

## Continuation pattern

After compaction, append new output items to the prior input items, then **drop
everything before the latest compaction item** — that item alone carries the
context needed to continue. This keeps each subsequent request small and cuts
long-tail latency. Combine with `previous_response_id` / `conversation` for
server-side state.

## ZDR

There is a **ZDR-compatible** ("Compaction (advanced)") path for Zero Data
Retention setups where the server does not persist conversation state — see the
conversation-state guide's advanced section.

## Relation to other features

Complementary to **prompt caching** (`16-prompt-caching.md`): compaction reduces
*how many* tokens you send; caching reduces the *cost/latency* of the tokens sent.
