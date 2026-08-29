"""
Manual smoke test for the Day 6 search & trash flow.

Same approach as the Day 3/4/5 scripts: in-memory SQLite in place of
Supabase Postgres, real route/model/schema code. init-upload's Supabase
call is faked; permanent delete's storage removal call is also faked so
it can be verified without live network.

Run: cd backend && .venv/bin/python scripts/dev_smoke_test_day6.py
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

_removed_objects = []


def fake_create_signed_upload_url(bucket, path):
    return {"signed_url": f"https://fake.supabase.co/upload/{path}?token=abc", "token": "abc", "path": path}


def fake_remove_object(bucket, path):
    _removed_objects.append(path)


storage_service.create_signed_upload_url = fake_create_signed_upload_url
storage_service.remove_object = fake_remove_object

user_id = uuid.uuid4()
other_id = uuid.uuid4()
db = TestSession()
db.add(User(id=user_id, email="dev@example.com", password_hash="x"))
db.add(User(id=other_id, email="other@example.com", password_hash="x"))
db.commit()
db.close()

client = TestClient(main_module.app)
headers = {"X-User-Id": str(user_id)}
other_headers = {"X-User-Id": str(other_id)}


def check(label, condition):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label}")
    if not condition:
        raise SystemExit(1)


def upload(filename, mime_type="text/plain", size_bytes=10, folder_id=None):
    body = {"filename": filename, "mime_type": mime_type, "size_bytes": size_bytes}
    if folder_id:
        body["folder_id"] = folder_id
    r = client.post("/files/init-upload", json=body, headers=headers)
    return r.json()["file_id"]


# ============ SEARCH ============

# 1. Create some folders and files to search across
r = client.post("/folders", json={"name": "Vacation Photos"}, headers=headers)
vacation = r.json()
r = client.post("/folders", json={"name": "Work Docs"}, headers=headers)
work = r.json()

photo_id = upload("beach.jpg", mime_type="image/jpeg", folder_id=vacation["id"])
report_id = upload("quarterly-report.pdf", mime_type="application/pdf", folder_id=work["id"])
notes_id = upload("meeting-notes.txt", mime_type="text/plain", folder_id=work["id"])

# 2. Name-based search, case-insensitive substring
r = client.get("/search?q=report", headers=headers)
check("GET /search?q=report -> 200", r.status_code == 200)
names = {item["name"] for item in r.json()}
check("finds quarterly-report.pdf", "quarterly-report.pdf" in names)
check("does not find unrelated files", "beach.jpg" not in names)

r = client.get("/search?q=REPORT", headers=headers)
check("search is case-insensitive", any(i["name"] == "quarterly-report.pdf" for i in r.json()))

# 3. Search also matches folder names
r = client.get("/search?q=vacation", headers=headers)
types = {(item["type"], item["name"]) for item in r.json()}
check("search matches folder names too", ("folder", "Vacation Photos") in types)

# 4. Type-based filtering: item_type=file excludes folders
r = client.get("/search?q=work", headers=headers)
check("q=work with no filter finds the folder", any(i["type"] == "folder" for i in r.json()))
r = client.get("/search?q=work&item_type=file", headers=headers)
check("item_type=file excludes folders even if name matches", all(i["type"] == "file" for i in r.json()))

# 5. Type-based filtering: mime_type prefix match
r = client.get("/search?q=e&mime_type=image/", headers=headers)
check("mime_type=image/ only returns images", all(i.get("mime_type", "").startswith("image/") for i in r.json()))
check("beach.jpg found via mime filter", any(i["name"] == "beach.jpg" for i in r.json()))

# 6. Search never returns another user's items
r = client.get("/search?q=e", headers=other_headers)
check("other user's search finds none of these items", not any(i["id"] == photo_id for i in r.json()))

# 7. Trashed items are excluded from search
client.delete(f"/files/{notes_id}", headers=headers)
r = client.get("/search?q=meeting", headers=headers)
check("trashed file excluded from search results", not any(i["id"] == notes_id for i in r.json()))
client.post(f"/trash/files/{notes_id}/restore", headers=headers)  # put it back for later checks

# ============ TRASH: listing, cascading trash, restore, permanent delete ============

# 8. Trash a whole folder tree: Work Docs (with report.pdf, notes.txt) + a nested subfolder
r = client.post("/folders", json={"name": "Archive", "parent_id": work["id"]}, headers=headers)
archive = r.json()
archived_file_id = upload("old.txt", folder_id=archive["id"])

r = client.delete(f"/folders/{work['id']}", headers=headers)
check("DELETE /folders/{id} (cascading trash) -> 204", r.status_code == 204)

# 9. Everything underneath got trashed too, not just the top folder
r = client.get(f"/files/{report_id}", headers=headers)
check("file inside trashed folder is flagged trashed", r.json()["is_trashed"] is True)
r = client.get(f"/folders/{archive['id']}", headers=headers)
check("nested subfolder is flagged trashed", r.json()["is_trashed"] is True)
r = client.get(f"/files/{archived_file_id}", headers=headers)
check("file inside nested trashed subfolder is flagged trashed", r.json()["is_trashed"] is True)

# 10. GET /trash shows only the root (Work Docs), not its cascaded children
r = client.get("/trash", headers=headers)
check("GET /trash -> 200", r.status_code == 200)
trash_ids = {item["id"] for item in r.json()}
check("trash lists the trashed root folder", work["id"] in trash_ids)
check("trash does NOT separately list the cascaded subfolder", archive["id"] not in trash_ids)
check("trash does NOT separately list cascaded files", report_id not in trash_ids and archived_file_id not in trash_ids)

# 11. Restoring is owner-only and requires the item to actually be trashed
r = client.post(f"/trash/folders/{vacation['id']}/restore", headers=headers)
check("restoring a non-trashed folder -> 400", r.status_code == 400)

# 12. Restore cascades back down
r = client.post(f"/trash/folders/{work['id']}/restore", headers=headers)
check("POST /trash/folders/{id}/restore -> 204", r.status_code == 204)
r = client.get(f"/files/{report_id}", headers=headers)
check("file restored along with its folder", r.json()["is_trashed"] is False)
r = client.get(f"/folders/{archive['id']}", headers=headers)
check("nested subfolder restored too", r.json()["is_trashed"] is False)
r = client.get("/trash", headers=headers)
check("trash is empty again after restore", len(r.json()) == 0)

# 13. Permanent delete requires the item to be trashed first
r = client.delete(f"/trash/files/{report_id}", headers=headers)
check("permanently deleting a non-trashed file -> 400", r.status_code == 400)

# 14. Trash then permanently delete a single file - storage object actually removed
removed_before_single = len(_removed_objects)
client.delete(f"/files/{report_id}", headers=headers)
r = client.delete(f"/trash/files/{report_id}", headers=headers)
check("DELETE /trash/files/{id} -> 204", r.status_code == 204)
r = client.get(f"/files/{report_id}", headers=headers)
check("permanently deleted file is really gone -> 404", r.status_code == 404)
check("storage object was actually removed", len(_removed_objects) == removed_before_single + 1)

# 15. Permanent delete of a folder cascades and cleans up storage for every file underneath
before_removed_count = len(_removed_objects)
client.delete(f"/folders/{work['id']}", headers=headers)  # trash again (has Archive/old.txt left)
r = client.delete(f"/trash/folders/{work['id']}", headers=headers)
check("DELETE /trash/folders/{id} (permanent, cascading) -> 204", r.status_code == 204)
r = client.get(f"/folders/{work['id']}", headers=headers)
check("permanently deleted folder is really gone -> 404", r.status_code == 404)
r = client.get(f"/folders/{archive['id']}", headers=headers)
check("cascaded subfolder is also really gone -> 404", r.status_code == 404)
r = client.get(f"/files/{archived_file_id}", headers=headers)
check("file inside cascaded subfolder is also really gone -> 404", r.status_code == 404)
check("storage cleanup happened for the cascaded file too", len(_removed_objects) > before_removed_count)

# 16. Ownership still enforced on trash endpoints
r = client.delete(f"/files/{photo_id}", headers=headers)
r = client.delete(f"/trash/files/{photo_id}", headers=other_headers)
check("non-owner cannot permanently delete someone else's file -> 404", r.status_code == 404)

print("\nAll checks passed.")
