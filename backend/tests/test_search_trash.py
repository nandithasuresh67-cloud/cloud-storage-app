from tests.conftest import complete_upload, upload_file


def test_search_matches_name_case_insensitively(client, owner):
    _, headers = owner
    upload_file(client, headers, "quarterly-report.pdf", mime_type="application/pdf")
    r = client.get("/search?q=REPORT", headers=headers)
    assert r.status_code == 200
    assert any(i["name"] == "quarterly-report.pdf" for i in r.json())


def test_search_matches_folder_names(client, owner):
    _, headers = owner
    client.post("/folders", json={"name": "Vacation Photos"}, headers=headers)
    r = client.get("/search?q=vacation", headers=headers)
    assert any(i["type"] == "folder" and i["name"] == "Vacation Photos" for i in r.json())


def test_search_item_type_filter_excludes_folders(client, owner):
    _, headers = owner
    client.post("/folders", json={"name": "Work"}, headers=headers)
    upload_file(client, headers, "work-notes.txt")
    r = client.get("/search?q=work&item_type=file", headers=headers)
    assert all(i["type"] == "file" for i in r.json())
    assert any(i["name"] == "work-notes.txt" for i in r.json())


def test_search_mime_type_prefix_filter(client, owner):
    _, headers = owner
    upload_file(client, headers, "beach.jpg", mime_type="image/jpeg")
    upload_file(client, headers, "notes.txt", mime_type="text/plain")
    r = client.get("/search?q=e&mime_type=image/", headers=headers)
    names = {i["name"] for i in r.json()}
    assert "beach.jpg" in names
    assert "notes.txt" not in names


def test_search_never_returns_other_users_items(client, owner, stranger):
    _, owner_headers = owner
    _, stranger_headers = stranger
    body = upload_file(client, owner_headers, "secret.txt")
    r = client.get("/search?q=secret", headers=stranger_headers)
    assert not any(i["id"] == body["file_id"] for i in r.json())


def test_search_excludes_trashed_items(client, owner):
    _, headers = owner
    body = upload_file(client, headers, "meeting-notes.txt")
    client.delete(f"/files/{body['file_id']}", headers=headers)
    r = client.get("/search?q=meeting", headers=headers)
    assert not any(i["id"] == body["file_id"] for i in r.json())


def test_deleting_folder_cascades_to_contents(client, owner):
    _, headers = owner
    work = client.post("/folders", json={"name": "Work"}, headers=headers).json()
    archive = client.post("/folders", json={"name": "Archive", "parent_id": work["id"]}, headers=headers).json()
    report = upload_file(client, headers, "report.pdf", folder_id=work["id"])
    old = upload_file(client, headers, "old.txt", folder_id=archive["id"])

    r = client.delete(f"/folders/{work['id']}", headers=headers)
    assert r.status_code == 204

    assert client.get(f"/files/{report['file_id']}", headers=headers).json()["is_trashed"] is True
    assert client.get(f"/folders/{archive['id']}", headers=headers).json()["is_trashed"] is True
    assert client.get(f"/files/{old['file_id']}", headers=headers).json()["is_trashed"] is True


def test_trash_lists_only_roots_not_cascaded_children(client, owner):
    _, headers = owner
    work = client.post("/folders", json={"name": "Work"}, headers=headers).json()
    archive = client.post("/folders", json={"name": "Archive", "parent_id": work["id"]}, headers=headers).json()
    report = upload_file(client, headers, "report.pdf", folder_id=work["id"])
    client.delete(f"/folders/{work['id']}", headers=headers)

    r = client.get("/trash", headers=headers)
    ids = {item["id"] for item in r.json()}
    assert work["id"] in ids
    assert archive["id"] not in ids
    assert report["file_id"] not in ids


def test_restoring_non_trashed_item_400(client, owner):
    _, headers = owner
    folder = client.post("/folders", json={"name": "Live"}, headers=headers).json()
    r = client.post(f"/trash/folders/{folder['id']}/restore", headers=headers)
    assert r.status_code == 400


def test_restore_cascades_back_down(client, owner):
    _, headers = owner
    work = client.post("/folders", json={"name": "Work"}, headers=headers).json()
    archive = client.post("/folders", json={"name": "Archive", "parent_id": work["id"]}, headers=headers).json()
    report = upload_file(client, headers, "report.pdf", folder_id=work["id"])
    client.delete(f"/folders/{work['id']}", headers=headers)

    r = client.post(f"/trash/folders/{work['id']}/restore", headers=headers)
    assert r.status_code == 204
    assert client.get(f"/folders/{archive['id']}", headers=headers).json()["is_trashed"] is False
    assert client.get(f"/files/{report['file_id']}", headers=headers).json()["is_trashed"] is False
    assert client.get("/trash", headers=headers).json() == []


def test_permanent_delete_requires_trashed_first(client, owner):
    _, headers = owner
    body = upload_file(client, headers, "live.txt")
    r = client.delete(f"/trash/files/{body['file_id']}", headers=headers)
    assert r.status_code == 400


def test_permanent_delete_removes_storage_object(client, owner, fake_storage):
    _, headers = owner
    body = upload_file(client, headers, "live.txt")
    complete_upload(client, headers, fake_storage, body["file_id"], body["storage_path"])
    client.delete(f"/files/{body['file_id']}", headers=headers)

    r = client.delete(f"/trash/files/{body['file_id']}", headers=headers)
    assert r.status_code == 204
    assert body["storage_path"] in fake_storage["removed_paths"]
    assert client.get(f"/files/{body['file_id']}", headers=headers).status_code == 404


def test_permanent_delete_folder_cascades_and_cleans_storage(client, owner, fake_storage):
    _, headers = owner
    work = client.post("/folders", json={"name": "Work"}, headers=headers).json()
    archive = client.post("/folders", json={"name": "Archive", "parent_id": work["id"]}, headers=headers).json()
    old = upload_file(client, headers, "old.txt", folder_id=archive["id"])
    complete_upload(client, headers, fake_storage, old["file_id"], old["storage_path"])

    client.delete(f"/folders/{work['id']}", headers=headers)
    r = client.delete(f"/trash/folders/{work['id']}", headers=headers)
    assert r.status_code == 204

    assert client.get(f"/folders/{work['id']}", headers=headers).status_code == 404
    assert client.get(f"/folders/{archive['id']}", headers=headers).status_code == 404
    assert client.get(f"/files/{old['file_id']}", headers=headers).status_code == 404
    assert old["storage_path"] in fake_storage["removed_paths"]


def test_permanent_delete_ownership_enforced(client, owner, stranger):
    _, owner_headers = owner
    _, stranger_headers = stranger
    body = upload_file(client, owner_headers, "mine.txt")
    client.delete(f"/files/{body['file_id']}", headers=owner_headers)

    r = client.delete(f"/trash/files/{body['file_id']}", headers=stranger_headers)
    assert r.status_code == 404
