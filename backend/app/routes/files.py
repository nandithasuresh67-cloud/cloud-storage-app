import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.deps import get_current_user_id
from app.models.file import File
from app.models.folder import Folder
from app.schemas.file import (
    FileCompleteUploadRequest,
    FileInitUploadRequest,
    FileInitUploadResponse,
    FileOut,
    FileOutWithDownloadUrl,
    FileUpdateRequest,
)
from app.services import storage_service

router = APIRouter(prefix="/files", tags=["files"])
settings = get_settings()


def _get_owned_file_or_404(db: Session, file_id: uuid.UUID, owner_id: uuid.UUID) -> File:
    file = db.query(File).filter(File.id == file_id, File.owner_id == owner_id).first()
    if file is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    return file


@router.post("/init-upload", response_model=FileInitUploadResponse, status_code=status.HTTP_201_CREATED)
def init_upload(
    payload: FileInitUploadRequest,
    db: Session = Depends(get_db),
    owner_id: uuid.UUID = Depends(get_current_user_id),
):
    """
    Step 1 of the upload flow: validate, create the metadata row (status
    "pending"), and hand back a signed URL the client uploads bytes to
    directly. Nothing here touches the file's actual bytes.
    """
    # --- Size validation ---
    if payload.size_bytes > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds the {settings.MAX_UPLOAD_SIZE_MB}MB upload limit.",
        )

    # --- Type validation ---
    if payload.mime_type in settings.BLOCKED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"File type '{payload.mime_type}' is not allowed.",
        )

    # --- Folder ownership check (if uploading into a folder) ---
    if payload.folder_id is not None:
        folder = (
            db.query(Folder)
            .filter(Folder.id == payload.folder_id, Folder.owner_id == owner_id, Folder.is_trashed.is_(False))
            .first()
        )
        if folder is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Folder not found")

    storage_path = f"{owner_id}/{uuid.uuid4()}/{payload.filename}"

    file = File(
        name=payload.filename,
        owner_id=owner_id,
        folder_id=payload.folder_id,
        storage_bucket=settings.SUPABASE_STORAGE_BUCKET,
        storage_path=storage_path,
        mime_type=payload.mime_type,
        size_bytes=payload.size_bytes,
        upload_status="pending",
    )
    db.add(file)
    db.commit()
    db.refresh(file)

    try:
        signed = storage_service.create_signed_upload_url(settings.SUPABASE_STORAGE_BUCKET, storage_path)
    except storage_service.StorageNotConfiguredError as exc:
        # Metadata row is already created (harmless - stays "pending"
        # forever if the client never retries), but surface a clear error
        # instead of a raw 500 so it's obvious Supabase creds are missing.
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    return FileInitUploadResponse(
        file_id=file.id,
        storage_bucket=file.storage_bucket,
        storage_path=file.storage_path,
        upload_url=signed["signed_url"],
        upload_token=signed["token"],
    )


@router.post("/{file_id}/complete-upload", response_model=FileOut)
def complete_upload(
    file_id: uuid.UUID,
    _payload: FileCompleteUploadRequest = FileCompleteUploadRequest(),
    db: Session = Depends(get_db),
    owner_id: uuid.UUID = Depends(get_current_user_id),
):
    """
    Step 2: client has PUT the bytes to the signed URL from init-upload and
    calls this to confirm. We verify the object actually exists in storage
    before flipping status to "uploaded" - a client calling this without
    ever uploading shouldn't be able to fake a completed file.
    """
    file = _get_owned_file_or_404(db, file_id, owner_id)

    if file.upload_status == "uploaded":
        return file  # idempotent - calling twice isn't an error

    try:
        exists = storage_service.object_exists(file.storage_bucket, file.storage_path)
    except storage_service.StorageNotConfiguredError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    if not exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No object found at the expected storage path - upload the file to upload_url before completing.",
        )

    file.upload_status = "uploaded"
    db.commit()
    db.refresh(file)
    return file


@router.get("/{file_id}", response_model=FileOutWithDownloadUrl)
def get_file(
    file_id: uuid.UUID,
    db: Session = Depends(get_db),
    owner_id: uuid.UUID = Depends(get_current_user_id),
):
    file = _get_owned_file_or_404(db, file_id, owner_id)

    download_url = None
    if file.upload_status == "uploaded":
        try:
            download_url = storage_service.create_signed_download_url(
                file.storage_bucket, file.storage_path, settings.SIGNED_URL_EXPIRES_IN_SECONDS
            )
        except storage_service.StorageNotConfiguredError:
            download_url = None  # metadata is still viewable even if storage isn't configured

    return FileOutWithDownloadUrl(**FileOut.model_validate(file).model_dump(), download_url=download_url)


@router.patch("/{file_id}", response_model=FileOut)
def update_file(
    file_id: uuid.UUID,
    payload: FileUpdateRequest,
    db: Session = Depends(get_db),
    owner_id: uuid.UUID = Depends(get_current_user_id),
):
    """Rename and/or move a file. Does not touch the object in storage - only metadata."""
    file = _get_owned_file_or_404(db, file_id, owner_id)
    fields_set = payload.model_fields_set

    if "name" in fields_set and payload.name is not None:
        file.name = payload.name

    if "folder_id" in fields_set:
        new_folder_id = payload.folder_id
        if new_folder_id is not None:
            folder = (
                db.query(Folder)
                .filter(Folder.id == new_folder_id, Folder.owner_id == owner_id, Folder.is_trashed.is_(False))
                .first()
            )
            if folder is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Folder not found")
        file.folder_id = new_folder_id

    db.commit()
    db.refresh(file)
    return file


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_file(
    file_id: uuid.UUID,
    db: Session = Depends(get_db),
    owner_id: uuid.UUID = Depends(get_current_user_id),
):
    """
    Soft delete - flips is_trashed, leaves the object in storage untouched.
    Permanent deletion (and restore) is a Day 6 (Trash & Restore) feature.
    """
    file = _get_owned_file_or_404(db, file_id, owner_id)
    if not file.is_trashed:
        file.is_trashed = True
        file.trashed_at = datetime.utcnow()
        db.commit()
    return None
