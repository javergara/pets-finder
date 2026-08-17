"""Swipes del deck de descubrimiento (AD-03 paso 6): `POST /api/swipes`.

⚠️ **`Swipe.user_id` es el ADOPTANTE**, al revés que en `pets`, donde `user_id`
es quien publicó. Es la colisión más peligrosa del portado desde `adopta-v1`, y
por eso las fixtures de aquí se llaman `adoptante` y `publicador`: si alguna vez
se confunden, `test_user_id_del_swipe_es_el_adoptante_no_el_publicador` se pone
en rojo.

⚠️ `Swipe`, `Match`, `Pet` y `User` se importan a nivel de módulo a propósito: el
fixture `db_session` hace `create_all` con lo que esté registrado en
`Base.metadata` en ese instante, y un import perezoso produce un `no such table:
swipes` intermitente según el orden de colección de pytest.

Desde **AD-05 paso 4** el "me interesa" hace dos cosas en el mismo commit: el
swipe y la **solicitud** (`matches`). Los casos de esa mitad viven abajo, en su
propia sección; los de AD-03 siguen valiendo tal cual porque el swipe no cambió.
"""

import pytest
from sqlalchemy import func, select

from reencuentro_api.models.match import Match
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


def _contar_matches(db_session, **filtros) -> int:
    """Filas reales de `matches`, no lo que diga la respuesta HTTP.

    Un `select(func.count())` y no `len(...)` de una lista: es la única forma de
    ver una segunda solicitud creada por un like repetido, que en el cuerpo de la
    respuesta sería invisible (las dos filas se verían iguales)."""
    query = select(func.count()).select_from(Match)
    for campo, valor in filtros.items():
        query = query.where(getattr(Match, campo) == valor)
    return db_session.execute(query).scalar_one()


def _solicitud_de(db_session, adoptante_id: int, pet_id: int) -> Match | None:
    return db_session.execute(
        select(Match).where(Match.user_id == adoptante_id, Match.pet_id == pet_id)
    ).scalar_one_or_none()


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


def test_solicitud_viene_null_en_el_pass(client, db_session, adoptante, mascota):
    """El campo existe siempre en el contrato, pero solo el "me interesa" lo llena.

    ⚠️ Este caso **nació con `direccion: "like"`** en AD-03, cuando `solicitud`
    era `null` para las dos direcciones porque nada la creaba. AD-05 paso 4 le
    quitó esa premisa al like —ahora sí crea la solicitud, ver
    `test_like_crea_la_solicitud...` abajo— así que se mueve al `pass`, que es
    donde la aserción sigue diciendo algo verdadero: descartar una mascota no
    puede pedirla en adopción."""
    respuesta = client.post(
        "/api/swipes",
        json={"user_id": adoptante.id, "pet_id": mascota.id, "direccion": "pass"},
    )

    cuerpo = respuesta.json()
    assert "solicitud" in cuerpo
    assert cuerpo["solicitud"] is None
    assert _contar_matches(db_session) == 0


def test_mensaje_y_telefono_no_son_columnas_del_swipe(client, db_session, adoptante, mascota):
    """La tabla `swipes` no tiene ninguno de los dos, y el `SwipeOut` tampoco.

    ⚠️ En AD-03 este caso se llamaba `..._se_aceptan_y_no_se_persisten`: los dos
    campos se aceptaban y se tiraban. AD-05 paso 4 los persiste, pero **en
    `matches`** (ver `test_mensaje_y_telefono_acaban_en_la_solicitud...`), así que
    lo que sigue siendo cierto —y lo que este caso vigila— es que no se cuelen en
    el swipe ni en su respuesta."""
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


# --- AD-05 paso 4: el "me interesa" crea la solicitud --------------------------


def test_like_crea_la_solicitud_y_aparece_en_mis_solicitudes(
    client, db_session, adoptante, mascota
):
    """El swipe-derecha **es** la solicitud: no hay un segundo botón que pulsar.

    Se comprueba de extremo a extremo —la fila en `matches` y la lista del
    adoptante— porque el contrato de `SwipeOut.solicitud` solo sirve si lo que
    devuelve el modal es lo mismo que después aparece en "mis solicitudes"."""
    respuesta = client.post(
        "/api/swipes",
        json={"user_id": adoptante.id, "pet_id": mascota.id, "direccion": "like"},
    )

    assert respuesta.status_code == 201
    solicitud = respuesta.json()["solicitud"]
    assert solicitud is not None
    assert solicitud["estado"] == "solicitado"
    assert solicitud["etiqueta"] == "Cuestionario nuevo"
    assert solicitud["pet"]["id"] == mascota.id
    assert solicitud["pet"]["nombre"] == "Canela"
    assert solicitud["creado_en"] is not None

    fila = db_session.get(Match, solicitud["id"])
    assert fila is not None
    # ⚠️ En `matches`, `user_id` es el ADOPTANTE (al revés que en `pets`).
    assert fila.user_id == adoptante.id
    assert fila.pet_id == mascota.id
    assert fila.estado == "solicitado"

    listado = client.get("/api/solicitudes", params={"adoptante_id": adoptante.id})
    assert listado.status_code == 200
    assert [s["id"] for s in listado.json()] == [solicitud["id"]]


