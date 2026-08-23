import uuid

from sqlalchemy.orm import Session

from app.models.folder import Folder
from app.schemas.folder import BreadcrumbItem


def get_breadcrumb(db: Session, folder: Folder | None) -> list[BreadcrumbItem]:
    """Walks parent_id up to the root, returning root-first order."""
    crumbs: list[BreadcrumbItem] = []
    current = folder
    seen: set[uuid.UUID] = set()
    while current is not None:
        if current.id in seen:
            break  # defensive: a corrupt/cyclic chain shouldn't hang the request
        seen.add(current.id)
        crumbs.append(BreadcrumbItem(id=current.id, name=current.name))
        current = db.query(Folder).filter(Folder.id == current.parent_id).first() if current.parent_id else None
    crumbs.reverse()
    return crumbs


def is_descendant(db: Session, candidate_id: uuid.UUID, ancestor_id: uuid.UUID) -> bool:
    """
    True if `candidate_id` is `ancestor_id` itself or lives somewhere under
    it. Used to block moving a folder into its own subtree, which would
    otherwise create a cycle in parent_id and break breadcrumb/listing
    logic forever.
    """
    current_id: uuid.UUID | None = candidate_id
    seen: set[uuid.UUID] = set()
    while current_id is not None:
        if current_id == ancestor_id:
            return True
        if current_id in seen:
            break
        seen.add(current_id)
        folder = db.query(Folder).filter(Folder.id == current_id).first()
        current_id = folder.parent_id if folder else None
    return False
