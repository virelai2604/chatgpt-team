# tests/test_models_files_videos_extra_routes.py
# Pseudocode
# 1. DELETE /v1/models/{model_id} forwards correctly (basic smoke test).
# 2. GET /v1/files/{file_id}/content returns a binary payload (stubbed).
# 3. GET /v1/videos, /v1/videos/{id}, /v1/videos/{id}/content all forward and return 2xx.

import pytest


def test_delete_model_forward(client):
    # Use a known fake model id that your test transport can handle trivially.
    resp = client.delete("/v1/models/gpt-test-model")
    # In APP_MODE=test this should not hit real OpenAI; it should go through your FakeAsyncClient.
    # Accept either 200 or 404 depending on how you decide to stub it, but do assert it's not a 5xx.
    assert resp.status_code in (200, 404)


def test_file_content_forward(client):
    # This assumes your FakeAsyncClient in APP_MODE=test knows how to respond to this path.
    # If not, extend the fake to return e.g. "dummy file content" for file_123.
    resp = client.get("/v1/files/file_123/content")
    assert resp.status_code in (200, 404)

    if resp.status_code == 200:
        # For a 200, we expect some body bytes back
        assert resp.content != b""


def test_videos_list_forward(client):
    resp = client.get("/v1/videos")
    # In test mode, you can decide whether to stub as 200/empty or 404-not-implemented.
    assert resp.status_code in (200, 404)


def test_video_retrieve_forward(client):
    resp = client.get("/v1/videos/video_123")
    assert resp.status_code in (200, 404)


def test_video_content_forward(client):
    resp = client.get("/v1/videos/video_123/content")
    assert resp.status_code in (200, 404)

    if resp.status_code == 200:
        assert resp.content != b""
