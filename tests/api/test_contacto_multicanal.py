"""Canales opcionales de contacto Instagram/Facebook (feature 40)."""

from datetime import date

import pytest

from reencuentro_api.models.user import User


@pytest.fixture()
def user_id(db_session):
    user = User(nombre="Ana", email="ana@example.co", ciudad="Cali")
    db_session.add(user)
    db_session.commit()
    return user.id


def _payload(user_id, **overrides):
    datos = {
        "user_id": user_id,
        "tipo": "perdido",
        "especie": "perro",
        "nombre_mascota": "Rocky",
        "descripcion": "Criollo con collar rojo",
        "zona": "Cali",
        "lat": 3.45,
        "lng": -76.53,
        "fecha_evento": str(date(2026, 8, 10)),
        "telefono_contacto": "3001234567",
    }
    datos.update(overrides)
    return datos


def test_reporte_manual_lleva_instagram_y_facebook_opcionales(client, user_id):
    r = client.post(
        "/api/reports",
        json=_payload(user_id, instagram=" @MiCuenta ", facebook="https://facebook.com/ana.perez"),
    )

    assert r.status_code == 201
    cuerpo = r.json()
    # El handle se guarda normalizado, sin @ ni espacios.
    assert cuerpo["instagram"] == "MiCuenta"
    assert cuerpo["facebook"] == "https://facebook.com/ana.perez"


def test_sin_canales_opcionales_quedan_null(client, user_id):
    r = client.post("/api/reports", json=_payload(user_id))

    assert r.status_code == 201
    assert r.json()["instagram"] is None
    assert r.json()["facebook"] is None


def test_instagram_solo_arroba_se_normaliza_a_null(client, user_id):
    r = client.post("/api/reports", json=_payload(user_id, instagram="@"))

    assert r.status_code == 201
    assert r.json()["instagram"] is None
