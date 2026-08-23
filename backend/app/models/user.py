import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Column, DateTime, String, Boolean
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False, index=True)
    full_name = Column(String, nullable=True)
    password_hash = Column(String, nullable=True)  # null for OAuth-only users
    oauth_provider = Column(String, nullable=True)  # e.g. "google"
    oauth_sub = Column(String, nullable=True)  # provider's user id
    avatar_url = Column(String, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    storage_quota_bytes = Column(BigInteger, default=15 * 1024 * 1024 * 1024, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
