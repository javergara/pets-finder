from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PetIn(BaseModel):
    """Payload de publicación de una mascota nueva (feature `09-shelter-panel`).

    Sin `lat`/`lng`: el formulario de publicación no captura ubicación individual
    de la mascota (quedan `None`, igual que en el modelo `Pet`). `estado` no es un
    campo de entrada: queda en su default `"disponible"` del modelo SQLAlchemy.
    """

    shelter_id: int
    nombre: str
    especie: str
    raza: str
    sexo: str
    edad_meses: int
    tamano: str
    energia: str
    historia: str
    tags: list[str] = []
    esterilizado: bool = False
    vacunas_al_dia: bool = False
    microchip: bool = False
    desparasitado: bool = False
    apto_ninos: bool = True
    apto_perros: bool = True
    apto_gatos: bool = True
    fotos: list[str] = []


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
    es_favorito: bool = False
    lat: float | None = None
    lng: float | None = None
    distancia_km: float | None = None
