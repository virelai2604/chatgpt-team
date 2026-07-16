---
source_id: gh_openai_node
title: openai/openai-node (official JS/TS SDK) — README + changelog metadata
category: node_sdk_metadata
source_urls:
  - https://github.com/openai/openai-node
  - https://raw.githubusercontent.com/openai/openai-node/master/README.md
  - https://raw.githubusercontent.com/openai/openai-node/master/CHANGELOG.md
retrieved_at: 2026-07-16
fetch_method: WebFetch of README.md + CHANGELOG.md on raw.githubusercontent.com (GitHub is fetchable)
pull_status: fetched
verify: version moves fast — check npm (openai) / CHANGELOG for the current release before pinning
---

# openai/openai-node — SDK metadata

> Provenance: `fetched` (2026-07-16) from the repo `README.md` + `CHANGELOG.md`
> (GitHub raw is fetchable). **Metadata only** — package/runtime/version facts, not an
> API walkthrough. The Node **Agents** SDK is a separate repo (`agents-sdk/openai-agents-js.md`).

## Package

| Field | Value |
|---|---|
| **Package** | `openai` (npm) |
| **Install** | `npm install openai` |
| **Language** | TypeScript / JavaScript |
| **Latest version** | **6.47.0** (2026-07-14) — *verify before pinning; moves fast* |

## Runtime support

- **Node.js 20 LTS+** (minimum).
- Also: **Deno** 1.28+, **Bun** 1.0+, **Cloudflare Workers**, **Vercel Edge**, **Nitro** 2.6+,
  Jest 28+ (node env), and **browsers** (only with `dangerouslyAllowBrowser: true`).

## Client instantiation (metadata)

```ts
import OpenAI from 'openai';
const client = new OpenAI({ apiKey: process.env['OPENAI_API_KEY'] });
```

- **Custom base URL:** the client accepts a **`baseURL`** option — this is the hook for
  routing SDK calls through the relay (`https://ai.lafiel.me/v1`). Confirm exact option
  name/casing against the current README before wiring.
- **Alt auth:** supports workload-identity auth via cloud identity providers
  (Kubernetes / Azure / GCP) as an alternative to a static API key.

## Primary API surfaces

- **Responses API** — `client.responses.create()`
- **Chat Completions** — `client.chat.completions.create()`

## Recent changelog (top 5, one-liners)

| Version | Summary |
|---|---|
| **6.47.0** (2026-07-14) | async event iterators; streaming file upload; `ResponseStream` improvements |
| 6.46.0 | GPT-5.6-sol model updates; array-delta fixes for assistants |
| 6.45.0 | `afterCompletion` hook in `runTools`; realtime sideband connections; response helpers |
| 6.44.0 | OpenAPI spec updates |
| 6.43.0 | repo converted to pnpm; TypeScript config fixes |

## Relevance to this repo (ChatGPT Team Relay / BIFL)

- This is the **base OpenAI SDK** a Node relay client would use; the **`baseURL`** option
  is what points it at `ai.lafiel.me/v1` (vs the Agents SDK, which is the higher-level
  agent-orchestration layer).
- Node 20+ is the floor — align any relay-side Node service accordingly.

## Verify / TODO

- Re-check the **latest version** on npm / `CHANGELOG.md` before pinning (6.47.0 as of pull).
- Confirm the exact **`baseURL`** option name/casing from the live README when wiring the
  relay route.
