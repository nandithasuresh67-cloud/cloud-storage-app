import uuid
from datetime import datetime, timedelta

from app.models.link_share import LinkShare
from tests.conftest import upload_file


def _setup_shared_folder(client, owner_headers):
    """Owner creates a folder with a file, shares it with a viewer and an editor."""
    folder = client.post("/folders", json={"name": "Team Docs"}, headers=owner_headers).json()
    body = upload_file(client, owner_headers, "plan.txt", folder_id=folder["id"])
    return folder, body["file_id"]


def test_stranger_has_no_access(client, owner, stranger):
    _, owner_headers = owner
    _, stranger_headers = stranger
    folder, file_id = _setup_shared_folder(client, owner_headers)
    assert client.get(f"/folders/{folder['id']}", headers=stranger_headers).status_code == 404
    assert client.get(f"/files/{file_id}", headers=stranger_headers).status_code == 404


def test_share_folder_with_viewer_and_editor(client, owner, make_user):
    _, owner_headers = owner
    _, _ = make_user("viewer@example.com")
    _, _ = make_user("editor@example.com")
    folder, _ = _setup_shared_folder(client, owner_headers)

    r = client.post("/shares", json={"folder_id": folder["id"], "email": "viewer@example.com", "role": "viewer"}, headers=owner_headers)
    assert r.status_code == 201
    r = client.post("/shares", json={"folder_id": folder["id"], "email": "editor@example.com", "role": "editor"}, headers=owner_headers)
    assert r.status_code == 201


def test_non_owner_cannot_share(client, owner, make_user):
    _, owner_headers = owner
    _, viewer_headers = make_user("viewer@example.com")
    folder, _ = _setup_shared_folder(client, owner_headers)
    client.post("/shares", json={"folder_id": folder["id"], "email": "viewer@example.com", "role": "viewer"}, headers=owner_headers)

    r = client.post("/shares", json={"folder_id": folder["id"], "email": "anyone@example.com", "role": "viewer"}, headers=viewer_headers)
    assert r.status_code == 403


def test_share_with_unknown_email_404(client, owner):
    _, owner_headers = owner
    folder, _ = _setup_shared_folder(client, owner_headers)
    r = client.post("/shares", json={"folder_id": folder["id"], "email": "nobody@example.com", "role": "viewer"}, headers=owner_headers)
    assert r.status_code == 404


def test_share_requires_exactly_one_target(client, owner):
    _, owner_headers = owner
    r = client.post("/shares", json={"email": "x@example.com", "role": "viewer"}, headers=owner_headers)
    assert r.status_code == 422


def test_cascading_folder_share_grants_file_access(client, owner, make_user):
    _, owner_headers = owner
    _, viewer_headers = make_user("viewer@example.com")
    folder, file_id = _setup_shared_folder(client, owner_headers)
    client.post("/shares", json={"folder_id": folder["id"], "email": "viewer@example.com", "role": "viewer"}, headers=owner_headers)

    assert client.get(f"/folders/{folder['id']}", headers=viewer_headers).status_code == 200
    assert client.get(f"/files/{file_id}", headers=viewer_headers).status_code == 200


def test_viewer_cannot_write(client, owner, make_user):
    _, owner_headers = owner
    _, viewer_headers = make_user("viewer@example.com")
    folder, file_id = _setup_shared_folder(client, owner_headers)
    client.post("/shares", json={"folder_id": folder["id"], "email": "viewer@example.com", "role": "viewer"}, headers=owner_headers)

    assert client.patch(f"/files/{file_id}", json={"name": "x"}, headers=viewer_headers).status_code == 403
    assert client.delete(f"/files/{file_id}", headers=viewer_headers).status_code == 403
    assert client.patch(f"/folders/{folder['id']}", json={"name": "x"}, headers=viewer_headers).status_code == 403


