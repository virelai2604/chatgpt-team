"""
Expose the relay-routed agent over HTTP.

This is a small standalone FastAPI app (separate from the relay) so you can call
your agent like an API:

    POST /agent/run   {"prompt": "..."}   ->   {"output": "...", ...}

It reuses the tools and relay-routing from relay_agent.py, so the data flow is
still:  HTTP client -> this agent server -> relay (ai.lafiel.me) -> OpenAI.

Run:
    pip install -r requirements.txt
    export RELAY_BASE_URL="https://ai.lafiel.me/v1"
    export RELAY_KEY="your-relay-key"
    export AGENT_MODEL="gpt-4o-mini"
    uvicorn agent_server:app --host 127.0.0.1 --port 8001

    curl -s localhost:8001/agent/run \
      -H 'content-type: application/json' \
      -d '{"prompt":"What is 23 * 19, and is it prime?"}'
"""
from __future__ import annotations

import os
from contextlib import asynccontextmanager

from agents import Agent, Runner
from fastapi import FastAPI
from pydantic import BaseModel

from relay_agent import _configure_route, is_prime, multiply

_MODEL = os.getenv("AGENT_MODEL", "gpt-4o-mini")
_route = "unconfigured"


def _build_agent() -> Agent:
    return Agent(
        name="Calc Assistant",
        instructions=(
            "You are a concise assistant. Use the provided tools for any "
            "arithmetic or primality checks instead of computing in your head."
        ),
        model=_MODEL,
        tools=[multiply, is_prime],
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Configure the relay route (or direct OpenAI) once at startup, then build
    # the agent and stash it on app.state for reuse across requests.
    global _route
    _route = _configure_route()
    app.state.agent = _build_agent()
    yield


app = FastAPI(title="relay-agent-server", version="0.1.0", lifespan=lifespan)


class RunRequest(BaseModel):
    prompt: str


class RunResponse(BaseModel):
    output: str
    route: str
    model: str


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "route": _route, "model": _MODEL}


@app.post("/agent/run", response_model=RunResponse)
async def run_agent(req: RunRequest) -> RunResponse:
    result = await Runner.run(app.state.agent, req.prompt)
    return RunResponse(output=result.final_output, route=_route, model=_MODEL)
