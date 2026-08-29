"""
Cascading trash operations for folders.

Trashing/restoring/permanently-deleting a folder recurses into every
subfolder and file underneath it - without this, trashing a folder would
only hide the folder itself while its contents stayed live and fully
listable by direct id, which isn't what "delete this folder" means to a
user.

Known limitation: restoring a folder restores ALL of its descendants,
even ones that were individually trashed before the folder itself was.
Getting that exactly right would mean tracking each item's own trash
"batch" separately, which is more bookkeeping than a Day 6 MVP needs -
noted here and in the README rather than silently doing the wrong thing.
"""

import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.file import File
from app.models.folder import Folder
from app.services import storage_service


def _descendant_folder_ids(db: Session, root_id: uuid.UUID) -> list[uuid.UUID]:
    """BFS over parent_id to find every folder nested under root_id (not including root_id itself)."""
    ids: list[uuid.UUID] = []
    frontier = [root_id]
    seen = {root_id}
    while frontier:
        children = db.query(Folder.id).filter(Folder.parent_id.in_(frontier)).all()
        frontier = [c.id for c in children if c.id not in seen]
        for c_id in frontier:
            seen.add(c_id)
            ids.append(c_id)
    return ids


def trash_folder_cascade(db: Session, folder: Folder) -> None:
    now = datetime.utcnow()
    folder_ids = [folder.id] + _descendant_folder_ids(db, folder.id)

    db.query(Folder).filter(Folder.id.in_(folder_ids), Folder.is_trashed.is_(False)).update(
        {"is_trashed": True, "trashed_at": now}, synchronize_session=False
    )
    db.query(File).filter(File.folder_id.in_(folder_ids), File.is_trashed.is_(False)).update(
        {"is_trashed": True, "trashed_at": now}, synchronize_session=False
    )
    db.commit()


def restore_folder_cascade(db: Session, folder: Folder) -> None:
    folder_ids = [folder.id] + _descendant_folder_ids(db, folder.id)

    db.query(Folder).filter(Folder.id.in_(folder_ids)).update(
        {"is_trashed": False, "trashed_at": None}, synchronize_session=False
    )
    db.query(File).filter(File.folder_id.in_(folder_ids)).update(
        {"is_trashed": False, "trashed_at": None}, synchronize_session=False
    )
    db.commit()


def permanently_delete_folder_cascade(db: Session, folder: Folder) -> None:
    """Deletes the folder, every descendant folder, every file inside any of them, and their storage objects."""
    folder_ids = [folder.id] + _descendant_folder_ids(db, folder.id)

    files = db.query(File).filter(File.folder_id.in_(folder_ids)).all()
    for file in files:
        try:
            storage_service.remove_object(file.storage_bucket, file.storage_path)
        except storage_service.StorageNotConfiguredError:
            pass  # DB row is still removed below; storage cleanup can't happen without credentials
        db.delete(file)

    # Delete child folders before parents to keep the FK chain tidy, though
    # ondelete=CASCADE on folders.parent_id would handle it either way.
    for folder_id in reversed(folder_ids):
        row = db.query(Folder).filter(Folder.id == folder_id).first()
        if row is not None:
            db.delete(row)

    db.commit()


def permanently_delete_file(db: Session, file: File) -> None:
    try:
        storage_service.remove_object(file.storage_bucket, file.storage_path)
    except storage_service.StorageNotConfiguredError:
        pass
    db.delete(file)
    db.commit()
