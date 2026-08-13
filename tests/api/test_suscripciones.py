"""Avísame si hay novedades (feature 39, ADR 0011)."""

from datetime import date

import pytest

from reencuentro_api.models.report import Report
from reencuentro_api.models.user import User
from reencuentro_api.services import notificaciones


@pytest.fixture()
def reporte(db_session):
    user = User(nombre="Ana", email="ana@example.co", ciudad="Cali")
    db_session.add(user)
    db_session.flush()
    r = Report(
        user_id=user.id,
        tipo="perdido",
        especie="perro",
        nombre_mascota="Rocky",
        descripcion="Criollo con collar rojo",
        zona="Cali",
        lat=3.45,
        lng=-76.53,
        fecha_evento=date(2026, 8, 10),
        telefono_contacto="3001234567",
    )
    db_session.add(r)
    db_session.commit()
    return r


def test_alta_guarda_el_correo_sin_exponer_token_ni_email(client, reporte):
    respuesta = client.post(
        f"/api/reports/{reporte.id}/suscripciones", json={"email": "vecina@example.co"}
    )

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["report_id"] == reporte.id
    assert "email" not in cuerpo and "token" not in cuerpo


def test_alta_es_idempotente_por_correo(client, reporte):
    primera = client.post(
        f"/api/reports/{reporte.id}/suscripciones", json={"email": "vecina@example.co"}
    )
    segunda = client.post(
        f"/api/reports/{reporte.id}/suscripciones", json={"email": "  VECINA@example.co "}
    )

    assert primera.status_code == 201
    assert segunda.status_code == 200
    assert segunda.json()["id"] == primera.json()["id"]


def test_alta_valida_correo_y_reporte(client, reporte):
    assert (
        client.post(f"/api/reports/{reporte.id}/suscripciones", json={"email": "no-es-correo"})
    ).status_code == 422
    assert (
        client.post("/api/reports/99999/suscripciones", json={"email": "a@b.co"})
    ).status_code == 404


def test_baja_por_token_borra_y_el_link_repetido_avisa(client, db_session, reporte):
    from reencuentro_api.models.suscripcion import Suscripcion

    client.post(f"/api/reports/{reporte.id}/suscripciones", json={"email": "vecina@example.co"})
    token = db_session.query(Suscripcion).one().token

    baja = client.get(f"/api/suscripciones/baja/{token}")
    repetida = client.get(f"/api/suscripciones/baja/{token}")

    assert baja.status_code == 200
    assert "no te escribimos más" in baja.text
    assert db_session.query(Suscripcion).count() == 0
    assert repetida.status_code == 404
    assert "ya no es válido" in repetida.text


def test_avistamiento_y_reunido_disparan_la_notificacion(client, db_session, reporte, monkeypatch):
    enviados = []
    monkeypatch.setattr(
        notificaciones,
        "_enviar_email",
        lambda destino, asunto, html: enviados.append((destino, asunto, html)),
    )
    client.post(f"/api/reports/{reporte.id}/suscripciones", json={"email": "vecina@example.co"})

    r = client.post(
        f"/api/reports/{reporte.id}/avistamientos",
        json={
            "lat": 3.45,
            "lng": -76.53,
            "fecha": "2026-08-13",
            "comentario": "La vi en el parque",
        },
    )
    assert r.status_code == 201
    assert len(enviados) == 1
    destino, asunto, html = enviados[0]
    assert destino == "vecina@example.co"
    assert "Rocky" in asunto
    assert "La vi en el parque" in html
    assert "/api/suscripciones/baja/" in html  # link de baja siempre presente

    r = client.post(f"/api/reports/{reporte.id}/reunido", json={"user_id": reporte.user_id})
    assert r.status_code == 200
    assert len(enviados) == 2
    assert "volvió a casa" in enviados[1][2]


def test_fallo_del_proveedor_no_rompe_el_endpoint(client, reporte, monkeypatch):
    def explota(*args):
        raise RuntimeError("proveedor caído")

    monkeypatch.setattr(notificaciones, "_enviar_email", explota)
    client.post(f"/api/reports/{reporte.id}/suscripciones", json={"email": "vecina@example.co"})

    r = client.post(
        f"/api/reports/{reporte.id}/avistamientos",
        json={"lat": 3.45, "lng": -76.53, "fecha": "2026-08-13", "comentario": "La vi"},
    )

    assert r.status_code == 201


def test_sin_api_key_el_envio_es_noop_con_log(monkeypatch, caplog):
    monkeypatch.delenv("RESEND_API_KEY", raising=False)

    with caplog.at_level("INFO"):
        resultado = notificaciones._enviar_email("a@b.co", "Prueba", "<p>hola</p>")

    assert resultado is False
    assert "RESEND_API_KEY sin configurar" in caplog.text
