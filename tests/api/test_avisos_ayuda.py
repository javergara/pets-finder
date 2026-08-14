"""Ayuda entre personas: pido/ofrezco (feature 42)."""

import pytest

from reencuentro_api.models.user import User


@pytest.fixture()
def user_id(db_session):
    user = User(nombre="Ana", email="ana@example.co", ciudad="Cali")
    db_session.add(user)
    db_session.commit()
    return user.id


@pytest.fixture()
def otro_user_id(db_session):
    user = User(nombre="Luis", email="luis@example.co", ciudad="Cali")
    db_session.add(user)
    db_session.commit()
    return user.id


def _payload(user_id, **overrides):
    datos = {
        "user_id": user_id,
        "tipo": "ofrezco",
        "categoria": "hogar_de_paso",
        "titulo": "Puedo recibir gatitos en casa",
        "descripcion": "Tengo espacio y experiencia con gatos.",
        "zona": "Cali",
        "barrio": "Los Chorros",
        "telefono_contacto": "3001234567",
    }
    datos.update(overrides)
    return datos


def test_publica_pido_y_ofrezco_y_lista_mas_reciente_primero(client, user_id):
    r1 = client.post("/api/avisos-ayuda", json=_payload(user_id))
    r2 = client.post(
        "/api/avisos-ayuda",
        json=_payload(user_id, tipo="pido", categoria="alimento", titulo="Necesito comida"),
    )

    assert r1.status_code == 201 and r2.status_code == 201
    lista = client.get("/api/avisos-ayuda").json()
    assert [a["id"] for a in lista] == [r2.json()["id"], r1.json()["id"]]


def test_filtra_por_tipo_categoria_y_zona(client, user_id):
    client.post("/api/avisos-ayuda", json=_payload(user_id))
    client.post("/api/avisos-ayuda", json=_payload(user_id, tipo="pido", categoria="salud"))
    client.post("/api/avisos-ayuda", json=_payload(user_id, zona="Armenia", categoria="transporte"))

    assert len(client.get("/api/avisos-ayuda", params={"tipo": "pido"}).json()) == 1
    assert len(client.get("/api/avisos-ayuda", params={"categoria": "hogar_de_paso"}).json()) == 1
    assert len(client.get("/api/avisos-ayuda", params={"zona": "Cali"}).json()) == 2


def test_validaciones_zona_categoria_y_usuario(client, user_id):
    assert (
        client.post("/api/avisos-ayuda", json=_payload(user_id, zona="Narnia")).status_code == 422
    )
    assert (
        client.post(
            "/api/avisos-ayuda", json=_payload(user_id, zona="Otro", ciudad_texto=None)
        ).status_code
        == 422
    )
    assert (
        client.post("/api/avisos-ayuda", json=_payload(user_id, categoria="magia")).status_code
        == 422
    )
    assert client.post("/api/avisos-ayuda", json=_payload(99999)).status_code == 404


def test_resolver_solo_el_autor_y_solo_una_vez(client, user_id, otro_user_id):
    aviso = client.post("/api/avisos-ayuda", json=_payload(user_id)).json()

    ajeno = client.post(f"/api/avisos-ayuda/{aviso['id']}/resuelto", json={"user_id": otro_user_id})
    propio = client.post(f"/api/avisos-ayuda/{aviso['id']}/resuelto", json={"user_id": user_id})
    repetido = client.post(f"/api/avisos-ayuda/{aviso['id']}/resuelto", json={"user_id": user_id})

    assert ajeno.status_code == 403
    assert propio.status_code == 200 and propio.json()["estado"] == "resuelto"
    assert repetido.status_code == 409
    # Resuelto sale del listado por defecto y vuelve con estado=todos.
    assert client.get("/api/avisos-ayuda").json() == []
    assert len(client.get("/api/avisos-ayuda", params={"estado": "todos"}).json()) == 1


def test_eliminar_solo_el_autor(client, user_id, otro_user_id):
    aviso = client.post("/api/avisos-ayuda", json=_payload(user_id)).json()

    assert (
        client.delete(f"/api/avisos-ayuda/{aviso['id']}", params={"user_id": otro_user_id})
    ).status_code == 403
    assert (
        client.delete(f"/api/avisos-ayuda/{aviso['id']}", params={"user_id": user_id})
    ).status_code == 204
    assert client.delete("/api/avisos-ayuda/99999", params={"user_id": user_id}).status_code == 404
