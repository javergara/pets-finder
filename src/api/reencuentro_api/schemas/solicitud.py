"""Contrato HTTP de la solicitud de adopción (AD-05).

La tabla se llama `matches` (ver `models/match.py`), pero en la API, en el copy y
en las pantallas esto es siempre una **solicitud**: quien busque "match" en el
producto no lo va a encontrar.

⚠️ **Ningún schema de este archivo declara `motivo_descarte`.** Es la nota
interna con la que el publicador cierra una solicitud, y quien no se quedó con la
mascota no tiene por qué leer por qué (ADR 0002). No es un olvido: es el contrato
de privacidad del módulo, y hay dos tests que comparan el texto crudo de la
respuesta para que no reaparezca anidado en un schema compartido.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from .pet import AfinidadOut, PetResumenOut, PublicadorOut
from .user import HomeProfileOut

#: Los cinco estados persistidos, espejo de `ESTADOS_SOLICITUD`
#: (`services/solicitudes.py`). Un candado en `tests/api/test_solicitudes.py`
#: exige que las dos listas digan lo mismo: si se separan, o la respuesta revienta
#: al serializar un estado real, o el schema legitima el `"aprobado"` inventado
#: que `calcular_etiqueta_solicitud` trataría como "solicitado".
EstadoSolicitud = Literal[
    "solicitado",
    "en_revision",
    "visita_agendada",
    "adoptado",
    "cerrado",
]

#: Las acciones que puede ejecutar quien publicó, espejo de `ORDEN_ACCIONES`.
#: **No son estados** (`aprobar` lleva a `adoptado`, `descartar` a `cerrado`):
#: son los nombres de las rutas `POST /api/solicitudes/{id}/{accion}` del paso 3.
AccionSolicitud = Literal[
    "agendar-visita",
    "pedir-informacion",
    "aprobar",
    "descartar",
]


class AdoptanteResumen(BaseModel):
    """Quién pide la mascota: nombre y nada más.

    ⚠️ **Sin `email`.** Sin contraseñas (ADR 0005) el correo es la credencial de
    acceso de todo el producto —`POST /api/users` entra o registra con solo ese
    dato—, así que filtrarlo en una lista que ve cualquier publicador sería
    repartir llaves. El contacto del adoptante viaja aparte, y solo en el
    detalle: el teléfono que él mismo dejó al pedir la mascota.
    """

    id: int
    nombre: str


class SolicitudResumenOut(BaseModel):
    """La solicitud recién creada, para devolverla junto al swipe (paso 4).

    Es lo mínimo que necesita el modal de "solicitud enviada": el estado en el
    que nace y de qué mascota se trata. Deliberadamente **no** lleva adoptante
    (es quien pregunta) ni afinidad (ya venía en la tarjeta del deck).
    """

    id: int
    estado: EstadoSolicitud
    etiqueta: str
    creado_en: datetime
    pet: PetResumenOut


class SolicitudOut(BaseModel):
    """Fila de `GET /api/solicitudes`, la misma para las dos pantallas.

    Sirve tanto a "mis solicitudes" (adoptante) como a "las que recibí"
    (publicador) porque el único campo que cambia entre las dos es
    `acciones_disponibles`, y eso lo decide el backend viendo quién pregunta:
    para el adoptante es **siempre `[]`** (el match no es mutuo, ADR 0002).

    `publicador` y `afinidad` son opcionales por razones distintas y las dos
    reales: una mascota puede colgar de una organización ya eliminada (feature
    32), y el adoptante puede no haber contestado el cuestionario de hogar
    (AD-04 lo dejó opcional a propósito).
    """

    id: int
    estado: EstadoSolicitud
    etiqueta: str
    creado_en: datetime
    actualizado_en: datetime | None = None
    pet: PetResumenOut
    publicador: PublicadorOut | None = None
    adoptante: AdoptanteResumen
    afinidad: AfinidadOut | None = None
    acciones_disponibles: list[AccionSolicitud] = Field(default_factory=list)


class SolicitudDetalleOut(SolicitudOut):
    """Lo que ve la pantalla de detalle: además, con qué decidir.

    `home_profile` es el contenido principal para el publicador (ADR 0002) y
    puede ser `null`: `adopta-v1` respondía 404 sin cuestionario y **saltaba la
    fila** en la lista, así que quien no lo había contestado desaparecía del
    panel sin ningún error visible.

    `mensaje` y `telefono_contacto` son los que dejó el adoptante al pedir la
    mascota; el teléfono está aquí y no en `AdoptanteResumen` porque solo tiene
    sentido para quien ya está evaluando esta solicitud concreta.
    """

    bio: str | None = None
    mensaje: str | None = None
    telefono_contacto: str | None = None
    home_profile: HomeProfileOut | None = None


class AccionSolicitudIn(BaseModel):
    """Body de las acciones sin datos extra (paso 3).

    `user_id` es quien pide la operación, igual que en `PetIn` y
    `OrganizacionUpdate`: sin contraseñas (ADR 0005) compararlo con el dueño de
    la mascota es toda la autorización que hay.
    """

    user_id: int


class DescartarIn(AccionSolicitudIn):
    """Body de `POST /api/solicitudes/{id}/descartar` (paso 3).

    El motivo es **obligatorio**: el publicador siempre deja constancia de por
    qué cierra una solicitud, aunque ese texto no se le muestre de vuelta al
    adoptante (ver el aviso de cabecera de este módulo).
    """

    motivo: str = Field(min_length=1, max_length=500)

    @field_validator("motivo")
    @classmethod
    def motivo_no_vacio(cls, valor: str) -> str:
        """`min_length=1` no alcanza: `"   "` mide 3 y no dice nada."""
        if not valor.strip():
            raise ValueError("El motivo no puede estar vacío")
        return valor.strip()
