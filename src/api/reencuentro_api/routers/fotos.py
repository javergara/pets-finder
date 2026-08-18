"""Proxy de fotos del bucket con caché en el edge de Vercel (feature 49).

Por qué existe: el egress del bucket agotó la cuota free de Supabase (aviso
Fair Use del 2026-08-18). El primer intento fue un rewrite estático de
vercel.json directo al bucket, pero Supabase sirve el `cache-control` desde la
metadata S3 del objeto —fijada solo al subir— y el edge de Vercel no cachea un
rewrite externo cuyo origen responde `no-cache`. Servir la foto desde esta
función sí funciona siempre: Vercel cachea las respuestas de funciones que
mandan `s-maxage`, sin importar qué diga el bucket.

Cada MISS del edge cuesta una invocación + una descarga del bucket; cada HIT es
gratis y no toca Supabase. Con nombres uuid inmutables, un año de caché es
seguro: un archivo jamás cambia de contenido bajo el mismo nombre (y por eso
mismo NUNCA se debe usar `x-upsert` para reemplazar bytes bajo un nombre vivo).
"""

import requests as http
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from ..media import _config_supabase

router = APIRouter(tags=["fotos"])

_TIMEOUT_SECONDS = 30
CACHE_INMUTABLE = "public, max-age=31536000, s-maxage=31536000, immutable"


# GET y HEAD: FastAPI no registra HEAD solo por declarar GET (daba 405) y
# algunos rastreadores hacen HEAD antes de descargar la og:image. Starlette
# recorta el body en el HEAD; los headers salen iguales.
@router.api_route("/fotos/{nombre}", methods=["GET", "HEAD"])
def foto_del_bucket(nombre: str) -> Response:
    """Sirve una foto del bucket `fotos` con caché larga.

    `nombre` es un path param de un solo segmento: FastAPI no matchea `/` en él,
    así que no hay traversal posible hacia otros buckets o rutas de Storage.

    En dev/tests no hay Supabase configurado y las fotos locales viven bajo
    `/media/...` (mediaUrl nunca produce `/fotos/...` para ellas): un 404 aquí
    es el comportamiento honesto, no un error a medias.
    """
    config = _config_supabase()
    if config is None:
        raise HTTPException(404, "El bucket de fotos no está configurado")
    url, _key, bucket = config

    r = http.get(
        f"{url}/storage/v1/object/public/{bucket}/{nombre}",
        timeout=_TIMEOUT_SECONDS,
    )
    if r.status_code != 200:
        raise HTTPException(404, f"La foto {nombre} no existe")

    return Response(
        content=r.content,
        media_type=r.headers.get("content-type", "image/jpeg"),
        headers={"Cache-Control": CACHE_INMUTABLE},
    )
