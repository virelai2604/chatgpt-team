---
source_id: gh_chatgpt_retrieval_plugin
title: openai/chatgpt-retrieval-plugin — reference implementation of a ChatGPT plugin
category: github_reference
source_urls:
  - https://github.com/openai/chatgpt-retrieval-plugin
retrieved_at: 2026-08-15
pinned_commit: b28ddce58474441da332d4e15c6dd60ddaa953ab
fetch_method: shallow clone (--depth 1 --filter=blob:none), files read locally
pull_status: fetched
verify: re-read .well-known/ai-plugin.json upstream before copying any field; the manifest schema has changed before
---

# openai/chatgpt-retrieval-plugin

> Provenance: `fetched` 2026-08-15 at `b28ddce`. **Reference only — not vendored.**
> Per `docs/policies/openai_workspace_index_exclusion_policy.md`, repos are summarised,
> not copied. The five small manifests under `reference/openai/plugin-manifests/` are the
> one deliberate exception.

## Why this one matters most

It is OpenAI's own implementation of the thing this relay is: a FastAPI service that
exposes itself to ChatGPT via `.well-known/ai-plugin.json` + an OpenAPI document. It is
the closest available benchmark for `static/.well-known/ai-plugin.json` and
`/openapi.actions.json`.

| Artefact | Path in that repo | Our equivalent |
|---|---|---|
| plugin manifest | `.well-known/ai-plugin.json` | `static/.well-known/ai-plugin.json` |
| OpenAPI document | `.well-known/openapi.yaml` | `/openapi.actions.json` (generated, not checked in) |
| auth variants | `examples/authentication-methods/{no-auth,oauth,service-http,user-http}` | we use `user-http` |

## What the comparison showed

The relay's manifest already matches the reference shape — `auth.type: user_http` with
`authorization_type: bearer`. It omits two optional fields the reference includes:
`contact_email` and `logo_url`.

One deliberate divergence: the reference checks in a static `openapi.yaml`. This relay
generates its Actions document from the live routes (`app/api/tools_api.py`) because the
previously checked-in file drifted to 32 declared paths against 59 served, 6 of which did
not exist. See `AGENTS.md`.

## Stack

Python / FastAPI / Poetry, with pluggable vector-store datastores. Not a dependency of
this project — read it, do not import it.
