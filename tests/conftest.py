# tests/conftest.py

import pytest
from starlette.testclient import TestClient

from .client import client as shared_client


@pytest.fixture(scope="session")
def client() -> TestClient:
    """Session-scoped TestClient hitting the local relay app."""
    return shared_client