def test_editor_can_write_and_upload_via_cascading_access(client, owner, make_user):
    _, owner_headers = owner
    _, editor_headers = make_user("editor@example.com")
    folder, file_id = _setup_shared_folder(client, owner_headers)
    client.post("/shares", json={"folder_id": folder["id"], "email": "editor@example.com", "role": "editor"}, headers=owner_headers)

    assert client.patch(f"/files/{file_id}", json={"name": "renamed.txt"}, headers=editor_headers).status_code == 200
    assert client.post(
        "/files/init-upload",
        json={"filename": "extra.txt", "mime_type": "text/plain", "size_bytes": 5, "folder_id": folder["id"]},
        headers=editor_headers,
    ).status_code == 201
    assert client.post("/folders", json={"name": "Sub", "parent_id": folder["id"]}, headers=editor_headers).status_code == 201


def test_editor_cannot_reshare_or_create_public_link(client, owner, make_user):
    _, owner_headers = owner
    _, editor_headers = make_user("editor@example.com")
    folder, _ = _setup_shared_folder(client, owner_headers)
    client.post("/shares", json={"folder_id": folder["id"], "email": "editor@example.com", "role": "editor"}, headers=owner_headers)

    assert client.post("/shares", json={"folder_id": folder["id"], "email": "x@example.com", "role": "viewer"}, headers=editor_headers).status_code == 403
    assert client.post("/public-link", json={"folder_id": folder["id"]}, headers=editor_headers).status_code == 403


def test_list_shares_is_owner_only(client, owner, make_user):
    _, owner_headers = owner
    _, viewer_headers = make_user("viewer@example.com")
    folder, _ = _setup_shared_folder(client, owner_headers)
    client.post("/shares", json={"folder_id": folder["id"], "email": "viewer@example.com", "role": "viewer"}, headers=owner_headers)

    r = client.get(f"/shares?folder_id={folder['id']}", headers=owner_headers)
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert client.get(f"/shares?folder_id={folder['id']}", headers=viewer_headers).status_code == 403


def test_shared_with_me_lists_the_folder(client, owner, make_user):
    _, owner_headers = owner
    _, viewer_headers = make_user("viewer@example.com")
    folder, _ = _setup_shared_folder(client, owner_headers)
    client.post("/shares", json={"folder_id": folder["id"], "email": "viewer@example.com", "role": "viewer"}, headers=owner_headers)

    r = client.get("/shares/shared-with-me", headers=viewer_headers)
    assert any(item["id"] == folder["id"] for item in r.json())


def test_resharing_updates_role_instead_of_duplicating(client, owner, make_user):
    _, owner_headers = owner
    _, viewer_headers = make_user("viewer@example.com")
    folder, file_id = _setup_shared_folder(client, owner_headers)
    client.post("/shares", json={"folder_id": folder["id"], "email": "viewer@example.com", "role": "viewer"}, headers=owner_headers)
    client.post("/shares", json={"folder_id": folder["id"], "email": "viewer@example.com", "role": "editor"}, headers=owner_headers)

    shares = client.get(f"/shares?folder_id={folder['id']}", headers=owner_headers).json()
    assert len(shares) == 1
    assert client.patch(f"/files/{file_id}", json={"name": "y.txt"}, headers=viewer_headers).status_code == 200


def test_revoking_share_removes_access(client, owner, make_user):
    _, owner_headers = owner
    _, editor_headers = make_user("editor@example.com")
    folder, _ = _setup_shared_folder(client, owner_headers)
    client.post("/shares", json={"folder_id": folder["id"], "email": "editor@example.com", "role": "editor"}, headers=owner_headers)
    share_id = client.get(f"/shares?folder_id={folder['id']}", headers=owner_headers).json()[0]["id"]

    r = client.delete(f"/shares/{share_id}", headers=owner_headers)
    assert r.status_code == 204
    assert client.get(f"/folders/{folder['id']}", headers=editor_headers).status_code == 404


def test_public_link_file_access_no_auth_required(client, owner):
    _, owner_headers = owner
    body = upload_file(client, owner_headers, "public.txt")
    link = client.post("/public-link", json={"file_id": body["file_id"]}, headers=owner_headers).json()

    r = client.post(f"/public-link/{link['token']}/access", json={})
    assert r.status_code == 200
    assert r.json()["name"] == "public.txt"


def test_public_link_bogus_token_404(client):
    r = client.post("/public-link/not-a-real-token/access", json={})
    assert r.status_code == 404


