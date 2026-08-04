from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Thread(Base):
    """Un hilo de mensajería por match (ADR 0004). Creación lazy en
    services/chat.py::obtener_o_crear_thread, no en services/matching.py."""

    __tablename__ = "threads"

    id: Mapped[int] = mapped_column(primary_key=True)
    match_id: Mapped[int] = mapped_column(ForeignKey("matches.id"), unique=True)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    ultimo_mensaje_en: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )


class Message(Base):
    """Mensaje dentro de un Thread. autor_tipo identifica el rol de quien lo
    envió (adoptante/refugio/sistema) sin necesidad de un id de autor polimórfico,
    porque el Thread ya está anclado 1:1 a un match con user_id/shelter_id."""

    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    thread_id: Mapped[int] = mapped_column(ForeignKey("threads.id"))
    autor_tipo: Mapped[str] = mapped_column(String(20))  # "adoptante" | "refugio" | "sistema"
    texto: Mapped[str] = mapped_column(String(2000))
    creado_en: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
