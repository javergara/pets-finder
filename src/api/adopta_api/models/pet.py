from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .shelter import Shelter


class Pet(Base):
    __tablename__ = "pets"

    id: Mapped[int] = mapped_column(primary_key=True)
    shelter_id: Mapped[int] = mapped_column(ForeignKey("shelters.id"))
    nombre: Mapped[str] = mapped_column(String(80))
    especie: Mapped[str] = mapped_column(String(20))  # "perro" | "gato"
    raza: Mapped[str] = mapped_column(String(80))
    sexo: Mapped[str] = mapped_column(String(10))  # "macho" | "hembra"
    edad_meses: Mapped[int] = mapped_column(Integer)
    tamano: Mapped[str] = mapped_column(String(20))  # "pequeño"|"mediano"|"grande"
    energia: Mapped[str] = mapped_column(String(20))  # "baja"|"media"|"alta"
    fotos: Mapped[list[str]] = mapped_column(JSON, default=list)
    historia: Mapped[str] = mapped_column(String(2000))
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    esterilizado: Mapped[bool] = mapped_column(Boolean, default=False)
    vacunas_al_dia: Mapped[bool] = mapped_column(Boolean, default=False)
    microchip: Mapped[bool] = mapped_column(Boolean, default=False)
    desparasitado: Mapped[bool] = mapped_column(Boolean, default=False)
    apto_ninos: Mapped[bool] = mapped_column(Boolean, default=True)
    apto_perros: Mapped[bool] = mapped_column(Boolean, default=True)
    apto_gatos: Mapped[bool] = mapped_column(Boolean, default=True)
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    estado: Mapped[str] = mapped_column(String(20), default="disponible")
    publicado_en: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    shelter: Mapped["Shelter"] = relationship()
