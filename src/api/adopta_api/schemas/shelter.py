from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .pet import AfinidadOut
from .user import HomeProfileOut


class ShelterMetricsOut(BaseModel):
    mascotas_publicadas: int
    interesados_este_mes: int
    visitas_agendadas: int
    adopciones_cerradas: int
    # Suma de Sponsorship.monto_cop activos de las mascotas de este refugio
    # (feature 12-sponsorship).
    apadrinamientos_recaudados_cop: int


class ShelterProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    ciudad: str
    verificado: bool
    tiempo_respuesta_horas: int
    logo_url: str | None = None
    # Se asigna en el router (requiere varias queries agregadas), no viene de from_attributes.
    metricas: ShelterMetricsOut


class SolicitanteResumen(BaseModel):
    id: int
    nombre: str


class SolicitudPetResumen(BaseModel):
    id: int
    nombre: str
    raza: str
    fotos: list[str]


class SolicitudOut(BaseModel):
    id: int  # id del Match, no un id de "solicitud" separado (no existe esa entidad).
    estado: str
    creado_en: datetime
    adoptante: SolicitanteResumen
    pet: SolicitudPetResumen
    afinidad: AfinidadOut
    etiqueta: str


class SolicitudDetalleOut(SolicitudOut):
    bio: str | None = None
    home_profile: HomeProfileOut


class DescartarIn(BaseModel):
    """Body de `POST .../descartar` (feature 10-adoption-request-flow).

    `motivo` es obligatorio y no puede ser vacío ni solo espacios en blanco -- el
    refugio siempre deja constancia de por qué descarta una solicitud, aunque ese
    texto no se le muestre de vuelta al adoptante (ver ADR 0002 y `schemas/match.py`).
    """

    motivo: str = Field(min_length=1)

    @field_validator("motivo")
    @classmethod
    def motivo_no_vacio(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("El motivo no puede estar vacío")
        return v.strip()
