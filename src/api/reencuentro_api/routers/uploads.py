"""Subida de la foto de un reporte (multipart).

La extensión del archivo guardado se deriva SIEMPRE del content-type declarado,
nunca del filename del cliente (que es input hostil: podría traer `../` o una
extensión ejecutable). El nombre es un uuid — imposible de adivinar o colisionar.

`UPLOADS_DIR` es una variable de módulo para que los tests puedan apuntarla a un
`tmp_path` con monkeypatch sin tocar el disco real.
"""

from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, HTTPException, UploadFile, status

router = APIRouter(prefix="/api/uploads", tags=["uploads"])

REPO_ROOT = Path(__file__).resolve().parents[3]
UPLOADS_DIR = REPO_ROOT / "data" / "media" / "uploads"

EXTENSION_POR_CONTENT_TYPE = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}
MAX_BYTES = 5 * 1024 * 1024
_CHUNK_BYTES = 256 * 1024


@router.post("", status_code=status.HTTP_201_CREATED)
async def subir_foto(foto: UploadFile) -> dict[str, str]:
    extension = EXTENSION_POR_CONTENT_TYPE.get(foto.content_type or "")
    if extension is None:
        raise HTTPException(415, "Formato de imagen no soportado. Sube una foto JPEG, PNG o WebP.")

    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    destino = UPLOADS_DIR / f"{uuid4().hex}.{extension}"

    # Lectura por chunks: el límite de tamaño se aplica sin cargar el archivo
    # completo en memoria, y si se supera se borra lo escrito a medias.
    total = 0
    try:
        with destino.open("wb") as archivo:
            while chunk := await foto.read(_CHUNK_BYTES):
                total += len(chunk)
                if total > MAX_BYTES:
                    raise HTTPException(413, "La foto supera el tamaño máximo de 5 MB.")
                archivo.write(chunk)
    except HTTPException:
        destino.unlink(missing_ok=True)
        raise

    return {"foto_url": f"/media/uploads/{destino.name}"}
