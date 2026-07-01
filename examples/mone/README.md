# M-One business tools

Small, practical AI tools for M-One built with the **official `openai-python` SDK
directly** — the Stage-2 tools from the roadmap (build useful tools before
agents). Each is one self-contained script.

These call OpenAI directly; they do **not** require the relay. They can
*optionally* route through your relay (`ai.lafiel.me`) if you set `RELAY_KEY`,
which keeps your OpenAI key server-side.

## Tool 1 — `review_miner.py`

Turns raw marketplace reviews (Shopee / Tokopedia / Lazada / TikTok) into
structured product intelligence:

- per review: sentiment, estimated star rating, normalized **issue tags**,
  praised aspects, one-line English summary
- aggregated: sentiment mix + **top recurring issues** (counted in Python, so
  the numbers are exact — the model isn't trusted to count)

Handles Indonesian / English / mixed reviews and normalizes tags to English so
they group across the whole dataset.

### Run

```powershell
pip install -r requirements.txt

# Option A — through your relay (key stays server-side)
$env:RELAY_BASE_URL = "https://ai.lafiel.me/v1"
$env:RELAY_KEY      = "<your relay key>"
$env:MODEL          = "gpt-4o-mini"       # or gpt-5.1
python review_miner.py sample_reviews.txt

# Option B — straight to OpenAI
$env:OPENAI_API_KEY = "sk-..."
python review_miner.py sample_reviews.txt
```

### Output

Prints per-review insights, the sentiment mix, and the top issues, and writes
`review_insights.json`. Example (shape):

```
=== Top issues ===
   3x  leaking bottle
   2x  slow delivery
   2x  clogs tire valve
   1x  wrong volume vs advertised
```

That "top issues" list is the business payoff: it tells R&D and QA what to fix,
and marketing what to address, straight from real customer voice.

### Use your real data

Replace `sample_reviews.txt` with your reviews — one review per line, or a
`.jsonl` file with `{"text": "..."}` per line:

```powershell
python review_miner.py my_shopee_reviews.txt
```

## Where this fits the roadmap

```
Stage 1: knowledge base (ingest company data)      <- next tool to build
Stage 2: business tools  ← review_miner.py is here
Stage 3: agents (wrap the best tools as workers)
Delivery: expose a tool to dealers/customers via a Custom GPT + your relay
```

Next candidates: a **complaint classifier** (category + severity + suggested
action) and the **knowledge-base ingestion pipeline** (SQLite + JSONL +
embeddings).
