"""Subida de la foto de un reporte (multipart).

La extensión del archivo guardado se deriva SIEMPRE del content-type declarado,
nunca del filename del cliente (que es input hostil: podría traer `../` o una
extensión ejecutable). El nombre es un uuid — imposible de adivinar o colisionar.

Destino (ADR 0006): con Supabase configurado la foto va al bucket de Storage y
`foto_url` es una URL pública absoluta; sin configurar (dev local, tests) va al
filesystem bajo `/media/uploads/` exactamente igual que siempre. `UPLOADS_DIR`
se re-exporta como variable de módulo (desde `..media`, la fuente única
compartida con el montaje `/media` de main.py) para que los tests puedan
apuntarla a un `tmp_path` con monkeypatch sin tocar el disco real.
"""

from uuid import uuid4

from fastapi import APIRouter, HTTPException, UploadFile, status

from .. import media
from ..media import UPLOADS_DIR

router = APIRouter(prefix="/api/uploads", tags=["uploads"])

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

    # Lectura por chunks con el límite aplicado durante la lectura: un archivo
    # gigante se rechaza en cuanto excede el máximo, sin bufferizarlo entero.
    partes: list[bytes] = []
    total = 0
    while chunk := await foto.read(_CHUNK_BYTES):
        total += len(chunk)
        if total > MAX_BYTES:
            raise HTTPException(413, "La foto supera el tamaño máximo de 5 MB.")
        partes.append(chunk)
    contenido = b"".join(partes)

    nombre = f"{uuid4().hex}.{extension}"

    if media.supabase_configurado():
        try:
            foto_url = media.subir_a_supabase(nombre, contenido, foto.content_type or "")
        except media.SupabaseError as exc:
            raise HTTPException(502, "No pudimos guardar la foto. Intenta de nuevo.") from exc
        return {"foto_url": foto_url}

    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    (UPLOADS_DIR / nombre).write_bytes(contenido)
    return {"foto_url": f"/media/uploads/{nombre}"}
