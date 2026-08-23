"""
Manual smoke test for the Day 4 folder & file operations flow.

Same approach as scripts/dev_smoke_test.py: in-memory SQLite in place of
Supabase Postgres, real route/model/schema code, no live network calls
(folders don't touch storage at all, so nothing needs mocking here).

Run: cd backend && .venv/bin/python scripts/dev_smoke_test_day4.py
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
from app.models.share import Share
from app.models.user import User
from app.services import storage_service
import app.main as main_module

engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
Base.metadata.create_all(engine, tables=[User.__table__, Folder.__table__, File.__table__, Share.__table__])
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

user_id = uuid.uuid4()
other_user_id = uuid.uuid4()
db = TestSession()
db.add(User(id=user_id, email="dev@example.com", password_hash="x"))
db.add(User(id=other_user_id, email="other@example.com", password_hash="x"))
db.commit()
db.close()

client = TestClient(main_module.app)
headers = {"X-User-Id": str(user_id)}
other_headers = {"X-User-Id": str(other_user_id)}


def check(label, condition):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label}")
    if not condition:
        raise SystemExit(1)


# 1. Create a root-level folder
r = client.post("/folders", json={"name": "Projects"}, headers=headers)
check("POST /folders (root) -> 201", r.status_code == 201)
projects = r.json()
check("parent_id is null for root folder", projects["parent_id"] is None)

# 2. Create a nested subfolder
r = client.post("/folders", json={"name": "Q3", "parent_id": projects["id"]}, headers=headers)
check("POST /folders (nested) -> 201", r.status_code == 201)
q3 = r.json()
check("parent_id matches parent", q3["parent_id"] == projects["id"])

# 3. Creating a folder under someone else's folder -> 404 (not 403 - don't leak existence)
r = client.post("/folders", json={"name": "sneaky", "parent_id": projects["id"]}, headers=other_headers)
check("create folder under another user's folder -> 404", r.status_code == 404)

# 4. Path traversal in folder name is rejected
r = client.post("/folders", json={"name": "../evil"}, headers=headers)
check("folder name with path traversal -> 422", r.status_code == 422)

# 5. GET /folders/{id} metadata
r = client.get(f"/folders/{q3['id']}", headers=headers)
check("GET /folders/{id} -> 200", r.status_code == 200)
check("GET /folders/{id} returns correct name", r.json()["name"] == "Q3")

# 6. Another user cannot read this folder
r = client.get(f"/folders/{q3['id']}", headers=other_headers)
check("other user GET folder -> 404", r.status_code == 404)

# 7. List root contents -> should show "Projects", nothing else
r = client.get("/folders/contents", headers=headers)
check("GET /folders/contents (root) -> 200", r.status_code == 200)
root_contents = r.json()
check("root folder is null", root_contents["folder"] is None)
check("root breadcrumb is empty", root_contents["breadcrumb"] == [])
check("root subfolders contains Projects", any(f["id"] == projects["id"] for f in root_contents["subfolders"]))

# 8. List Projects contents -> should show Q3, breadcrumb = [Projects]
r = client.get(f"/folders/contents?folder_id={projects['id']}", headers=headers)
check("GET /folders/contents?folder_id=Projects -> 200", r.status_code == 200)
projects_contents = r.json()
check("breadcrumb = [Projects]", [b["name"] for b in projects_contents["breadcrumb"]] == ["Projects"])
check("subfolders contains Q3", any(f["id"] == q3["id"] for f in projects_contents["subfolders"]))

# 9. List Q3 contents -> breadcrumb = [Projects, Q3]
r = client.get(f"/folders/contents?folder_id={q3['id']}", headers=headers)
check("breadcrumb = [Projects, Q3]", [b["name"] for b in r.json()["breadcrumb"]] == ["Projects", "Q3"])

# 10. Rename Q3 -> "Q3 Final"
r = client.patch(f"/folders/{q3['id']}", json={"name": "Q3 Final"}, headers=headers)
check("PATCH rename folder -> 200", r.status_code == 200)
check("name actually changed", r.json()["name"] == "Q3 Final")
check("parent_id untouched by rename-only patch", r.json()["parent_id"] == projects["id"])

# 11. Create a second root folder, then move Q3 into it
r = client.post("/folders", json={"name": "Archive"}, headers=headers)
archive = r.json()
r = client.patch(f"/folders/{q3['id']}", json={"parent_id": archive["id"]}, headers=headers)
check("PATCH move folder -> 200", r.status_code == 200)
check("parent_id updated", r.json()["parent_id"] == archive["id"])

# 12. Move Q3 back to root explicitly (parent_id: null)
r = client.patch(f"/folders/{q3['id']}", json={"parent_id": None}, headers=headers)
check("PATCH move folder to root (explicit null) -> 200", r.status_code == 200)
check("parent_id is null", r.json()["parent_id"] is None)

# 13. A folder cannot be moved into itself
r = client.patch(f"/folders/{q3['id']}", json={"parent_id": q3["id"]}, headers=headers)
check("move folder into itself -> 400", r.status_code == 400)

# 14. A folder cannot be moved into its own descendant (cycle prevention)
r = client.post("/folders", json={"name": "Sub", "parent_id": q3["id"]}, headers=headers)
sub = r.json()
r = client.patch(f"/folders/{q3['id']}", json={"parent_id": sub["id"]}, headers=headers)
check("move folder into its own child -> 400 (cycle prevented)", r.status_code == 400)

# 15. Create a file inside Projects, then rename + move it via PATCH
r = client.post(
    "/files/init-upload",
    json={"filename": "notes.txt", "mime_type": "text/plain", "size_bytes": 10, "folder_id": projects["id"]},
    headers=headers,
)
check("create file inside a folder -> 201", r.status_code == 201)
file_id = r.json()["file_id"]

r = client.patch(f"/files/{file_id}", json={"name": "notes-renamed.txt"}, headers=headers)
check("PATCH rename file -> 200", r.status_code == 200)
check("file name changed", r.json()["name"] == "notes-renamed.txt")
check("file folder_id untouched by rename-only patch", r.json()["folder_id"] == projects["id"])

r = client.patch(f"/files/{file_id}", json={"folder_id": archive["id"]}, headers=headers)
check("PATCH move file -> 200", r.status_code == 200)
check("file folder_id updated", r.json()["folder_id"] == archive["id"])

r = client.patch(f"/files/{file_id}", json={"folder_id": None}, headers=headers)
check("PATCH move file to root -> 200", r.status_code == 200)
check("file folder_id is null", r.json()["folder_id"] is None)

# 16. Moving a file into a folder you don't own -> 404
r = client.patch(f"/files/{file_id}", json={"folder_id": str(uuid.uuid4())}, headers=headers)
check("move file into nonexistent/unowned folder -> 404", r.status_code == 404)

# 17. Soft delete a file
r = client.delete(f"/files/{file_id}", headers=headers)
check("DELETE /files/{id} -> 204", r.status_code == 204)
r = client.get(f"/files/{file_id}", headers=headers)
# NOTE: current GET /files/{id} doesn't filter out trashed files - it still
# returns them (Day 6's Trash feature is what adds "list only trashed" /
# "restore" UX). What matters here is the is_trashed flag flipped.
check("file still fetchable directly, but flagged trashed", r.json()["is_trashed"] is True)

# 18. Trashed file no longer appears in folder contents listing
r = client.get("/folders/contents", headers=headers)
check("trashed file excluded from root contents", not any(f["id"] == file_id for f in r.json()["files"]))

# 19. Soft delete a folder (no cascade yet - documented)
r = client.delete(f"/folders/{archive['id']}", headers=headers)
check("DELETE /folders/{id} -> 204", r.status_code == 204)
r = client.get("/folders/contents", headers=headers)
check("trashed folder excluded from root contents", not any(f["id"] == archive["id"] for f in r.json()["subfolders"]))

# 20. Idempotent delete (deleting an already-trashed folder doesn't error)
r = client.delete(f"/folders/{archive['id']}", headers=headers)
check("deleting an already-trashed folder is still 204", r.status_code == 204)

print("\nAll checks passed.")
