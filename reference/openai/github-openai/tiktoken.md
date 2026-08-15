---
source_id: gh_tiktoken
title: openai/tiktoken — BPE tokeniser for OpenAI models
category: github_reference
source_urls:
  - https://github.com/openai/tiktoken
retrieved_at: 2026-08-15
pinned_commit: 08a5f3b2c987ada4fc5aa1f16c643c203fa8acaa
fetch_method: shallow clone (--depth 1 --filter=blob:none), README read locally
pull_status: fetched
verify: encoding names are model-specific and change with new models — check get_encoding_for_model before hardcoding one
---

# openai/tiktoken

> Provenance: `fetched` 2026-08-15 at `08a5f3b`. Reference only — not vendored.

Fast byte-pair-encoding tokeniser for OpenAI models. Rust core with Python bindings
(`Cargo.toml` + `pyproject.toml`).

```python
import tiktoken
enc = tiktoken.get_encoding("o200k_base")
assert enc.decode(enc.encode("hello world")) == "hello world"
```

## Relevance to this relay

Currently **none** — the relay is a transparent pass-through and never inspects request
bodies for length. This is the library to reach for if that changes, i.e. if the relay
ever needs to:

- reject oversized inputs before paying for an upstream round trip,
- budget or report token usage per relay key,
- truncate context on `/v1/responses/compact`.

Adding it means adding a Rust-backed dependency to a service that currently has none.
Weigh that against just letting OpenAI return the error.
