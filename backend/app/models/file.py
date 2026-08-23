import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class File(Base):
    __tablename__ = "files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    folder_id = Column(UUID(as_uuid=True), ForeignKey("folders.id", ondelete="SET NULL"), nullable=True, index=True)

    # Object storage pointer (Supabase Storage bucket + object path)
    storage_bucket = Column(String, nullable=False)
    storage_path = Column(String, nullable=False, unique=True)

    mime_type = Column(String, nullable=True)
    size_bytes = Column(BigInteger, nullable=False, default=0)

    is_starred = Column(Boolean, default=False, nullable=False)
    is_trashed = Column(Boolean, default=False, nullable=False)
    trashed_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
