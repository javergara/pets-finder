"""Páginas HTML para los rastreadores de redes sociales (feature 21, ADR 0009).

La SPA sirve el mismo index.html para toda ruta, así que WhatsApp/Facebook ven
una vista previa genérica al compartir un reporte. Un rewrite de Vercel manda
SOLO a los bots (por user-agent) de /reporte/:id a esta ruta, que responde un
HTML mínimo con los og tags del reporte; los humanos siguen recibiendo la SPA.

Desde AD-08 pasa lo mismo con /adoptar/mascota/:id. Regla común a todas las
páginas de este módulo: **todo lo que escribió una persona va por `escape`**.
Es HTML que servimos a terceros y un `"` sin escapar cierra el atributo.
"""

import os
import re
from html import escape

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models.pet import Pet
from ..models.report import Report
from ..services.db import get_session
from ..services.titulos import titulo_pet, titulo_reporte

router = APIRouter(tags=["paginas"])

ETIQUETA_TIPO = {"perdido": "Se perdió", "encontrado": "Encontrada"}


def _sitio() -> str:
    return os.environ.get("SITE_URL", "https://petfinder-col.com").strip().rstrip("/")


# Una foto del bucket propio: cualquier host, ruta pública del bucket `fotos`.
# El nombre no lleva `/` ni query (es un uuid + extensión, uploads.py lo fija).
_FOTO_BUCKET = re.compile(r"^https?://[^/]+/storage/v1/object/public/fotos/([^/?#]+)$")


def _absoluta(ruta: str, sitio: str) -> str:
    """Las fotos llegan de dos sitios: Supabase Storage las da absolutas
    (`https://…`) y las locales/del seed relativas (`/media/…`). Ningún
    rastreador resuelve una relativa, así que la de casa se absolutiza con
    `SITE_URL` y la de fuera se deja intacta.

    Las del bucket propio se reescriben a `{sitio}/fotos/{nombre}` (feature 49):
    el rewrite de vercel.json las sirve desde el dominio con caché larga, y el
    rastreador de WhatsApp/Facebook —que descarga la og:image en cada
    compartida— deja de gastar egress del bucket."""
    bucket = _FOTO_BUCKET.match(ruta)
    if bucket:
        return f"{sitio}/fotos/{bucket.group(1)}"
    return ruta if ruta.startswith("http") else sitio + ruta


@router.get("/reporte/{report_id}", response_class=HTMLResponse)
def pagina_reporte_para_bots(
    report_id: int, session: Session = Depends(get_session)
) -> HTMLResponse:
    report = session.get(Report, report_id)
    if report is None:
        raise HTTPException(404, f"El reporte {report_id} no existe")

    sitio = _sitio()
    nombre = titulo_reporte(report)
    lugar = report.ciudad_texto if report.zona == "Otro" else report.zona
    titulo = escape(f"{nombre} — {ETIQUETA_TIPO.get(report.tipo, '')} en {lugar or 'Colombia'}")
    descripcion = escape(report.descripcion[:200])
    url = f"{sitio}/reporte/{report.id}"

    if report.foto_url:
        foto = escape(_absoluta(report.foto_url, sitio))
        og_imagen = f'<meta property="og:image" content="{foto}">'
    else:
        og_imagen = ""

    html = f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>{titulo} | Pet Finder Col</title>
