from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    autor_tipo: str
    texto: str
    creado_en: datetime


class ThreadOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    match_id: int
    creado_en: datetime
    ultimo_mensaje_en: datetime


class ThreadConMensajesOut(BaseModel):
    """Orden de `mensajes` (creado_en ascendente) se garantiza en el servicio/
    router (services/chat.py, routers/chat.py), no aquí."""

    thread: ThreadOut
    mensajes: list[MessageOut]