def test_like_repetido_devuelve_la_misma_solicitud_sin_crear_otra(
    client, db_session, adoptante, mascota
):
    """El doble-tap del gesto duplicaría la solicitud, no solo el swipe: quien
    publica vería a la misma familia dos veces en su panel."""
    cuerpo = {"user_id": adoptante.id, "pet_id": mascota.id, "direccion": "like"}

    primera = client.post("/api/swipes", json=cuerpo)
    segunda = client.post("/api/swipes", json=cuerpo)

    assert primera.status_code == 201
    assert segunda.status_code == 200
    assert segunda.json()["solicitud"]["id"] == primera.json()["solicitud"]["id"]
    assert _contar_matches(db_session, user_id=adoptante.id, pet_id=mascota.id) == 1
    assert _contar_swipes(db_session, user_id=adoptante.id, pet_id=mascota.id) == 1


def test_like_repetido_no_pisa_el_mensaje_de_la_solicitud(client, db_session, adoptante, mascota):
    """Idempotente de verdad, igual que la dirección del swipe: el segundo intento
    devuelve lo que ya había en vez de reescribirlo. Reenviar el gesto no puede
    borrarle a quien publica el texto que ya estaba leyendo."""
    primera = client.post(
        "/api/swipes",
        json={
            "user_id": adoptante.id,
            "pet_id": mascota.id,
            "direccion": "like",
            "mensaje": "Tengo patio y otro perro.",
            "telefono_contacto": "3001112233",
        },
    )
    segunda = client.post(
        "/api/swipes",
        json={
            "user_id": adoptante.id,
            "pet_id": mascota.id,
            "direccion": "like",
            "mensaje": "Ay, perdón, se me fue el dedo.",
            "telefono_contacto": "3009998877",
        },
    )

    assert segunda.status_code == 200
    assert segunda.json()["solicitud"]["id"] == primera.json()["solicitud"]["id"]
    fila = _solicitud_de(db_session, adoptante.id, mascota.id)
    assert fila.mensaje == "Tengo patio y otro perro."
    assert fila.telefono_contacto == "3001112233"


def test_mensaje_y_telefono_acaban_en_la_solicitud_no_en_el_swipe(
    client, db_session, adoptante, mascota
):
    """Los dos campos que `SwipeIn` aceptaba y tiraba desde AD-03 llegan a su
    destino: son columnas de `matches`, no de `swipes` (y AD-06 los usa para el
    contacto por WhatsApp)."""
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
    solicitud = _solicitud_de(db_session, adoptante.id, mascota.id)
    assert solicitud.mensaje == "Tengo patio y otro perro, me encantaría conocerla."
    assert solicitud.telefono_contacto == "3001112233"

    swipe = db_session.get(Swipe, respuesta.json()["id"])
    assert not hasattr(swipe, "mensaje")
    assert not hasattr(swipe, "telefono_contacto")


@pytest.mark.parametrize("mensaje", [None, "", "   "])
def test_solicitud_sin_mensaje_queda_en_none_no_en_cadena_vacia(
    client, db_session, adoptante, mascota, mensaje
):
    """El mensaje es opcional y "sin mensaje" se guarda como `NULL`.

    Una cadena vacía (o de espacios) pintaría en el detalle una cita en blanco
    atribuida al adoptante, indistinguible de un mensaje que se perdió."""
    respuesta = client.post(
        "/api/swipes",
        json={
            "user_id": adoptante.id,
            "pet_id": mascota.id,
            "direccion": "like",
            "mensaje": mensaje,
        },
    )

    assert respuesta.status_code == 201
    solicitud = _solicitud_de(db_session, adoptante.id, mascota.id)
    assert solicitud.mensaje is None
    assert solicitud.telefono_contacto is None


