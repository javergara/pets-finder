from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class SwipeIn(BaseModel):
    """Payload de un swipe del deck (AD-03).

    ⚠️ **`user_id` es el ADOPTANTE**, quien mira el deck — no quien publicó la
    mascota (eso es `Pet.user_id`, y viaja como `PetIn.rescatista_id`). Misma
    trampa que documenta `models/swipe.py`: las dos son FK a `users.id` y nadie
    va a avisar si se cruzan.

    ⚠️ `mensaje` y `telefono_contacto` se aceptan **y se descartan**: no existen
    como columnas de `swipes`. Están declarados desde ya porque el formulario de
    AD-05/AD-06 los va a mandar en esta misma petición (el "me interesa" pasa a
    crear una solicitud) y vivirán en `matches`. Aceptarlos hoy evita que el
    cliente de AD-05 tenga que hablar con una API que le devuelva 422 mientras
    dura el despliegue incremental; no es un olvido de persistencia.
    """

    user_id: int
    pet_id: int
    direccion: Literal["like", "pass"]
    mensaje: str | None = Field(default=None, max_length=500)
    telefono_contacto: str | None = Field(default=None, max_length=20)


class SwipeOut(BaseModel):
    """El swipe registrado.

    `user_id` es el adoptante, igual que en `SwipeIn`.

    `solicitud` viaja **siempre `null` en AD-03**: el swipe no crea nada más. La
    solicitud (tabla `matches`, "solicitud" en el copy — ver la nota de vigencia
    del ADR 0002) la crea AD-05, que ampliará el tipo a `SolicitudResumenOut |
    None` cuando ese schema exista. Se declara ya para que el frontend lea el
    campo desde el primer día en vez de estrenar una clave nueva a mitad de
    camino; declararle hoy una forma que nada llena sería inventar un contrato.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    pet_id: int
    direccion: str
    creado_en: datetime
    solicitud: None = None
