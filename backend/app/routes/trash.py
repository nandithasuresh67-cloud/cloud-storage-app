import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session, aliased

from app.core.database import get_db
from app.core.deps import get_current_user_id
from app.models.file import File
from app.models.folder import Folder
from app.schemas.trash import TrashItem
from app.services import trash_service
from app.services.permissions import Role, require_file_access, require_folder_access

router = APIRouter(prefix="/trash", tags=["trash"])


@router.get("", response_model=list[TrashItem])
def list_trash(
    db: Session = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """
    Lists only the *roots* of trashed items - i.e. things you explicitly
    trashed, not their cascaded children. A trashed folder's contents went
    to trash with it (see trash_service), but showing every nested file as
    its own trash entry would be noisy and duplicate the folder entry
    that already represents them. An item counts as a root if its parent
    is either missing or itself not trashed.
    """
    ParentFolder = aliased(Folder)

    folders = (
        db.query(Folder)
        .outerjoin(ParentFolder, Folder.parent_id == ParentFolder.id)
        .filter(
            Folder.owner_id == user_id,
            Folder.is_trashed.is_(True),
            or_(Folder.parent_id.is_(None), ParentFolder.is_trashed.is_(False)),
        )
        .all()
    )
    files = (
        db.query(File)
        .outerjoin(Folder, File.folder_id == Folder.id)
        .filter(
            File.owner_id == user_id,
            File.is_trashed.is_(True),
            or_(File.folder_id.is_(None), Folder.is_trashed.is_(False)),
        )
        .all()
    )

    items = [TrashItem(type="folder", id=f.id, name=f.name, trashed_at=f.trashed_at) for f in folders]
    items += [TrashItem(type="file", id=f.id, name=f.name, trashed_at=f.trashed_at) for f in files]
    items.sort(key=lambda i: i.trashed_at or datetime.min, reverse=True)
    return items


@router.post("/folders/{folder_id}/restore", status_code=status.HTTP_204_NO_CONTENT)
def restore_folder(
    folder_id: uuid.UUID,
    db: Session = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Owner-only - restoring is a trash-management action, not something an editor share grants."""
    folder = require_folder_access(db, folder_id, user_id, Role.OWNER)
    if not folder.is_trashed:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This folder is not in the trash.")
    trash_service.restore_folder_cascade(db, folder)
    return None


@router.post("/files/{file_id}/restore", status_code=status.HTTP_204_NO_CONTENT)
def restore_file(
    file_id: uuid.UUID,
    db: Session = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    file = require_file_access(db, file_id, user_id, Role.OWNER)
    if not file.is_trashed:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This file is not in the trash.")
    file.is_trashed = False
    file.trashed_at = None
    db.commit()
    return None


@router.delete("/folders/{folder_id}", status_code=status.HTTP_204_NO_CONTENT)
def permanently_delete_folder(
    folder_id: uuid.UUID,
    db: Session = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Requires the folder to already be trashed - permanent delete is a second, deliberate step, not a shortcut around trash."""
    folder = require_folder_access(db, folder_id, user_id, Role.OWNER)
    if not folder.is_trashed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Move this folder to the trash before permanently deleting it.",
        )
    trash_service.permanently_delete_folder_cascade(db, folder)
    return None


@router.delete("/files/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
def permanently_delete_file(
    file_id: uuid.UUID,
    db: Session = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    file = require_file_access(db, file_id, user_id, Role.OWNER)
    if not file.is_trashed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Move this file to the trash before permanently deleting it.",
        )
    trash_service.permanently_delete_file(db, file)
    return None
