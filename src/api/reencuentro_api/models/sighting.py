from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Sighting(Base):
    """Avistamiento de terceros sobre un reporte perdido: "la vi por aquí".

    Sin autoría (feature 28): quien vio la mascota deja pin + fecha + comentario
    y opcionalmente su nombre, sin registrarse — en una emergencia, cada fricción
    para avisar es una pista que se pierde. Solo aplica a reportes "perdido"
    activos (validado en el router); no hay edición ni borrado de avistamientos
    en el MVP.
    """

    __tablename__ = "sightings"

    id: Mapped[int] = mapped_column(primary_key=True)
    report_id: Mapped[int] = mapped_column(ForeignKey("reports.id"))
    lat: Mapped[float] = mapped_column(Float)
    lng: Mapped[float] = mapped_column(Float)
    fecha: Mapped[date] = mapped_column(Date)
    comentario: Mapped[str] = mapped_column(String(200))
    nombre: Mapped[str | None] = mapped_column(String(80), nullable=True)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
