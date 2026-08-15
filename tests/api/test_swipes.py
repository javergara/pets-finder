"""Swipes del deck de descubrimiento (AD-03 paso 6): `POST /api/swipes`.

⚠️ **`Swipe.user_id` es el ADOPTANTE**, al revés que en `pets`, donde `user_id`
es quien publicó. Es la colisión más peligrosa del portado desde `adopta-v1`, y
por eso las fixtures de aquí se llaman `adoptante` y `publicador`: si alguna vez
se confunden, `test_user_id_del_swipe_es_el_adoptante_no_el_publicador` se pone
en rojo.

⚠️ `Swipe`, `Pet` y `User` se importan a nivel de módulo a propósito: el fixture
`db_session` hace `create_all` con lo que esté registrado en `Base.metadata` en
ese instante, y un import perezoso produce un `no such table: swipes`
intermitente según el orden de colección de pytest.
"""

import pytest
from sqlalchemy import func, select

from reencuentro_api.models.pet import Pet
from reencuentro_api.models.swipe import Swipe
from reencuentro_api.models.user import User
from reencuentro_api.routers import swipes as router_swipes


@pytest.fixture()
def adoptante(db_session):
    """Quien mira el deck: el `user_id` que viaja en el swipe."""
    user = User(nombre="Ana", email="ana@example.co", ciudad="Armenia")
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture()
def otro_adoptante(db_session):
    user = User(nombre="Lucía", email="lucia@example.co", ciudad="Pereira")
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture()
def publicador(db_session):
    """El rescatista dueño de la mascota: NO es quien swipea."""
    user = User(nombre="Carlos", email="carlos@example.co", ciudad="Pereira")
    db_session.add(user)
    db_session.commit()
    return user


def _pet(publicador_id: int, **overrides) -> Pet:
    campos = {
        "user_id": publicador_id,
        "telefono_contacto": "3105558899",
        "nombre": "Canela",
        "especie": "perro",
        "sexo": "hembra",
        "edad_meses": 18,
        "tamano": "mediano",
        "energia": "media",
        "historia": "Rescatada en Armenia tras el sismo, busca hogar.",
        "zona": "Armenia",
    }
    campos.update(overrides)
    return Pet(**campos)


@pytest.fixture()
def mascota(db_session, publicador):
    pet = _pet(publicador.id)
    db_session.add(pet)
    db_session.commit()
    return pet


def _contar_swipes(db_session, **filtros) -> int:
    query = select(func.count()).select_from(Swipe)
    for campo, valor in filtros.items():
        query = query.where(getattr(Swipe, campo) == valor)
    return db_session.execute(query).scalar_one()


# --- 201: el swipe nuevo -------------------------------------------------------


def test_like_devuelve_201_y_guarda_la_fila(client, db_session, adoptante, mascota):
    respuesta = client.post(
        "/api/swipes",
        json={"user_id": adoptante.id, "pet_id": mascota.id, "direccion": "like"},
    )

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["user_id"] == adoptante.id
    assert cuerpo["pet_id"] == mascota.id
    assert cuerpo["direccion"] == "like"
    assert cuerpo["creado_en"] is not None

    guardado = db_session.get(Swipe, cuerpo["id"])
    assert guardado is not None
    assert guardado.user_id == adoptante.id
    assert guardado.pet_id == mascota.id
    assert guardado.direccion == "like"


def test_pass_devuelve_201(client, db_session, adoptante, mascota):
    respuesta = client.post(
        "/api/swipes",
        json={"user_id": adoptante.id, "pet_id": mascota.id, "direccion": "pass"},
    )

    assert respuesta.status_code == 201
    assert respuesta.json()["direccion"] == "pass"
    assert _contar_swipes(db_session) == 1


def test_user_id_del_swipe_es_el_adoptante_no_el_publicador(
    client, db_session, adoptante, publicador, mascota
):
    """La colisión de nombres del portado, fijada por un test: en `pets`,
    `user_id` es quien publicó; aquí es quien mira."""
    respuesta = client.post(
        "/api/swipes",
        json={"user_id": adoptante.id, "pet_id": mascota.id, "direccion": "like"},
    )

    guardado = db_session.get(Swipe, respuesta.json()["id"])
    assert guardado.user_id == adoptante.id
    assert guardado.user_id != mascota.user_id
    assert mascota.user_id == publicador.id


