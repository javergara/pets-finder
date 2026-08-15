from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ..services.ciudades import ZONA_OTRO, zona_valida

EspeciePet = Literal["perro", "gato", "otro"]
SexoPet = Literal["macho", "hembra"]
TamanoPet = Literal["pequeño", "mediano", "grande"]
EnergiaPet = Literal["baja", "media", "alta"]
EstadoPet = Literal["disponible", "en_proceso", "adoptado"]
TipoPublicador = Literal["organizacion", "rescatista"]


class PetIn(BaseModel):
    """Payload para publicar una mascota en adopción (AD-01).

    ⚠️ `user_id` es SIEMPRE quien hace el request (autoría → 403 en el router),
    nunca el dueño de la mascota. El dueño se declara aparte y es exclusivo:
    `organizacion_id` **o** `rescatista_id` — y `rescatista_id` es el que se
    persiste en la columna `Pet.user_id`. Es la trampa más peligrosa del portado
    desde `adopta-v1`, donde `user_id` significaba "el adoptante que mira".

    El XOR del publicador se valida en dos niveles a propósito: aquí para dar el
    422 en español, y en `ck_pets_publicador_exclusivo` para que ningún seed,
    SQL manual o endpoint futuro pueda meter una fila inconsistente.
    """

    user_id: int
    organizacion_id: int | None = None
    rescatista_id: int | None = None
    nombre: str = Field(min_length=1, max_length=80)
    especie: EspeciePet
    sexo: SexoPet
    tamano: TamanoPet
    energia: EnergiaPet
    raza: str | None = Field(default=None, max_length=80)
    edad_meses: int = Field(ge=0, le=360)
    historia: str = Field(min_length=1, max_length=2000)
    tags: list[str] = Field(default_factory=list, max_length=8)
    fotos: list[str] = Field(default_factory=list, max_length=3)
    esterilizado: bool = False
    vacunas_al_dia: bool = False
    microchip: bool = False
    desparasitado: bool = False
    apto_ninos: bool = True
    apto_perros: bool = True
    apto_gatos: bool = True
    zona: str
    ciudad_texto: str | None = Field(default=None, max_length=80)
    barrio: str | None = Field(default=None, max_length=80)
    lat: float | None = None
    lng: float | None = None
    telefono_contacto: str | None = Field(default=None, max_length=20)
    # Puente con un reporte de "encontrada" que nadie reclamó (AD-02).
    report_id: int | None = None

    @model_validator(mode="after")
    def validar(self) -> "PetIn":
        """Publicador exclusivo, autoría del rescatista, contacto y zona.

        Las reglas que necesitan DB (que el dueño exista, que el reporte sea
        propio y del tipo correcto) viven en el router: aquí solo lo que se
        decide con el payload en la mano.
        """
        if (self.organizacion_id is None) == (self.rescatista_id is None):
            raise ValueError(
                "Una mascota en adopción cuelga de una organización O de un "
                "rescatista: manda 'organizacion_id' o 'rescatista_id', exactamente uno"
            )
        if self.rescatista_id is not None:
            if self.rescatista_id != self.user_id:
                raise ValueError("Un rescatista solo puede publicar mascotas a su propio nombre")
            if not (self.telefono_contacto or "").strip():
                raise ValueError(
                    "Un rescatista necesita un teléfono de contacto para que puedan escribirle"
                )
        if not zona_valida(self.zona):
            raise ValueError(
                f"Zona desconocida: '{self.zona}'. Usa una de las zonas cubiertas u 'Otro'"
            )
        if self.zona == ZONA_OTRO and not (self.ciudad_texto or "").strip():
            raise ValueError("Con zona 'Otro' se necesita 'ciudad_texto' con la ciudad real")
        return self


class PetUpdate(BaseModel):
    """Edición parcial por quien publicó (patrón de `OrganizacionUpdate`).

    `user_id` no es editable: identifica a quien pide el cambio para validar
    autoría en el router. **No se puede cambiar el publicador** (organización ni
    rescatista) **ni la zona**: mudar una mascota de dueño o de zona cambiaría
    su encuadre en el mapa y en las coincidencias — para eso se despublica y se
    vuelve a publicar.

    ⚠️ `fotos` y `tags` se reemplazan como lista completa, nunca se mutan
    in-place (las columnas JSON no llevan `MutableList`).
    """

    user_id: int
    nombre: str | None = Field(default=None, min_length=1, max_length=80)
    especie: EspeciePet | None = None
    sexo: SexoPet | None = None
    tamano: TamanoPet | None = None
    energia: EnergiaPet | None = None
    raza: str | None = Field(default=None, max_length=80)
    edad_meses: int | None = Field(default=None, ge=0, le=360)
    historia: str | None = Field(default=None, min_length=1, max_length=2000)
    tags: list[str] | None = Field(default=None, max_length=8)
    fotos: list[str] | None = Field(default=None, max_length=3)
    esterilizado: bool | None = None
    vacunas_al_dia: bool | None = None
    microchip: bool | None = None
    desparasitado: bool | None = None
    apto_ninos: bool | None = None
    apto_perros: bool | None = None
    apto_gatos: bool | None = None
    barrio: str | None = Field(default=None, max_length=80)
    lat: float | None = None
    lng: float | None = None
    telefono_contacto: str | None = Field(default=None, max_length=20)
    estado: EstadoPet | None = None


class PublicadorOut(BaseModel):
    """Quién publica, en un solo objeto (nunca dos campos sueltos).

    `id` es el de la `Organizacion` o el del `User`, según `tipo`. Lo arma el
    router con dos queries batch — el modelo `Pet` no declara `relationship()`.
    """

    tipo: TipoPublicador
    id: int
    nombre: str
    telefono_contacto: str | None = None
    zona: str | None = None
    ciudad_texto: str | None = None
    barrio: str | None = None
    foto_url: str | None = None


class AfinidadOut(BaseModel):
    """Qué tan bien encaja la mascota con el hogar de quien mira (AD-03)."""

    score: int
    explicacion: str
    razones: list[str] = Field(default_factory=list)
    incompatible: bool


class PetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organizacion_id: int | None
    user_id: int | None
    report_id: int | None
    nombre: str
    especie: str
    raza: str | None
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
    zona: str
    ciudad_texto: str | None
    barrio: str | None
    lat: float | None
    lng: float | None
    telefono_contacto: str | None
    estado: str
    publicado_en: datetime
    adoptado_en: datetime | None
    # Calculados por el router (patrón `OrganizacionOut.necesidades_pendientes`):
    # el ORM no tiene estos atributos, por eso el default.
    publicador: PublicadorOut | None = None
    afinidad: AfinidadOut | None = None
    es_favorito: bool = False
    ya_solicitada: bool = False
    distancia_km: float | None = None


class PetResumenOut(BaseModel):
    """Tarjeta mínima: franja de celebración y listas de solicitudes."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    especie: str
    raza: str | None
    edad_meses: int
    fotos: list[str]
    estado: str


class AdopcionesResumenOut(BaseModel):
    """La métrica de esperanza del módulo, espejo de `ReunidosResumenOut`."""

    total: int
    recientes: list[PetResumenOut]
