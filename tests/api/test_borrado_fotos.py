"""Borrado de la foto al eliminar un registro (feature 20): tolerante a fallos."""

from datetime import date

import pytest

from reencuentro_api import media
from reencuentro_api.models.report import Report
from reencuentro_api.models.user import User

BUCKET_URL = "https://abc123.supabase.co/storage/v1/object/public/fotos"


@pytest.fixture()
def usuario(db_session):
    user = User(nombre="Ana", email="ana@example.co", ciudad="Armenia")
    db_session.add(user)
    db_session.commit()
    return user


def _crear_reporte(db_session, usuario, foto_url):
    reporte = Report(
        user_id=usuario.id,
        tipo="perdido",
        especie="perro",
        nombre_mascota="Rocky",
        descripcion="Criollo color miel",
        foto_url=foto_url,
        zona="Armenia",
        lat=4.54,
        lng=-75.68,
        fecha_evento=date(2026, 8, 10),
        telefono_contacto="3001234567",
    )
    db_session.add(reporte)
    db_session.commit()
    return reporte


@pytest.fixture()
def supabase_activo(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://abc123.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_KEY", "service-key-de-prueba")
    monkeypatch.setenv("SUPABASE_BUCKET", "fotos")


def test_eliminar_reporte_borra_el_objeto_del_bucket(
    client, db_session, usuario, supabase_activo, monkeypatch
):
    reporte = _crear_reporte(db_session, usuario, f"{BUCKET_URL}/mifoto.jpg")
    llamadas = []

    class RespuestaOk:
        status_code = 200

    def fake_delete(url, headers=None, timeout=None):
        llamadas.append((url, headers))
        return RespuestaOk()

    monkeypatch.setattr(media.requests, "delete", fake_delete)

    respuesta = client.delete(f"/api/reports/{reporte.id}?user_id={usuario.id}")

    assert respuesta.status_code == 204
    assert llamadas == [
        (
            "https://abc123.supabase.co/storage/v1/object/fotos/mifoto.jpg",
            {"Authorization": "Bearer service-key-de-prueba"},
        )
    ]


def test_si_el_bucket_falla_el_reporte_se_elimina_igual(
    client, db_session, usuario, supabase_activo, monkeypatch, caplog
):
    reporte = _crear_reporte(db_session, usuario, f"{BUCKET_URL}/mifoto.jpg")

    def fake_delete(url, headers=None, timeout=None):
        raise media.requests.exceptions.ConnectionError("bucket caído")

    monkeypatch.setattr(media.requests, "delete", fake_delete)

    respuesta = client.delete(f"/api/reports/{reporte.id}?user_id={usuario.id}")

    # Nunca un 500 por una foto: 204 y un log del fallo.
    assert respuesta.status_code == 204
    assert client.get(f"/api/reports/{reporte.id}").status_code == 404
    assert any("se elimina igual" in r.message for r in caplog.records)


def test_foto_de_otro_host_no_se_toca(client, db_session, usuario, supabase_activo, monkeypatch):
    reporte = _crear_reporte(db_session, usuario, "https://cdn.example.com/foto.jpg")

    def fake_delete(*args, **kwargs):  # pragma: no cover - no debe llamarse
        raise AssertionError("no debería intentar borrar fotos de otros hosts")

    monkeypatch.setattr(media.requests, "delete", fake_delete)

    assert client.delete(f"/api/reports/{reporte.id}?user_id={usuario.id}").status_code == 204


def test_foto_local_de_uploads_se_borra_del_disco(
    client, db_session, usuario, tmp_path, monkeypatch
):
    monkeypatch.setattr(media, "UPLOADS_DIR", tmp_path)
    archivo = tmp_path / "abc.jpg"
    archivo.write_bytes(b"foto")
    reporte = _crear_reporte(db_session, usuario, "/media/uploads/abc.jpg")

    assert client.delete(f"/api/reports/{reporte.id}?user_id={usuario.id}").status_code == 204
    assert not archivo.exists()


def test_foto_del_seed_no_se_toca(client, db_session, usuario, tmp_path, monkeypatch):
    monkeypatch.setattr(media, "MEDIA_DIR", tmp_path)
    seed_dir = tmp_path / "seed"
    seed_dir.mkdir()
    archivo = seed_dir / "report_1.jpg"
    archivo.write_bytes(b"foto del seed")
    reporte = _crear_reporte(db_session, usuario, "/media/seed/report_1.jpg")

    assert client.delete(f"/api/reports/{reporte.id}?user_id={usuario.id}").status_code == 204
    assert archivo.exists()


def test_sin_foto_no_pasa_nada(client, db_session, usuario):
    reporte = _crear_reporte(db_session, usuario, None)

    assert client.delete(f"/api/reports/{reporte.id}?user_id={usuario.id}").status_code == 204
