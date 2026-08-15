# Vendored: openai/openai-developers-for-claude

This directory is a **vendored copy** of the OpenAI Developers plugin for Claude Code.

| Field | Value |
|---|---|
| Upstream | https://github.com/openai/openai-developers-for-claude |
| Pinned commit | `3c5c0debdec2695f657c5f1b99a32df6d23dd0ed` |
| Retrieved | 2026-08-15 |
| License | Apache-2.0 (see `LICENSE`) |
| Method | `git clone --filter=blob:none`, checked out at the pinned commit, runtime files copied verbatim |

## What is included

The runtime plugin bundle, byte-for-byte from upstream:

- `.claude-plugin/marketplace.json` — marketplace `openai-developers`
- `plugins/openai-developers/` — plugin metadata, `.mcp.json`, and 6 skills
  (`openai-docs`, `agents-sdk`, `build-chatgpt-app`, `chatgpt-app-submission`,
  `openai-api-troubleshooting`, `openai-platform-api-key`)
- `LICENSE`, `README.md`, `SECURITY.md`

## What is excluded

Upstream development harness, not needed to run the plugin:

- `package.json`, `tests/` (upstream's own structure/contract tests)
- `.gitignore`

## MCP dependency

`plugins/openai-developers/.mcp.json` bundles an HTTP MCP server:
`https://developers.openai.com/mcp?source=claude`. That host is known to return
**403 to automated fetch from sandboxed environments** — the docs MCP works from a
normally-networked Claude Code client but may be unreachable from a restricted
sandbox. This is expected, not a vendoring error.

## Updating

Re-clone upstream at a newer commit and re-copy the runtime files; bump the pinned
commit above and in `reference/manifests/openai_upstream_pins_20260815.json`.
Do not hand-edit the vendored files — they are meant to mirror upstream.
