"""Hasta 3 fotos por reporte (feature 41)."""

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
        "descripcion": "Criollo con collar rojo",
        "foto_url": "/media/uploads/principal.jpg",
        "zona": "Cali",
        "lat": 3.45,
        "lng": -76.53,
        "fecha_evento": str(date(2026, 8, 10)),
        "telefono_contacto": "3001234567",
    }
    datos.update(overrides)
    return datos


def test_fotos_extra_se_guardan_y_vuelven_en_orden(client, user_id):
    r = client.post(
        "/api/reports",
        json=_payload(user_id, fotos_extra=["/media/uploads/e1.jpg", "/media/uploads/e2.jpg"]),
    )

    assert r.status_code == 201
    creado = r.json()
    assert creado["fotos"] == [
        "/media/uploads/principal.jpg",
        "/media/uploads/e1.jpg",
        "/media/uploads/e2.jpg",
    ]
    # La principal no cambia: tarjetas, mapa y og siguen igual.
    assert creado["foto_url"] == "/media/uploads/principal.jpg"

    obtenido = client.get(f"/api/reports/{creado['id']}").json()
    assert obtenido["fotos"] == creado["fotos"]


def test_mas_de_dos_extras_es_422(client, user_id):
    r = client.post(
        "/api/reports",
        json=_payload(user_id, fotos_extra=["/a.jpg", "/b.jpg", "/c.jpg"]),
    )

    assert r.status_code == 422


def test_sin_extras_fotos_es_solo_la_principal(client, user_id):
    r = client.post("/api/reports", json=_payload(user_id))

    assert r.status_code == 201
    assert r.json()["fotos"] == ["/media/uploads/principal.jpg"]


def test_sin_ninguna_foto_la_lista_es_vacia(client, user_id):
    r = client.post("/api/reports", json=_payload(user_id, foto_url=None))

    assert r.status_code == 201
    assert r.json()["fotos"] == []


def test_eliminar_borra_tambien_las_fotos_extra(client, user_id, monkeypatch):
    borradas = []
    from reencuentro_api.routers import reports as modulo

    monkeypatch.setattr(modulo, "borrar_foto", lambda url: borradas.append(url))

    creado = client.post(
        "/api/reports", json=_payload(user_id, fotos_extra=["/media/uploads/e1.jpg"])
    ).json()
    r = client.delete(f"/api/reports/{creado['id']}", params={"user_id": user_id})

    assert r.status_code == 204
    assert borradas == ["/media/uploads/principal.jpg", "/media/uploads/e1.jpg"]
