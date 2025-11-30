# tests/client.py
"""
Simple shared TestClient instance for tests that import `client` directly
instead of using the pytest `client` fixture.

Used by e.g. tests/test_images_and_videos_routes_extra.py.
"""

from starlette.testclient import TestClient

from app.main import app

client = TestClient(app)
