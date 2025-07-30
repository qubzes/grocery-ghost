import enum
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Index,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column
from database import Base


class SessionStatus(enum.Enum):
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


class ScrapeSession(Base):
    __tablename__ = "sessions"
    
    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid4())
    )
    url: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str | None] = mapped_column(String)
    total_pages: Mapped[int] = mapped_column(Integer, default=0)
    scraped_pages: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[SessionStatus] = mapped_column(
        Enum(SessionStatus), nullable=False, default=SessionStatus.QUEUED, index=True
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), index=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)
    error: Mapped[str | None] = mapped_column(Text)  # Use Text for longer error messages

    # Performance indexes
    __table_args__ = (
        Index('idx_sessions_started_at_desc', started_at.desc()),
        Index('idx_sessions_status', status),
    )


class Product(Base):
    __tablename__ = "products"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid4())
    )
    session_id: Mapped[str] = mapped_column(
        String, ForeignKey("sessions.id"), nullable=False, index=True
    )
    url: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str | None] = mapped_column(String, index=True)  # Index for search
    current_price: Mapped[str | None] = mapped_column(String)
    original_price: Mapped[str | None] = mapped_column(String)
    unit_size: Mapped[str | None] = mapped_column(String)
    image_url: Mapped[str | None] = mapped_column(Text)  # URLs can be long
    category: Mapped[str | None] = mapped_column(String, index=True)  # Index for filtering
    dietary_tags: Mapped[str | None] = mapped_column(String)

    # Performance indexes for common queries
    __table_args__ = (
        Index('idx_products_session_id', session_id),
        Index('idx_products_name', name),
        Index('idx_products_category', category),
        Index('idx_products_session_category', session_id, category),  # Composite index
    )
