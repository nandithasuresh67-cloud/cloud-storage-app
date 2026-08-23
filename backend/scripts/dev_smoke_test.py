"""
Manual smoke test for the Day 3 upload flow.

Not a permanent part of the app - this sandbox's network egress doesn't
allow api.supabase.co, so there's no way to hit real Supabase Storage from
here. This script proves the endpoint logic (validation, DB writes,
signed-URL handoff, status transitions) is correct by:
  - using an in-memory SQLite DB instead of Supabase Postgres
  - monkeypatching app.services.storage_service to fake the storage calls

Run: cd backend && .venv/bin/python scripts/dev_smoke_test.py
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

# --- In-memory SQLite wired in place of Supabase Postgres ---
# StaticPool keeps a single connection alive for the whole process - a
# plain in-memory sqlite DB is otherwise wiped every time a new connection
# is opened, which is exactly what SQLAlchemy's session-per-request does.
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

# --- Seed a user (files.owner_id has a real FK to users.id) ---
user_id = uuid.uuid4()
db = TestSession()
db.add(User(id=user_id, email="dev@example.com", password_hash="x"))
db.commit()
db.close()

# --- Fake storage backend so no real network call to Supabase happens ---
_fake_storage_objects = set()


def fake_create_signed_upload_url(bucket, path):
    return {"signed_url": f"https://fake.supabase.co/upload/{path}?token=abc", "token": "abc", "path": path}


def fake_object_exists(bucket, path):
    return path in _fake_storage_objects


def fake_create_signed_download_url(bucket, path, expires_in):
    return f"https://fake.supabase.co/download/{path}"


storage_service.create_signed_upload_url = fake_create_signed_upload_url
storage_service.object_exists = fake_object_exists
storage_service.create_signed_download_url = fake_create_signed_download_url

client = TestClient(main_module.app)
headers = {"X-User-Id": str(user_id)}


def check(label, condition):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label}")
    if not condition:
        raise SystemExit(1)


# 1. health + root still work
r = client.get("/health")
check("GET /health -> 200", r.status_code == 200)

# 2. init-upload with a valid request
r = client.post(
    "/files/init-upload",
    json={"filename": "report.pdf", "mime_type": "application/pdf", "size_bytes": 1024},
    headers=headers,
)
check("POST /files/init-upload -> 201", r.status_code == 201)
body = r.json()
check("response has upload_url", "upload_url" in body and body["upload_url"].startswith("https://"))
file_id = body["file_id"]

# 3. oversized file is rejected
r = client.post(
    "/files/init-upload",
    json={"filename": "huge.bin", "mime_type": "application/octet-stream", "size_bytes": 999_999_999_999},
    headers=headers,
)
check("oversized file -> 413", r.status_code == 413)

# 4. blocked mime type is rejected
r = client.post(
    "/files/init-upload",
    json={"filename": "virus.exe", "mime_type": "application/x-msdownload", "size_bytes": 100},
    headers=headers,
)
check("blocked mime type -> 415", r.status_code == 415)

# 5. path traversal filename is rejected
r = client.post(
    "/files/init-upload",
    json={"filename": "../../etc/passwd", "mime_type": "text/plain", "size_bytes": 10},
    headers=headers,
)
check("path traversal filename -> 422", r.status_code == 422)

# 6. complete-upload before the object exists in storage -> 409
r = client.post(f"/files/{file_id}/complete-upload", json={}, headers=headers)
check("complete-upload before real upload -> 409", r.status_code == 409)

# 7. "upload" the object to fake storage, then complete-upload succeeds
storage_path = body["storage_path"]
_fake_storage_objects.add(storage_path)
r = client.post(f"/files/{file_id}/complete-upload", json={}, headers=headers)
check("complete-upload after real upload -> 200", r.status_code == 200)
check("upload_status == uploaded", r.json()["upload_status"] == "uploaded")

# 8. complete-upload is idempotent
r = client.post(f"/files/{file_id}/complete-upload", json={}, headers=headers)
check("complete-upload called twice -> still 200", r.status_code == 200)

# 9. get file returns metadata + a download url now that it's uploaded
r = client.get(f"/files/{file_id}", headers=headers)
check("GET /files/{id} -> 200", r.status_code == 200)
check("download_url present once uploaded", r.json()["download_url"] is not None)

# 10. another user cannot read someone else's file
other_user = uuid.uuid4()
db = TestSession()
db.add(User(id=other_user, email="other@example.com", password_hash="x"))
db.commit()
db.close()
r = client.get(f"/files/{file_id}", headers={"X-User-Id": str(other_user)})
check("other user cannot GET someone else's file -> 404", r.status_code == 404)

# 11. missing/invalid X-User-Id header is rejected
r = client.post(
    "/files/init-upload",
    json={"filename": "a.txt", "mime_type": "text/plain", "size_bytes": 10},
    headers={"X-User-Id": "not-a-uuid"},
)
check("invalid X-User-Id -> 401", r.status_code == 401)

print("\nAll checks passed.")
