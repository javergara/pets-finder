"""Notificaciones por correo a los suscritos de un reporte (feature 39, ADR 0011).

El envío va por la API HTTP de Resend detrás de dos env vars: sin
`RESEND_API_KEY` el envío es un no-op con log — la app entera funciona igual
(mismo criterio que el resto de config externa: la falta de credenciales nunca
rompe un endpoint). El fallo del proveedor tampoco: quien registra un
avistamiento no tiene la culpa de que el email no salga.
"""

import logging
import os
from html import escape

import requests

from ..models.report import Report
from ..models.suscripcion import Suscripcion
from .titulos import titulo_reporte

logger = logging.getLogger(__name__)

RESEND_URL = "https://api.resend.com/emails"


def _sitio() -> str:
    return os.environ.get("SITE_URL", "https://petfinder-col.com").strip().rstrip("/")


def _enviar_email(destinatario: str, asunto: str, html: str) -> bool:
    """Un email vía Resend. False (con log) si no hay credenciales o falla."""
    api_key = os.environ.get("RESEND_API_KEY", "").strip()
    if not api_key:
        logger.info("RESEND_API_KEY sin configurar: no se envía '%s'", asunto)
        return False

    remitente = os.environ.get("RESEND_FROM", "Pet Finder Col <onboarding@resend.dev>").strip()
    try:
        respuesta = requests.post(
            RESEND_URL,
            json={"from": remitente, "to": [destinatario], "subject": asunto, "html": html},
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=10,
        )
        if respuesta.status_code >= 400:
            logger.warning("Resend respondió %s: %s", respuesta.status_code, respuesta.text[:200])
            return False
        return True
    except requests.RequestException:
        logger.exception("Fallo enviando email vía Resend")
        return False


def notificar_novedad(report: Report, suscripciones: list[Suscripcion], novedad: str) -> None:
    """Avisa a todos los suscritos del reporte; jamás lanza (best-effort)."""
    if not suscripciones:
        return

    sitio = _sitio()
    titulo = titulo_reporte(report)
    asunto = f"Novedades de {titulo} — Pet Finder Col"
    url_reporte = f"{sitio}/reporte/{report.id}"

    for suscripcion in suscripciones:
        baja = f"{sitio}/api/suscripciones/baja/{suscripcion.token}"
        html = (
            f"<p>{escape(novedad)}</p>"
            f'<p><a href="{url_reporte}">Ver el reporte de {escape(titulo)}</a></p>'
            f'<p style="color:#888;font-size:12px">Recibes este correo porque pediste '
            f"novedades de este reporte en Pet Finder Col. "
            f'<a href="{baja}">Dejar de recibir avisos</a></p>'
        )
        try:
            _enviar_email(suscripcion.email, asunto, html)
        except Exception:  # noqa: BLE001 — el aviso jamás rompe el endpoint que lo dispara
            logger.exception("Fallo notificando a un suscrito del reporte %s", report.id)
