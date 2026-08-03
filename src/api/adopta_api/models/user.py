from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .home_profile import HomeProfile


class User(Base):
    """Adoptante. No hay autenticación real en el MVP (ADR 0001/docs/architecture.md §6)."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(200), unique=True)
    ciudad: Mapped[str] = mapped_column(String(80), default="Bogotá")
    barrio: Mapped[str | None] = mapped_column(String(80), nullable=True)
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(300), nullable=True)
    bio: Mapped[str | None] = mapped_column(String(500), nullable=True)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    home_profile: Mapped["HomeProfile"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
