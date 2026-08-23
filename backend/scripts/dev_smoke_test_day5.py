"""
Manual smoke test for the Day 5 sharing & permissions flow.

Same approach as the Day 3/4 scripts: in-memory SQLite in place of
Supabase Postgres, real route/model/schema code. init-upload's Supabase
call is faked; everything else (shares, public links, permission checks)
is pure DB logic and needs no faking.

Run: cd backend && .venv/bin/python scripts/dev_smoke_test_day5.py
"""

import sys
import uuid

sys.path.insert(0, ".")

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.models.file import File
from app.models.folder import Folder
from app.models.link_share import LinkShare
from app.models.share import Share
from app.models.user import User
from app.services import storage_service
import app.main as main_module

engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
Base.metadata.create_all(
    engine, tables=[User.__table__, Folder.__table__, File.__table__, Share.__table__, LinkShare.__table__]
)
TestSession = sessionmaker(bind=engine)


def override_get_db():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


main_module.app.dependency_overrides[get_db] = override_get_db


def fake_create_signed_upload_url(bucket, path):
    return {"signed_url": f"https://fake.supabase.co/upload/{path}?token=abc", "token": "abc", "path": path}


storage_service.create_signed_upload_url = fake_create_signed_upload_url

# --- Seed three users: owner, an editor, and a viewer ---
owner_id, editor_id, viewer_id, stranger_id = (uuid.uuid4() for _ in range(4))
db = TestSession()
db.add(User(id=owner_id, email="owner@example.com", password_hash="x"))
db.add(User(id=editor_id, email="editor@example.com", password_hash="x"))
db.add(User(id=viewer_id, email="viewer@example.com", password_hash="x"))
db.add(User(id=stranger_id, email="stranger@example.com", password_hash="x"))
db.commit()
db.close()

client = TestClient(main_module.app)
owner_h = {"X-User-Id": str(owner_id)}
editor_h = {"X-User-Id": str(editor_id)}
viewer_h = {"X-User-Id": str(viewer_id)}
stranger_h = {"X-User-Id": str(stranger_id)}


def check(label, condition):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label}")
    if not condition:
        raise SystemExit(1)


# --- Setup: owner creates a folder with a file in it ---
r = client.post("/folders", json={"name": "Team Docs"}, headers=owner_h)
folder = r.json()
r = client.post(
    "/files/init-upload",
    json={"filename": "plan.txt", "mime_type": "text/plain", "size_bytes": 10, "folder_id": folder["id"]},
    headers=owner_h,
)
file_id = r.json()["file_id"]

# 1. A stranger cannot see the folder or file at all
r = client.get(f"/folders/{folder['id']}", headers=stranger_h)
check("stranger GET folder -> 404 (no access)", r.status_code == 404)
r = client.get(f"/files/{file_id}", headers=stranger_h)
check("stranger GET file -> 404 (no access)", r.status_code == 404)

# 2. Owner shares the folder: viewer as viewer, editor as editor
r = client.post("/shares", json={"folder_id": folder["id"], "email": "viewer@example.com", "role": "viewer"}, headers=owner_h)
check("POST /shares (folder, viewer) -> 201", r.status_code == 201)
r = client.post("/shares", json={"folder_id": folder["id"], "email": "editor@example.com", "role": "editor"}, headers=owner_h)
check("POST /shares (folder, editor) -> 201", r.status_code == 201)

# 3. A non-owner cannot share something they don't own
r = client.post("/shares", json={"folder_id": folder["id"], "email": "stranger@example.com", "role": "viewer"}, headers=viewer_h)
check("non-owner cannot create a share -> 403", r.status_code == 403)

# 4. Sharing with a nonexistent email -> 404
r = client.post("/shares", json={"folder_id": folder["id"], "email": "nobody@example.com", "role": "viewer"}, headers=owner_h)
check("share with unknown email -> 404", r.status_code == 404)

# 5. Sharing requires exactly one target
r = client.post("/shares", json={"email": "viewer@example.com", "role": "viewer"}, headers=owner_h)
check("share with neither file_id nor folder_id -> 422", r.status_code == 422)

# --- Cascading permission: sharing the FOLDER should grant access to the FILE inside it ---
# 6. Viewer can now read the folder and the file inside it, without being shared the file directly
r = client.get(f"/folders/{folder['id']}", headers=viewer_h)
check("viewer (via folder share) GET folder -> 200", r.status_code == 200)
r = client.get(f"/files/{file_id}", headers=viewer_h)
check("viewer (via cascading folder share) GET file -> 200", r.status_code == 200)

# 7. Viewer cannot rename/move/delete (read-only)
r = client.patch(f"/files/{file_id}", json={"name": "hacked.txt"}, headers=viewer_h)
check("viewer PATCH file -> 403", r.status_code == 403)
r = client.delete(f"/files/{file_id}", headers=viewer_h)
check("viewer DELETE file -> 403", r.status_code == 403)
r = client.patch(f"/folders/{folder['id']}", json={"name": "hacked"}, headers=viewer_h)
check("viewer PATCH folder -> 403", r.status_code == 403)

