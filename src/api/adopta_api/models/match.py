from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Match(Base):
    """Se crea de inmediato al hacer like (ADR 0002). Sin columna de afinidad: se
    calcula al vuelo (ADR 0003, docs/decisions/0003-afinidad-calculada-al-vuelo.md)."""

    __tablename__ = "matches"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    pet_id: Mapped[int] = mapped_column(ForeignKey("pets.id"))
    shelter_id: Mapped[int] = mapped_column(ForeignKey("shelters.id"))
    estado: Mapped[str] = mapped_column(String(20), default="solicitado")
    creado_en: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    motivo_descarte: Mapped[str | None] = mapped_column(String(500), nullable=True)
