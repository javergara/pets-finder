from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ShelterOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    ciudad: str
    verificado: bool
    adopciones_cerradas: int
    tiempo_respuesta_horas: int
    logo_url: str | None = None


class AfinidadOut(BaseModel):
    score: int
    explicacion: str
    incompatible: bool


class PetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    shelter_id: int
    nombre: str
    especie: str
    raza: str
    sexo: str
    edad_meses: int
    tamano: str
    energia: str
    fotos: list[str]
    historia: str
    tags: list[str]
    esterilizado: bool
    vacunas_al_dia: bool
    microchip: bool
    desparasitado: bool
    apto_ninos: bool
    apto_perros: bool
    apto_gatos: bool
    estado: str
    publicado_en: datetime
    shelter: ShelterOut | None = None
    afinidad: AfinidadOut | None = None
