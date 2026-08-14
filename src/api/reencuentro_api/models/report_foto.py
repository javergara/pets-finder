from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class ReportFoto(Base):
    """Foto adicional de un reporte (feature 41, benchmark Patas en Cali §10).

    `Report.foto_url` sigue siendo la principal (tarjetas, mapa y og tags no
    cambian); aquí viven hasta 2 extras — el flyer y las fotos reales de la
    mascota se complementan. `orden` preserva el orden en que se subieron.
    """

    __tablename__ = "report_fotos"

    id: Mapped[int] = mapped_column(primary_key=True)
    report_id: Mapped[int] = mapped_column(ForeignKey("reports.id"), index=True)
    foto_url: Mapped[str] = mapped_column(String(300))
    orden: Mapped[int] = mapped_column(Integer, default=0)
