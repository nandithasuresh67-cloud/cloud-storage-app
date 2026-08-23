import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class FileInitUploadRequest(BaseModel):
    filename: str = Field(..., min_length=1, max_length=255)
    mime_type: str = Field(..., min_length=1, max_length=255)
    size_bytes: int = Field(..., gt=0)
    folder_id: Optional[uuid.UUID] = None

    @field_validator("filename")
    @classmethod
    def no_path_separators(cls, v: str) -> str:
        # Filenames become part of the storage path - reject anything that
        # could be used to escape the intended object path.
        if "/" in v or "\\" in v or v in (".", ".."):
            raise ValueError("filename must not contain path separators")
        return v


class FileInitUploadResponse(BaseModel):
    file_id: uuid.UUID
    storage_bucket: str
    storage_path: str
    upload_url: str
    upload_token: str


class FileCompleteUploadRequest(BaseModel):
    # Nothing required today - the file id comes from the URL path. Kept as
    # a real request body (rather than an empty POST) so a future client
    # checksum or client-reported size can be added here without breaking
    # the endpoint shape.
    pass


class FileOut(BaseModel):
    id: uuid.UUID
    name: str
    owner_id: uuid.UUID
    folder_id: Optional[uuid.UUID]
    mime_type: Optional[str]
    size_bytes: int
    upload_status: str
    is_starred: bool
    is_trashed: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class FileOutWithDownloadUrl(FileOut):
    download_url: Optional[str] = None
