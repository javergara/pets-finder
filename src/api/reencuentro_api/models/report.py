from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Report(Base):
    """Reporte de mascota perdida (dueño) o encontrada (rescatista).

    Un solo modelo para ambos tipos (ADR 0005 §2): los únicos campos asimétricos
    son `nombre_mascota` (solo tiene sentido en "perdido") y `situacion` (solo en
    "encontrado": "conmigo" = la tiene resguardada, "vista" = la vio pero no pudo
    atraparla). La validación condicional vive en el schema (ReportIn), no aquí.

    `zona` es una de las claves de services/ciudades.py::ZONAS o "Otro" (con la
    ciudad real en `ciudad_texto`). `estado` solo tiene dos valores: "activo" y
    "reunido" — nunca hay un estado de fracaso (docs/product-research.md §4).
    """

    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    tipo: Mapped[str] = mapped_column(String(20))  # "perdido" | "encontrado"
    especie: Mapped[str] = mapped_column(String(20))  # "perro" | "gato" | "otro"
    nombre_mascota: Mapped[str | None] = mapped_column(String(80), nullable=True)
    descripcion: Mapped[str] = mapped_column(String(2000))
    foto_url: Mapped[str | None] = mapped_column(String(300), nullable=True)
    zona: Mapped[str] = mapped_column(String(40))
    ciudad_texto: Mapped[str | None] = mapped_column(String(80), nullable=True)
    barrio: Mapped[str | None] = mapped_column(String(80), nullable=True)
    lat: Mapped[float] = mapped_column(Float)
    lng: Mapped[float] = mapped_column(Float)
    situacion: Mapped[str | None] = mapped_column(String(20), nullable=True)
    fecha_evento: Mapped[date] = mapped_column(Date)
    telefono_contacto: Mapped[str] = mapped_column(String(20))
    estado: Mapped[str] = mapped_column(String(20), default="activo")  # "activo" | "reunido"
    creado_en: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    resuelto_en: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
