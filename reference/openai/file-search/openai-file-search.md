---
source_id: oa_file_search
source_url: https://developers.openai.com/api/docs/guides/tools-file-search
category: file_search_vector_store
priority: P0
fetched: 2026-07-07
fetch_method: developers.openai.com 403s automated fetch; reconstructed from web search of the same docs + the cookbook File_Search_Responses example.
pull_status: fetched
---

# File Search (hosted RAG over Vector Stores)

`file_search` is a **hosted tool** in the Responses API: the model retrieves from
a knowledge base of uploaded files via semantic + keyword search. No retrieval
code on your side.

> Note: File Search was beta in the Assistants API; it is now a built-in
> Responses-API tool. **Assistants API is deprecated (shuts down 2026-08-26).**
> Use the Responses API + Vector Stores.

## Setup (3 steps)

```python
from openai import OpenAI
client = OpenAI()

# 1) upload a file
f = client.files.create(file=open("distilled.md", "rb"), purpose="user_data")

# 2) create a vector store
vs = client.vector_stores.create(name="bifl_distilled")

# 3) add the file (triggers chunk+embed+index; poll until completed)
client.vector_stores.files.create_and_poll(vector_store_id=vs.id, file_id=f.id)
print(vs.id)   # -> set as BIFL_VECTOR_STORE_ID
```

## Query with the tool

```python
r = client.responses.create(
    model="gpt-5.1",
    input="What are the top tire-sealant complaints?",
    tools=[{"type": "file_search",
            "vector_store_ids": [vs.id],
            "max_num_results": 5}],
)
print(r.output_text)
```

## BIFL fit

This is the hosted retrieval layer for **distilled** knowledge (sync summaries,
not all 380K chunks). The relay's `/v1/bifl/search` and `agent_pro.py`'s
`FileSearchTool` both target a vector store id — set `BIFL_VECTOR_STORE_ID` to the
`vs.id` above to light them up.
