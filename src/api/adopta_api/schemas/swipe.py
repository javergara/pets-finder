from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class SwipeIn(BaseModel):
    user_id: int
    pet_id: int
    direccion: Literal["like", "pass"]


class MatchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    pet_id: int
    shelter_id: int
    estado: str
    creado_en: datetime


class SwipeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    pet_id: int
    direccion: str
    creado_en: datetime
    match: MatchOut | None = None
