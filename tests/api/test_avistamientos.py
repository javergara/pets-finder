"""Avistamientos de terceros (feature 28): "la vi por aquí" sin registro."""

from datetime import date

import pytest

from reencuentro_api.models.report import Report
from reencuentro_api.models.user import User


@pytest.fixture()
def usuario(db_session):
    user = User(nombre="Ana", email="ana@example.co", ciudad="Armenia")
    db_session.add(user)
    db_session.commit()
    return user


def _crear_reporte(db_session, usuario, **overrides):
    datos = dict(
        user_id=usuario.id,
        tipo="perdido",
        especie="perro",
        nombre_mascota="Rocky",
        descripcion="Criollo color miel",
        zona="Armenia",
        lat=4.54,
        lng=-75.68,
        fecha_evento=date(2026, 8, 10),
        telefono_contacto="3001234567",
    )
    datos.update(overrides)
    reporte = Report(**datos)
    db_session.add(reporte)
    db_session.commit()
    return reporte


def _payload(**overrides):
    payload = {
        "lat": 4.55,
        "lng": -75.67,
        "fecha": "2026-08-12",
        "comentario": "Lo vi cerca al parque de La Castellana, corría hacia el norte.",
        "nombre": "Carlos",
    }
    payload.update(overrides)
    return payload


def test_crear_avistamiento_en_perdido_activo_devuelve_201(client, db_session, usuario):
    reporte = _crear_reporte(db_session, usuario)

    respuesta = client.post(f"/api/reports/{reporte.id}/avistamientos", json=_payload())

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["report_id"] == reporte.id
    assert cuerpo["lat"] == 4.55
    assert cuerpo["comentario"].startswith("Lo vi cerca")
    assert cuerpo["nombre"] == "Carlos"


def test_avistamiento_sin_nombre_es_valido(client, db_session, usuario):
    reporte = _crear_reporte(db_session, usuario)

    respuesta = client.post(
        f"/api/reports/{reporte.id}/avistamientos", json=_payload(nombre=None)
    )

    assert respuesta.status_code == 201
    assert respuesta.json()["nombre"] is None


def test_listado_ordena_por_fecha_del_avistamiento_descendente(client, db_session, usuario):
    reporte = _crear_reporte(db_session, usuario)
    client.post(f"/api/reports/{reporte.id}/avistamientos", json=_payload(fecha="2026-08-11"))
    client.post(f"/api/reports/{reporte.id}/avistamientos", json=_payload(fecha="2026-08-13"))
    client.post(f"/api/reports/{reporte.id}/avistamientos", json=_payload(fecha="2026-08-12"))

    fechas = [
        a["fecha"] for a in client.get(f"/api/reports/{reporte.id}/avistamientos").json()
    ]

    assert fechas == ["2026-08-13", "2026-08-12", "2026-08-11"]


def test_avistamiento_en_reporte_encontrado_devuelve_409(client, db_session, usuario):
    reporte = _crear_reporte(
        db_session, usuario, tipo="encontrado", nombre_mascota=None, situacion="vista"
    )

    respuesta = client.post(f"/api/reports/{reporte.id}/avistamientos", json=_payload())

    assert respuesta.status_code == 409
    assert "perdidas" in respuesta.json()["detail"]


def test_avistamiento_en_reporte_reunido_devuelve_409(client, db_session, usuario):
    reporte = _crear_reporte(db_session, usuario, estado="reunido")

    respuesta = client.post(f"/api/reports/{reporte.id}/avistamientos", json=_payload())

    assert respuesta.status_code == 409


def test_avistamiento_en_reporte_inexistente_devuelve_404(client, db_session):
    assert client.post("/api/reports/999/avistamientos", json=_payload()).status_code == 404
    assert client.get("/api/reports/999/avistamientos").status_code == 404


def test_comentario_vacio_devuelve_422(client, db_session, usuario):
    reporte = _crear_reporte(db_session, usuario)

    respuesta = client.post(
        f"/api/reports/{reporte.id}/avistamientos", json=_payload(comentario="")
    )

    assert respuesta.status_code == 422
