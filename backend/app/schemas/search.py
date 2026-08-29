import uuid
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel


class SearchResultItem(BaseModel):
    type: Literal["file", "folder"]
    id: uuid.UUID
    name: str
    mime_type: Optional[str] = None
    size_bytes: Optional[int] = None
    parent_id: Optional[uuid.UUID] = None  # folder_id for files, parent_id for folders
    updated_at: datetime
