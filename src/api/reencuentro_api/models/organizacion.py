from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Organizacion(Base):
    """Lugar de la red de apoyo (feature 32): centro de acopio, fundación,
    tienda de mascotas o veterinaria.

    Publicada por cualquier usuario con la cuenta liviana (mismo nivel de
    confianza que los reportes, ADR 0005 §4): el autor edita, cierra y elimina.
    `direccion` es obligatoria — para llevar una donación se necesita dirección
    escrita, no solo el pin. `como_donar` es texto libre informativo (Nequi,
    cuenta, link): la app no procesa pagos.
    """

    __tablename__ = "organizaciones"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    # "centro_acopio" | "fundacion" | "tienda" | "veterinaria"
    tipo: Mapped[str] = mapped_column(String(20))
    nombre: Mapped[str] = mapped_column(String(120))
    descripcion: Mapped[str] = mapped_column(String(2000))
    zona: Mapped[str] = mapped_column(String(40))
    ciudad_texto: Mapped[str | None] = mapped_column(String(80), nullable=True)
    barrio: Mapped[str | None] = mapped_column(String(80), nullable=True)
    direccion: Mapped[str] = mapped_column(String(200))
    lat: Mapped[float] = mapped_column(Float)
    lng: Mapped[float] = mapped_column(Float)
    telefono_contacto: Mapped[str] = mapped_column(String(20))
    horario: Mapped[str | None] = mapped_column(String(120), nullable=True)
    como_donar: Mapped[str | None] = mapped_column(String(300), nullable=True)
    foto_url: Mapped[str | None] = mapped_column(String(300), nullable=True)
    estado: Mapped[str] = mapped_column(String(20), default="activo")  # "activo" | "cerrado"
    creado_en: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
