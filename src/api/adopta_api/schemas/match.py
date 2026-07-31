from datetime import datetime

from pydantic import BaseModel, ConfigDict

from .pet import AfinidadOut


class MatchPetSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    raza: str
    edad_meses: int
    fotos: list[str]
    estado: str


class MatchWithPetOut(BaseModel):
    id: int
    estado: str
    creado_en: datetime
    pet: MatchPetSummary
    afinidad: AfinidadOut
