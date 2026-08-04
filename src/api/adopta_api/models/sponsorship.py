from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Sponsorship(Base):
    """Compromiso de apadrinamiento de una mascota (feature 12-sponsorship).

    Registro de compromiso, no una transacción de dinero real: no hay integración
    de pasarela de pago (design/prototypes/HANDOFF.md §11)."""

    __tablename__ = "sponsorships"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    pet_id: Mapped[int] = mapped_column(ForeignKey("pets.id"))
    monto_cop: Mapped[int] = mapped_column(Integer)
    periodicidad: Mapped[str] = mapped_column(String(20))  # "mensual" | "unico"
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    iniciado_en: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
