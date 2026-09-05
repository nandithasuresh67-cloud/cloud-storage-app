import secrets
import uuid
from datetime import datetime, timedelta
from typing import Optional, Union

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.deps import get_current_user_id
from app.core.security import hash_password, verify_password
from app.models.file import File
from app.models.folder import Folder
from app.models.link_share import LinkShare
from app.schemas.public_link import (
    PublicLinkAccessRequest,
    PublicLinkCreateRequest,
    PublicLinkFileAccess,
    PublicLinkFolderAccess,
    PublicLinkFolderEntry,
    PublicLinkOut,
)
from app.services import storage_service
from app.services.permissions import Role, require_file_access, require_folder_access

router = APIRouter(tags=["public-links"])
settings = get_settings()


def _to_out(link: LinkShare) -> PublicLinkOut:
    return PublicLinkOut(
        id=link.id,
        file_id=link.file_id,
        folder_id=link.folder_id,
        token=link.token,
        has_password=link.password_hash is not None,
        expires_at=link.expires_at,
        created_at=link.created_at,
    )


@router.get("/public-link", response_model=list[PublicLinkOut])
def list_public_links(
    file_id: Optional[uuid.UUID] = Query(None),
    folder_id: Optional[uuid.UUID] = Query(None),
    db: Session = Depends(get_db),
    owner_id: uuid.UUID = Depends(get_current_user_id),
):
    """
    Lists active public links for a file or folder - owner-only, same
    shape as GET /shares. Exists so the frontend Share modal can show
    "this already has a public link" instead of only ever being able to
    create new ones with no way to see or manage existing ones.
    """
    if (file_id is None) == (folder_id is None):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Provide exactly one of file_id or folder_id.")

    if file_id is not None:
        require_file_access(db, file_id, owner_id, Role.OWNER)
    else:
        require_folder_access(db, folder_id, owner_id, Role.OWNER)

    links = db.query(LinkShare).filter(LinkShare.file_id == file_id, LinkShare.folder_id == folder_id).all()
    return [_to_out(link) for link in links]


@router.post("/public-link", response_model=PublicLinkOut, status_code=status.HTTP_201_CREATED)
def create_public_link(
    payload: PublicLinkCreateRequest,
    db: Session = Depends(get_db),
    owner_id: uuid.UUID = Depends(get_current_user_id),
):
    """Only the owner can create a public link - an editor with cascading access can't mint a public link on someone's behalf."""
    if payload.file_id is not None:
        require_file_access(db, payload.file_id, owner_id, Role.OWNER)
    else:
        require_folder_access(db, payload.folder_id, owner_id, Role.OWNER)

    expires_at = None
    if payload.expires_in_hours is not None:
        expires_at = datetime.utcnow() + timedelta(hours=payload.expires_in_hours)

    link = LinkShare(
        file_id=payload.file_id,
        folder_id=payload.folder_id,
        token=secrets.token_urlsafe(24),
        password_hash=hash_password(payload.password) if payload.password else None,
        expires_at=expires_at,
        created_by=owner_id,
    )
    db.add(link)
    db.commit()
    db.refresh(link)
    return _to_out(link)


@router.delete("/public-link/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_public_link(
    link_id: uuid.UUID,
    db: Session = Depends(get_db),
    owner_id: uuid.UUID = Depends(get_current_user_id),
):
    link = db.query(LinkShare).filter(LinkShare.id == link_id).first()
    if link is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")

    if link.file_id is not None:
        require_file_access(db, link.file_id, owner_id, Role.OWNER)
    else:
        require_folder_access(db, link.folder_id, owner_id, Role.OWNER)

    db.delete(link)
    db.commit()
    return None


@router.post("/public-link/{token}/access", response_model=Union[PublicLinkFileAccess, PublicLinkFolderAccess])
def access_public_link(
    token: str,
    payload: PublicLinkAccessRequest = PublicLinkAccessRequest(),
    db: Session = Depends(get_db),
):
    """
    No auth required - this is the "Public User" access path from the
    spec's role list. POST (not GET) so a password can be sent in the body
    rather than as a query string that ends up in server/proxy logs.
    """
    link = db.query(LinkShare).filter(LinkShare.token == token).first()
    if link is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found or has been revoked.")

    if link.expires_at is not None and link.expires_at < datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="This link has expired.")

    if link.password_hash is not None:
        if not payload.password or not verify_password(payload.password, link.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect or missing password.")

    if link.file_id is not None:
        file = db.query(File).filter(File.id == link.file_id, File.is_trashed.is_(False)).first()
        if file is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found or has been deleted.")

        download_url = None
        if file.upload_status == "uploaded":
            try:
                download_url = storage_service.create_signed_download_url(
                    file.storage_bucket, file.storage_path, settings.SIGNED_URL_EXPIRES_IN_SECONDS
                )
            except storage_service.StorageNotConfiguredError:
                download_url = None

        return PublicLinkFileAccess(
            name=file.name, size_bytes=file.size_bytes, mime_type=file.mime_type, download_url=download_url
        )

    folder = db.query(Folder).filter(Folder.id == link.folder_id, Folder.is_trashed.is_(False)).first()
    if folder is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Folder not found or has been deleted.")

    # One level deep only - browsing into a subfolder via a public link
    # isn't wired up yet (would need per-subfolder access derived from the
    # same token). Documented as a known limitation.
    subfolders = db.query(Folder).filter(Folder.parent_id == folder.id, Folder.is_trashed.is_(False)).all()
    files = db.query(File).filter(File.folder_id == folder.id, File.is_trashed.is_(False)).all()
    entries = [PublicLinkFolderEntry(type="folder", id=f.id, name=f.name) for f in subfolders] + [
        PublicLinkFolderEntry(type="file", id=f.id, name=f.name) for f in files
    ]
    return PublicLinkFolderAccess(name=folder.name, entries=entries)
