from datetime import datetime, UTC

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Link(Base):
    __tablename__ = "links"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    short_code: Mapped[str] = mapped_column(String(10), unique=True, index=True, nullable=False)
    original_url: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(UTC), nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)