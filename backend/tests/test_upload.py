from tests.conftest import complete_upload, upload_file


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"


def test_init_upload_success(client, owner):
    _, headers = owner
    body = upload_file(client, headers, "report.pdf", mime_type="application/pdf")
    assert body["upload_url"].startswith("https://")
    assert body["storage_bucket"]
    assert body["storage_path"]


def test_init_upload_oversized_rejected(client, owner):
    _, headers = owner
    r = client.post(
        "/files/init-upload",
        json={"filename": "huge.bin", "mime_type": "application/octet-stream", "size_bytes": 999_999_999_999},
        headers=headers,
    )
    assert r.status_code == 413


def test_init_upload_blocked_mime_rejected(client, owner):
    _, headers = owner
    r = client.post(
        "/files/init-upload",
        json={"filename": "virus.exe", "mime_type": "application/x-msdownload", "size_bytes": 100},
        headers=headers,
    )
    assert r.status_code == 415


def test_init_upload_path_traversal_rejected(client, owner):
    _, headers = owner
    r = client.post(
        "/files/init-upload",
        json={"filename": "../../etc/passwd", "mime_type": "text/plain", "size_bytes": 10},
        headers=headers,
    )
    assert r.status_code == 422


def test_complete_upload_before_bytes_uploaded_conflicts(client, owner):
    _, headers = owner
    body = upload_file(client, headers, "test.txt")
    r = client.post(f"/files/{body['file_id']}/complete-upload", json={}, headers=headers)
    assert r.status_code == 409


def test_complete_upload_after_bytes_uploaded_succeeds(client, owner, fake_storage):
    _, headers = owner
    body = upload_file(client, headers, "test.txt")
    result = complete_upload(client, headers, fake_storage, body["file_id"], body["storage_path"])
    assert result["upload_status"] == "uploaded"


def test_complete_upload_is_idempotent(client, owner, fake_storage):
    _, headers = owner
    body = upload_file(client, headers, "test.txt")
    complete_upload(client, headers, fake_storage, body["file_id"], body["storage_path"])
    r = client.post(f"/files/{body['file_id']}/complete-upload", json={}, headers=headers)
    assert r.status_code == 200
    assert r.json()["upload_status"] == "uploaded"


def test_get_file_includes_download_url_once_uploaded(client, owner, fake_storage):
    _, headers = owner
    body = upload_file(client, headers, "test.txt")
    complete_upload(client, headers, fake_storage, body["file_id"], body["storage_path"])
    r = client.get(f"/files/{body['file_id']}", headers=headers)
    assert r.status_code == 200
    assert r.json()["download_url"] is not None


def test_get_file_no_download_url_while_pending(client, owner):
    _, headers = owner
    body = upload_file(client, headers, "test.txt")
    r = client.get(f"/files/{body['file_id']}", headers=headers)
    assert r.status_code == 200
    assert r.json()["download_url"] is None


def test_get_file_other_user_gets_404(client, owner, stranger):
    _, owner_headers = owner
    _, stranger_headers = stranger
    body = upload_file(client, owner_headers, "test.txt")
    r = client.get(f"/files/{body['file_id']}", headers=stranger_headers)
    assert r.status_code == 404


def test_invalid_user_id_header_rejected(client):
    r = client.post(
        "/files/init-upload",
        json={"filename": "a.txt", "mime_type": "text/plain", "size_bytes": 10},
        headers={"X-User-Id": "not-a-uuid"},
    )
    assert r.status_code == 401


def test_missing_user_id_header_rejected(client):
    r = client.post(
        "/files/init-upload",
        json={"filename": "a.txt", "mime_type": "text/plain", "size_bytes": 10},
    )
    assert r.status_code in (401, 422)  # FastAPI 422s a missing required header before our handler ever runs
