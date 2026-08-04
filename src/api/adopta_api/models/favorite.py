from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Favorite(Base):
    """Independiente de `Swipe` a propósito (feature `13-favorites`).

    Marcar/desmarcar un favorito nunca pasa por `services/matching.py`, nunca
    inserta una fila en `swipes` ni crea un `Match`, y nunca excluye la
    mascota de `routers/pets.py::listar_mascotas` (que solo filtra por
    `Swipe.pet_id`). "Guardar para revisar después" es un concepto totalmente
    separado de un swipe definitivo — la existencia de la fila es la señal
    (mismo criterio que `HomeProfile`/`Thread`), sin campo de estado.
    """

    __tablename__ = "favorites"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    pet_id: Mapped[int] = mapped_column(ForeignKey("pets.id"))
    creado_en: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
