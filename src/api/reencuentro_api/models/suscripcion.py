from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Suscripcion(Base):
    """ "Avísame si hay novedades" sobre un reporte (feature 39, ADR 0011).

    Cualquiera deja su correo en un reporte y recibe un email cuando hay una
    novedad (avistamiento nuevo o reencuentro). Sin cuenta: el correo es la
    identidad, y el `token` (aleatorio, único) es el mecanismo de baja en un
    click desde el propio email — nunca se expone en la API de lectura.
    """

    __tablename__ = "suscripciones"
    __table_args__ = (
        # El mismo correo no se suscribe dos veces al mismo reporte: el POST
        # repetido es idempotente (200), no un duplicado.
        UniqueConstraint("report_id", "email", name="uq_suscripcion_report_email"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    report_id: Mapped[int] = mapped_column(ForeignKey("reports.id"), index=True)
    email: Mapped[str] = mapped_column(String(120))
    token: Mapped[str] = mapped_column(String(64), unique=True)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
