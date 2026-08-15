from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Swipe(Base):
    """Decisión de quien mira el deck sobre una mascota: "me interesa" o "ahora no".

    Portado de la era Adopta (`adopta-v1`). Es independiente de la solicitud
    (tabla `matches`, AD-05) a propósito — ver ADR 0002: el match **no es mutuo**,
    así que un "like" es información del adoptante, no un acuerdo entre dos
    partes. En AD-03 el swipe solo sirve para no volver a mostrar la misma carta.

    ⚠️ **`user_id` aquí es el ADOPTANTE**, quien mira el deck — exactamente al
    revés que en `pets`, donde `Pet.user_id` es el rescatista que **publicó** la
    mascota. Es la colisión más peligrosa del portado: confundirlas mostraría el
    deck de una persona a otra, o dejaría a alguien swipeando sus propias
    mascotas. La FK apunta a `users.id` en los dos casos, así que ninguna base de
    datos va a avisar del error.

    `UniqueConstraint("user_id", "pet_id")` es **nuevo** respecto a `adopta-v1`:
    sin él, un doble-tap del gesto en un móvil mete dos filas y, en AD-05, dos
    solicitudes a la misma organización. El endpoint hace además un select previo
    para responder 200 en vez de un error, pero la garantía real es esta
    restricción — en serverless dos requests corren de verdad a la vez.

    Los índices por `user_id` y `pet_id` son los dos accesos del módulo: excluir
    del deck lo ya visto (por adoptante) y, más adelante, contar el interés que
    despertó una mascota (por mascota).
    """

    __tablename__ = "swipes"
    __table_args__ = (UniqueConstraint("user_id", "pet_id", name="uq_swipe_user_pet"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    # El adoptante que mira (ver el aviso del docstring), no quien publicó.
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    pet_id: Mapped[int] = mapped_column(ForeignKey("pets.id"), index=True)
    direccion: Mapped[str] = mapped_column(String(10))  # "like" | "pass"
    creado_en: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
