# tests/test_files_and_vectorstores.py
from starlette.testclient import TestClient


def test_list_files_forward(client: TestClient, forward_spy):
    resp = client.get("/v1/files")
    assert resp.status_code == 200

    data = resp.json()
    # Echoed by the httpx stub
    assert data["echo_path"] == "/v1/files"
    assert data["echo_method"] == "GET"

    # Check what we actually forwarded out
    assert forward_spy["method"] == "GET"
    assert forward_spy["json"] is None
    assert forward_spy["body"] == ""


def test_create_file_forward(client: TestClient, forward_spy, tmp_path):
    # Prepare a small file on disk
    file_path = tmp_path / "dummy.txt"
    file_path.write_text("hello relay")

    with file_path.open("rb") as f:
        resp = client.post(
            "/v1/files",
            files={"file": ("dummy.txt", f, "text/plain")},
        )

    assert resp.status_code == 200

    data = resp.json()
    assert data["echo_path"] == "/v1/files"
    assert data["echo_method"] == "POST"

    # Since this is multipart/form-data, forward_spy["json"] will be None
    assert forward_spy["method"] == "POST"
    assert forward_spy["json"] is None
    # But body should contain our file content
    assert "hello relay" in forward_spy["body"]


def test_retrieve_file_forward(client: TestClient, forward_spy):
    resp = client.get("/v1/files/file_123")
    assert resp.status_code == 200

    data = resp.json()
    assert data["echo_path"] == "/v1/files/file_123"
    assert data["echo_method"] == "GET"

    assert forward_spy["method"] == "GET"
    assert forward_spy["json"] is None


def test_delete_file_forward(client: TestClient, forward_spy):
    resp = client.delete("/v1/files/file_456")
    assert resp.status_code == 200

    data = resp.json()
    assert data["echo_path"] == "/v1/files/file_456"
    assert data["echo_method"] == "DELETE"

    assert forward_spy["method"] == "DELETE"


def test_list_vector_stores_forward(client: TestClient, forward_spy):
    resp = client.get("/v1/vector_stores")
    assert resp.status_code == 200

    data = resp.json()
    assert data["echo_path"] == "/v1/vector_stores"
    assert data["echo_method"] == "GET"

    assert forward_spy["method"] == "GET"


def test_retrieve_vector_store_forward(client: TestClient, forward_spy):
    resp = client.get("/v1/vector_stores/vs_123")
    assert resp.status_code == 200

    data = resp.json()
    assert data["echo_path"] == "/v1/vector_stores/vs_123"
    assert data["echo_method"] == "GET"

    assert forward_spy["method"] == "GET"


def test_nested_vector_store_files_forward(client: TestClient, forward_spy):
    resp = client.get("/v1/vector_stores/vs_123/files")
    assert resp.status_code == 200

    data = resp.json()
    assert data["echo_path"] == "/v1/vector_stores/vs_123/files"
    assert data["echo_method"] == "GET"

    assert forward_spy["method"] == "GET"


def test_vector_store_file_batches_forward(client: TestClient, forward_spy):
    resp = client.get("/v1/vector_stores/vs_456/file_batches")
    assert resp.status_code == 200

    data = resp.json()
    assert data["echo_path"] == "/v1/vector_stores/vs_456/file_batches"
    assert data["echo_method"] == "GET"

    assert forward_spy["method"] == "GET"
