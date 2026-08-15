---
source_id: gh_chatgpt_retrieval_plugin_manifests
title: OpenAI's canonical ai-plugin.json manifests (all four auth types)
category: github_reference
source_urls:
  - https://github.com/openai/chatgpt-retrieval-plugin/blob/main/.well-known/ai-plugin.json
  - https://github.com/openai/chatgpt-retrieval-plugin/tree/main/examples/authentication-methods
retrieved_at: 2026-08-15
pinned_commit: b28ddce58474441da332d4e15c6dd60ddaa953ab
fetch_method: copied verbatim from a shallow clone of openai/chatgpt-retrieval-plugin
pull_status: fetched
verify: re-read upstream before copying any field — the plugin manifest schema has changed before
---

# Reference plugin manifests

Five small JSON files copied verbatim from `openai/chatgpt-retrieval-plugin` at
`b28ddce`. This is a deliberate, narrow exception to the "reference, do not vendor" rule
in `docs/policies/openai_workspace_index_exclusion_policy.md`: they are tiny, authored by
OpenAI, provenance-stamped, and their value is in being byte-exact rather than described.

| File | `auth.type` |
|---|---|
| `ai-plugin.reference.json` | `user_http` — the repo's own live manifest |
| `ai-plugin.no-auth.json` | `none` |
| `ai-plugin.oauth.json` | `oauth` |
| `ai-plugin.service-http.json` | `service_http` |
| `ai-plugin.user-http.json` | `user_http` |

## How this relay compares

`static/.well-known/ai-plugin.json` **matches the reference shape**: `auth.type:
user_http` with `authorization_type: bearer`, which is the correct choice for a relay
where each caller presents their own `RELAY_KEY`.

Two optional fields the reference carries and this relay omits:

- `contact_email`
- `logo_url` — deliberately absent. `tests/test_plugin_manifest.py` asserts that if
  `logo_url` is declared the file must exist; it previously pointed at a missing asset.

One deliberate divergence beyond the manifest itself: the reference checks in a static
`.well-known/openapi.yaml`. This relay generates its Actions document from live routes
(`app/api/tools_api.py`), because the checked-in file it used to ship drifted to 32
declared paths against 59 served, six of which did not exist. See `AGENTS.md`.

## Not a template

Do not copy `ai-plugin.reference.json` over the relay's manifest. It carries
`your-app-url.com` placeholders and `has_user_authentication: false`, both wrong here.
Use it to check *shape*, not content.
