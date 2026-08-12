"""Esquema de extracción: qué campos saca el LLM de un pantallazo de redes.

Las descripciones de los campos NO son documentación pasiva: LlamaExtract las
usa como instrucciones de extracción, por eso están redactadas como reglas.
Los valores de especie/raza/color/tamaño deben coincidir con el catálogo del
frontend (src/web/src/lib/caracteristicas.ts) para que los filtros matcheen.
"""

from typing import Literal

from pydantic import BaseModel, Field


class MascotaExtraida(BaseModel):
    tipo: Literal["perdido", "encontrado"] = Field(
        description=(
            "'perdido' si la publicación la hace la familia buscando a su mascota; "
            "'encontrado' si alguien reporta una mascota que vio o rescató."
        )
    )
    especie: Literal["perro", "gato", "otro"]
    nombre_mascota: str | None = Field(
        default=None,
        description=(
            "Nombre propio de la mascota SOLO si la publicación lo dice (típico en perdidos)."
        ),
    )
    raza: str | None = Field(
        default=None,
        description=(
            "Raza si es reconocible, con estos valores exactos cuando apliquen: "
            "'Criollo / mestizo', 'Labrador', 'Beagle', 'Siamés'. Si no está claro, null."
        ),
    )
    color: str | None = Field(
        default=None,
        description=(
            "Color del PELAJE del animal (nunca el del collar, pañoleta o accesorios), "
            "uno de: 'Negro', 'Blanco', 'Café', 'Miel / dorado', 'Gris', 'Naranja', "
            "'Atigrado', 'Bicolor (manchas)', 'Tricolor', 'Otro'. Si no se ve, null."
        ),
    )
    tamano: Literal["pequeño", "mediano", "grande"] | None = None
    situacion: Literal["conmigo", "vista"] | None = Field(
        default=None,
        description=(
            "Solo para 'encontrado': 'conmigo' si quien publica tiene a la mascota resguardada, "
            "'vista' si solo la vio. Si no se puede saber, null."
        ),
    )
    descripcion: str = Field(
        description=(
            "Las señas de ESTA mascota según el TEXTO de la publicación (collar, "
            "manchas, comportamiento, dónde exactamente se vio/perdió), más rasgos "
            "físicos distintivos visibles en la foto que sirvan para reconocerla. "
            "SIEMPRE en español (es-CO), aunque la publicación esté en otro idioma. "
            "NUNCA describas la escena o composición de la foto (el fondo, el mueble "
            "donde está echada, la pose): eso no ayuda a reconocerla en la calle."
        )
    )


class PostExtraido(BaseModel):
    """Resultado de extraer un pantallazo completo (puede traer varias mascotas)."""

    es_publicacion: bool = Field(
        description=(
            "true si la imagen es una publicación de redes con texto (caption, "
            "interfaz de la app, texto sobre la foto); false si es SOLO una foto "
            "del animal sin ningún texto. Sin texto no hay señal confiable de "
            "tipo, nombre ni contacto: no inventes esos campos."
        )
    )

    plataforma: Literal["instagram", "facebook", "whatsapp", "x", "tiktok", "desconocida"] = Field(
        description=(
            "Plataforma reconocible por la interfaz del pantallazo (red social o "
            "mensajería). Pistas: una barra 'Responder' o 'Enviar mensaje…' al pie "
            "es una historia de Instagram; burbujas verdes son WhatsApp; 'Me gusta/"
            "Comentar/Compartir' es Facebook. Si de verdad no se distingue, 'desconocida'."
        )
    )
    autor_handle: str | None = Field(
        default=None,
        description=(
            "Usuario/cuenta que publicó (sin @). Suele ser lo más legible del pantallazo: "
            "extráelo siempre que se vea, aunque no se pueda leer nada más. Si es una "
            "historia que comparte un post de otra cuenta, prefiere la cuenta ORIGINAL "
            "(la del post compartido), que es la de la familia de la mascota."
        ),
    )
    grupo: str | None = Field(
        default=None,
        description=(
            "SOLO para Facebook o WhatsApp: nombre del grupo/comunidad donde se "
            "publicó (p. ej. 'Mascotas Perdidas Cali'), si el pantallazo lo muestra."
        ),
    )
    telefono: str | None = Field(
        default=None,
        description="Teléfono de contacto SI aparece en el texto o la imagen (solo dígitos).",
    )
    ciudad_texto: str | None = Field(
        default=None,
        description="Ciudad o municipio mencionado en la publicación (p. ej. 'Cali', 'Armenia').",
    )
    barrio: str | None = Field(
        default=None,
        description="Barrio, sector o punto de referencia mencionado (p. ej. 'Ciudad Jardín').",
    )
    fecha_evento: str | None = Field(
        default=None,
        description=(
            "Fecha en que se perdió/encontró en formato YYYY-MM-DD si la publicación la menciona."
        ),
    )
    mascotas: list[MascotaExtraida] = Field(
        description=(
            "Una entrada POR CADA mascota individualizable (se distingue en la foto o el texto "
            "la describe por separado). Si es un grupo genérico sin individuos distinguibles "
            "('rescatamos 15 perritos'), UNA sola entrada colectiva que lo diga en la descripción."
        )
    )
    confianza: float = Field(
        ge=0.0,
        le=1.0,
        description="Confianza global de la extracción entre 0 y 1 (legibilidad del pantallazo).",
    )
