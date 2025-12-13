import httpx
import pytest

from app.main import create_app


@pytest.mark.asyncio
async def test_responses_streaming_forwards_beta_header(monkeypatch):
    """
    Assert that streaming /v1/responses forwards OpenAI-Beta: assistants=v2.
    """

    captured = {}

    # ✅ MUST be a normal function returning an async context manager
    def fake_stream(method, url, headers=None, **kwargs):
        captured.update(headers or {})

        class FakeStream:
            status_code = 200
            headers = {"content-type": "text/event-stream"}

            async def aiter_raw(self):
                yield b"data: test\n\n"

        class CM:
            async def __aenter__(self):
                return FakeStream()

            async def __aexit__(self, exc_type, exc, tb):
                return None

        return CM()

    app = create_app()
    transport = httpx.ASGITransport(app=app)

    from app.core.http_client import get_async_httpx_client
    client = get_async_httpx_client()
    monkeypatch.setattr(client, "stream", fake_stream)

    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
        # ✅ matches pytest.ini
        headers={"X-Relay-Key": "dummy-tests-relay-key"},
    ) as ac:
        resp = await ac.post(
            "/v1/responses",
            json={"model": "gpt-4.1-mini", "input": "hi", "stream": True},
        )

    assert resp.status_code == 200
    assert captured.get("OpenAI-Beta") == "assistants=v2"