def test_solicitud_viene_null(client, db_session, adoptante, mascota):
    """`SwipeOut.solicitud` existe desde ya en el contrato, pero la crea AD-05:
    en AD-03 un "me interesa" registra el swipe y nada más."""
    respuesta = client.post(
        "/api/swipes",
        json={"user_id": adoptante.id, "pet_id": mascota.id, "direccion": "like"},
    )

    cuerpo = respuesta.json()
    assert "solicitud" in cuerpo
    assert cuerpo["solicitud"] is None


def test_mensaje_y_telefono_se_aceptan_y_no_se_persisten(client, db_session, adoptante, mascota):
    """`SwipeIn` ya declara los dos campos pensando en AD-05/AD-06, pero la tabla
    `swipes` no los tiene: se aceptan y se descartan, sin 422 y sin guardarlos."""
    respuesta = client.post(
        "/api/swipes",
        json={
            "user_id": adoptante.id,
            "pet_id": mascota.id,
            "direccion": "like",
            "mensaje": "Tengo patio y otro perro, me encantaría conocerla.",
            "telefono_contacto": "3001112233",
        },
    )

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert "mensaje" not in cuerpo
    assert "telefono_contacto" not in cuerpo
    guardado = db_session.get(Swipe, cuerpo["id"])
    assert not hasattr(guardado, "mensaje")


def test_dos_adoptantes_pueden_swipear_la_misma_mascota(
    client, db_session, adoptante, otro_adoptante, mascota
):
    """El único es (adoptante, mascota), no la mascota sola."""
    primera = client.post(
        "/api/swipes",
        json={"user_id": adoptante.id, "pet_id": mascota.id, "direccion": "like"},
    )
    segunda = client.post(
        "/api/swipes",
        json={"user_id": otro_adoptante.id, "pet_id": mascota.id, "direccion": "pass"},
    )

    assert primera.status_code == 201
    assert segunda.status_code == 201
    assert _contar_swipes(db_session, pet_id=mascota.id) == 2


# --- 200: el swipe repetido es idempotente -------------------------------------


def test_swipe_repetido_devuelve_200_con_el_mismo_id_y_sin_segunda_fila(
    client, db_session, adoptante, mascota
):
    """Un doble-tap del gesto en móvil no puede duplicar la fila (ni, en AD-05,
    la solicitud). Patrón de `entrar_o_registrar`: 200, no 409."""
    cuerpo = {"user_id": adoptante.id, "pet_id": mascota.id, "direccion": "like"}

    primera = client.post("/api/swipes", json=cuerpo)
    segunda = client.post("/api/swipes", json=cuerpo)

    assert primera.status_code == 201
    assert segunda.status_code == 200
    assert segunda.json()["id"] == primera.json()["id"]
    assert segunda.json()["creado_en"] == primera.json()["creado_en"]
    assert _contar_swipes(db_session, user_id=adoptante.id, pet_id=mascota.id) == 1


def test_swipe_repetido_no_cambia_la_direccion(client, db_session, adoptante, mascota):
    """Idempotente de verdad: el segundo swipe no reescribe el primero. Descartar
    y volver a "me interesa" es una decisión de producto (AD-05/AD-07), no un
    efecto colateral de repetir el gesto."""
    descarte = client.post(
        "/api/swipes",
        json={"user_id": adoptante.id, "pet_id": mascota.id, "direccion": "pass"},
    )
    reintento = client.post(
        "/api/swipes",
        json={"user_id": adoptante.id, "pet_id": mascota.id, "direccion": "like"},
    )

    assert descarte.status_code == 201
    assert reintento.status_code == 200
    assert reintento.json()["direccion"] == "pass"
    assert db_session.get(Swipe, descarte.json()["id"]).direccion == "pass"
    assert _contar_swipes(db_session) == 1


