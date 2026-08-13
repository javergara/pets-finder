"""Baja de suscripciones por token (feature 39, ADR 0011).

Es un GET con HTML mínimo porque el destino es un click desde el correo: sin
app, sin login — el token aleatorio ES la autorización (quien tiene el link es
quien recibió el email).
"""

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.suscripcion import Suscripcion
from ..services.db import get_session

router = APIRouter(prefix="/api/suscripciones", tags=["suscripciones"])


def _pagina(titulo: str, mensaje: str, codigo: int) -> HTMLResponse:
    html = f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8"><title>{titulo} | Pet Finder Col</title></head>
<body style="font-family:sans-serif;max-width:32rem;margin:4rem auto;padding:0 1rem;color:#1b1a17">
<h1 style="color:#1f4d3a">{titulo}</h1><p>{mensaje}</p>
<p><a href="/" style="color:#1f4d3a">Volver a Pet Finder Col</a></p>
</body></html>"""
    return HTMLResponse(html, status_code=codigo)


@router.get("/baja/{token}", response_class=HTMLResponse)
def dar_de_baja(token: str, session: Session = Depends(get_session)) -> HTMLResponse:
    suscripcion = session.scalar(select(Suscripcion).where(Suscripcion.token == token))
    if suscripcion is None:
        return _pagina(
            "Este enlace ya no es válido",
            "Puede que ya te hayas dado de baja antes. No te llegarán más avisos de ese reporte.",
            404,
        )

    session.delete(suscripcion)
    session.commit()
    return _pagina(
        "Listo, no te escribimos más", "Quitamos tu correo de los avisos de ese reporte.", 200
    )
