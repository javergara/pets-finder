from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Pet(Base):
    """Mascota publicada en adopción (AD-01), la fase 2 del producto.

    Portada de la era Adopta (`adopta-v1`) y adaptada al stack actual: donde
    antes colgaba siempre de un `Shelter`, aquí cuelga de **una organización de
    la red de apoyo O de un rescatista individual**, nunca de ambos ni de
    ninguno — el invariante lo protege `ck_pets_publicador_exclusivo` a nivel de
    DB, además del 422 en español que da `PetIn` (ver `schemas/pet.py`).

    ⚠️ **`user_id` aquí es el rescatista dueño de la mascota**, no quien hace el
    request. En el contrato HTTP ese dueño viaja como `PetIn.rescatista_id`, y
    `PetIn.user_id` significa otra cosa: quien pide la operación (autoría → 403).
    Confundirlos produce un bug silencioso de privacidad.

    `zona`/`ciudad_texto`/`barrio`/`lat`/`lng` van desnormalizados, igual que en
    `Report` y `Organizacion`: el `User` no tiene zona (solo `ciudad`), así que
    sin esto una mascota de rescatista no se podría filtrar por zona — y el
    rescatista individual es el caso central de esta emergencia. Una mascota
    también puede estar en hogar de paso en otra zona que la fundación.

    `telefono_contacto` vive aquí porque el modelo `User` no tiene teléfono: sin
    esta columna una mascota de rescatista sería incontactable. Es obligatorio
    cuando publica un rescatista; en organizaciones cae al de la organización.

    `report_id` es el puente con un reporte de "encontrada" que nadie reclamó
    (AD-02): `unique` porque un reporte produce como máximo una mascota — los
    NULL no chocan entre sí, así que las mascotas sin reporte no se estorban.

    ⚠️ `fotos` y `tags` son columnas JSON **sin `MutableList`**: nunca se mutan
    in-place (`pet.fotos.append(...)` no se persiste). Se reasigna la lista
    completa (`pet.fotos = [...]`).
    """

    __tablename__ = "pets"
    __table_args__ = (
        CheckConstraint(
            "(organizacion_id IS NULL) <> (user_id IS NULL)",
            name="ck_pets_publicador_exclusivo",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    organizacion_id: Mapped[int | None] = mapped_column(
        ForeignKey("organizaciones.id"), nullable=True, index=True
    )
    # El rescatista dueño (ver el aviso del docstring), no quien hace el request.
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    report_id: Mapped[int | None] = mapped_column(
        ForeignKey("reports.id"), nullable=True, unique=True
    )
    nombre: Mapped[str] = mapped_column(String(80))
    especie: Mapped[str] = mapped_column(String(20))  # "perro" | "gato" | "otro"
    raza: Mapped[str | None] = mapped_column(String(80), nullable=True)
    sexo: Mapped[str] = mapped_column(String(10))  # "macho" | "hembra"
    edad_meses: Mapped[int] = mapped_column(Integer)
    tamano: Mapped[str] = mapped_column(String(20))  # "pequeño" | "mediano" | "grande"
    energia: Mapped[str] = mapped_column(String(20))  # "baja" | "media" | "alta"
    fotos: Mapped[list[str]] = mapped_column(JSON, default=list)
    historia: Mapped[str] = mapped_column(String(2000))
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    esterilizado: Mapped[bool] = mapped_column(Boolean, default=False)
    vacunas_al_dia: Mapped[bool] = mapped_column(Boolean, default=False)
    microchip: Mapped[bool] = mapped_column(Boolean, default=False)
    desparasitado: Mapped[bool] = mapped_column(Boolean, default=False)
    apto_ninos: Mapped[bool] = mapped_column(Boolean, default=True)
    apto_perros: Mapped[bool] = mapped_column(Boolean, default=True)
    apto_gatos: Mapped[bool] = mapped_column(Boolean, default=True)
    zona: Mapped[str] = mapped_column(String(40), index=True)
    ciudad_texto: Mapped[str | None] = mapped_column(String(80), nullable=True)
    barrio: Mapped[str | None] = mapped_column(String(80), nullable=True)
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    telefono_contacto: Mapped[str | None] = mapped_column(String(20), nullable=True)
    # "disponible" | "en_proceso" | "adoptado" — sin estado de fracaso.
    estado: Mapped[str] = mapped_column(String(20), default="disponible", index=True)
    publicado_en: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    adoptado_en: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