def test_like_sobre_mascota_adoptada_no_crea_solicitud(client, db_session, adoptante, publicador):
    """El 409 va **antes** de escribir nada: una solicitud sobre una mascota que ya
    tiene hogar mandaría a una familia a esperar por algo imposible."""
    adoptada = _pet(publicador.id, nombre="Duque", estado="adoptado")
    db_session.add(adoptada)
    db_session.commit()

    respuesta = client.post(
        "/api/swipes",
        json={
            "user_id": adoptante.id,
            "pet_id": adoptada.id,
            "direccion": "like",
            "mensaje": "Me encantaría adoptarlo.",
        },
    )

    assert respuesta.status_code == 409
    assert _contar_matches(db_session) == 0
    assert _contar_swipes(db_session) == 0


def test_like_sobre_mascota_en_proceso_si_crea_solicitud(client, db_session, adoptante, publicador):
    """`en_proceso` no bloquea: si esa adopción no cuaja, esta solicitud es lo que
    evita empezar de cero (mismo criterio que el swipe de AD-03)."""
    en_proceso = _pet(publicador.id, nombre="Nube", estado="en_proceso")
    db_session.add(en_proceso)
    db_session.commit()

    respuesta = client.post(
        "/api/swipes",
        json={"user_id": adoptante.id, "pet_id": en_proceso.id, "direccion": "like"},
    )

    assert respuesta.status_code == 201
    assert respuesta.json()["solicitud"]["pet"]["id"] == en_proceso.id
    assert _contar_matches(db_session, pet_id=en_proceso.id) == 1


def test_like_preexistente_sin_solicitud_la_crea(client, db_session, adoptante, mascota):
    """Las filas que dejó AD-03 (swipe sí, solicitud no) no pueden quedar mudas.

    Existen de verdad en la base local de cualquiera que probara el deck antes de
    AD-05: si el repetido se limitara a devolver el swipe, esa persona seguiría
    swipeando a la derecha sin que su solicitud llegue nunca a quien publica."""
    huerfano = Swipe(user_id=adoptante.id, pet_id=mascota.id, direccion="like")
    db_session.add(huerfano)
    db_session.commit()
    assert _contar_matches(db_session) == 0

    respuesta = client.post(
        "/api/swipes",
        json={
            "user_id": adoptante.id,
            "pet_id": mascota.id,
            "direccion": "like",
            "mensaje": "Sigo interesada.",
        },
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["id"] == huerfano.id
    assert respuesta.json()["solicitud"] is not None
    assert _contar_matches(db_session, user_id=adoptante.id, pet_id=mascota.id) == 1
    assert _solicitud_de(db_session, adoptante.id, mascota.id).mensaje == "Sigo interesada."


def test_pass_preexistente_no_crea_solicitud_al_reintentar_con_like(
    client, db_session, adoptante, mascota
):
    """El repetido no cambia la dirección ya guardada (AD-03), así que tampoco
    puede crear la solicitud por la puerta de atrás: quien descartó y vuelve a
    swipear sigue con su `pass`. Pasar de "ahora no" a "me interesa" es una
    decisión de producto (AD-07), no un efecto colateral del gesto."""
    client.post(
        "/api/swipes",
        json={"user_id": adoptante.id, "pet_id": mascota.id, "direccion": "pass"},
    )
    reintento = client.post(
        "/api/swipes",
        json={"user_id": adoptante.id, "pet_id": mascota.id, "direccion": "like"},
    )

    assert reintento.status_code == 200
    assert reintento.json()["direccion"] == "pass"
    assert reintento.json()["solicitud"] is None
    assert _contar_matches(db_session) == 0


def test_carrera_por_el_mismo_like_no_duplica_la_solicitud(
    client, db_session, adoptante, mascota, monkeypatch
):
    """El select previo ciego, como en la carrera real de dos requests en
    serverless: ahora el `IntegrityError` puede venir de `uq_swipe_user_pet` **o**
    de `uq_match_user_pet`, y el `rollback()` tiene que dejar las dos tablas con
    una fila y devolver el 200 idempotente en vez de un 500 con traza."""
    cuerpo = {
        "user_id": adoptante.id,
        "pet_id": mascota.id,
        "direccion": "like",
        "mensaje": "Tengo patio.",
    }
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
    assert respuesta.json()["solicitud"]["id"] == primera.json()["solicitud"]["id"]
    assert _contar_swipes(db_session, user_id=adoptante.id, pet_id=mascota.id) == 1
    assert _contar_matches(db_session, user_id=adoptante.id, pet_id=mascota.id) == 1
    assert len(llamadas) == 2
