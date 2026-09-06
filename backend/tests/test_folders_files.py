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


def test_default_sort_is_name_ascending(client, owner):
    _, headers = owner
    for name in ["Charlie", "Alpha", "Bravo"]:
        client.post("/folders", json={"name": name}, headers=headers)
    r = client.get("/folders/contents", headers=headers)
    names = [f["name"] for f in r.json()["subfolders"]]
    assert names == ["Alpha", "Bravo", "Charlie"]


def test_sort_by_name_descending(client, owner):
    _, headers = owner
    for name in ["Charlie", "Alpha", "Bravo"]:
        client.post("/folders", json={"name": name}, headers=headers)
    r = client.get("/folders/contents?sort_by=name&sort_order=desc", headers=headers)
    names = [f["name"] for f in r.json()["subfolders"]]
    assert names == ["Charlie", "Bravo", "Alpha"]


def test_sort_files_by_size(client, owner):
    _, headers = owner
    upload_file(client, headers, "small.txt", size_bytes=10)
    upload_file(client, headers, "large.txt", size_bytes=10_000)
    upload_file(client, headers, "medium.txt", size_bytes=500)

    r = client.get("/folders/contents?sort_by=size&sort_order=asc", headers=headers)
    names = [f["name"] for f in r.json()["files"]]
    assert names == ["small.txt", "medium.txt", "large.txt"]

    r = client.get("/folders/contents?sort_by=size&sort_order=desc", headers=headers)
    names = [f["name"] for f in r.json()["files"]]
    assert names == ["large.txt", "medium.txt", "small.txt"]


def test_sort_by_size_on_folders_falls_back_to_name(client, owner):
    """Folders have no size column - sort_by=size shouldn't error or return an arbitrary/undefined order."""
    for name in ["Charlie", "Alpha", "Bravo"]:
        client.post("/folders", json={"name": name}, headers=owner[1])
    r = client.get("/folders/contents?sort_by=size&sort_order=asc", headers=owner[1])
    assert r.status_code == 200
    names = [f["name"] for f in r.json()["subfolders"]]
    assert names == ["Alpha", "Bravo", "Charlie"]


def test_invalid_sort_by_rejected(client, owner):
    r = client.get("/folders/contents?sort_by=nonsense", headers=owner[1])
    assert r.status_code == 422


def test_pagination_limit_and_offset(client, owner):
    _, headers = owner
    for i in range(5):
        client.post("/folders", json={"name": f"Folder{i}"}, headers=headers)

    r = client.get("/folders/contents?limit=2&offset=0", headers=headers)
    body = r.json()
    assert len(body["subfolders"]) == 2
    assert body["subfolders_total"] == 5
    assert [f["name"] for f in body["subfolders"]] == ["Folder0", "Folder1"]

    r = client.get("/folders/contents?limit=2&offset=2", headers=headers)
    body = r.json()
    assert len(body["subfolders"]) == 2
    assert [f["name"] for f in body["subfolders"]] == ["Folder2", "Folder3"]

    r = client.get("/folders/contents?limit=2&offset=4", headers=headers)
    body = r.json()
    assert len(body["subfolders"]) == 1
    assert body["subfolders"][0]["name"] == "Folder4"


def test_pagination_pages_do_not_overlap_or_skip(client, owner):
    """Walking every page with a fixed limit should reconstruct the exact full set exactly once each."""
    _, headers = owner
    expected_names = {f"Item{i}" for i in range(7)}
    for name in expected_names:
        client.post("/folders", json={"name": name}, headers=headers)

    seen = []
    offset = 0
    limit = 3
    while True:
        r = client.get(f"/folders/contents?limit={limit}&offset={offset}", headers=headers)
        page = r.json()["subfolders"]
        if not page:
            break
        seen.extend(f["name"] for f in page)
        offset += limit

    assert len(seen) == len(expected_names), "pagination produced duplicates or a different count than created"
    assert set(seen) == expected_names


def test_pagination_totals_reflect_full_count_not_page_size(client, owner):
    _, headers = owner
    for i in range(3):
        client.post("/folders", json={"name": f"F{i}"}, headers=headers)
    upload_file(client, headers, "a.txt")
    upload_file(client, headers, "b.txt")

    r = client.get("/folders/contents?limit=1&offset=0", headers=headers)
    body = r.json()
    assert body["subfolders_total"] == 3
    assert body["files_total"] == 2
    assert len(body["subfolders"]) == 1
    assert len(body["files"]) == 1


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
