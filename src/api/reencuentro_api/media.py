"""Media: rutas locales y almacenamiento remoto en Supabase Storage (ADR 0006).

Rutas locales — fuente única para el montaje estático y el endpoint de uploads:
`main.py` monta `/media` sirviendo `MEDIA_DIR`; `routers/uploads.py` escribe en
`UPLOADS_DIR` (su subdirectorio `uploads/`). Definirlas juntas aquí evita que
cada módulo calcule la raíz del repo por su cuenta con un `parents[N]` distinto
— exactamente el bug que encontró el revisor de la feature 03 (uploads.py está
un nivel más profundo que main.py y guardaba fuera del directorio servido).

Supabase Storage — en despliegue la API no tiene disco (render.yaml sin volumen):
si `SUPABASE_URL` + `SUPABASE_SERVICE_KEY` están en el entorno, las fotos (de
uploads y del seed) suben al bucket vía la API REST de Storage y se guardan como
URL pública absoluta. Sin esas variables (dev local, tests), todo sigue en el
filesystem exactamente igual que antes. Se usa `requests` directo — el flujo es
un solo POST, no amerita el SDK de supabase-py.
"""

import os
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).resolve().parents[3]
MEDIA_DIR = REPO_ROOT / "data" / "media"
UPLOADS_DIR = MEDIA_DIR / "uploads"

_SUPABASE_TIMEOUT_SECONDS = 10


class SupabaseError(Exception):
    """El bucket rechazó la subida (config inválida, bucket inexistente, red)."""


def _config_supabase() -> tuple[str, str, str] | None:
    """Lee la config del entorno en el momento de la llamada (no al importar):
    así los tests pueden activarla/desactivarla con monkeypatch.setenv.

    Todo se pasa por .strip(): las env vars pegadas a mano en el dashboard de
    Vercel pueden traer espacios accidentales — pasó en producción y el espacio
    inicial de SUPABASE_URL se colaba en cada foto_url generada.
    """
    url = os.environ.get("SUPABASE_URL", "").strip().rstrip("/")
    # SUPABASE_SERVICE_ROLE_KEY es el nombre que inyecta la integración
    # Vercel×Supabase del Marketplace; SUPABASE_SERVICE_KEY, el nuestro.
    key = (
        os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
    ).strip()
    if not url or not key:
        return None
    bucket = os.environ.get("SUPABASE_BUCKET", "fotos").strip()
    return url, key, bucket


def supabase_configurado() -> bool:
    return _config_supabase() is not None


def subir_a_supabase(nombre: str, contenido: bytes, content_type: str) -> str:
    """Sube el archivo al bucket y devuelve su URL pública absoluta.

    `x-upsert: true` hace la operación idempotente (el seed puede re-correrse
    sin chocar con archivos ya subidos).
    """
    config = _config_supabase()
    if config is None:
        raise SupabaseError("Supabase no está configurado (SUPABASE_URL/SUPABASE_SERVICE_KEY)")
    url, key, bucket = config

    respuesta = requests.post(
        f"{url}/storage/v1/object/{bucket}/{nombre}",
        data=contenido,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": content_type,
            "x-upsert": "true",
        },
        timeout=_SUPABASE_TIMEOUT_SECONDS,
    )
    if respuesta.status_code not in (200, 201):
        raise SupabaseError(f"Supabase Storage respondió {respuesta.status_code} al subir {nombre}")

    return f"{url}/storage/v1/object/public/{bucket}/{nombre}"


def borrar_foto(foto_url: str | None) -> None:
    """Borra la foto asociada a un registro eliminado (feature 20) — tolerante.

    NUNCA lanza: si el borrado falla (bucket caído, archivo ya inexistente,
    URL de otro host), se loguea y la eliminación del registro sigue — una foto
    huérfana es aceptable, un 500 al eliminar no. Las fotos del seed
    (/media/seed/) no se tocan: son regenerables y compartidas.
    """
    import logging

    logger = logging.getLogger("reencuentro")
    if not foto_url:
        return

    try:
        config = _config_supabase()
        if foto_url.startswith("http"):
            if config is None:
                logger.warning("No se borra %s: Supabase sin configurar", foto_url)
                return
            url, key, bucket = config
            prefijo = f"{url}/storage/v1/object/public/{bucket}/"
            if not foto_url.startswith(prefijo):
                logger.warning("No se borra %s: no es del bucket propio", foto_url)
                return
            nombre = foto_url[len(prefijo) :]
            respuesta = requests.delete(
                f"{url}/storage/v1/object/{bucket}/{nombre}",
                headers={"Authorization": f"Bearer {key}"},
                timeout=_SUPABASE_TIMEOUT_SECONDS,
            )
            if respuesta.status_code not in (200, 204):
                logger.warning("Supabase respondió %s al borrar %s", respuesta.status_code, nombre)
        elif foto_url.startswith("/media/uploads/"):
            archivo = UPLOADS_DIR / Path(foto_url).name
            archivo.unlink(missing_ok=True)
        # /media/seed/ y cualquier otra ruta: intocables a propósito.
    except Exception:  # noqa: BLE001 — tolerancia total por diseño (ver docstring)
        logger.exception("Fallo borrando la foto %s; el registro se elimina igual", foto_url)
