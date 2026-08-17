from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .solicitud import SolicitudResumenOut


class SwipeIn(BaseModel):
    """Payload de un swipe del deck (AD-03).

    ⚠️ **`user_id` es el ADOPTANTE**, quien mira el deck — no quien publicó la
    mascota (eso es `Pet.user_id`, y viaja como `PetIn.rescatista_id`). Misma
    trampa que documenta `models/swipe.py`: las dos son FK a `users.id` y nadie
    va a avisar si se cruzan.

    ⚠️ `mensaje` y `telefono_contacto` **no son columnas de `swipes`**: desde
    AD-05 el "me interesa" los copia a la **solicitud** que crea en `matches`, en
    el mismo commit que el swipe. AD-03 ya los aceptaba (y los tiraba) para que el
    cliente no tuviera que hablar con una API que le devolviera 422 mientras
    duraba el despliegue incremental. Un `pass` los ignora: descartar una mascota
    no pide nada.
    """

    user_id: int
    pet_id: int
    direccion: Literal["like", "pass"]
    mensaje: str | None = Field(default=None, max_length=500)
    telefono_contacto: str | None = Field(default=None, max_length=20)


class SwipeOut(BaseModel):
    """El swipe registrado.

    `user_id` es el adoptante, igual que en `SwipeIn`.

    `solicitud` es lo que el swipe-derecha creó (tabla `matches`, "solicitud" en
    el copy — ver la nota de vigencia del ADR 0002) y viene `null` en un `pass`.
    Va aquí, y no en un `POST /api/solicitudes` aparte, porque el gesto es uno
    solo: pedir la mascota **es** swipear a la derecha, y una segunda petición
    podría fallar dejando el swipe sin solicitud.

    ⚠️ `solicitud` **no se rellena desde el ORM**: `Swipe` no tiene ese atributo
    (no hay `relationship()` entre las dos tablas, a propósito) y el router la
    arma a mano. Por eso conserva el default: sin él, un `model_validate` de un
    `pass` reventaría.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    pet_id: int
    direccion: str
    creado_en: datetime
    solicitud: SolicitudResumenOut | None = None
