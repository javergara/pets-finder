from datetime import datetime

from pydantic import BaseModel, ConfigDict

from .pet import AfinidadOut
from .user import HomeProfileOut


class ShelterMetricsOut(BaseModel):
    mascotas_publicadas: int
    interesados_este_mes: int
    visitas_agendadas: int
    adopciones_cerradas: int
    # Siempre 0: no existe tabla Sponsorship todavía (feature 12-sponsorship, backlog).
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
