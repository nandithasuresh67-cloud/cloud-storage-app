"""
Shared fixtures for the pytest suite.

Every test gets a FRESH in-memory SQLite database (function-scoped) rather
than one shared engine - this makes tests independent and order-safe,
unlike the earlier backend/scripts/dev_smoke_test*.py scripts, which were
written as sequential manual-run scenarios sharing one long-lived engine.
Both approaches are kept: the smoke test scripts remain useful for a
human to eyeball a full end-to-end scenario at once, while these pytest
tests are what CI/`pytest` actually runs.

Supabase Storage calls are monkeypatched to fakes for every test
(autouse) - this suite never touches the network, matching this sandbox's
egress restrictions and making the suite fast and deterministic.
"""

import sys
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import Base, get_db  # noqa: E402
from app.models.file import File  # noqa: E402
from app.models.folder import Folder  # noqa: E402
from app.models.link_share import LinkShare  # noqa: E402
from app.models.share import Share  # noqa: E402
from app.models.user import User  # noqa: E402
from app.services import storage_service  # noqa: E402
import app.main as main_module  # noqa: E402


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(
        engine, tables=[User.__table__, Folder.__table__, File.__table__, Share.__table__, LinkShare.__table__]
    )
    TestSession = sessionmaker(bind=engine)
    session = TestSession()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass  # db_session fixture owns closing it

    main_module.app.dependency_overrides[get_db] = override_get_db
    yield TestClient(main_module.app)
    main_module.app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def fake_storage(monkeypatch):
    """Replaces every Supabase Storage call with an in-memory fake. Autouse - no test needs to opt in."""
    uploaded_paths: set[str] = set()
    removed_paths: list[str] = []

    def fake_create_signed_upload_url(bucket, path):
        return {"signed_url": f"https://fake.supabase.co/upload/{path}?token=abc", "token": "abc", "path": path}

    def fake_object_exists(bucket, path):
        return path in uploaded_paths

    def fake_create_signed_download_url(bucket, path, expires_in):
        return f"https://fake.supabase.co/download/{path}"

    def fake_remove_object(bucket, path):
        removed_paths.append(path)
        uploaded_paths.discard(path)

    monkeypatch.setattr(storage_service, "create_signed_upload_url", fake_create_signed_upload_url)
    monkeypatch.setattr(storage_service, "object_exists", fake_object_exists)
    monkeypatch.setattr(storage_service, "create_signed_download_url", fake_create_signed_download_url)
    monkeypatch.setattr(storage_service, "remove_object", fake_remove_object)

    return {"uploaded_paths": uploaded_paths, "removed_paths": removed_paths}


@pytest.fixture()
def make_user(db_session):
    """Factory fixture: make_user() -> (user_id, headers). Call multiple times for multiple users."""

    def _make_user(email: str | None = None):
        user_id = uuid.uuid4()
        db_session.add(User(id=user_id, email=email or f"{user_id}@example.com", password_hash="x"))
        db_session.commit()
        return user_id, {"X-User-Id": str(user_id)}

    return _make_user


@pytest.fixture()
def owner(make_user):
    return make_user("owner@example.com")


@pytest.fixture()
def stranger(make_user):
    return make_user("stranger@example.com")


def upload_file(client, headers, filename, mime_type="text/plain", size_bytes=10, folder_id=None):
    """Helper: calls init-upload and returns the parsed response body."""
    body = {"filename": filename, "mime_type": mime_type, "size_bytes": size_bytes}
    if folder_id:
        body["folder_id"] = str(folder_id)
    r = client.post("/files/init-upload", json=body, headers=headers)
    assert r.status_code == 201, r.text
    return r.json()


def complete_upload(client, headers, fake_storage, file_id, storage_path):
    """Helper: simulates the client having PUT bytes, then calls complete-upload."""
    fake_storage["uploaded_paths"].add(storage_path)
    r = client.post(f"/files/{file_id}/complete-upload", json={}, headers=headers)
    assert r.status_code == 200, r.text
    return r.json()
