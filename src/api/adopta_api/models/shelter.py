from sqlalchemy import Boolean, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Shelter(Base):
    __tablename__ = "shelters"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120))
    ciudad: Mapped[str] = mapped_column(String(80), default="Bogotá")
    verificado: Mapped[bool] = mapped_column(Boolean, default=True)
    adopciones_cerradas: Mapped[int] = mapped_column(Integer, default=0)
    tiempo_respuesta_horas: Mapped[int] = mapped_column(Integer, default=24)
    logo_url: Mapped[str | None] = mapped_column(String(300), nullable=True)
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lng: Mapped[float | None] = mapped_column(Float, nullable=True)
