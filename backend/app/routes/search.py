import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user_id
from app.models.file import File
from app.models.folder import Folder
from app.models.share import Share
from app.schemas.search import SearchResultItem

router = APIRouter(tags=["search"])


@router.get("/search", response_model=list[SearchResultItem])
def search(
    q: str = Query(..., min_length=1, max_length=255, description="Name-based search, case-insensitive substring match"),
    item_type: Optional[str] = Query(None, pattern="^(file|folder)$", description="Restrict to 'file' or 'folder'"),
    mime_type: Optional[str] = Query(None, description="Type-based filter, prefix match against mime type, e.g. 'image/' or 'application/pdf'. Only applies to files."),
    db: Session = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """
    Searches items you own plus items directly shared with you (name match,
    optionally narrowed by type). This does NOT recurse into the contents
    of folders that were shared with you via cascading folder access -
    only your own items and things with a direct Share row show up here.
    Once you open a shared folder's contents (GET /folders/contents),
    cascading permission checks take over as usual; extending search to
    cover that would mean walking every shared folder's subtree on every
    keystroke, which isn't worth the cost for a Day 6 MVP.
    """
    pattern = f"%{q.lower()}%"
    shared_folder_ids = [
        row.folder_id
        for row in db.query(Share.folder_id).filter(Share.shared_with_user_id == user_id, Share.folder_id.isnot(None)).all()
    ]
    shared_file_ids = [
        row.file_id
        for row in db.query(Share.file_id).filter(Share.shared_with_user_id == user_id, Share.file_id.isnot(None)).all()
    ]

    results: list[SearchResultItem] = []

    if item_type in (None, "folder"):
        folder_scope = or_(Folder.owner_id == user_id, Folder.id.in_(shared_folder_ids))
        folders = (
            db.query(Folder)
            .filter(folder_scope, Folder.is_trashed.is_(False), func.lower(Folder.name).like(pattern))
            .order_by(Folder.name)
            .all()
        )
        results += [
            SearchResultItem(type="folder", id=f.id, name=f.name, parent_id=f.parent_id, updated_at=f.updated_at)
            for f in folders
        ]

    if item_type in (None, "file"):
        file_scope = or_(File.owner_id == user_id, File.id.in_(shared_file_ids))
        query = db.query(File).filter(file_scope, File.is_trashed.is_(False), func.lower(File.name).like(pattern))
        if mime_type:
            query = query.filter(File.mime_type.like(f"{mime_type}%"))
        files = query.order_by(File.name).all()
        results += [
            SearchResultItem(
                type="file",
                id=f.id,
                name=f.name,
                mime_type=f.mime_type,
                size_bytes=f.size_bytes,
                parent_id=f.folder_id,
                updated_at=f.updated_at,
            )
            for f in files
        ]

    return results
