
---

```md
# GOVERNANCE.md

This document defines how the **chatgpt-team-relay** is maintained to preserve a **BIFL** posture: stable, conservative, low-churn, and safe to operate long-term.

## Guiding principles

1. **Surface area is liability**
   - Prefer explicit, minimal routes over generic forwarding.
   - Do not expand proxy allowlists without demonstrated product need.

2. **Hard separation of concerns**
   - `/v1/actions/*` = Actions-safe wrappers only
   - `/v1/proxy` = allowlisted JSON forwarding only
   - `/v1/*` = canonical endpoints where safe
   - Internal-only endpoints must not leak into public schema

3. **Guardrails must fail closed**
   - Every endpoint must be classified into exactly one policy bucket.
   - Unknown/unclassified endpoints are treated as defects.

## Roles & decision rights

- **Maintainers**:
  - Approve changes to routing, proxy allowlists, wrappers, security policy, and OpenAPI curation.
  - Own release tagging and versioning decisions.

- **Contributors**:
  - May propose and implement features following `CONTRIBUTING.md`.
  - Must not widen proxy allowlist or expose new Actions endpoints without maintainer approval.

## API contract and policy buckets

Every endpoint in `/openapi.json` must fall into exactly one of:

1. **ACTIONS_DIRECT**
   - Explicitly included in `openapi.actions.json`
   - Must be Actions-safe (no multipart required from Actions; no binary downloads)

2. **PROXY_HARNESS**
   - Allowlisted by `/v1/proxy` policy and safe to forward
   - Must not include:
     - multipart endpoints
     - colon paths
     - binary `/content` downloads

3. **WRAPPER_REQUIRED**
   - The endpoint exists in the full schema but is blocked from proxy/Actions direct use.
   - A wrapper is required if the product needs Actions access.
   - Examples:
     - multipart file uploads
     - resumable uploads
     - SSE streaming (`/v1/responses:stream`)
     - video multipart endpoints

4. **EXCLUDED**
   - Explicitly not supported or intentionally hidden.
   - Examples:
     - wildcard routers
     - binary `/content` downloads
     - legacy or metadata-only paths
     - local-only helpers not meant for clients

## OpenAPI governance

- `GET /openapi.json` is the **full schema** for the relay runtime.
- `GET /openapi.actions.json` is the **Actions subset** and is a curated contract.

Rules:
- Actions OpenAPI must not contain duplicate `operationId`.
- Actions OpenAPI must not contain wildcards.
- Actions OpenAPI must not expose internal-only endpoints.
- Any new Actions-exposed endpoint must have a stable `operation_id` and tests.

## Internal-only endpoint rule

Internal operator endpoints (e.g., `/actions/system/info`) are permitted only if:

- Not included in `openapi.actions.json`
- Preferably excluded from `openapi.json` as well (when feasible)
- Not proxy-allowlisted
- Documented as internal metadata
- Still classified by the coverage guardrail (not UNKNOWN)

This prevents accidental “API surface creep.”

## Change control

### Required checks for any PR touching routes/proxy/OpenAPI

- `pytest -m integration` (against local relay)
- `./scripts/coverage_report.sh` must report **no UNKNOWN**
- `curl /openapi.actions.json` must validate and contain no duplicate operationIds

### Proxy allowlist expansion (high scrutiny)

Allowlist additions require:
- A clear product requirement
- Security review notes (why safe to forward)
- Additional integration tests that exercise the new allowlisted path(s)
- Coverage report confirming bucket mapping

## Versioning and releases

- Patch releases: bug fixes, docs, test improvements (no API contract change)
- Minor releases: additive features that preserve backward compatibility
- Major releases: breaking changes to routes, schemas, or policy behavior

Tag releases in Git (e.g., `v1.0.0`, `v1.1.0`).

---

## v1.1 Change Policy (Incremental, Low-Risk)

The v1.1 goal is **incremental feature additions without refactoring risk**. The policy below is designed to prevent destabilization.

### Scope allowed in v1.1

Allowed categories:

1. **New wrappers (prefer over proxy expansion)**
   - Add Actions-friendly wrappers for endpoints Actions cannot call directly.
   - Prefer JSON→multipart (base64) conversion when needed.

2. **Small allowlist expansions ONLY with tests**
   - Only if an endpoint is strictly JSON, low-risk, and needed.
   - Must add explicit tests and update coverage expectations.

3. **Operational hardening**
   - Better error mapping, timeouts, logging consistency
   - Documentation improvements and clearer runbooks

4. **New explicit exclusions**
   - If OpenAI adds new endpoints that are unsafe or irrelevant, explicitly exclude them.

### Scope not allowed in v1.1 (unless escalated)

- Re-architecting proxy policy or routing system
- Broad allowlisting of large families (e.g., conversations wildcard-style)
- Exposing binary `/content` or multipart endpoints to Actions
- Introducing wildcard routes into Actions schema
- Adding WebSocket bridges for Actions (high complexity) unless product requires it

### Realtime policy (v1.1)

- Keep Actions support limited to **HTTP session creation** unless a real business requirement appears.
- WebSocket relay is supported for non-Actions clients via `/v1/realtime/ws`.
- Any REST-to-WS bridge proposal requires a design review and a risk memo.

### Video policy (v1.1)

- Keep the existing Actions wrappers for video multipart usage.
- Add video polling/status wrappers only if Actions must manage async jobs.
- Do not expose `/content` downloads.

### Definition of done for any v1.1 change

A change is “done” only when:

- Tests added/updated (integration where appropriate)
- Coverage report has **no UNKNOWN**
- Actions OpenAPI remains curated, minimal, and duplicate-free
- No proxy relaxations without explicit, reviewed allowlist changes

---

## Escalation path for risky changes

If a proposed change increases surface area materially:

1. Write a short proposal (1–2 pages max) describing:
   - Endpoint(s)
   - Risk class (Actions-safe vs proxy allowlist vs excluded)
   - Abuse scenarios and mitigations
   - Test plan

2. Maintainers approve before implementation begins.

This ensures the relay remains stable and maintainable long-term.
