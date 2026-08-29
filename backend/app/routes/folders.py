import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user_id
from app.models.file import File
from app.models.folder import Folder
from app.schemas.folder import FolderContents, FolderCreateRequest, FolderOut, FolderUpdateRequest
from app.services import folder_service, trash_service
from app.services.permissions import Role, require_folder_access

router = APIRouter(prefix="/folders", tags=["folders"])


@router.post("", response_model=FolderOut, status_code=status.HTTP_201_CREATED)
def create_folder(
    payload: FolderCreateRequest,
    db: Session = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    if payload.parent_id is not None:
        # Creating inside a shared folder requires EDITOR+ on that folder.
        require_folder_access(db, payload.parent_id, user_id, Role.EDITOR)

    folder = Folder(name=payload.name, owner_id=user_id, parent_id=payload.parent_id)
    db.add(folder)
    db.commit()
    db.refresh(folder)
    return folder


@router.get("/contents", response_model=FolderContents)
def list_contents(
    folder_id: Optional[uuid.UUID] = Query(None, description="Omit to list your own root"),
    db: Session = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """
    Lists the subfolders and files directly inside `folder_id` (or your
    own root, if omitted), plus the breadcrumb path to get there. Requires
    VIEWER+ access - works for folders shared with you too, not just ones
    you own. (The root itself isn't shareable as a whole - it's always
    your own root when folder_id is omitted.)
    """
    folder = None
    if folder_id is not None:
        folder = require_folder_access(db, folder_id, user_id, Role.VIEWER)
        owner_id_for_listing = folder.owner_id
    else:
        owner_id_for_listing = user_id

    subfolders = (
        db.query(Folder)
        .filter(Folder.owner_id == owner_id_for_listing, Folder.parent_id == folder_id, Folder.is_trashed.is_(False))
        .order_by(Folder.name)
        .all()
    )
    files = (
        db.query(File)
        .filter(File.owner_id == owner_id_for_listing, File.folder_id == folder_id, File.is_trashed.is_(False))
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
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    return require_folder_access(db, folder_id, user_id, Role.VIEWER)


@router.patch("/{folder_id}", response_model=FolderOut)
def update_folder(
    folder_id: uuid.UUID,
    payload: FolderUpdateRequest,
    db: Session = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    folder = require_folder_access(db, folder_id, user_id, Role.EDITOR)
    fields_set = payload.model_fields_set

    if "name" in fields_set and payload.name is not None:
        folder.name = payload.name

    if "parent_id" in fields_set:
        new_parent_id = payload.parent_id
        if new_parent_id is not None:
            if new_parent_id == folder.id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A folder cannot be its own parent.")
            require_folder_access(db, new_parent_id, user_id, Role.EDITOR)
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
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """
    Soft delete, cascading to every subfolder and file underneath. Requires
    EDITOR+ access. See app/services/trash_service.py for the cascade
    logic and its restore-ordering limitation. Permanent deletion lives
    under /trash.
    """
    folder = require_folder_access(db, folder_id, user_id, Role.EDITOR)
    if not folder.is_trashed:
        trash_service.trash_folder_cascade(db, folder)
    return None
