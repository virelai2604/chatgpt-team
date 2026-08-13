---
source_id: gh_openai_python
source_url: https://github.com/openai/openai-python
category: sdk_python
priority: P1
fetched: 2026-08-13
fetch_method: Read directly from a clone of openai/openai-python at v3.0.0 (commit a1eeab5).
pull_status: fetched
sdk_version: 3.0.0
---

# openai/openai-python — official Python SDK

Generated from OpenAI's [OpenAPI specification](https://github.com/openai/openai-openapi).
Requires **Python 3.10+**. Sync and async clients are powered by
[HTTPX2](https://httpx2.pydantic.dev/).

This repo pins `openai>=3.0,<4.0` (see `pyproject.toml`). The one exception is
`examples/agents/`, which is held at `openai>=2.45,<3.0` because the Agents SDK
has not migrated yet — see the note at the bottom.

## Install

```bash
pip install openai
```

## Minimal usage

```python
from openai import OpenAI
client = OpenAI()   # reads OPENAI_API_KEY

# Responses API — the primary interface
r = client.responses.create(model="gpt-5.5", input="Say hi.")
print(r.output_text)

# Chat Completions — previous standard, supported indefinitely
c = client.chat.completions.create(model="gpt-5.5",
        messages=[{"role": "user", "content": "Hello!"}])
print(c.choices[0].message.content)

# Embeddings
e = client.embeddings.create(model="text-embedding-3-small", input=["a", "b"])
```

## Async + base_url

```python
from openai import AsyncOpenAI
client = AsyncOpenAI(base_url="https://ai.lafiel.me/v1")   # or OPENAI_BASE_URL env
```

Async mirrors sync with `await`. `base_url` is how your scripts/agents route
through the relay.

## What changed in 3.0 (2026-08-12)

The single breaking change is the transport swap. Upstream guide:
[`httpx2.md`](https://github.com/openai/openai-python/blob/main/httpx2.md).

- **HTTPX2 is the default HTTP client.** `httpx` and `certifi` are no longer
  installed with the SDK; `httpx2` is.
- **The TLS trust store changed.** HTTPX previously verified against `certifi`.
  HTTPX2 uses the **operating-system trust store**. This bites minimal
  containers with no system CA certificates, and TLS-inspecting corporate
  proxies. Fix with `SSL_CERT_FILE` / `SSL_CERT_DIR`, or pass an
  `ssl.SSLContext` via `DefaultHttpx2Client(verify=...)`.
- **Custom clients must be HTTPX2 objects**: `httpx.Client` → `httpx2.Client`,
  `httpx.Timeout` → `httpx2.Timeout`, `httpx.Limits` → `httpx2.Limits`,
  `httpx.HTTPTransport` → `httpx2.HTTPTransport`, and so on. Prefer the
  `DefaultHttpx2Client` / `DefaultAsyncHttpx2Client` helpers, which keep the
  SDK's recommended timeout, pool, and redirect defaults. The old
  `DefaultHttpxClient` names still work but now build HTTPX2 clients.
- **Mocks and auth hooks now see HTTPX2 objects.** RESPX setups that patch only
  legacy HTTPX cannot intercept the default client.
- **Escape hatch:** you can `pip install openai httpx` and inject a legacy
  client, but it is runtime-only — the type annotations accept HTTPX2, so it
  needs `cast(Any, ...)`, and it may be discontinued.
- Nothing about parsed response models, streaming APIs, retries, or numeric
  timeouts changed.

### Why the relay is unaffected

`app/` is a transparent proxy: it forwards with its **own** `httpx.AsyncClient`
(`app/core/http_client.py`) and imports the SDK only for the `OpenAIError`
exception type (`app/utils/error_handler.py`). No `http_client` is injected into
an `OpenAI()` constructor and no httpx object crosses an SDK boundary, so the
transport swap is a no-op here. The relay's own `httpx` dependency is now
declared explicitly in `pyproject.toml` rather than inherited from the SDK.

## Other 3.0-era repo facts worth knowing

- Python floor is **3.10**, raised in 2.49.0. The repo documents its support
  policy in `PYTHON_VERSION_POLICY.md`: every non-EOL CPython is supported, and
  floor increases ship in a minor release, not a patch.
- Code generation attribution moved off Stainless (2.54.0 → "Castiron"), and
  3.0.0 removed the remaining Stainless infrastructure.
- `openai[aiohttp]` now uses an HTTPX2-native transport; `DefaultAioHttpClient()`
  is an `httpx2.AsyncClient`, and the external `httpx-aiohttp` adapter is no
  longer used.
- Optional extras as of 3.0.0: `aiohttp`, `realtime` (`websockets>=13,<16`),
  `datalib`, `voice_helpers`, `bedrock`.

## Agents SDK compatibility (blocker)

`openai-agents` has **not** shipped openai 3.x support. Every published release
through **0.20.0** declares `openai>=2.45,<3`, so `openai-agents` + `openai>=3`
is an unsatisfiable resolution. `examples/agents/requirements.txt` therefore
stays on the 2.x line and should be installed in its own virtualenv, separate
from the relay's. Bump both pins together once openai-agents allows 3.x.
