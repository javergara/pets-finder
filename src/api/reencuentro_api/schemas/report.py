from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ..services.ciudades import ZONA_OTRO, zona_valida

Tipo = Literal["perdido", "encontrado"]
Especie = Literal["perro", "gato", "otro"]
Situacion = Literal["conmigo", "vista"]
Tamano = Literal["pequeño", "mediano", "grande"]
Fuente = Literal["manual", "crawl"]


class _CrawlMetadataBase(BaseModel):
    """Procedencia de un reporte creado por el crawler de redes (ADR 0010).

    Campos comunes a toda plataforma; cada una aporta los suyos en su variante
    de la unión discriminada por `plataforma` (lo que da Instagram no es lo que
    da Facebook — y no todo origen es una red social: WhatsApp es mensajería).
    Todos los campos son texto/números planos (JSON-serializables tal cual): la
    columna `Report.crawl_metadata` guarda este objeto como JSON. Un mismo post
    puede producir varios reportes (varias mascotas en un pantallazo): comparten
    `url_post` y se distinguen por `indice_mascota`.

    `extra="forbid"`: un campo fuera de la variante correcta es un 422, no un
    descarte silencioso — la unión pierde el sentido si acepta cualquier cosa.
    """

    model_config = ConfigDict(extra="forbid")

    url_post: str | None = None
    autor_handle: str | None = None  # a veces lo único legible del pantallazo
    fecha_post: str | None = None  # ISO "YYYY-MM-DD" (str para ser JSON-safe)
    texto_original: str | None = None
    modelo_extraccion: str | None = None
    confianza: float | None = Field(default=None, ge=0.0, le=1.0)
    indice_mascota: int = 0
    total_mascotas: int = 1

    @field_validator("url_post")
    @classmethod
    def validar_url_post(cls, v: str | None) -> str | None:
        # La UI renderiza url_post como href y el POST es público sin auth:
        # solo URLs http(s) absolutas — nunca javascript:, data:, etc.
        if v is not None and not v.startswith(("https://", "http://")):
            raise ValueError("'url_post' debe ser una URL http(s) absoluta")
        return v

    def tiene_origen(self) -> bool:
        """¿Hay un camino de vuelta a la publicación o a quien publicó?

        Es lo que hace contactable a un reporte crawleado sin teléfono: la URL
        del post, o al menos la cuenta que lo publicó."""
        return bool((self.url_post or "").strip() or (self.autor_handle or "").strip())


class CrawlInstagram(_CrawlMetadataBase):
    plataforma: Literal["instagram"]


class CrawlFacebook(_CrawlMetadataBase):
    plataforma: Literal["facebook"]
    # Los posts de mascotas en Facebook viven en grupos ("Mascotas Perdidas
    # Cali"): el nombre es señal de zona y un camino para encontrar el post
    # aunque el pantallazo no deje leer la URL.
    grupo: str | None = None


class CrawlWhatsApp(_CrawlMetadataBase):
    plataforma: Literal["whatsapp"]
    # Las cadenas de WhatsApp no tienen URL: el nombre del grupo/comunidad es
    # muchas veces la única pista de origen del pantallazo.
    nombre_grupo: str | None = None


class CrawlX(_CrawlMetadataBase):
    plataforma: Literal["x"]


class CrawlTikTok(_CrawlMetadataBase):
    plataforma: Literal["tiktok"]


class CrawlPlataformaDesconocida(_CrawlMetadataBase):
    # "desconocida", no "otra": el pantallazo no deja ver de dónde salió el
    # post. Una plataforma reconocible que no esté en el catálogo merece su
    # propia variante, no un bucket genérico.
    plataforma: Literal["desconocida"]


CrawlMetadata = Annotated[
    CrawlInstagram
    | CrawlFacebook
    | CrawlWhatsApp
    | CrawlX
    | CrawlTikTok
    | CrawlPlataformaDesconocida,
    Field(discriminator="plataforma"),
]


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
    telefono_contacto: str | None = None
    fuente: Fuente = "manual"
    crawl_metadata: CrawlMetadata | None = None
    # Clave de idempotencia opcional (ADR 0010): mismo valor → mismo reporte,
    # nunca un duplicado. La usa el crawler para que sus retries sean seguros.
    idempotency_id: str | None = Field(default=None, max_length=300)

    @model_validator(mode="after")
    def validar_condicionales(self) -> "ReportIn":
        """Reglas que dependen del `tipo` (ADR 0005 §2) y de la `fuente` (ADR 0010).

        - `situacion` es obligatoria en "encontrado" y no aplica en "perdido".
        - `nombre_mascota` solo aplica en "perdido" (quien encuentra no lo conoce).
        - `zona` debe ser una de las conocidas u "Otro" (y "Otro" exige `ciudad_texto`).
        - Con fuente "manual" el teléfono sigue siendo obligatorio y no hay metadata.
        - Con fuente "crawl" la metadata es obligatoria, y sin teléfono se exige al
          menos `url_post` o `autor_handle` — el reporte necesita algún camino de
          contacto o no sirve para reunir a nadie.
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
        sin_telefono = not (self.telefono_contacto or "").strip()
        if self.fuente == "manual":
            if self.crawl_metadata is not None:
                raise ValueError("'crawl_metadata' solo aplica a reportes con fuente 'crawl'")
            if sin_telefono:
                raise ValueError("El teléfono de contacto es obligatorio")
        else:
            if self.crawl_metadata is None:
                raise ValueError("Un reporte con fuente 'crawl' necesita 'crawl_metadata'")
            if sin_telefono and not self.crawl_metadata.tiene_origen():
                raise ValueError(
                    "Un reporte 'crawl' sin teléfono necesita un camino de contacto en "
                    "crawl_metadata (la URL de la publicación o la cuenta que la publicó): "
                    "sin eso el reporte no reúne a nadie"
                )
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
    # Edición completa (feature 29): características y ubicación del pin.
    # La zona NO se edita (cambiaría el encuadre del mapa y las coincidencias;
    # para eso: eliminar y re-crear el reporte).
    raza: str | None = None
    color: str | None = None
    tamano: Tamano | None = None
    lat: float | None = None
    lng: float | None = None


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
    telefono_contacto: str | None
    fuente: str
    crawl_metadata: dict | None
    idempotency_id: str | None
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


class SightingIn(BaseModel):
    """Avistamiento de un tercero (feature 28): pin + fecha + comentario.

    Sin user_id a propósito: avisar no requiere registro. `nombre` es opcional
    para que quien avisa pueda identificarse ante la familia.
    """

    lat: float
    lng: float
    fecha: date
    comentario: str = Field(min_length=1, max_length=200)
    nombre: str | None = Field(default=None, max_length=80)


class SightingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    report_id: int
    lat: float
    lng: float
    fecha: date
    comentario: str
    nombre: str | None
    creado_en: datetime


class ConteosOut(BaseModel):
    """Reportes activos por tipo (feature 34): la dimensión del problema, en vivo."""

    perdidos: int
    encontrados: int
