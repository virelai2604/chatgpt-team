"""
Upgraded OpenAI Agents SDK example — hosted tools + streaming.

Improvements over relay_agent.py:
  - FileSearchTool: native RAG grounding over an OpenAI Vector Store (your
    distilled knowledge) — enabled automatically when BIFL_VECTOR_STORE_ID is set.
  - WebSearchTool: live web lookups — enabled with ENABLE_WEB_SEARCH=1.
  - A custom @function_tool (word_count) alongside the hosted tools.
  - Streaming output via Runner.run_streamed (tokens print as they arrive).

Routing is the same as relay_agent.py: through the relay if RELAY_KEY is set,
else directly against OpenAI (OPENAI_API_KEY). For hosted tools (web/file
search), pointing straight at OpenAI is the most reliable.

Run:
    pip install -r requirements.txt
    export OPENAI_API_KEY="sk-..."            # or RELAY_BASE_URL + RELAY_KEY
    export AGENT_MODEL="gpt-4o-mini"
    export BIFL_VECTOR_STORE_ID="vs_..."      # optional: turns on RAG grounding
    export ENABLE_WEB_SEARCH=1                # optional: turns on web search
    python agent_pro.py "What are the top complaints about our tire sealant?"
"""
from __future__ import annotations

import asyncio
import os
import sys

from agents import Agent, FileSearchTool, Runner, WebSearchTool, function_tool
from openai.types.responses import ResponseTextDeltaEvent

from relay_agent import _configure_route  # reuse relay/direct routing


@function_tool
def word_count(text: str) -> int:
    """Return the number of whitespace-separated words in text."""
    return len(text.split())


def build_agent() -> Agent:
    model = os.getenv("AGENT_MODEL", "gpt-4o-mini")
    tools: list = [word_count]

    vs = os.getenv("BIFL_VECTOR_STORE_ID")
    if vs:
        # Native RAG: the model searches your vector store before answering.
        tools.append(FileSearchTool(vector_store_ids=[vs], max_num_results=5))

    if os.getenv("ENABLE_WEB_SEARCH") == "1":
        tools.append(WebSearchTool())

    instructions = (
        "You are the M-One assistant (Indonesian motorcycle aftermarket brand). "
        "When a knowledge/file-search tool is available, ground answers in it and "
        "cite what you found; do not invent facts. Use web search only for current "
        "external info. Be concise and practical for a business audience."
    )
    return Agent(name="M-One Assistant", instructions=instructions, model=model, tools=tools)


async def main() -> None:
    route = _configure_route()
    agent = build_agent()
    prompt = " ".join(sys.argv[1:]) or "Summarize the most common product complaints."

    tool_names = [getattr(t, "name", type(t).__name__) for t in agent.tools]
    print(f"[route] {route}\n[model] {agent.model}\n[tools] {tool_names}\n")
    print("--- answer ---")

    result = Runner.run_streamed(agent, prompt)
    async for event in result.stream_events():
        if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
            print(event.data.delta, end="", flush=True)
    print("\n")


if __name__ == "__main__":
    asyncio.run(main())
