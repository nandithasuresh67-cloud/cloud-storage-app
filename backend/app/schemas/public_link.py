import uuid
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, model_validator


class PublicLinkCreateRequest(BaseModel):
    file_id: Optional[uuid.UUID] = None
    folder_id: Optional[uuid.UUID] = None
    expires_in_hours: Optional[int] = Field(None, gt=0, le=24 * 365, description="Omit for a link that never expires.")
    password: Optional[str] = Field(None, min_length=4, max_length=255, description="Omit for no password.")

    @model_validator(mode="after")
    def exactly_one_target(self):
        if (self.file_id is None) == (self.folder_id is None):
            raise ValueError("Exactly one of file_id or folder_id must be set.")
        return self


class PublicLinkOut(BaseModel):
    id: uuid.UUID
    file_id: Optional[uuid.UUID]
    folder_id: Optional[uuid.UUID]
    token: str
    has_password: bool
    expires_at: Optional[datetime]
    created_at: datetime


class PublicLinkAccessRequest(BaseModel):
    password: Optional[str] = None


class PublicLinkFileAccess(BaseModel):
    type: Literal["file"] = "file"
    name: str
    size_bytes: int
    mime_type: Optional[str]
    download_url: Optional[str]


class PublicLinkFolderEntry(BaseModel):
    type: Literal["file", "folder"]
    id: uuid.UUID
    name: str


class PublicLinkFolderAccess(BaseModel):
    type: Literal["folder"] = "folder"
    name: str
    entries: list[PublicLinkFolderEntry]
