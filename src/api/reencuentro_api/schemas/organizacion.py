from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ..services.ciudades import ZONA_OTRO, zona_valida

TipoOrganizacion = Literal["centro_acopio", "fundacion", "tienda", "veterinaria"]
EstadoOrganizacion = Literal["activo", "cerrado"]


class OrganizacionIn(BaseModel):
    user_id: int
    tipo: TipoOrganizacion
    nombre: str = Field(min_length=1, max_length=120)
    descripcion: str = Field(min_length=1, max_length=2000)
    zona: str
    ciudad_texto: str | None = None
    barrio: str | None = None
    direccion: str = Field(min_length=1, max_length=200)
    lat: float
    lng: float
    telefono_contacto: str
    horario: str | None = Field(default=None, max_length=120)
    como_donar: str | None = Field(default=None, max_length=300)
    foto_url: str | None = None

    @model_validator(mode="after")
    def validar(self) -> "OrganizacionIn":
        """Mismas reglas de zona/contacto que los reportes (ReportIn)."""
        if not zona_valida(self.zona):
            raise ValueError(
                f"Zona desconocida: '{self.zona}'. Usa una de las zonas cubiertas u 'Otro'"
            )
        if self.zona == ZONA_OTRO and not (self.ciudad_texto or "").strip():
            raise ValueError("Con zona 'Otro' se necesita 'ciudad_texto' con la ciudad real")
        if not self.telefono_contacto.strip():
            raise ValueError("El teléfono de contacto es obligatorio")
        return self


class OrganizacionUpdate(BaseModel):
    """Edición parcial por el autor; `estado: "cerrado"` cierra el lugar."""

    user_id: int
    nombre: str | None = Field(default=None, min_length=1, max_length=120)
    descripcion: str | None = Field(default=None, min_length=1, max_length=2000)
    direccion: str | None = Field(default=None, min_length=1, max_length=200)
    telefono_contacto: str | None = None
    horario: str | None = Field(default=None, max_length=120)
    como_donar: str | None = Field(default=None, max_length=300)
    foto_url: str | None = None
    estado: EstadoOrganizacion | None = None


class OrganizacionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    tipo: TipoOrganizacion
    nombre: str
    descripcion: str
    zona: str
    ciudad_texto: str | None
    barrio: str | None
    direccion: str
    lat: float
    lng: float
    telefono_contacto: str
    horario: str | None
    como_donar: str | None
    foto_url: str | None
    estado: str
    creado_en: datetime
    # Contador calculado (feature 33): cuántas necesidades pendientes tiene —
    # el router lo llena; el ORM no tiene este atributo, por eso el default.
    necesidades_pendientes: int = 0


CategoriaNecesidad = Literal[
    "alimento", "medicinas", "insumos", "voluntarios", "hogar_de_paso", "dinero", "otro"
]


class NecesidadIn(BaseModel):
    """La publica el autor de la organización (validado en el router)."""

    user_id: int
    categoria: CategoriaNecesidad
    descripcion: str = Field(min_length=1, max_length=300)


class NecesidadOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organizacion_id: int
    categoria: CategoriaNecesidad
    descripcion: str
    estado: str
    creado_en: datetime
    cubierta_en: datetime | None


class CubrirNecesidadIn(BaseModel):
    user_id: int
