import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class TrashItem(BaseModel):
    type: Literal["file", "folder"]
    id: uuid.UUID
    name: str
    trashed_at: datetime | None