def test_carrera_por_el_mismo_swipe_devuelve_200_sin_duplicar(
    client, db_session, adoptante, mascota, monkeypatch
):
    """El select previo ciego, como en una carrera real entre dos requests (en
    serverless corren a la vez): el `UniqueConstraint` es quien rechaza el
    insert, y sin atrapar el `IntegrityError` con su `rollback()` eso sería un
    500 con traza en vez del 200 idempotente."""
    cuerpo = {"user_id": adoptante.id, "pet_id": mascota.id, "direccion": "like"}
    primera = client.post("/api/swipes", json=cuerpo)
    assert primera.status_code == 201

    consulta_real = router_swipes._swipe_existente
    llamadas = []

    def _ciego_la_primera_vez(session, user_id, pet_id):
        llamadas.append((user_id, pet_id))
        return None if len(llamadas) == 1 else consulta_real(session, user_id, pet_id)

    monkeypatch.setattr(router_swipes, "_swipe_existente", _ciego_la_primera_vez)

    respuesta = client.post("/api/swipes", json=cuerpo)

    assert respuesta.status_code == 200
    assert respuesta.json()["id"] == primera.json()["id"]
    assert _contar_swipes(db_session, user_id=adoptante.id, pet_id=mascota.id) == 1
    # El select previo Y el de después del rollback: la segunda consulta es la
    # que convierte el error de DB en la respuesta idempotente.
    assert len(llamadas) == 2


# --- 404 / 409 / 422 -----------------------------------------------------------


def test_mascota_inexistente_devuelve_404(client, db_session, adoptante):
    """⚠️ SQLite no fuerza las FK: sin esta comprobación **en el código**, el
    insert pasaría en los tests y reventaría con un 500 recién en Postgres."""
    respuesta = client.post(
        "/api/swipes",
        json={"user_id": adoptante.id, "pet_id": 9999, "direccion": "like"},
    )

    assert respuesta.status_code == 404
    assert respuesta.json()["detail"] == "La mascota 9999 no existe"
    assert _contar_swipes(db_session) == 0


def test_adoptante_inexistente_devuelve_404(client, db_session, mascota):
    """Mismo motivo que el anterior: la integridad la impone el código, no la DB."""
    respuesta = client.post(
        "/api/swipes",
        json={"user_id": 9999, "pet_id": mascota.id, "direccion": "like"},
    )

    assert respuesta.status_code == 404
    assert respuesta.json()["detail"] == "El usuario 9999 no existe"
    assert _contar_swipes(db_session) == 0


def test_swipe_sobre_mascota_adoptada_devuelve_409(client, db_session, adoptante, publicador):
    """Una mascota que ya encontró hogar no se puede pedir en adopción: el deck
    no la muestra, pero una carta vieja en pantalla sí puede llegar aquí."""
    adoptada = _pet(publicador.id, nombre="Duque", estado="adoptado")
    db_session.add(adoptada)
    db_session.commit()

    respuesta = client.post(
        "/api/swipes",
        json={"user_id": adoptante.id, "pet_id": adoptada.id, "direccion": "like"},
    )

    assert respuesta.status_code == 409
    assert respuesta.json()["detail"] == "Esta mascota ya encontró hogar"
    assert _contar_swipes(db_session) == 0


def test_swipe_sobre_mascota_en_proceso_se_acepta(client, db_session, adoptante, publicador):
    """`en_proceso` no bloquea: una adopción puede no cuajar y el interés de otra
    familia es justamente lo que evita empezar de cero (`PUT /api/pets` ya
    permite volver a `disponible`)."""
    en_proceso = _pet(publicador.id, nombre="Nube", estado="en_proceso")
    db_session.add(en_proceso)
    db_session.commit()

    respuesta = client.post(
        "/api/swipes",
        json={"user_id": adoptante.id, "pet_id": en_proceso.id, "direccion": "like"},
    )

    assert respuesta.status_code == 201
    assert _contar_swipes(db_session, pet_id=en_proceso.id) == 1


@pytest.mark.parametrize("direccion", ["quizas", "LIKE", "", "super_like"])
def test_direccion_invalida_devuelve_422(client, db_session, adoptante, mascota, direccion):
    respuesta = client.post(
        "/api/swipes",
        json={"user_id": adoptante.id, "pet_id": mascota.id, "direccion": direccion},
    )

    assert respuesta.status_code == 422
    assert _contar_swipes(db_session) == 0
