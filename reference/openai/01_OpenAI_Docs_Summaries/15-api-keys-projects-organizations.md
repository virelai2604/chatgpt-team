---
source_id: oa_docs_keys_projects_orgs
title: API Keys / Projects / Organizations
category: openai_docs
source_urls:
  - https://platform.openai.com/docs/guides/production-best-practices
  - https://platform.openai.com/settings
  - https://help.openai.com
  - https://github.com/openai/openai-python
fetched: 2026-07-12
fetch_method: Headers confirmed from openai-python SDK src/openai/_client.py (raw.githubusercontent.com, main). Hierarchy, roles, service accounts, and scoping web-searched — platform.openai.com, help.openai.com, and developers.openai.com all return 403 to automated fetches.
pull_status: web_verified
verify: curl -sS https://raw.githubusercontent.com/openai/openai-python/main/src/openai/_client.py | grep -nE "OpenAI-Organization|OpenAI-Project|OPENAI_ORG_ID|OPENAI_PROJECT_ID"
---

# API Keys / Projects / Organizations

> Provenance: The two request-header names are confirmed byte-for-byte from the openai-python SDK client source (fetched 2026-07-12); the hierarchy, role names, service-account behavior, and per-project scoping are web-verified against OpenAI Help Center / developer docs because platform.openai.com, help.openai.com, and developers.openai.com are 403-blocked to automated fetches.

## What it is (Org > Project > Key hierarchy)
OpenAI's API platform is a three-level tree:

- **Organization** — top-level account. Billing, members, and org-wide roles live here. Every org has an ID of the form `org-...`.
- **Project** — a workspace inside an org that isolates API keys, service accounts, members, files, rate/usage limits, and (optionally) allowed models. Project IDs look like `proj_...`. An org can hold many projects; resources in one project are isolated from others.
- **API key** — a credential created **inside a specific project** (project-scoped). It carries that project's rate limits, model access, and billing attribution.

This structure gives isolation, independent key rotation, and per-project auditing. Historically OpenAI also had "legacy user keys" bound to a person and to the default project; the current model favors project-scoped keys and service-account keys. *(Web-verified; confirm exact wording at source.)*

## API keys (project-scoped keys, service accounts, roles) — verify
**Key types (web-verified — confirm at platform.openai.com/settings):**
- **Project-scoped keys** — tied to one project; usage and limits count against that project.
- **Service-account keys** — a service account is a **project-scoped bot identity** (a "pseudo-user"), not a person. Only **organization owners or project owners** can create them. Ideal for servers / CI / production because the key survives team-member changes and a compromise is contained to that one service account. *(Web-verified.)*

**API key permission levels (web-verified — verify exact labels at source):**
- **All** — full access to the project's resources.
- **Restricted** — per-capability scoping (e.g. models, threads/assistants, fine-tuning, storage set to read/write/none).
- **Read Only** — read access only.

**Roles (RBAC) — names web-verified, mark "verify at source":**
- **Organization roles:** `owner` and `reader`. Owners manage the org, members, billing, and rate limits; readers can use the API and invite other readers but cannot change billing or invite owners.
- **Project roles:** `owner` and `member`. Project owners manage project settings, budgets, and members; project members can make API requests that read/modify data. (Org-level roles apply across all projects; project-level roles apply only within that project.)
- *Do not treat these four names as exhaustive — enterprise/admin tiers may add roles. Verify the live list at platform.openai.com/settings and the RBAC guide.*

## Request headers (Authorization: Bearer; OpenAI-Organization; OpenAI-Project) — confirm
Every call authenticates with a bearer token; org/project may optionally be pinned via headers. Confirmed from openai-python `src/openai/_client.py` (default-headers block):

```
Authorization: Bearer $OPENAI_API_KEY
OpenAI-Organization: $ORGANIZATION_ID   # org-...
OpenAI-Project: $PROJECT_ID             # proj_...
```

- The SDK reads `organization` from env **`OPENAI_ORG_ID`** and `project` from env **`OPENAI_PROJECT_ID`**, then emits them as the `OpenAI-Organization` / `OpenAI-Project` headers only when set (otherwise omitted). *(Confirmed in SDK source, lines ~235–240 and ~528–529.)*
- These headers are primarily needed when a caller belongs to **multiple organizations** or uses a **legacy user key** that can see multiple projects. A project-scoped key or service-account key already belongs to exactly one project, so the headers are usually redundant with those. *(Web-verified.)*
- Mismatch caveat: sending an `OpenAI-Organization` that doesn't match the key's org yields `401` "OpenAI-Organization header should match organization for API key." *(Web-verified from community reports; confirm at source.)*

## Best practices (never in code, rotate, scope)
From production-best-practices guidance *(web-verified — page 403-blocked to fetch, confirm wording at source)*:
- **Never hardcode keys** in source, client-side code, or git. Load from environment variables / a secret manager.
- **Rotate keys** periodically and immediately on suspected exposure; delete unused keys.
- **Scope narrowly** — one project (and ideally one service account) per workload; use Restricted/Read-Only permissions where possible so a leaked key has minimal blast radius.
- **Use service accounts for automation** rather than a person's user key, so credentials outlive staff changes.
- **Separate projects** for prod vs. dev/staging to keep rate limits, usage, and billing distinct.

## Relevance to this repo (OPENAI_API_KEY server-side only; RELAY_KEY is separate client-facing auth; keys in Render env, sync:false)
- `render.yaml` declares **`OPENAI_API_KEY`** with `sync: false` — the real upstream key is injected via the Render dashboard, never committed. This is the single server-side credential the relay uses to call `https://api.openai.com/v1` (`OPENAI_API_BASE`). It should be a **project-scoped or service-account key**, matching best practice above.
- **`RELAY_KEY`** (also `sync: false`) is a **separate, client-facing** secret gating the relay itself (`RELAY_AUTH_ENABLED: true`). It is not an OpenAI credential — clients present `RELAY_KEY` to the relay; the relay presents `OPENAI_API_KEY` to OpenAI. Keeping the two distinct means the upstream key is never exposed to relay clients.
- The repo does **not** currently set `OPENAI_ORG_ID` / `OPENAI_PROJECT_ID` in `render.yaml`. With a project-scoped key that is fine (project is implied by the key). If a multi-org key were ever used, those env vars would need to be added so the SDK emits the pinning headers.
- `CHATGPT_ACTIONS_SECRET` is a third `sync: false` secret, unrelated to OpenAI key auth.

## Verify / TODO
- Confirm exact org/project **role names** and whether additional roles exist (admin/billing tiers) at platform.openai.com/settings and the RBAC guide — developers.openai.com/api/docs/guides/rbac is 403 to fetch.
- Confirm the **API key permission labels** (All / Restricted / Read Only) and the restricted-scope capability list against the live "Assign API Key Permissions" help article.
- Confirm production-best-practices key-handling wording directly once platform.openai.com is reachable.
- Verify whether service-account keys are the only recommended production key type in July 2026, or whether project-scoped personal keys remain first-class.
