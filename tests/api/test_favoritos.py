"""Favoritos del módulo de adopción (AD-07 paso 2): las tres rutas de
`/api/users/{user_id}/favorites`.

Doce de estos casos vienen portados de `adopta-v1` (`tests/api/test_favorites.py`,
consultable con `git show origin/adopta-v1:tests/api/test_favorites.py`); los
demás son nuevos y cubren lo que aquella versión no tenía: el 403 de la lista
ajena y su orden respecto al 404, la colisión de `user_id`, el orden explícito de
la lista y la lista sin perfil de hogar.

⚠️ **`Favorite.user_id` es el ADOPTANTE que MIRA**, al revés que `Pet.user_id`,
que es quien **PUBLICA**. Las dos son FK a `users.id` y ninguna base de datos
avisa si se cruzan (ver `models/favorite.py`), así que las fixtures de aquí se
llaman `adoptante` y `publicador` y
`test_los_favoritos_no_se_cruzan_con_quien_publico_la_mascota` es el candado.

⚠️ `Favorite`, `Pet`, `User`, `Swipe` y `Match` se importan a nivel de módulo a
propósito: el fixture `db_session` hace `create_all` con lo que esté registrado en
`Base.metadata` en ese instante, y un import perezoso produce un `no such table`
intermitente según el orden de colección de pytest.
"""

from datetime import datetime, timezone

import pytest
from sqlalchemy import func, select

from reencuentro_api.models.favorite import Favorite
from reencuentro_api.models.match import Match
from reencuentro_api.models.pet import Pet
from reencuentro_api.models.swipe import Swipe
from reencuentro_api.models.user import User


@pytest.fixture()
def adoptante(db_session):
    """Quien guarda mascotas: el `user_id` de la ruta de favoritos."""
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
    """El rescatista dueño de la mascota: NO es quien la guarda."""
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


def _contar_favoritos(db_session, **filtros) -> int:
    """Filas reales de `favorites`, no lo que diga la respuesta HTTP.

    Sin filtros cuenta la tabla entera: es la única forma de ver una fila que se
    insertó igual mientras el endpoint respondía un 404 (SQLite no fuerza las FK).
    """
    query = select(func.count()).select_from(Favorite)
    for campo, valor in filtros.items():
        query = query.where(getattr(Favorite, campo) == valor)
    return db_session.execute(query).scalar_one()


# --- POST /api/users/{user_id}/favorites --------------------------------------


def test_marcar_favorito_nuevo_devuelve_201(client, db_session, adoptante, mascota):
    respuesta = client.post(f"/api/users/{adoptante.id}/favorites", json={"pet_id": mascota.id})

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["id"] == mascota.id
    # La respuesta tiene que decir ya lo que la pantalla va a pintar: sin esto el
    # corazón se apagaría al llegar la respuesta del toque que lo encendió.
    assert cuerpo["es_favorito"] is True

    persistido = db_session.execute(
        select(Favorite).where(Favorite.user_id == adoptante.id, Favorite.pet_id == mascota.id)
    ).scalar_one_or_none()
    assert persistido is not None


def test_marcar_favorito_dos_veces_es_idempotente(client, db_session, adoptante, mascota):
    primera = client.post(f"/api/users/{adoptante.id}/favorites", json={"pet_id": mascota.id})
    segunda = client.post(f"/api/users/{adoptante.id}/favorites", json={"pet_id": mascota.id})

    assert primera.status_code == 201
    assert segunda.status_code == 200
    assert segunda.json()["es_favorito"] is True
    assert _contar_favoritos(db_session, user_id=adoptante.id, pet_id=mascota.id) == 1


def test_marcar_favorito_usuario_inexistente_devuelve_404(client, mascota):
    respuesta = client.post("/api/users/9999/favorites", json={"pet_id": mascota.id})

    assert respuesta.status_code == 404
    assert "9999" in respuesta.json()["detail"]


def test_marcar_favorito_mascota_inexistente_devuelve_404(client, db_session, adoptante):
    respuesta = client.post(f"/api/users/{adoptante.id}/favorites", json={"pet_id": 9999})

    assert respuesta.status_code == 404
    assert "9999" in respuesta.json()["detail"]
    # ⚠️ El status por sí solo no prueba nada: SQLite no fuerza las FK, así que si
    # el 404 no saliera de una comprobación explícita en el router, la fila se
    # insertaría igual y este test seguiría verde. Se asevera el estado.
    assert _contar_favoritos(db_session) == 0


# --- DELETE /api/users/{user_id}/favorites/{pet_id} ---------------------------


