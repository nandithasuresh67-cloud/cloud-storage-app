import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, Column, DateTime, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class File(Base):
    __tablename__ = "files"
    __table_args__ = (
        # Covers the most common query shape: "this user's files in this
        # folder (or root), excluding trash" - used by folder-contents
        # listing on every navigation.
        Index("ix_files_owner_folder_trashed", "owner_id", "folder_id", "is_trashed"),
        # Covers trash listing and the "your files" search scope.
        Index("ix_files_owner_trashed", "owner_id", "is_trashed"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    folder_id = Column(UUID(as_uuid=True), ForeignKey("folders.id", ondelete="SET NULL"), nullable=True, index=True)

    # Object storage pointer (Supabase Storage bucket + object path)
    storage_bucket = Column(String, nullable=False)
    storage_path = Column(String, nullable=False, unique=True)

    mime_type = Column(String, nullable=True, index=True)
    size_bytes = Column(BigInteger, nullable=False, default=0)

    # "pending" once init-upload creates the metadata row and hands out a
    # signed upload URL; "uploaded" once complete-upload confirms the bytes
    # landed in storage. Files stuck in "pending" are safe to garbage-collect.
    upload_status = Column(String, nullable=False, default="pending")

    is_starred = Column(Boolean, default=False, nullable=False)
    is_trashed = Column(Boolean, default=False, nullable=False)
    trashed_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


# Case-insensitive name search (ILIKE-equivalent) without a full table
# scan - defined after the class so it can reference the real column
# object. Postgres and SQLite (3.9+) both support expression indexes.
Index("ix_files_name_lower", func.lower(File.name))
