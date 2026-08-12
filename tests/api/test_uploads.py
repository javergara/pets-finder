import io

import pytest

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
