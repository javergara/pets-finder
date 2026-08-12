from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Necesidad(Base):
    """Pedido concreto de ayuda de una organización (feature 33).

    La publica y la marca como cubierta solo el autor de la organización;
    quien quiere ayudar contacta por WhatsApp (sin transacciones en la app).
    "Cubierta" es la mecánica de esperanza de la red de apoyo, como "reunido"
    en los reportes.
    """

    __tablename__ = "necesidades"

    id: Mapped[int] = mapped_column(primary_key=True)
    organizacion_id: Mapped[int] = mapped_column(ForeignKey("organizaciones.id"))
    # alimento|medicinas|insumos|voluntarios|hogar_de_paso|dinero|otro
    categoria: Mapped[str] = mapped_column(String(20))
    descripcion: Mapped[str] = mapped_column(String(300))
    estado: Mapped[str] = mapped_column(String(20), default="pendiente")  # pendiente|cubierta
    creado_en: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    cubierta_en: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
