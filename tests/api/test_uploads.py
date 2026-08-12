import io

import pytest

from reencuentro_api import media
from reencuentro_api.routers import uploads


@pytest.fixture(autouse=True)
def uploads_en_tmp(tmp_path, monkeypatch):
    """Redirige UPLOADS_DIR a un tmp_path: los tests nunca escriben en data/media/."""
    monkeypatch.setattr(uploads, "UPLOADS_DIR", tmp_path)
    return tmp_path


def _subir(client, contenido: bytes, content_type: str, filename: str = "mi foto.jpg"):
    return client.post(
        "/api/uploads",
        files={"foto": (filename, io.BytesIO(contenido), content_type)},
    )


def test_subir_jpeg_valido_devuelve_201_con_foto_url(client, uploads_en_tmp):
    respuesta = _subir(client, b"bytes-de-una-foto", "image/jpeg")

    assert respuesta.status_code == 201
    foto_url = respuesta.json()["foto_url"]
    assert foto_url.startswith("/media/uploads/")
    assert foto_url.endswith(".jpg")

    archivos = list(uploads_en_tmp.iterdir())
    assert len(archivos) == 1
    assert archivos[0].read_bytes() == b"bytes-de-una-foto"


def test_el_nombre_guardado_es_uuid_no_el_filename_del_cliente(client, uploads_en_tmp):
    respuesta = _subir(client, b"x", "image/png", filename="../../etc/passwd.png")

    nombre = respuesta.json()["foto_url"].rsplit("/", 1)[-1]
    tallo, extension = nombre.rsplit(".", 1)
    # uuid4().hex: 32 caracteres hexadecimales; la extensión sale del content-type.
    assert len(tallo) == 32
    assert int(tallo, 16) >= 0
    assert extension == "png"
    assert "passwd" not in nombre
    # Nada se escribió fuera del directorio de uploads.
    assert [p.name for p in uploads_en_tmp.iterdir()] == [nombre]


def test_content_type_no_permitido_devuelve_415_en_espanol(client, uploads_en_tmp):
    respuesta = _subir(client, b"GIF89a...", "image/gif")

    assert respuesta.status_code == 415
    assert "JPEG, PNG o WebP" in respuesta.json()["detail"]
    assert list(uploads_en_tmp.iterdir()) == []


def test_archivo_de_mas_de_5mb_devuelve_413_y_no_deja_restos(client, uploads_en_tmp):
    contenido = b"0" * (5 * 1024 * 1024 + 1)

    respuesta = _subir(client, contenido, "image/jpeg")

    assert respuesta.status_code == 413
    assert "5 MB" in respuesta.json()["detail"]
    # El archivo a medias se borró.
    assert list(uploads_en_tmp.iterdir()) == []


def test_webp_valido_tambien_se_acepta(client, uploads_en_tmp):
    respuesta = _subir(client, b"RIFF....WEBP", "image/webp", filename="foto.webp")

    assert respuesta.status_code == 201
    assert respuesta.json()["foto_url"].endswith(".webp")


def test_uploads_dir_es_subdirectorio_del_media_montado():
    """Regresión del hallazgo del revisor (feature 03): uploads.py calculaba la raíz
    del repo con su propio `parents[3]` — al vivir un nivel más profundo que main.py
    resolvía a `src/` y las fotos se guardaban FUERA del directorio servido en /media
    (201 con un foto_url que daba 404). Ambas rutas deben salir de la misma fuente."""
    assert media.UPLOADS_DIR == media.MEDIA_DIR / "uploads"
    assert media.MEDIA_DIR == media.REPO_ROOT / "data" / "media"
    # La raíz calculada es de verdad la raíz del repo (contiene init.sh).
    assert (media.REPO_ROOT / "init.sh").exists()


def test_con_supabase_configurado_la_foto_va_al_bucket_y_no_al_disco(
    client, uploads_en_tmp, monkeypatch
):
    """ADR 0006: con SUPABASE_URL/SUPABASE_SERVICE_KEY la foto sube al bucket
    (POST a la API de Storage mockeado) y foto_url es la URL pública absoluta."""
    monkeypatch.setenv("SUPABASE_URL", "https://abc123.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_KEY", "service-key-de-prueba")
    llamadas = []

    def fake_post(url, data=None, headers=None, timeout=None):
        llamadas.append({"url": url, "data": data, "headers": headers})

        class Respuesta:
            status_code = 200

        return Respuesta()

    monkeypatch.setattr(media.requests, "post", fake_post)

    respuesta = _subir(client, b"bytes-al-bucket", "image/jpeg")

    assert respuesta.status_code == 201
    foto_url = respuesta.json()["foto_url"]
    assert foto_url.startswith("https://abc123.supabase.co/storage/v1/object/public/fotos/")
    assert foto_url.endswith(".jpg")
    # El POST fue al bucket con el contenido y la autorización correctos.
    assert llamadas[0]["url"].startswith("https://abc123.supabase.co/storage/v1/object/fotos/")
    assert llamadas[0]["data"] == b"bytes-al-bucket"
    assert llamadas[0]["headers"]["Authorization"] == "Bearer service-key-de-prueba"
    assert llamadas[0]["headers"]["Content-Type"] == "image/jpeg"
    # Nada tocó el disco local.
    assert list(uploads_en_tmp.iterdir()) == []


def test_si_supabase_falla_responde_502_en_espanol(client, uploads_en_tmp, monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://abc123.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_KEY", "service-key-de-prueba")

    def fake_post(*args, **kwargs):
        class Respuesta:
            status_code = 403

        return Respuesta()

    monkeypatch.setattr(media.requests, "post", fake_post)

    respuesta = _subir(client, b"x", "image/jpeg")

    assert respuesta.status_code == 502
    assert "No pudimos guardar la foto" in respuesta.json()["detail"]
    assert list(uploads_en_tmp.iterdir()) == []


def test_foto_subida_es_servible_bajo_media(client, monkeypatch):
    """Ciclo completo sin monkeypatch de directorio: la foto subida por el endpoint
    real debe responder 200 en el GET de su propio foto_url (montaje estático)."""
    monkeypatch.setattr(uploads, "UPLOADS_DIR", media.UPLOADS_DIR)

    respuesta = _subir(client, b"bytes-servibles", "image/jpeg")
    assert respuesta.status_code == 201
    foto_url = respuesta.json()["foto_url"]

    archivo_en_disco = media.UPLOADS_DIR / foto_url.rsplit("/", 1)[-1]
    try:
        descarga = client.get(foto_url)
        assert descarga.status_code == 200
        assert descarga.content == b"bytes-servibles"
    finally:
        archivo_en_disco.unlink(missing_ok=True)
