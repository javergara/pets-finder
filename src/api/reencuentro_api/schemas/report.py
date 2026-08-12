from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, model_validator

from ..services.ciudades import ZONA_OTRO, zona_valida

Tipo = Literal["perdido", "encontrado"]
Especie = Literal["perro", "gato", "otro"]
Situacion = Literal["conmigo", "vista"]
Tamano = Literal["pequeño", "mediano", "grande"]


class ReportIn(BaseModel):
    user_id: int
    tipo: Tipo
    especie: Especie
    nombre_mascota: str | None = None
    # Características predefinidas (feature 15) — el catálogo de opciones vive en
    # el frontend (lib/caracteristicas.ts); aquí solo se acota longitud/valores.
    raza: str | None = None
    color: str | None = None
    tamano: Tamano | None = None
    descripcion: str
    foto_url: str | None = None
    zona: str
    ciudad_texto: str | None = None
    barrio: str | None = None
    lat: float
    lng: float
    situacion: Situacion | None = None
    fecha_evento: date
    telefono_contacto: str

    @model_validator(mode="after")
    def validar_condicionales(self) -> "ReportIn":
        """Reglas que dependen del `tipo` (ADR 0005 §2) — un 422 con mensaje de producto.

        - `situacion` es obligatoria en "encontrado" y no aplica en "perdido".
        - `nombre_mascota` solo aplica en "perdido" (quien encuentra no lo conoce).
        - `zona` debe ser una de las conocidas u "Otro" (y "Otro" exige `ciudad_texto`).
        """
        if self.tipo == "encontrado" and self.situacion is None:
            raise ValueError(
                "Un reporte de mascota encontrada necesita 'situacion': "
                "'conmigo' (la tienes resguardada) o 'vista' (la viste pero no pudiste atraparla)"
            )
        if self.tipo == "perdido" and self.situacion is not None:
            raise ValueError("'situacion' solo aplica a reportes de mascota encontrada")
        if self.tipo == "encontrado" and self.nombre_mascota is not None:
            raise ValueError("'nombre_mascota' solo aplica a reportes de mascota perdida")
        if not zona_valida(self.zona):
            raise ValueError(
                f"Zona desconocida: '{self.zona}'. Usa una de las zonas cubiertas u 'Otro'"
            )
        if self.zona == ZONA_OTRO and not (self.ciudad_texto or "").strip():
            raise ValueError("Con zona 'Otro' se necesita 'ciudad_texto' con la ciudad real")
        if not self.telefono_contacto.strip():
            raise ValueError("El teléfono de contacto es obligatorio")
        return self


class ReportUpdate(BaseModel):
    """Edición parcial por el autor (feature 09): solo campos descriptivos.

    `user_id` no es editable — identifica a quien pide el cambio para validar
    autoría en el router. Ni `tipo` ni `estado` se editan por aquí (el estado
    solo cambia vía POST /api/reports/{id}/reunido).
    """

    user_id: int
    nombre_mascota: str | None = None
    descripcion: str | None = None
    foto_url: str | None = None
    barrio: str | None = None
    telefono_contacto: str | None = None
    fecha_evento: date | None = None


class ReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    tipo: str
    especie: str
    nombre_mascota: str | None
    raza: str | None
    color: str | None
    tamano: str | None
    descripcion: str
    foto_url: str | None
    zona: str
    ciudad_texto: str | None
    barrio: str | None
    lat: float
    lng: float
    situacion: str | None
    fecha_evento: date
    telefono_contacto: str
    estado: str
    creado_en: datetime
    resuelto_en: datetime | None


class CoincidenciaOut(ReportOut):
    """Un candidato a ser la misma mascota, con su distancia geográfica real."""

    distancia_km: float


class ReunidoIn(BaseModel):
    """Quien pide marcar el reencuentro — debe ser el autor del reporte."""

    user_id: int


class ReunidosResumenOut(BaseModel):
    """La métrica de esperanza: total de reencuentros + los más recientes."""

    total: int
    recientes: list[ReportOut]
