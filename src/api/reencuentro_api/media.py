"""Rutas de media: fuente única para el montaje estático y el endpoint de uploads.

`main.py` monta `/media` sirviendo `MEDIA_DIR`; `routers/uploads.py` escribe en
`UPLOADS_DIR` (su subdirectorio `uploads/`). Definirlas juntas aquí evita que
cada módulo calcule la raíz del repo por su cuenta con un `parents[N]` distinto
— exactamente el bug que encontró el revisor de la feature 03 (uploads.py está
un nivel más profundo que main.py y guardaba fuera del directorio servido).
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
MEDIA_DIR = REPO_ROOT / "data" / "media"
UPLOADS_DIR = MEDIA_DIR / "uploads"
