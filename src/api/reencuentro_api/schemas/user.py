from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UserIn(BaseModel):
    nombre: str
    email: str
    ciudad: str = "Armenia"
    barrio: str | None = None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    email: str
    ciudad: str
    barrio: str | None
    lat: float | None
    lng: float | None
    avatar_url: str | None
    bio: str | None
    creado_en: datetime
