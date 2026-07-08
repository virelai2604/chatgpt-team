---
source_id: gh_openai_python
source_url: https://github.com/openai/openai-python
category: sdk_python
priority: P1
fetched: 2026-07-07
fetch_method: WebFetch of the GitHub README.
pull_status: fetched
---

# openai/openai-python — official Python SDK

Generated from OpenAI's OpenAPI spec (Stainless). Requires **Python 3.9+**.
You have it pinned at `openai==2.44`.

## Install

```bash
pip install openai
```

## Minimal usage

```python
from openai import OpenAI
client = OpenAI()   # reads OPENAI_API_KEY

# Responses API
r = client.responses.create(model="gpt-5.1", input="Say hi.")
print(r.output_text)

# Chat Completions
c = client.chat.completions.create(model="gpt-5.1",
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
