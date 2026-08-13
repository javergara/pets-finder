"""Páginas HTML para los rastreadores de redes sociales (feature 21, ADR 0009).

La SPA sirve el mismo index.html para toda ruta, así que WhatsApp/Facebook ven
una vista previa genérica al compartir un reporte. Un rewrite de Vercel manda
SOLO a los bots (por user-agent) de /reporte/:id a esta ruta, que responde un
HTML mínimo con los og tags del reporte; los humanos siguen recibiendo la SPA.
"""

import os
from html import escape

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from ..models.report import Report
from ..services.db import get_session

router = APIRouter(tags=["paginas"])

ETIQUETA_TIPO = {"perdido": "Se perdió", "encontrado": "Encontrada"}
ETIQUETA_ESPECIE = {"perro": "Perro", "gato": "Gato", "otro": "Otro animal"}


def _sitio() -> str:
    return os.environ.get("SITE_URL", "https://petfinder-col.com").strip().rstrip("/")


@router.get("/reporte/{report_id}", response_class=HTMLResponse)
def pagina_reporte_para_bots(
    report_id: int, session: Session = Depends(get_session)
) -> HTMLResponse:
    report = session.get(Report, report_id)
    if report is None:
        raise HTTPException(404, f"El reporte {report_id} no existe")

    sitio = _sitio()
    nombre = report.nombre_mascota or ETIQUETA_ESPECIE.get(report.especie, "Mascota")
    lugar = report.ciudad_texto if report.zona == "Otro" else report.zona
    titulo = escape(f"{nombre} — {ETIQUETA_TIPO.get(report.tipo, '')} en {lugar or 'Colombia'}")
    descripcion = escape(report.descripcion[:200])
    url = f"{sitio}/reporte/{report.id}"

    if report.foto_url:
        foto = report.foto_url if report.foto_url.startswith("http") else sitio + report.foto_url
        og_imagen = f'<meta property="og:image" content="{escape(foto)}">'
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
