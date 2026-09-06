import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from app.schemas.file import FileOut


class FolderCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    parent_id: Optional[uuid.UUID] = None

    @field_validator("name")
    @classmethod
    def no_path_separators(cls, v: str) -> str:
        if "/" in v or "\\" in v or v in (".", ".."):
            raise ValueError("name must not contain path separators")
        return v


class FolderUpdateRequest(BaseModel):
    """
    Partial update for rename and/or move. Only fields the client actually
    sent are applied - the route checks `model_fields_set` so that e.g.
    `{"parent_id": null}` (explicit "move to root") is distinguishable from
    the client simply not mentioning parent_id at all.
    """

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    parent_id: Optional[uuid.UUID] = None

    @field_validator("name")
    @classmethod
    def no_path_separators(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if "/" in v or "\\" in v or v in (".", ".."):
            raise ValueError("name must not contain path separators")
        return v


class FolderOut(BaseModel):
    id: uuid.UUID
    name: str
    owner_id: uuid.UUID
    parent_id: Optional[uuid.UUID]
    is_trashed: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BreadcrumbItem(BaseModel):
    id: uuid.UUID
    name: str


class FolderContents(BaseModel):
    folder: Optional[FolderOut]  # None when listing the root
    breadcrumb: List[BreadcrumbItem]
    subfolders: List[FolderOut]
    files: List[FileOut]
    # Counts BEFORE the limit/offset slice was applied, so the frontend
    # can compute "is there more to load" without a second request.
    subfolders_total: int
    files_total: int