<meta property="og:type" content="website">
<meta property="og:site_name" content="Pet Finder Col">
<meta property="og:title" content="{titulo}">
<meta property="og:description" content="{descripcion}">
<meta property="og:url" content="{url}">
{og_imagen}
<meta name="twitter:card" content="summary_large_image">
</head>
<body>
<p><a href="{url}">Ver el reporte de {titulo} en Pet Finder Col</a></p>
</body>
</html>"""
    return HTMLResponse(html)


# El estado que se anuncia al compartir (AD-08). `en_proceso` se comparte como
# "En adopción" a propósito: es un matiz interno entre quien publica y quien ya
# solicitó, y a quien recibe el link no le aporta nada — la mascota todavía puede
# ser suya. "adoptado" sí cambia el copy: anunciar "En adopción" una mascota que
# ya tiene hogar manda gente a escribir en vano y quema la confianza del sitio.
ETIQUETA_ESTADO_ADOPCION = {
    "disponible": "En adopción",
    "en_proceso": "En adopción",
    "adoptado": "Ya tiene hogar",
}


@router.get("/adoptar/mascota/{pet_id}", response_class=HTMLResponse)
def pagina_mascota_para_bots(pet_id: int, session: Session = Depends(get_session)) -> HTMLResponse:
    """Calcada de `pagina_reporte_para_bots`: mismo rewrite por user-agent en
    vercel.json, mismas etiquetas, mismo escapado. Lo que cambia es de dónde
    salen el título (`titulo_pet`), la foto (la primera de `fotos`) y el estado."""
    pet = session.get(Pet, pet_id)
    if pet is None:
        raise HTTPException(404, f"La mascota {pet_id} no existe")

    sitio = _sitio()
    nombre = titulo_pet(pet)
    # Mismo criterio que `MascotaCard`: con zona "Otro" el lugar lo dice la
    # ciudad que escribió quien publica.
    lugar = pet.ciudad_texto if pet.zona == "Otro" else pet.zona
    estado = ETIQUETA_ESTADO_ADOPCION.get(pet.estado, "En adopción")
    titulo = escape(f"{nombre} — {estado} en {lugar or 'Colombia'}")
    descripcion = escape(pet.historia[:200])
    url = f"{sitio}/adoptar/mascota/{pet.id}"

    fotos = pet.fotos or []
    if fotos:
        foto = escape(_absoluta(fotos[0], sitio))
        og_imagen = f'<meta property="og:image" content="{foto}">'
    else:
        # Sin foto no va la etiqueta: un `og:image` vacío pinta un hueco roto.
        og_imagen = ""

    html = f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>{titulo} | Pet Finder Col</title>
<meta property="og:type" content="website">
<meta property="og:site_name" content="Pet Finder Col">
<meta property="og:title" content="{titulo}">
<meta property="og:description" content="{descripcion}">
<meta property="og:url" content="{url}">
{og_imagen}
<meta name="twitter:card" content="summary_large_image">
</head>
<body>
<p><a href="{url}">Conoce a {titulo} en Pet Finder Col</a></p>
</body>
</html>"""
    return HTMLResponse(html)


# Slugs de las landings por zona (feature 46) — espejo de lib/ciudades.ts.
SLUG_ZONAS = {
    "cali": "Cali",
    "armenia": "Armenia",
    "pereira": "Pereira",
    "manizales": "Manizales",
    "quibdo": "Quibdó",
    "bogota": "Bogotá",
    "medellin": "Medellín",
}


def pagina_zona_para_bots(slug: str, session: Session) -> HTMLResponse:
    """og tags de la landing de zona (feature 46). El rewrite por user-agent de
    vercel.json conserva el path original (/cali, /armenia, …), así que cada
    slug se registra como ruta explícita más abajo — nunca un catch-all que
    eclipse al resto de la API."""
    zona = SLUG_ZONAS.get(slug.lower())
    if zona is None:
        raise HTTPException(404, f"No hay landing para '{slug}'")

    query = (
        select(Report.tipo, func.count())
        .where(Report.estado == "activo", Report.zona == zona)
        .group_by(Report.tipo)
    )
    filas = dict(session.execute(query).all())
    perdidos, encontrados = filas.get("perdido", 0), filas.get("encontrado", 0)

    sitio = _sitio()
    titulo = escape(f"Mascotas perdidas y encontradas en {zona}")
    descripcion = escape(
        f"Ahora mismo la comunidad busca a {perdidos} mascotas perdidas y cuida "
        f"{encontrados} encontradas en {zona}. Reporta, busca por descripción y "
        "contacta directo por WhatsApp."
    )
    url = f"{sitio}/{slug.lower()}"

    html = f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>{titulo} | Pet Finder Col</title>
<meta name="description" content="{descripcion}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Pet Finder Col">
<meta property="og:title" content="{titulo}">
<meta property="og:description" content="{descripcion}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{sitio}/og-image.png">
</head>
<body><p>{titulo} — Pet Finder Col. <a href="{url}">{url}</a></p></body>
</html>"""
    return HTMLResponse(html)


def _ruta_zona(slug: str):
    def handler(session: Session = Depends(get_session)) -> HTMLResponse:
        return pagina_zona_para_bots(slug, session)

    return handler


for _slug in SLUG_ZONAS:
    router.add_api_route(
        f"/{_slug}", _ruta_zona(_slug), methods=["GET"], response_class=HTMLResponse
    )