def test_public_link_password_protection(client, owner):
    _, owner_headers = owner
    body = upload_file(client, owner_headers, "secret.txt")
    link = client.post("/public-link", json={"file_id": body["file_id"], "password": "sesame"}, headers=owner_headers).json()
    assert link["has_password"] is True

    assert client.post(f"/public-link/{link['token']}/access", json={}).status_code == 401
    assert client.post(f"/public-link/{link['token']}/access", json={"password": "wrong"}).status_code == 401
    assert client.post(f"/public-link/{link['token']}/access", json={"password": "sesame"}).status_code == 200


def test_expired_public_link_returns_410(client, owner, db_session):
    _, owner_headers = owner
    body = upload_file(client, owner_headers, "temp.txt")
    link = client.post("/public-link", json={"file_id": body["file_id"], "expires_in_hours": 1}, headers=owner_headers).json()

    row = db_session.query(LinkShare).filter(LinkShare.token == link["token"]).first()
    row.expires_at = datetime.utcnow() - timedelta(hours=1)
    db_session.commit()

    r = client.post(f"/public-link/{link['token']}/access", json={})
    assert r.status_code == 410


def test_public_folder_link_lists_immediate_contents(client, owner):
    _, owner_headers = owner
    folder, file_id = _setup_shared_folder(client, owner_headers)
    client.post("/folders", json={"name": "Sub", "parent_id": folder["id"]}, headers=owner_headers)
    link = client.post("/public-link", json={"folder_id": folder["id"]}, headers=owner_headers).json()

    r = client.post(f"/public-link/{link['token']}/access", json={})
    assert r.status_code == 200
    names = {e["name"] for e in r.json()["entries"]}
    assert "plan.txt" in names
    assert "Sub" in names


def test_list_public_links_for_a_file(client, owner):
    _, owner_headers = owner
    body = upload_file(client, owner_headers, "shared.txt")

    r = client.get(f"/public-link?file_id={body['file_id']}", headers=owner_headers)
    assert r.status_code == 200
    assert r.json() == []

    created = client.post("/public-link", json={"file_id": body["file_id"]}, headers=owner_headers).json()

    r = client.get(f"/public-link?file_id={body['file_id']}", headers=owner_headers)
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["id"] == created["id"]
    assert r.json()[0]["token"] == created["token"]


def test_list_public_links_requires_exactly_one_target(client, owner):
    _, owner_headers = owner
    assert client.get("/public-link", headers=owner_headers).status_code == 400


def test_list_public_links_is_owner_only(client, owner, make_user):
    _, owner_headers = owner
    _, viewer_headers = make_user("viewer@example.com")
    body = upload_file(client, owner_headers, "shared.txt")
    client.post("/shares", json={"file_id": body["file_id"], "email": "viewer@example.com", "role": "viewer"}, headers=owner_headers)
    client.post("/public-link", json={"file_id": body["file_id"]}, headers=owner_headers)

    assert client.get(f"/public-link?file_id={body['file_id']}", headers=viewer_headers).status_code == 403


def test_revoked_link_no_longer_appears_in_listing(client, owner):
    _, owner_headers = owner
    body = upload_file(client, owner_headers, "shared.txt")
    link = client.post("/public-link", json={"file_id": body["file_id"]}, headers=owner_headers).json()

    client.delete(f"/public-link/{link['id']}", headers=owner_headers)

    r = client.get(f"/public-link?file_id={body['file_id']}", headers=owner_headers)
    assert r.json() == []


def test_only_owner_can_revoke_public_link(client, owner, make_user):
    _, owner_headers = owner
    _, viewer_headers = make_user("viewer@example.com")
    body = upload_file(client, owner_headers, "public.txt")
    client.post("/shares", json={"file_id": body["file_id"], "email": "viewer@example.com", "role": "viewer"}, headers=owner_headers)
    link = client.post("/public-link", json={"file_id": body["file_id"]}, headers=owner_headers).json()

    # Viewer has real (read-only) access to the file, but that's not enough
    # to revoke a public link - this should be 403 (insufficient role), not
    # 404, since they can genuinely see the file exists.
    assert client.delete(f"/public-link/{link['id']}", headers=viewer_headers).status_code == 403
    assert client.delete(f"/public-link/{link['id']}", headers=owner_headers).status_code == 204
    assert client.post(f"/public-link/{link['token']}/access", json={}).status_code == 404
