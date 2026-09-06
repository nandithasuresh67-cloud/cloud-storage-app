"""Day 13 final API smoke test: trash lifecycle and permission boundaries.

Uses the real FastAPI app with an in-memory SQLite database and a fake
storage provider, matching the deterministic pytest environment.
"""
import sys
import uuid
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import Base, get_db
from app.models.file import File
from app.models.folder import Folder
from app.models.user import User
from app.services import storage_service
from app.main import app

engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
Base.metadata.create_all(engine, tables=[User.__table__, Folder.__table__, File.__table__])
Session = sessionmaker(bind=engine)
db = Session()

paths = set()
removed = []
storage_service.create_signed_upload_url = lambda bucket, path: {"signed_url": f"https://fake/{path}", "token": "x", "path": path}
storage_service.object_exists = lambda bucket, path: path in paths
storage_service.create_signed_download_url = lambda bucket, path, expires_in: f"https://fake/download/{path}"
storage_service.remove_object = lambda bucket, path: (removed.append(path), paths.discard(path))

def override_db():
    yield db

app.dependency_overrides[get_db] = override_db
client = TestClient(app)

owner_id = uuid.uuid4()
stranger_id = uuid.uuid4()
db.add_all([
    User(id=owner_id, email="day13-owner@example.com", password_hash="x"),
    User(id=stranger_id, email="day13-stranger@example.com", password_hash="x"),
])
db.commit()
owner = {"X-User-Id": str(owner_id)}
stranger = {"X-User-Id": str(stranger_id)}

folder = client.post("/folders", json={"name": "Day 13 Test"}, headers=owner).json()
file = client.post("/files/init-upload", json={"filename": "trash-test.txt", "mime_type": "text/plain", "size_bytes": 5, "folder_id": folder["id"]}, headers=owner).json()
paths.add(file["storage_path"])
assert client.post(f"/files/{file['file_id']}/complete-upload", headers=owner).status_code == 200
assert client.delete(f"/folders/{folder['id']}", headers=owner).status_code == 204
assert len(client.get("/trash", headers=owner).json()) == 1
assert client.post(f"/trash/folders/{folder['id']}/restore", headers=owner).status_code == 204
assert client.get("/trash", headers=owner).json() == []
assert client.delete(f"/files/{file['file_id']}", headers=owner).status_code == 204
assert client.get("/trash", headers=owner).json()[0]["id"] == file["file_id"]
assert client.delete(f"/trash/files/{file['file_id']}", headers=stranger).status_code == 404
assert client.delete(f"/trash/files/{file['file_id']}", headers=owner).status_code == 204
assert file["storage_path"] in removed

print("Day 13 API smoke test: PASS")
