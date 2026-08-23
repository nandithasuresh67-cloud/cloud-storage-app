import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user_id
from app.models.file import File
from app.models.folder import Folder
from app.models.share import Share, ShareRole
from app.models.user import User
from app.schemas.share import ShareCreateRequest, ShareOut, SharedWithMeItem
from app.services.permissions import Role, require_file_access, require_folder_access

router = APIRouter(prefix="/shares", tags=["shares"])


@router.post("", response_model=ShareOut, status_code=status.HTTP_201_CREATED)
def create_share(
    payload: ShareCreateRequest,
    db: Session = Depends(get_db),
    owner_id: uuid.UUID = Depends(get_current_user_id),
):
    """
    Share a file or folder with another user by email. Only the resource's
    OWNER can share it - an editor with cascading folder access can't
    re-share it to someone else. Sharing a folder cascades to everything
    inside it (see app/services/permissions.py).
    """
    if payload.file_id is not None:
        require_file_access(db, payload.file_id, owner_id, Role.OWNER)
    else:
        require_folder_access(db, payload.folder_id, owner_id, Role.OWNER)

    target_user = db.query(User).filter(User.email == payload.email).first()
    if target_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No user found with that email.")
    if target_user.id == owner_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You already own this resource.")

    role = ShareRole.EDITOR if payload.role == "editor" else ShareRole.VIEWER

    # Upsert: sharing again with the same person just updates their role,
    # rather than creating a duplicate share row.
    existing = (
        db.query(Share)
        .filter(
            Share.file_id == payload.file_id,
            Share.folder_id == payload.folder_id,
            Share.shared_with_user_id == target_user.id,
        )
        .first()
    )
    if existing is not None:
        existing.role = role
        share = existing
    else:
        share = Share(
            file_id=payload.file_id,
            folder_id=payload.folder_id,
            shared_with_user_id=target_user.id,
            shared_by_user_id=owner_id,
            role=role,
        )
        db.add(share)

    db.commit()
    db.refresh(share)
    return ShareOut(
        id=share.id,
        file_id=share.file_id,
        folder_id=share.folder_id,
        shared_with_user_id=share.shared_with_user_id,
        shared_with_email=target_user.email,
        shared_by_user_id=share.shared_by_user_id,
        role=share.role.value,
        created_at=share.created_at,
    )


@router.get("", response_model=list[ShareOut])
def list_shares(
    file_id: Optional[uuid.UUID] = Query(None),
    folder_id: Optional[uuid.UUID] = Query(None),
    db: Session = Depends(get_db),
    owner_id: uuid.UUID = Depends(get_current_user_id),
):
    """Lists everyone a file/folder is shared with. Owner-only - this is 'manage access', not something editors see."""
    if (file_id is None) == (folder_id is None):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Provide exactly one of file_id or folder_id.")

    if file_id is not None:
        require_file_access(db, file_id, owner_id, Role.OWNER)
    else:
        require_folder_access(db, folder_id, owner_id, Role.OWNER)

    shares = db.query(Share).filter(Share.file_id == file_id, Share.folder_id == folder_id).all()
    out = []
    for share in shares:
        user = db.query(User).filter(User.id == share.shared_with_user_id).first()
        out.append(
            ShareOut(
                id=share.id,
                file_id=share.file_id,
                folder_id=share.folder_id,
                shared_with_user_id=share.shared_with_user_id,
                shared_with_email=user.email if user else "",
                shared_by_user_id=share.shared_by_user_id,
                role=share.role.value,
                created_at=share.created_at,
            )
        )
    return out


@router.delete("/{share_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_share(
    share_id: uuid.UUID,
    db: Session = Depends(get_db),
    owner_id: uuid.UUID = Depends(get_current_user_id),
):
    share = db.query(Share).filter(Share.id == share_id).first()
    if share is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Share not found")

    # Only the resource owner can revoke - re-check ownership fresh rather
    # than trusting share.shared_by_user_id (ownership could have changed).
    if share.file_id is not None:
        require_file_access(db, share.file_id, owner_id, Role.OWNER)
    else:
        require_folder_access(db, share.folder_id, owner_id, Role.OWNER)

    db.delete(share)
    db.commit()
    return None


@router.get("/shared-with-me", response_model=list[SharedWithMeItem])
def shared_with_me(
    db: Session = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """
    Top-level items directly shared with the current user - not a
    recursive listing of everything inside shared folders. Once a user
    opens a shared folder, GET /folders/contents handles the rest via
    cascading permission checks.
    """
    shares = db.query(Share).filter(Share.shared_with_user_id == user_id).all()
    items: list[SharedWithMeItem] = []
    for share in shares:
        if share.file_id is not None:
            file = db.query(File).filter(File.id == share.file_id, File.is_trashed.is_(False)).first()
            if file is not None:
                items.append(
                    SharedWithMeItem(
                        share_id=share.id,
                        type="file",
                        id=file.id,
                        name=file.name,
                        role=share.role.value,
                        shared_by_user_id=share.shared_by_user_id,
                        created_at=share.created_at,
                    )
                )
        else:
            folder = db.query(Folder).filter(Folder.id == share.folder_id, Folder.is_trashed.is_(False)).first()
            if folder is not None:
                items.append(
                    SharedWithMeItem(
                        share_id=share.id,
                        type="folder",
                        id=folder.id,
                        name=folder.name,
                        role=share.role.value,
                        shared_by_user_id=share.shared_by_user_id,
                        created_at=share.created_at,
                    )
                )
    return items
