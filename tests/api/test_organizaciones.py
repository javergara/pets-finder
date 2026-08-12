"""Red de apoyo (feature 32): centros de acopio, fundaciones, tiendas, veterinarias."""

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


def _payload(usuario, **overrides):
    payload = {
        "user_id": usuario.id,
        "tipo": "fundacion",
        "nombre": "Fundación Huellitas del Quindío",
        "descripcion": "Rescatamos y damos hogar de paso a mascotas afectadas por el sismo.",
        "zona": "Armenia",
        "barrio": "Centro",
        "direccion": "Cra 14 #10-25",
        "lat": 4.535,
        "lng": -75.68,
        "telefono_contacto": "3001112233",
        "horario": "Lun-Sáb 8am-5pm",
        "como_donar": "Nequi 3001112233 a nombre de la fundación",
    }
    payload.update(overrides)
    return payload


def test_crear_organizacion_devuelve_201(client, usuario):
    respuesta = client.post("/api/organizaciones", json=_payload(usuario))

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["nombre"] == "Fundación Huellitas del Quindío"
    assert cuerpo["tipo"] == "fundacion"
    assert cuerpo["estado"] == "activo"
    assert cuerpo["como_donar"].startswith("Nequi")


def test_crear_centro_de_acopio_devuelve_201(client, usuario):
    respuesta = client.post(
        "/api/organizaciones",
        json=_payload(
            usuario,
            tipo="centro_acopio",
            nombre="Acopio Parque Sucre",
            horario="24 horas",
            como_donar=None,
        ),
    )

    assert respuesta.status_code == 201
    assert respuesta.json()["tipo"] == "centro_acopio"


def test_crear_con_usuario_inexistente_devuelve_404(client, db_session):
    class Falso:
        id = 999

    respuesta = client.post("/api/organizaciones", json=_payload(Falso()))

    assert respuesta.status_code == 404


def test_tipo_invalido_devuelve_422(client, usuario):
    assert (
        client.post("/api/organizaciones", json=_payload(usuario, tipo="circo")).status_code == 422
    )


def test_zona_invalida_devuelve_422(client, usuario):
    respuesta = client.post("/api/organizaciones", json=_payload(usuario, zona="Palmira"))

    assert respuesta.status_code == 422
    assert "Zona desconocida" in str(respuesta.json())


def test_zona_otro_sin_ciudad_texto_devuelve_422(client, usuario):
    assert (
        client.post("/api/organizaciones", json=_payload(usuario, zona="Otro")).status_code == 422
    )


def test_zona_otro_con_ciudad_texto_devuelve_201(client, usuario):
    respuesta = client.post(
        "/api/organizaciones", json=_payload(usuario, zona="Otro", ciudad_texto="Palmira")
    )

    assert respuesta.status_code == 201


def test_listado_filtra_por_tipo_y_zona_y_excluye_cerradas(client, usuario):
    client.post("/api/organizaciones", json=_payload(usuario))
    client.post(
        "/api/organizaciones",
        json=_payload(usuario, tipo="centro_acopio", nombre="Acopio Pereira", zona="Pereira"),
    )
    cerrada = client.post(
        "/api/organizaciones", json=_payload(usuario, nombre="Cerrada")
    ).json()
    client.put(
        f"/api/organizaciones/{cerrada['id']}",
        json={"user_id": usuario.id, "estado": "cerrado"},
    )

    activos = client.get("/api/organizaciones").json()
    assert {o["nombre"] for o in activos} == {
        "Fundación Huellitas del Quindío",
        "Acopio Pereira",
    }

    solo_acopios = client.get("/api/organizaciones?tipo=centro_acopio").json()
    assert [o["nombre"] for o in solo_acopios] == ["Acopio Pereira"]

    por_zona = client.get("/api/organizaciones?zona=Armenia").json()
    assert [o["nombre"] for o in por_zona] == ["Fundación Huellitas del Quindío"]

    todas = client.get("/api/organizaciones?estado=todos").json()
    assert len(todas) == 3


def test_editar_solo_el_autor(client, usuario, otro_usuario):
    org = client.post("/api/organizaciones", json=_payload(usuario)).json()

    ajeno = client.put(
        f"/api/organizaciones/{org['id']}",
        json={"user_id": otro_usuario.id, "horario": "hackeado"},
    )
    assert ajeno.status_code == 403
    assert ajeno.json()["detail"] == "Solo quien registró la organización puede editarla"

    propio = client.put(
        f"/api/organizaciones/{org['id']}",
        json={"user_id": usuario.id, "horario": "Lun-Dom 24h", "como_donar": "Bancolombia 123"},
    )
    assert propio.status_code == 200
    assert propio.json()["horario"] == "Lun-Dom 24h"
    assert propio.json()["como_donar"] == "Bancolombia 123"


def test_eliminar_solo_el_autor(client, usuario, otro_usuario):
    org = client.post("/api/organizaciones", json=_payload(usuario)).json()

    assert (
        client.delete(f"/api/organizaciones/{org['id']}?user_id={otro_usuario.id}").status_code
        == 403
    )
    assert client.delete(f"/api/organizaciones/{org['id']}?user_id={usuario.id}").status_code == 204
    assert client.get(f"/api/organizaciones/{org['id']}").status_code == 404


def test_obtener_inexistente_devuelve_404(client, db_session):
    assert client.get("/api/organizaciones/999").status_code == 404
