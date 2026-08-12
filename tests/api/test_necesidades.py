"""Necesidades de la red de apoyo (feature 33): pedir ayuda concreta y cubrirla."""

import pytest

from reencuentro_api.models.user import User


@pytest.fixture()
def usuario(db_session):
    user = User(nombre="Ana", email="ana@example.co", ciudad="Armenia")
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture()
def otro_usuario(db_session):
    user = User(nombre="Carlos", email="carlos@example.co", ciudad="Pereira")
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture()
def organizacion(client, usuario):
    return client.post(
        "/api/organizaciones",
        json={
            "user_id": usuario.id,
            "tipo": "fundacion",
            "nombre": "Fundación Huellitas",
            "descripcion": "Rescatamos mascotas.",
            "zona": "Armenia",
            "direccion": "Cra 14 #10-25",
            "lat": 4.535,
            "lng": -75.68,
            "telefono_contacto": "3001112233",
        },
    ).json()


def _publicar(client, organizacion, usuario, **overrides):
    payload = {
        "user_id": usuario.id,
        "categoria": "alimento",
        "descripcion": "50 kg de comida para perro adulto",
    }
    payload.update(overrides)
    return client.post(f"/api/organizaciones/{organizacion['id']}/necesidades", json=payload)


def test_el_autor_publica_una_necesidad(client, organizacion, usuario):
    respuesta = _publicar(client, organizacion, usuario)

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["categoria"] == "alimento"
    assert cuerpo["estado"] == "pendiente"
    assert cuerpo["cubierta_en"] is None


def test_otro_usuario_no_puede_publicar(client, organizacion, otro_usuario):
    respuesta = _publicar(client, organizacion, otro_usuario)

    assert respuesta.status_code == 403
    assert "publicar necesidades" in respuesta.json()["detail"]


def test_categoria_invalida_devuelve_422(client, organizacion, usuario):
    assert _publicar(client, organizacion, usuario, categoria="magia").status_code == 422


def test_listado_pone_pendientes_primero(client, organizacion, usuario):
    primera = _publicar(client, organizacion, usuario, descripcion="Cobijas").json()
    _publicar(client, organizacion, usuario, categoria="voluntarios", descripcion="Brigada sábado")
    client.post(
        f"/api/organizaciones/{organizacion['id']}/necesidades/{primera['id']}/cubierta",
        json={"user_id": usuario.id},
    )

    necesidades = client.get(f"/api/organizaciones/{organizacion['id']}/necesidades").json()

    assert [n["estado"] for n in necesidades] == ["pendiente", "cubierta"]
    assert necesidades[0]["descripcion"] == "Brigada sábado"


def test_cubrir_solo_el_autor_y_solo_una_vez(client, organizacion, usuario, otro_usuario):
    necesidad = _publicar(client, organizacion, usuario).json()
    url = f"/api/organizaciones/{organizacion['id']}/necesidades/{necesidad['id']}/cubierta"

    assert client.post(url, json={"user_id": otro_usuario.id}).status_code == 403

    ok = client.post(url, json={"user_id": usuario.id})
    assert ok.status_code == 200
    assert ok.json()["estado"] == "cubierta"
    assert ok.json()["cubierta_en"] is not None

    repetida = client.post(url, json={"user_id": usuario.id})
    assert repetida.status_code == 409
    assert repetida.json()["detail"] == "Esta necesidad ya está marcada como cubierta"


def test_contador_de_pendientes_en_listado_y_detalle(client, organizacion, usuario):
    _publicar(client, organizacion, usuario)
    cubierta = _publicar(client, organizacion, usuario, descripcion="Cobijas").json()
    client.post(
        f"/api/organizaciones/{organizacion['id']}/necesidades/{cubierta['id']}/cubierta",
        json={"user_id": usuario.id},
    )

    listado = client.get("/api/organizaciones").json()
    assert listado[0]["necesidades_pendientes"] == 1

    detalle = client.get(f"/api/organizaciones/{organizacion['id']}").json()
    assert detalle["necesidades_pendientes"] == 1


def test_necesidad_de_organizacion_inexistente_devuelve_404(client, usuario):
    respuesta = client.post(
        "/api/organizaciones/999/necesidades",
        json={"user_id": usuario.id, "categoria": "alimento", "descripcion": "x"},
    )
    assert respuesta.status_code == 404
    assert client.get("/api/organizaciones/999/necesidades").status_code == 404


def test_cubrir_necesidad_de_otra_organizacion_devuelve_404(client, organizacion, usuario):
    necesidad = _publicar(client, organizacion, usuario).json()
    otra = client.post(
        "/api/organizaciones",
        json={
            "user_id": usuario.id,
            "tipo": "tienda",
            "nombre": "Tienda Peludos",
            "descripcion": "Venta de alimento.",
            "zona": "Armenia",
            "direccion": "Cll 20 #5-10",
            "lat": 4.54,
            "lng": -75.67,
            "telefono_contacto": "3009998877",
        },
    ).json()

    respuesta = client.post(
        f"/api/organizaciones/{otra['id']}/necesidades/{necesidad['id']}/cubierta",
        json={"user_id": usuario.id},
    )
    assert respuesta.status_code == 404
