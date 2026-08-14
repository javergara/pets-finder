from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class AvisoAyuda(Base):
    """Ayuda puntual entre personas (feature 42, benchmark Patas en Cali §10).

    El tercer flujo de la emergencia: "necesito ayuda" (rescate, salud,
    alimento) y "ofrezco ayuda" (hogar de paso, transporte). No es una
    organización con dirección física (eso es `Organizacion`): es un vecino con
    un aviso puntual, con la misma cuenta liviana como autoría y contacto
    directo por WhatsApp. Se cierra con "resuelto", igual que los reencuentros.
    """

    __tablename__ = "avisos_ayuda"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    tipo: Mapped[str] = mapped_column(String(10))  # "pido" | "ofrezco"
    categoria: Mapped[str] = mapped_column(String(20))
    titulo: Mapped[str] = mapped_column(String(120))
    descripcion: Mapped[str] = mapped_column(String(2000))
    zona: Mapped[str] = mapped_column(String(40))
    ciudad_texto: Mapped[str | None] = mapped_column(String(80), nullable=True)
    barrio: Mapped[str | None] = mapped_column(String(80), nullable=True)
    telefono_contacto: Mapped[str] = mapped_column(String(20))
    estado: Mapped[str] = mapped_column(String(10), default="activo")  # "activo" | "resuelto"
    creado_en: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    resuelto_en: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
