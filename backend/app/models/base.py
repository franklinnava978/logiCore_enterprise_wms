from datetime import datetime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import DateTime
from sqlalchemy.sql import func

class Base(DeclarativeBase):
    """Base model for all SQLAlchemy models."""
    pass

class TimestampMixin:
    """Mixin to add created_at and updated_at columns cleanly to any model."""
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())