# 8. Editor CAN rename/upload/delete via cascading folder access
r = client.patch(f"/files/{file_id}", json={"name": "plan-v2.txt"}, headers=editor_h)
check("editor PATCH file (cascading access) -> 200", r.status_code == 200)
r = client.post(
    "/files/init-upload",
    json={"filename": "notes.txt", "mime_type": "text/plain", "size_bytes": 5, "folder_id": folder["id"]},
    headers=editor_h,
)
check("editor init-upload into shared folder -> 201", r.status_code == 201)
r = client.post("/folders", json={"name": "Subfolder", "parent_id": folder["id"]}, headers=editor_h)
check("editor create subfolder in shared folder -> 201", r.status_code == 201)

# 9. But editor still cannot SHARE the folder further (owner-only) or create a public link
r = client.post("/shares", json={"folder_id": folder["id"], "email": "stranger@example.com", "role": "viewer"}, headers=editor_h)
check("editor cannot re-share -> 403", r.status_code == 403)
r = client.post("/public-link", json={"folder_id": folder["id"]}, headers=editor_h)
check("editor cannot create a public link -> 403", r.status_code == 403)

# 10. GET /shares lists who has access (owner-only)
r = client.get(f"/shares?folder_id={folder['id']}", headers=owner_h)
check("GET /shares (owner) -> 200", r.status_code == 200)
check("2 shares listed", len(r.json()) == 2)
r = client.get(f"/shares?folder_id={folder['id']}", headers=viewer_h)
check("GET /shares (non-owner) -> 403", r.status_code == 403)

# 11. Shared-with-me lists the folder for both viewer and editor
r = client.get("/shares/shared-with-me", headers=viewer_h)
check("shared-with-me for viewer includes the folder", any(item["id"] == folder["id"] for item in r.json()))

# 12. Sharing again with the same person updates their role instead of duplicating
r = client.post("/shares", json={"folder_id": folder["id"], "email": "viewer@example.com", "role": "editor"}, headers=owner_h)
check("re-sharing updates role -> 201", r.status_code == 201)
r = client.get(f"/shares?folder_id={folder['id']}", headers=owner_h)
check("still only 2 shares (upsert, not duplicate)", len(r.json()) == 2)
r = client.patch(f"/files/{file_id}", json={"name": "plan-v3.txt"}, headers=viewer_h)
check("viewer (now promoted to editor) can PATCH -> 200", r.status_code == 200)

# 13. Revoke a share; access is gone afterward
r = client.get(f"/shares?folder_id={folder['id']}", headers=owner_h)
editor_share_id = next(s["id"] for s in r.json() if s["shared_with_email"] == "editor@example.com")
r = client.delete(f"/shares/{editor_share_id}", headers=owner_h)
check("DELETE /shares/{id} -> 204", r.status_code == 204)
r = client.get(f"/folders/{folder['id']}", headers=editor_h)
check("editor access revoked -> 404", r.status_code == 404)

# --- Public links ---
# 14. Owner creates a public link for the file (no password, no expiry)
r = client.post("/public-link", json={"file_id": file_id}, headers=owner_h)
check("POST /public-link (file) -> 201", r.status_code == 201)
link = r.json()
check("link has a token", len(link["token"]) > 10)

# 15. Anyone (no auth) can resolve the token
r = client.post(f"/public-link/{link['token']}/access", json={})
check("public access to file link (no auth) -> 200", r.status_code == 200)
check("public access returns file metadata", r.json()["name"] == "plan-v3.txt")

# 16. A made-up token doesn't work
r = client.post("/public-link/not-a-real-token/access", json={})
check("bogus token -> 404", r.status_code == 404)

# 17. Password-protected link
r = client.post("/public-link", json={"file_id": file_id, "password": "sesame"}, headers=owner_h)
protected_link = r.json()
check("password link has_password is true", protected_link["has_password"] is True)
r = client.post(f"/public-link/{protected_link['token']}/access", json={})
check("access without password -> 401", r.status_code == 401)
r = client.post(f"/public-link/{protected_link['token']}/access", json={"password": "wrong"})
check("access with wrong password -> 401", r.status_code == 401)
r = client.post(f"/public-link/{protected_link['token']}/access", json={"password": "sesame"})
check("access with correct password -> 200", r.status_code == 200)

# 18. Expired link
r = client.post("/public-link", json={"file_id": file_id, "expires_in_hours": 1}, headers=owner_h)
expiring_link = r.json()
db = TestSession()
row = db.query(LinkShare).filter(LinkShare.token == expiring_link["token"]).first()
from datetime import datetime, timedelta

row.expires_at = datetime.utcnow() - timedelta(hours=1)  # force it into the past
db.commit()
db.close()
r = client.post(f"/public-link/{expiring_link['token']}/access", json={})
check("expired link -> 410", r.status_code == 410)

# 19. Public link for a folder returns one level of contents
r = client.post("/public-link", json={"folder_id": folder["id"]}, headers=owner_h)
folder_link = r.json()
r = client.post(f"/public-link/{folder_link['token']}/access", json={})
check("public access to folder link -> 200", r.status_code == 200)
entry_names = {e["name"] for e in r.json()["entries"]}
check("folder link lists its contents", "notes.txt" in entry_names and "Subfolder" in entry_names)

# 20. Only the owner can revoke a public link
r = client.delete(f"/public-link/{link['id']}", headers=viewer_h)
check("non-owner cannot revoke public link -> 403", r.status_code == 403)
r = client.delete(f"/public-link/{link['id']}", headers=owner_h)
check("owner revokes public link -> 204", r.status_code == 204)
r = client.post(f"/public-link/{link['token']}/access", json={})
check("revoked link no longer resolves -> 404", r.status_code == 404)

print("\nAll checks passed.")
