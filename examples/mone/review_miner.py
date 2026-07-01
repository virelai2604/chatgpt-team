"""
M-One marketplace review miner.

Reads marketplace reviews (Shopee / Tokopedia / Lazada / TikTok) and uses the
OpenAI Responses API structured outputs to extract, per review: sentiment, an
estimated star rating, normalized issue tags, praised aspects, and a one-line
English summary. It then aggregates the most common issues in Python
(deterministic — the model is not trusted to count).

Routing (same pattern as examples/agents):
  - RELAY_KEY set   -> calls through your relay (base_url = RELAY_BASE_URL),
                       keeping your real OpenAI key server-side.
  - else OPENAI_API_KEY set -> calls OpenAI directly.

Run:
    pip install -r requirements.txt

    # Option A - through your relay:
    $env:RELAY_BASE_URL = "https://ai.lafiel.me/v1"
    $env:RELAY_KEY      = "<your relay key>"
    $env:MODEL          = "gpt-4o-mini"      # or gpt-5.1
    python review_miner.py sample_reviews.txt

    # Option B - direct:
    $env:OPENAI_API_KEY = "sk-..."
    python review_miner.py sample_reviews.txt

Output: prints per-review insights + sentiment mix + top issues, and writes
review_insights.json.
"""
from __future__ import annotations

import json
import os
import sys
from collections import Counter
from typing import List, Literal

from openai import OpenAI
from pydantic import BaseModel, Field


class ReviewInsight(BaseModel):
    index: int = Field(description="0-based index of the review in the input list")
    language: str = Field(description="Detected language code, e.g. 'id', 'en', or 'mixed'")
    sentiment: Literal["positive", "neutral", "negative"]
    rating_estimate: int = Field(ge=1, le=5, description="Estimated 1-5 star rating")
    issues: List[str] = Field(
        default_factory=list,
        description=(
            "Short, normalized problem tags in English so they aggregate across "
            "reviews, e.g. 'leaking bottle', 'slow delivery', 'clogs tire valve'. "
            "Empty list if the review reports no problem."
        ),
    )
    praises: List[str] = Field(
        default_factory=list,
        description="Short, normalized positive aspect tags in English.",
    )
    summary: str = Field(description="One-line English summary of the review.")


class ReviewAnalysis(BaseModel):
    reviews: List[ReviewInsight]


INSTRUCTIONS = (
    "You are a product-feedback analyst for M-One, an Indonesian motorcycle "
    "aftermarket brand (tire sealant and rider safety products). Analyze each "
    "marketplace review. Reviews may be in Indonesian, English, or mixed. "
    "Normalize issue and praise tags to short English phrases so they aggregate "
    "cleanly across many reviews. Stay faithful to the review text; never invent "
    "problems that are not stated or clearly implied."
)


def _make_client() -> "tuple[OpenAI, str]":
    relay_key = os.getenv("RELAY_KEY")
    if relay_key:
        base_url = os.getenv("RELAY_BASE_URL", "https://ai.lafiel.me/v1")
        return OpenAI(base_url=base_url, api_key=relay_key), f"via relay {base_url}"
    if os.getenv("OPENAI_API_KEY"):
        return OpenAI(), "directly via api.openai.com"
    print(
        "ERROR: set RELAY_KEY (+ optional RELAY_BASE_URL) to use your relay, "
        "or OPENAI_API_KEY to call OpenAI directly.",
        file=sys.stderr,
    )
    raise SystemExit(2)


def _load_reviews(path: str) -> List[str]:
    with open(path, encoding="utf-8") as f:
        if path.endswith(".jsonl"):
            return [json.loads(line)["text"] for line in f if line.strip()]
        return [line.strip() for line in f if line.strip()]


def main() -> None:
    path = sys.argv[1] if len(sys.argv) > 1 else "sample_reviews.txt"
    model = os.getenv("MODEL", "gpt-4o-mini")
    client, route = _make_client()
    reviews = _load_reviews(path)
    if not reviews:
        print(f"No reviews found in {path}", file=sys.stderr)
        raise SystemExit(1)

    numbered = "\n".join(f"[{i}] {r}" for i, r in enumerate(reviews))
    print(f"[route] {route}\n[model] {model}\n[reviews] {len(reviews)}\n")

    resp = client.responses.parse(
        model=model,
        instructions=INSTRUCTIONS,
        input=f"Analyze these {len(reviews)} reviews and return one entry per review:\n{numbered}",
        text_format=ReviewAnalysis,
    )
    analysis = resp.output_parsed
    if analysis is None:
        print("Model did not return a parsed result.", file=sys.stderr)
        raise SystemExit(1)

    # Deterministic aggregation in Python (don't trust the model for counts).
    issue_counts = Counter(iss.strip().lower() for r in analysis.reviews for iss in r.issues)
    sentiments = Counter(r.sentiment for r in analysis.reviews)

    print("=== Per-review ===")
    for r in analysis.reviews:
        print(f"[{r.index}] {r.sentiment:<8} ~{r.rating_estimate}*  {r.summary}")
        if r.issues:
            print(f"      issues: {', '.join(r.issues)}")

    print("\n=== Sentiment mix ===")
    for s, n in sentiments.most_common():
        print(f"  {s}: {n}")

    print("\n=== Top issues ===")
    for issue, n in issue_counts.most_common(10):
        print(f"  {n:>2}x  {issue}")

    out = {
        "route": route,
        "model": model,
        "review_count": len(reviews),
        "sentiment_mix": dict(sentiments),
        "top_issues": issue_counts.most_common(10),
        "reviews": [r.model_dump() for r in analysis.reviews],
    }
    with open("review_insights.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print("\nWrote review_insights.json")


if __name__ == "__main__":
    main()