def test_desmarcar_favorito_existente_devuelve_204_y_borra(client, db_session, adoptante, mascota):
    client.post(f"/api/users/{adoptante.id}/favorites", json={"pet_id": mascota.id})

    respuesta = client.delete(f"/api/users/{adoptante.id}/favorites/{mascota.id}")

    assert respuesta.status_code == 204
    assert _contar_favoritos(db_session, user_id=adoptante.id, pet_id=mascota.id) == 0


def test_desmarcar_favorito_inexistente_devuelve_204_igual(client, adoptante, mascota):
    """Quitar algo que no estaba guardado es un 204, nunca un 404.

    El gesto que importa es el resultado ("esta mascota ya no está en mi lista"),
    y ese resultado ya se cumple. Un 404 haría que la pantalla pintara un error
    por un doble-tap.
    """
    respuesta = client.delete(f"/api/users/{adoptante.id}/favorites/{mascota.id}")

    assert respuesta.status_code == 204


# --- GET /api/users/{user_id}/favorites ---------------------------------------


def test_listar_favoritos_devuelve_mascotas_con_es_favorito_true(
    client, db_session, adoptante, publicador
):
    canela = _pet(publicador.id, nombre="Canela")
    michi = _pet(publicador.id, nombre="Michi", especie="gato")
    db_session.add_all([canela, michi])
    db_session.commit()
    client.post(f"/api/users/{adoptante.id}/favorites", json={"pet_id": canela.id})
    client.post(f"/api/users/{adoptante.id}/favorites", json={"pet_id": michi.id})

    respuesta = client.get(f"/api/users/{adoptante.id}/favorites?solicitante_id={adoptante.id}")

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert {m["nombre"] for m in cuerpo} == {"Canela", "Michi"}
    assert all(m["es_favorito"] is True for m in cuerpo)
    # El publicador viaja igual que en el catálogo: la lista reusa `_pet_out`.
    assert all(m["publicador"]["id"] == publicador.id for m in cuerpo)


def test_listar_favoritos_usuario_inexistente_devuelve_404(client):
    """Auto-consulta con un id que no existe: 404, no 403.

    `solicitante_id` es el mismo `user_id` a propósito — con otro daría 403 antes
    de mirar si el usuario existe, que es justo lo que fija el test del oráculo.
    """
    respuesta = client.get("/api/users/9999/favorites?solicitante_id=9999")

    assert respuesta.status_code == 404
    assert "9999" in respuesta.json()["detail"]


def test_listar_favoritos_sin_favoritos_devuelve_200_vacio(client, adoptante):
    respuesta = client.get(f"/api/users/{adoptante.id}/favorites?solicitante_id={adoptante.id}")

    assert respuesta.status_code == 200
    assert respuesta.json() == []


def test_listar_favoritos_de_otra_persona_devuelve_403(client, adoptante, otro_adoptante, mascota):
    """Los favoritos son un historial de navegación con nombre propio.

    No es autenticación (`solicitante_id` es autodeclarado y la app no tiene
    login): impide la fuga accidental y obliga a que una fuga sea deliberada.
    """
    client.post(f"/api/users/{adoptante.id}/favorites", json={"pet_id": mascota.id})

    respuesta = client.get(
        f"/api/users/{adoptante.id}/favorites?solicitante_id={otro_adoptante.id}"
    )

    assert respuesta.status_code == 403
    # Ni un nombre de mascota se filtra en el cuerpo del rechazo.
    assert "Canela" not in respuesta.text


def test_listar_favoritos_ajenos_de_un_usuario_inexistente_devuelve_403(client, adoptante):
    """El 403 va ANTES del 404, y este es el test que lo fija.

    Al revés, la respuesta sería un oráculo de enumeración: 404 diría "ese id no
    existe" y 403 "ese id sí existe", y los ids de esta app son secuenciales.
    """
    respuesta = client.get(f"/api/users/9999/favorites?solicitante_id={adoptante.id}")

    assert respuesta.status_code == 403


