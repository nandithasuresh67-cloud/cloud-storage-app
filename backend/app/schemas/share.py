import uuid
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, model_validator


class ShareCreateRequest(BaseModel):
    file_id: Optional[uuid.UUID] = None
    folder_id: Optional[uuid.UUID] = None
    email: EmailStr  # the user to share with, looked up by email
    role: Literal["viewer", "editor"] = "viewer"

    @model_validator(mode="after")
    def exactly_one_target(self):
        if (self.file_id is None) == (self.folder_id is None):
            raise ValueError("Exactly one of file_id or folder_id must be set.")
        return self


class ShareOut(BaseModel):
    id: uuid.UUID
    file_id: Optional[uuid.UUID]
    folder_id: Optional[uuid.UUID]
    shared_with_user_id: uuid.UUID
    shared_with_email: str
    shared_by_user_id: uuid.UUID
    role: str
    created_at: datetime

    model_config = {"from_attributes": True}


class SharedWithMeItem(BaseModel):
    share_id: uuid.UUID
    type: Literal["file", "folder"]
    id: uuid.UUID
    name: str
    role: str
    shared_by_user_id: uuid.UUID
    created_at: datetime
