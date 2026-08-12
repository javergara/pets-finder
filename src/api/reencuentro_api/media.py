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
    así los tests pueden activarla/desactivarla con monkeypatch.setenv."""
    url = os.environ.get("SUPABASE_URL", "").rstrip("/")
    key = os.environ.get("SUPABASE_SERVICE_KEY", "")
    if not url or not key:
        return None
    bucket = os.environ.get("SUPABASE_BUCKET", "fotos")
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
