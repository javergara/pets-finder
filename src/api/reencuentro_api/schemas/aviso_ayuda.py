from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ..services.ciudades import ZONA_OTRO, zona_valida

TipoAviso = Literal["pido", "ofrezco"]
CategoriaAviso = Literal["hogar_de_paso", "transporte", "alimento", "salud", "rescate", "otro"]


class AvisoAyudaIn(BaseModel):
    user_id: int
    tipo: TipoAviso
    categoria: CategoriaAviso
    titulo: str = Field(min_length=1, max_length=120)
    descripcion: str = Field(min_length=1, max_length=2000)
    zona: str
    ciudad_texto: str | None = None
    barrio: str | None = Field(default=None, max_length=80)
    telefono_contacto: str

    @model_validator(mode="after")
    def validar(self) -> "AvisoAyudaIn":
        """Mismas reglas de zona/contacto que reportes y organizaciones."""
        if not zona_valida(self.zona):
            raise ValueError(
                f"Zona desconocida: '{self.zona}'. Usa una de las zonas cubiertas u 'Otro'"
            )
        if self.zona == ZONA_OTRO and not (self.ciudad_texto or "").strip():
            raise ValueError("Con zona 'Otro' se necesita 'ciudad_texto' con la ciudad real")
        if not (self.telefono_contacto or "").strip():
            raise ValueError("El teléfono de contacto es obligatorio")
        return self


class AvisoResueltoIn(BaseModel):
    """Quién declara resuelto el aviso (mismo patrón que ReunidoIn)."""

    user_id: int


class AvisoAyudaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    tipo: str
    categoria: str
    titulo: str
    descripcion: str
    zona: str
    ciudad_texto: str | None
    barrio: str | None
    telefono_contacto: str
    estado: str
    creado_en: datetime
    resuelto_en: datetime | None
