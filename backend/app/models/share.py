import enum
import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, Column, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class ShareRole(str, enum.Enum):
    VIEWER = "viewer"
    EDITOR = "editor"


class Share(Base):
    __tablename__ = "shares"
    __table_args__ = (
        CheckConstraint(
            "(file_id IS NOT NULL AND folder_id IS NULL) OR (file_id IS NULL AND folder_id IS NOT NULL)",
            name="share_target_exactly_one",
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    file_id = Column(UUID(as_uuid=True), ForeignKey("files.id", ondelete="CASCADE"), nullable=True, index=True)
    folder_id = Column(UUID(as_uuid=True), ForeignKey("folders.id", ondelete="CASCADE"), nullable=True, index=True)
    shared_with_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    shared_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(Enum(ShareRole), nullable=False, default=ShareRole.VIEWER)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
