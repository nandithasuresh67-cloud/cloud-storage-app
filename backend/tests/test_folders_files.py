import uuid

from tests.conftest import upload_file


def test_create_root_folder(client, owner):
    _, headers = owner
    r = client.post("/folders", json={"name": "Projects"}, headers=headers)
    assert r.status_code == 201
    assert r.json()["parent_id"] is None


def test_create_nested_folder(client, owner):
    _, headers = owner
    parent = client.post("/folders", json={"name": "Projects"}, headers=headers).json()
    r = client.post("/folders", json={"name": "Q3", "parent_id": parent["id"]}, headers=headers)
    assert r.status_code == 201
    assert r.json()["parent_id"] == parent["id"]


def test_create_folder_under_unowned_parent_404(client, owner, stranger):
    _, owner_headers = owner
    _, stranger_headers = stranger
    parent = client.post("/folders", json={"name": "Projects"}, headers=owner_headers).json()
    r = client.post("/folders", json={"name": "sneaky", "parent_id": parent["id"]}, headers=stranger_headers)
    assert r.status_code == 404


def test_folder_name_path_traversal_rejected(client, owner):
    _, headers = owner
    r = client.post("/folders", json={"name": "../evil"}, headers=headers)
    assert r.status_code == 422


def test_get_folder_metadata(client, owner):
    _, headers = owner
    folder = client.post("/folders", json={"name": "Q3"}, headers=headers).json()
    r = client.get(f"/folders/{folder['id']}", headers=headers)
    assert r.status_code == 200
    assert r.json()["name"] == "Q3"


def test_get_folder_other_user_404(client, owner, stranger):
    _, owner_headers = owner
    _, stranger_headers = stranger
    folder = client.post("/folders", json={"name": "Q3"}, headers=owner_headers).json()
    r = client.get(f"/folders/{folder['id']}", headers=stranger_headers)
    assert r.status_code == 404


def test_list_root_contents(client, owner):
    _, headers = owner
    folder = client.post("/folders", json={"name": "Projects"}, headers=headers).json()
    r = client.get("/folders/contents", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert body["folder"] is None
    assert body["breadcrumb"] == []
    assert any(f["id"] == folder["id"] for f in body["subfolders"])


def test_breadcrumb_reflects_nesting_depth(client, owner):
    _, headers = owner
    projects = client.post("/folders", json={"name": "Projects"}, headers=headers).json()
    q3 = client.post("/folders", json={"name": "Q3", "parent_id": projects["id"]}, headers=headers).json()

    r = client.get(f"/folders/contents?folder_id={projects['id']}", headers=headers)
    assert [b["name"] for b in r.json()["breadcrumb"]] == ["Projects"]

    r = client.get(f"/folders/contents?folder_id={q3['id']}", headers=headers)
    assert [b["name"] for b in r.json()["breadcrumb"]] == ["Projects", "Q3"]


def test_rename_folder_leaves_parent_untouched(client, owner):
    _, headers = owner
    parent = client.post("/folders", json={"name": "Projects"}, headers=headers).json()
    child = client.post("/folders", json={"name": "Q3", "parent_id": parent["id"]}, headers=headers).json()

    r = client.patch(f"/folders/{child['id']}", json={"name": "Q3 Final"}, headers=headers)
    assert r.status_code == 200
    assert r.json()["name"] == "Q3 Final"
    assert r.json()["parent_id"] == parent["id"]


def test_move_folder(client, owner):
    _, headers = owner
    a = client.post("/folders", json={"name": "A"}, headers=headers).json()
    b = client.post("/folders", json={"name": "B"}, headers=headers).json()
    r = client.patch(f"/folders/{b['id']}", json={"parent_id": a["id"]}, headers=headers)
    assert r.status_code == 200
    assert r.json()["parent_id"] == a["id"]


def test_move_folder_to_root_explicit_null(client, owner):
    _, headers = owner
    a = client.post("/folders", json={"name": "A"}, headers=headers).json()
    b = client.post("/folders", json={"name": "B", "parent_id": a["id"]}, headers=headers).json()
    r = client.patch(f"/folders/{b['id']}", json={"parent_id": None}, headers=headers)
    assert r.status_code == 200
    assert r.json()["parent_id"] is None


def test_move_folder_into_itself_rejected(client, owner):
    _, headers = owner
    a = client.post("/folders", json={"name": "A"}, headers=headers).json()
    r = client.patch(f"/folders/{a['id']}", json={"parent_id": a["id"]}, headers=headers)
    assert r.status_code == 400


def test_move_folder_into_own_descendant_rejected(client, owner):
    _, headers = owner
    a = client.post("/folders", json={"name": "A"}, headers=headers).json()
    b = client.post("/folders", json={"name": "B", "parent_id": a["id"]}, headers=headers).json()
    r = client.patch(f"/folders/{a['id']}", json={"parent_id": b["id"]}, headers=headers)
    assert r.status_code == 400


def test_rename_file(client, owner):
    _, headers = owner
    body = upload_file(client, headers, "notes.txt")
    r = client.patch(f"/files/{body['file_id']}", json={"name": "notes-v2.txt"}, headers=headers)
    assert r.status_code == 200
    assert r.json()["name"] == "notes-v2.txt"


def test_move_file_between_folders(client, owner):
    _, headers = owner
    folder = client.post("/folders", json={"name": "Archive"}, headers=headers).json()
    body = upload_file(client, headers, "notes.txt")
    r = client.patch(f"/files/{body['file_id']}", json={"folder_id": folder["id"]}, headers=headers)
    assert r.status_code == 200
    assert r.json()["folder_id"] == folder["id"]


def test_move_file_to_root(client, owner):
    _, headers = owner
    folder = client.post("/folders", json={"name": "Archive"}, headers=headers).json()
    body = upload_file(client, headers, "notes.txt", folder_id=folder["id"])
    r = client.patch(f"/files/{body['file_id']}", json={"folder_id": None}, headers=headers)
    assert r.status_code == 200
    assert r.json()["folder_id"] is None


def test_move_file_into_unowned_folder_404(client, owner):
    _, headers = owner
    body = upload_file(client, headers, "notes.txt")
    r = client.patch(f"/files/{body['file_id']}", json={"folder_id": str(uuid.uuid4())}, headers=headers)
    assert r.status_code == 404


def test_delete_file_soft_deletes(client, owner):
    _, headers = owner
    body = upload_file(client, headers, "notes.txt")
    r = client.delete(f"/files/{body['file_id']}", headers=headers)
    assert r.status_code == 204
    r = client.get(f"/files/{body['file_id']}", headers=headers)
    assert r.json()["is_trashed"] is True


def test_trashed_file_excluded_from_folder_listing(client, owner):
    _, headers = owner
    body = upload_file(client, headers, "notes.txt")
    client.delete(f"/files/{body['file_id']}", headers=headers)
    r = client.get("/folders/contents", headers=headers)
    assert not any(f["id"] == body["file_id"] for f in r.json()["files"])


def test_deleting_already_trashed_folder_is_idempotent(client, owner):
    _, headers = owner
    folder = client.post("/folders", json={"name": "A"}, headers=headers).json()
    client.delete(f"/folders/{folder['id']}", headers=headers)
    r = client.delete(f"/folders/{folder['id']}", headers=headers)
    assert r.status_code == 204
