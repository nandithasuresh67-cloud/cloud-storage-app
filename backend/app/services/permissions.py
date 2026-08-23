"""
Central permission logic. Every route that touches a file or folder should
go through require_file_access / require_folder_access instead of a raw
ownership filter, so "owner OR shared-with-sufficient-role" is enforced
consistently in one place.

Role model (ranked low -> high): VIEWER < EDITOR < OWNER.
- OWNER: the resource's owner_id. Full control.
- EDITOR: explicit share row with role=editor (or inherited - see below).
  Upload, rename, move, delete.
- VIEWER: explicit share row with role=viewer (or inherited). Read-only.

Sharing a FOLDER cascades down: being shared a folder (as viewer or
editor) grants that same role on every file/subfolder inside it, found by
walking up each item's parent_id chain looking for a share on any
ancestor. This matches how Drive-style sharing is expected to behave -
sharing a folder shouldn't require re-sharing everything inside it.
Sharing a FILE only grants access to that one file.
"""

import enum
import uuid
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.file import File
from app.models.folder import Folder
from app.models.share import Share, ShareRole


class Role(str, enum.Enum):
    VIEWER = "viewer"
    EDITOR = "editor"
    OWNER = "owner"


_RANK = {Role.VIEWER: 0, Role.EDITOR: 1, Role.OWNER: 2}


def _share_role_to_role(share_role: ShareRole) -> Role:
    return Role.EDITOR if share_role == ShareRole.EDITOR else Role.VIEWER


def get_folder_role(db: Session, folder: Folder, user_id: uuid.UUID) -> Optional[Role]:
    if folder.owner_id == user_id:
        return Role.OWNER

    share = db.query(Share).filter(Share.folder_id == folder.id, Share.shared_with_user_id == user_id).first()
    if share is not None:
        return _share_role_to_role(share.role)

    # Walk up ancestors looking for a share that cascades down to this folder.
    seen: set[uuid.UUID] = {folder.id}
    current = folder
    while current.parent_id is not None:
        if current.parent_id in seen:
            break  # defensive: don't loop forever on a corrupt cycle
        seen.add(current.parent_id)
        parent = db.query(Folder).filter(Folder.id == current.parent_id).first()
        if parent is None:
            break
        if parent.owner_id == user_id:
            return Role.OWNER
        share = db.query(Share).filter(Share.folder_id == parent.id, Share.shared_with_user_id == user_id).first()
        if share is not None:
            return _share_role_to_role(share.role)
        current = parent

    return None


def get_file_role(db: Session, file: File, user_id: uuid.UUID) -> Optional[Role]:
    if file.owner_id == user_id:
        return Role.OWNER

    share = db.query(Share).filter(Share.file_id == file.id, Share.shared_with_user_id == user_id).first()
    if share is not None:
        return _share_role_to_role(share.role)

    if file.folder_id is not None:
        folder = db.query(Folder).filter(Folder.id == file.folder_id).first()
        if folder is not None:
            return get_folder_role(db, folder, user_id)

    return None


def require_file_access(db: Session, file_id: uuid.UUID, user_id: uuid.UUID, min_role: Role) -> File:
    file = db.query(File).filter(File.id == file_id).first()
    if file is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    role = get_file_role(db, file, user_id)
    if role is None:
        # No access at all - 404 rather than 403 so we don't confirm the file exists.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    if _RANK[role] < _RANK[min_role]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"This action requires {min_role.value} access; you have {role.value} access.",
        )
    return file


def require_folder_access(db: Session, folder_id: uuid.UUID, user_id: uuid.UUID, min_role: Role) -> Folder:
    folder = db.query(Folder).filter(Folder.id == folder_id).first()
    if folder is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Folder not found")

    role = get_folder_role(db, folder, user_id)
    if role is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Folder not found")
    if _RANK[role] < _RANK[min_role]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"This action requires {min_role.value} access; you have {role.value} access.",
        )
    return folder
