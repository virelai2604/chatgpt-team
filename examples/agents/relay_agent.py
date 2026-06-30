"""
Minimal OpenAI Agents SDK example that routes through the chatgpt-team relay.

Flow:  this agent  ->  your relay (ai.lafiel.me)  ->  OpenAI

The agent never sees your real OpenAI key. It authenticates to the relay with
RELAY_KEY; the relay injects the real OPENAI_API_KEY server-side. If RELAY_KEY
is not set, the agent falls back to calling OpenAI directly with OPENAI_API_KEY,
so you can run it either way.

Run:
    pip install -r requirements.txt

    # Route through your relay (recommended — keeps your OpenAI key server-side):
    export RELAY_BASE_URL="https://ai.lafiel.me/v1"   # your relay's /v1 base
    export RELAY_KEY="your-relay-key"                 # the key your relay checks
    export AGENT_MODEL="gpt-4o-mini"                  # any model your relay allows
    python relay_agent.py "What is 23 * 19, and is the result prime?"

    # ...or call OpenAI directly (no relay):
    export OPENAI_API_KEY="sk-..."
    python relay_agent.py "Multiply 6 and 7"
"""
from __future__ import annotations

import asyncio
import os
import sys

from agents import (
    Agent,
    Runner,
    function_tool,
    set_default_openai_client,
    set_tracing_disabled,
)
from openai import AsyncOpenAI


@function_tool
def multiply(a: float, b: float) -> float:
    """Multiply two numbers and return the product."""
    return a * b


@function_tool
def is_prime(n: int) -> bool:
    """Return True if n is a prime number, otherwise False."""
    if n < 2:
        return False
    i = 2
    while i * i <= n:
        if n % i == 0:
            return False
        i += 1
    return True


def _configure_route() -> str:
    """
    Point the Agents SDK at the relay when RELAY_KEY is set; otherwise call
    OpenAI directly. Returns a short description of the route in use.
    """
    relay_key = os.getenv("RELAY_KEY")
    if relay_key:
        base_url = os.getenv("RELAY_BASE_URL", "https://ai.lafiel.me/v1")
        set_default_openai_client(AsyncOpenAI(base_url=base_url, api_key=relay_key))
        # Tracing exports would otherwise try to reach OpenAI's tracing endpoint
        # with the relay key; disable to keep this example self-contained.
        set_tracing_disabled(True)
        return f"via relay {base_url}"

    if os.getenv("OPENAI_API_KEY"):
        return "directly via api.openai.com (no RELAY_KEY set)"

    print(
        "ERROR: set RELAY_KEY (+ optional RELAY_BASE_URL) to use your relay, "
        "or OPENAI_API_KEY to call OpenAI directly.",
        file=sys.stderr,
    )
    raise SystemExit(2)


async def main() -> None:
    route = _configure_route()
    model = os.getenv("AGENT_MODEL", "gpt-4o-mini")
    prompt = " ".join(sys.argv[1:]) or "What is 23 * 19, and is the result prime?"

    agent = Agent(
        name="Calc Assistant",
        instructions=(
            "You are a concise assistant. Use the provided tools for any "
            "arithmetic or primality checks instead of computing in your head."
        ),
        model=model,
        tools=[multiply, is_prime],
    )

    print(f"[route] {route}")
    print(f"[model] {model}")
    print(f"[ask  ] {prompt}\n")

    result = await Runner.run(agent, prompt)
    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
