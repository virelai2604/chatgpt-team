# tests/test_embeddings_images_videos.py

from starlette.testclient import TestClient


def test_embeddings_forward(client: TestClient, forward_spy):
    payload = {
        "model": "text-embedding-3-small",
        "input": "Hello from pytest",
    }

    resp = client.post("/v1/embeddings", json=payload)
    assert resp.status_code == 200

    data = resp.json()
    assert data["object"] == "test_proxy"
    assert data["echo_path"] == "/v1/embeddings"
    assert data["echo_method"] == "POST"

    # Ensure the relay forwarded the exact payload
    assert forward_spy["json"] == payload


def test_image_generations_forward(client: TestClient, forward_spy):
    payload = {
        "model": "gpt-image-1",
        "prompt": "A relay server drawn as a train station",
        "size": "1024x1024",
    }

    resp = client.post("/v1/images/generations", json=payload)
    assert resp.status_code == 200

    data = resp.json()
    assert data["object"] == "test_proxy"
    assert data["echo_path"] == "/v1/images/generations"
    assert data["echo_method"] == "POST"

    assert forward_spy["json"] == payload


def test_video_generations_forward(client: TestClient, forward_spy):
    payload = {
        "model": "gpt-video-1",
        "prompt": "A short clip of a motorcycle riding safely in the rain",
        "duration": 5,
    }

    resp = client.post("/v1/videos/generations", json=payload)
    assert resp.status_code == 200

    data = resp.json()
    assert data["object"] == "test_proxy"
    assert data["echo_path"] == "/v1/videos/generations"
    assert data["echo_method"] == "POST"

    assert forward_spy["json"] == payload
