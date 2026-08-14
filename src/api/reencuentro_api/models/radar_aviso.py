from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class RadarAviso(Base):
    """Pareja (perdido, candidato) ya avisada por el radar (feature 43).

    El radar corre a diario: sin este registro re-avisaría las mismas
    coincidencias en cada corrida. Una fila = "de esta pareja ya se habló";
    nunca se borra — el silencio también es información.
    """

    __tablename__ = "radar_avisos"
    __table_args__ = (UniqueConstraint("report_id", "candidato_id", name="uq_radar_pareja"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    report_id: Mapped[int] = mapped_column(ForeignKey("reports.id"), index=True)
    candidato_id: Mapped[int] = mapped_column(ForeignKey("reports.id"))
    creado_en: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
