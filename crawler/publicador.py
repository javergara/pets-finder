"""Convierte un PostExtraido en ReportIn de la API y los publica.

Un post con N mascotas produce N reportes que comparten foto, zona, fecha y
url_post, distinguidos por crawl_metadata.indice_mascota (ADR 0010). El
contrato es el REAL: `convertir` construye y valida `ReportIn` (importado de
la API vía crawler/__init__), así una extracción no publicable falla aquí,
localmente y con los mismos mensajes de producto del backend — nunca como un
422 remoto a mitad de corrida.
"""

import re
from datetime import date
from typing import Any

import requests

from reencuentro_api.schemas.report import ReportIn

from .schema import PostExtraido
from .zonas import resolver_zona

MODELO_EXTRACCION = "llamaextract"


def _telefono_saneado(crudo: str | None) -> str | None:
    """Primer teléfono plausible del texto extraído, solo dígitos, o None.

    La columna de la API es String(20) y el número alimenta links wa.me/tel:
    un texto tipo '300 123 4567 / 310 987 6543' debe quedar en el primer
    número, nunca pasar crudo (>20 chars revienta el VARCHAR de Postgres) ni
    concatenado (un "teléfono" de 20 dígitos que no marca a nadie)."""
    if not crudo:
        return None
    primero = re.split(r"[/,;]| y | o ", crudo)[0]
    digitos = re.sub(r"\D", "", primero)
    return digitos if 7 <= len(digitos) <= 15 else None


def convertir(
    post: PostExtraido,
    user_id: int,
    url_post: str | None = None,
    foto_url: str | None = None,
    fecha_fallback: date | None = None,
    clave_post: str | None = None,
    ciudad_fallback: str | None = None,
) -> list[ReportIn]:
    """Devuelve un ReportIn validado por mascota del post.

    Lanza ValidationError (con el copy del backend) si la extracción no es
    publicable — p. ej. sin ningún camino de contacto.

    `ciudad_fallback` cubre el caso común de los pantallazos: el post no dice
    la ciudad, pero quien lo recolectó sí la sabe (el grupo/cuenta es de una
    zona concreta).

    `clave_post` (la clave de dedup: url o sha256 del pantallazo) genera el
    `idempotency_id` de cada reporte (`<clave>#<indice>`): si una corrida muere
    a mitad de publicar y se reintenta, la API devuelve los ya creados en vez
    de duplicarlos."""
    zona, ciudad_texto, lat, lng = resolver_zona(post.ciudad_texto or ciudad_fallback)
    fecha = post.fecha_evento or (fecha_fallback or date.today()).isoformat()
    total = len(post.mascotas)

    # crawl_metadata es una unión discriminada por plataforma (extra=forbid):
    # los campos específicos solo van en su variante; ReportIn valida el dict
    # contra la variante correcta.
    def _metadata(indice: int) -> dict[str, Any]:
        meta: dict[str, Any] = {
            "plataforma": post.plataforma,
            "url_post": url_post,
            "autor_handle": post.autor_handle,
            "fecha_post": post.fecha_evento,
            "modelo_extraccion": MODELO_EXTRACCION,
            "confianza": post.confianza,
            "indice_mascota": indice,
            "total_mascotas": total,
        }
        if post.plataforma == "facebook":
            meta["grupo"] = post.grupo
        elif post.plataforma == "whatsapp":
            meta["nombre_grupo"] = post.grupo
        return meta

    return [
        ReportIn(
            user_id=user_id,
            tipo=mascota.tipo,
            especie=mascota.especie,
            # El LLM puede traer ruido: se aplican aquí las reglas del schema
            # (nombre solo en perdidos, situacion solo en encontrados) para
            # que ninguna extracción rara rebote por un 422 evitable.
            nombre_mascota=mascota.nombre_mascota if mascota.tipo == "perdido" else None,
            raza=mascota.raza,
            color=mascota.color,
            tamano=mascota.tamano,
            descripcion=mascota.descripcion,
            foto_url=foto_url,
            zona=zona,
            ciudad_texto=ciudad_texto,
            barrio=post.barrio,
            lat=lat,
            lng=lng,
            # Sin evidencia de que esté resguardada, lo honesto es "vista".
            situacion=(mascota.situacion or "vista") if mascota.tipo == "encontrado" else None,
            fecha_evento=fecha,
            telefono_contacto=_telefono_saneado(post.telefono),
            fuente="crawl",
            crawl_metadata=_metadata(indice),
            idempotency_id=f"{clave_post}#{indice}" if clave_post else None,
        )
        for indice, mascota in enumerate(post.mascotas)
    ]


def a_json(payloads: list[ReportIn]) -> list[dict[str, Any]]:
    """Forma JSON-serializable (para el registro de dedup y para imprimir)."""
    return [p.model_dump(mode="json") for p in payloads]


def desde_json(crudos: list[dict[str, Any]]) -> list[ReportIn]:
    """Re-valida payloads guardados en el registro de dedup."""
    return [ReportIn.model_validate(c) for c in crudos]


def publicar(payloads: list[ReportIn], api_url: str) -> list[int]:
    """POST de cada payload; devuelve los ids creados. Falla rápido: un 4xx/5xx
    detiene la corrida (mejor un post a medias visible que errores silenciosos)."""
    ids: list[int] = []
    for payload in payloads:
        respuesta = requests.post(
            f"{api_url.rstrip('/')}/api/reports",
            json=payload.model_dump(mode="json"),
            timeout=30,
        )
        respuesta.raise_for_status()
        ids.append(respuesta.json()["id"])
    return ids
