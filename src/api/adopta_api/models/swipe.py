from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Swipe(Base):
    """Independiente de Match a propósito — ver ADR 0002 (el match no es mutuo)."""

    __tablename__ = "swipes"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    pet_id: Mapped[int] = mapped_column(ForeignKey("pets.id"))
    direccion: Mapped[str] = mapped_column(String(10))  # "like" | "pass"
    creado_en: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