def test_listar_favoritos_respeta_el_orden_de_guardado(client, db_session, adoptante, publicador):
    """Lo último guardado primero, con `pet_id` desc como desempate.

    ⚠️ Los `creado_en` se fijan a mano porque el orden tiene que ser el de
    guardado y **no** el de inserción de las filas: sin `ORDER BY`, SQLite
    devuelve el segundo y parece correcto, pero en Postgres el orden es
    arbitrario y la rejilla se baraja entre recargas (el defecto de `adopta-v1`,
    que además hacía dos queries).
    """
    mascotas = [_pet(publicador.id, nombre=f"Mascota {i}") for i in range(1, 5)]
    db_session.add_all(mascotas)
    db_session.commit()
    p1, p2, p3, p4 = mascotas
    momentos = {
        p1.id: datetime(2026, 8, 16, 10, 0, tzinfo=timezone.utc),
        p2.id: datetime(2026, 8, 16, 12, 0, tzinfo=timezone.utc),
        p3.id: datetime(2026, 8, 16, 11, 0, tzinfo=timezone.utc),
        # Empate exacto con p2: decide el `pet_id` desc.
        p4.id: datetime(2026, 8, 16, 12, 0, tzinfo=timezone.utc),
    }
    # Se insertan en orden de id (1, 2, 3, 4), que NO es el orden esperado.
    for pet in mascotas:
        db_session.add(Favorite(user_id=adoptante.id, pet_id=pet.id, creado_en=momentos[pet.id]))
    db_session.commit()

    respuesta = client.get(f"/api/users/{adoptante.id}/favorites?solicitante_id={adoptante.id}")

    assert respuesta.status_code == 200
    assert [m["id"] for m in respuesta.json()] == [p4.id, p2.id, p3.id, p1.id]


def test_listar_favoritos_no_exige_perfil_de_hogar(client, adoptante, mascota):
    """Sin `HomeProfile` la lista responde 200 con `afinidad: null`.

    Mismo criterio que el deck de AD-03: un guard bloqueante rompería el
    onboarding de quien todavía no llenó el cuestionario, que es la mayoría.
    """
    client.post(f"/api/users/{adoptante.id}/favorites", json={"pet_id": mascota.id})

    respuesta = client.get(f"/api/users/{adoptante.id}/favorites?solicitante_id={adoptante.id}")

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert len(cuerpo) == 1
    assert cuerpo[0]["afinidad"] is None


def test_los_favoritos_no_se_cruzan_con_quien_publico_la_mascota(
    client, db_session, adoptante, publicador
):
    """El candado de la colisión de `user_id` (ver el aviso del módulo).

    `Favorite.user_id` es quien MIRA y `Pet.user_id` quien PUBLICA: si el router
    consultara la columna equivocada, a quien publicó le saldrían sus propias
    mascotas como "mis favoritas" y la lista de quien las guardó saldría vacía.
    Ninguna base de datos avisa de ese cruce: las dos son FK a `users.id`.
    """
    pet = _pet(publicador.id, nombre="Canela")
    db_session.add(pet)
    db_session.commit()

    client.post(f"/api/users/{adoptante.id}/favorites", json={"pet_id": pet.id})

    del_publicador = client.get(
        f"/api/users/{publicador.id}/favorites?solicitante_id={publicador.id}"
    )
    del_adoptante = client.get(f"/api/users/{adoptante.id}/favorites?solicitante_id={adoptante.id}")

    assert del_publicador.status_code == 200
    assert del_publicador.json() == []
    assert [m["id"] for m in del_adoptante.json()] == [pet.id]


# --- Acceptance 2: favoritos es independiente de swipes y solicitudes ----------


def test_marcar_favorito_no_crea_swipe_ni_solicitud(client, db_session, adoptante, mascota):
    """Guardar no es decidir: el corazón no puede pedir una mascota en adopción.

    Se cuentan las filas de `swipes` y `matches`, no la respuesta HTTP: una
    solicitud creada de más sería invisible en el cuerpo del POST y le aparecería
    a quien publica en su panel como una familia interesada que nunca escribió.
    """
    client.post(f"/api/users/{adoptante.id}/favorites", json={"pet_id": mascota.id})

    swipes = db_session.execute(select(func.count()).select_from(Swipe)).scalar_one()
    solicitudes = db_session.execute(select(func.count()).select_from(Match)).scalar_one()

    assert swipes == 0
    assert solicitudes == 0


def test_la_mascota_favoriteada_sigue_en_el_deck(client, adoptante, mascota):
    """El deck solo excluye por `Swipe.pet_id`, nunca por favorito.

    Si guardar sacara la carta, el gesto más inocente de la pantalla haría
    desaparecer la mascota de la única vista donde se descubre.
    """
    client.post(f"/api/users/{adoptante.id}/favorites", json={"pet_id": mascota.id})

    respuesta = client.get(f"/api/pets/deck?adoptante_id={adoptante.id}")

    assert respuesta.status_code == 200
    assert [m["id"] for m in respuesta.json()] == [mascota.id]
