from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Match(Base):
    """Solicitud de adopción: alguien pidió quedarse con una mascota publicada.

    Portada de la era Adopta (`adopta-v1`). **La tabla se sigue llamando
    `matches`** —es el nombre de las migraciones del backlog y el del ADR 0002—
    pero en la API, en el copy y en las pantallas se llama siempre
    **"solicitud"**: quien busque "match" en el producto no lo va a encontrar.

    Se crea de inmediato con el swipe-derecha, sin que el publicador acepte nada
    (ADR 0002: el match **no es mutuo**). Lo que el publicador decide después es
    el **estado** de la solicitud, no su existencia: `solicitado` →
    `en_revision` / `visita_agendada` → `adoptado` / `cerrado`, según la matriz
    de `services/solicitudes.py`.

    ⚠️ **`user_id` aquí es el ADOPTANTE**, quien pidió la mascota — exactamente
    al revés que en `pets`, donde `Pet.user_id` es el rescatista que la
    **publicó**. Es la colisión más peligrosa del portado: confundirlas mostraría
    a alguien las solicitudes de otro, o dejaría al adoptante gestionando la
    mascota ajena. La FK apunta a `users.id` en los dos casos, así que ninguna
    base de datos va a avisar del error.

    **Sin `shelter_id`**: los refugios de aquella era ya no existen y una mascota
    cuelga de una organización **o** de un rescatista individual. El publicador se
    resuelve por join a `pets` (`_dueno_user_id`), lo que evita duplicar aquí el
    XOR de `ck_pets_publicador_exclusivo` y quedar rancio si una mascota cambia de
    dueño. **Sin columna de afinidad**: el score se calcula al vuelo (ADR 0003) y
    persistirlo lo dejaría mintiendo en cuanto el adoptante edite su hogar.

    `mensaje` y `telefono_contacto` los deja el adoptante al swipear y entran ya
    aquí aunque los use AD-06 (contacto por WhatsApp): así esa feature no necesita
    un `ALTER TABLE` ni una segunda ventana de migración autorizada. El teléfono
    es del adoptante porque el modelo `User` no tiene ninguno.

    `motivo_descarte` **no se expone en ningún schema**: es la nota interna del
    publicador, y quien no se quedó con la mascota no tiene por qué leer por qué.

    `UniqueConstraint("user_id", "pet_id")` es lo que hace idempotente al
    swipe-derecha: en serverless dos requests del mismo dedo corren de verdad a la
    vez y los dos pueden ver vacío el select previo del endpoint.

    Los índices por `user_id` y `pet_id` son los dos accesos del módulo: las
    solicitudes de un adoptante (`/adoptar/mis-solicitudes`) y las de una mascota
    —el join del panel del publicador y el cierre masivo al aprobar—.
    """

    __tablename__ = "matches"
    __table_args__ = (UniqueConstraint("user_id", "pet_id", name="uq_match_user_pet"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    # El adoptante que pide la mascota (ver el aviso del docstring), no quien la publicó.
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    pet_id: Mapped[int] = mapped_column(ForeignKey("pets.id"), index=True)
    # Uno de ESTADOS_SOLICITUD (services/solicitudes.py). Nunca "aprobado".
    estado: Mapped[str] = mapped_column(String(20), default="solicitado")
    mensaje: Mapped[str | None] = mapped_column(String(500), nullable=True)
    telefono_contacto: Mapped[str | None] = mapped_column(String(20), nullable=True)
    motivo_descarte: Mapped[str | None] = mapped_column(String(500), nullable=True)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    # Nulo hasta que el publicador ejecuta la primera acción.
    actualizado_en: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
