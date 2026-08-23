import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user_id
from app.models.file import File
from app.models.folder import Folder
from app.schemas.folder import FolderContents, FolderCreateRequest, FolderOut, FolderUpdateRequest
from app.services import folder_service

router = APIRouter(prefix="/folders", tags=["folders"])


def _get_owned_folder_or_404(db: Session, folder_id: uuid.UUID, owner_id: uuid.UUID) -> Folder:
    folder = db.query(Folder).filter(Folder.id == folder_id, Folder.owner_id == owner_id).first()
    if folder is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Folder not found")
    return folder


@router.post("", response_model=FolderOut, status_code=status.HTTP_201_CREATED)
def create_folder(
    payload: FolderCreateRequest,
    db: Session = Depends(get_db),
    owner_id: uuid.UUID = Depends(get_current_user_id),
):
    if payload.parent_id is not None:
        # 404 rather than a generic 400 - from the caller's point of view a
        # parent they don't own is indistinguishable from one that doesn't exist.
        _get_owned_folder_or_404(db, payload.parent_id, owner_id)

    folder = Folder(name=payload.name, owner_id=owner_id, parent_id=payload.parent_id)
    db.add(folder)
    db.commit()
    db.refresh(folder)
    return folder


@router.get("/contents", response_model=FolderContents)
def list_contents(
    folder_id: Optional[uuid.UUID] = Query(None, description="Omit to list the root"),
    db: Session = Depends(get_db),
    owner_id: uuid.UUID = Depends(get_current_user_id),
):
    """
    Lists the subfolders and files directly inside `folder_id` (or the
    root, if omitted), plus the breadcrumb path to get there. This is what
    the frontend's file browser calls when navigating.
    """
    folder = None
    if folder_id is not None:
        folder = _get_owned_folder_or_404(db, folder_id, owner_id)

    subfolders = (
        db.query(Folder)
        .filter(Folder.owner_id == owner_id, Folder.parent_id == folder_id, Folder.is_trashed.is_(False))
        .order_by(Folder.name)
        .all()
    )
    files = (
        db.query(File)
        .filter(File.owner_id == owner_id, File.folder_id == folder_id, File.is_trashed.is_(False))
        .order_by(File.name)
        .all()
    )

    return FolderContents(
        folder=folder,
        breadcrumb=folder_service.get_breadcrumb(db, folder),
        subfolders=subfolders,
        files=files,
    )


@router.get("/{folder_id}", response_model=FolderOut)
def get_folder(
    folder_id: uuid.UUID,
    db: Session = Depends(get_db),
    owner_id: uuid.UUID = Depends(get_current_user_id),
):
    return _get_owned_folder_or_404(db, folder_id, owner_id)


@router.patch("/{folder_id}", response_model=FolderOut)
def update_folder(
    folder_id: uuid.UUID,
    payload: FolderUpdateRequest,
    db: Session = Depends(get_db),
    owner_id: uuid.UUID = Depends(get_current_user_id),
):
    folder = _get_owned_folder_or_404(db, folder_id, owner_id)
    fields_set = payload.model_fields_set

    if "name" in fields_set and payload.name is not None:
        folder.name = payload.name

    if "parent_id" in fields_set:
        new_parent_id = payload.parent_id
        if new_parent_id is not None:
            if new_parent_id == folder.id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A folder cannot be its own parent.")
            _get_owned_folder_or_404(db, new_parent_id, owner_id)
            if folder_service.is_descendant(db, new_parent_id, folder.id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot move a folder into one of its own subfolders.",
                )
        folder.parent_id = new_parent_id

    db.commit()
    db.refresh(folder)
    return folder


@router.delete("/{folder_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_folder(
    folder_id: uuid.UUID,
    db: Session = Depends(get_db),
    owner_id: uuid.UUID = Depends(get_current_user_id),
):
    """
    Soft delete only - flips is_trashed on this folder. Does NOT cascade to
    child files/folders yet; recursive trash/restore semantics are a Day 6
    (Trash & Restore) feature. For now a trashed folder's children remain
    is_trashed=False and would still show up if fetched directly by id.
    """
    folder = _get_owned_folder_or_404(db, folder_id, owner_id)
    if not folder.is_trashed:
        folder.is_trashed = True
        folder.trashed_at = datetime.utcnow()
        db.commit()
    return None
