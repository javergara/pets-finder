from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Favorite(Base):
    """Mascota guardada "para revisar después" por quien busca adoptar (AD-07).

    Portado de la era Adopta (`adopta-v1`). Es **independiente de `Swipe` y de
    `Match`** a propósito: marcar o desmarcar un favorito nunca inserta una fila
    en `swipes`, nunca crea una solicitud y **nunca saca la mascota del deck**
    (que solo excluye por `Swipe.pet_id`). "Guardar" y "decidir" son dos
    mecanismos distintos, y confundirlos haría desaparecer una carta por el gesto
    más inocente de la pantalla. La existencia de la fila es la señal (mismo
    criterio que `HomeProfile`), sin campo de estado.

    ⚠️ **`user_id` aquí es el ADOPTANTE que MIRA** — exactamente al revés que en
    `pets`, donde `Pet.user_id` es quien **PUBLICA** la mascota. Las dos son
    claves foráneas a `users.id`, así que ninguna base de datos avisa si se
    cruzan: el síntoma sería que a quien publica le salgan sus propias mascotas
    como "mis favoritas", o que la lista de una persona muestre lo que guardó
    otra. Por eso el helper del paso 3 se llama `_ids_favoritos(session,
    adoptante_id)` y no `user_id` a secas.

    `UniqueConstraint("user_id", "pet_id")` es **nuevo** respecto a `adopta-v1`,
    que resolvía la idempotencia solo con un select previo en el router. Mismo
    criterio que `uq_suscripcion_report_email` y `uq_swipe_user_pet`: con Postgres
    y concurrencia real, dos toques al corazón corren de verdad a la vez y los dos
    pueden ver ese select vacío; la garantía va en la base de datos. El endpoint
    hará igual el select previo, pero para responder 200 en vez de un error.

    Los índices por `user_id` y `pet_id` son los dos accesos del módulo: las
    favoritas de una persona (la pantalla `/adoptar/mis-favoritas` y el `select`
    que llena `es_favorito` en catálogo, ficha y deck) y, más adelante, el interés
    que despertó una mascota.
    """

    __tablename__ = "favorites"
    __table_args__ = (UniqueConstraint("user_id", "pet_id", name="uq_favorite_user_pet"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    # El adoptante que mira (ver el aviso del docstring), no quien publicó.
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    pet_id: Mapped[int] = mapped_column(ForeignKey("pets.id"), index=True)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
