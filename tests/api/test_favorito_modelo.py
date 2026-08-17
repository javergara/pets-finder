"""Modelo `Favorite` (AD-07 paso 1): "guardar para después", persistido.

Un favorito es un marcador de navegación, no una decisión: **no** crea un
`Swipe`, **no** crea una solicitud (`matches`) y **no** saca la mascota del deck.
Esa independencia es una regla heredada de `adopta-v1` y se prueba de verdad en
el paso 3, cuando exista el endpoint; aquí solo se prueba la **persistencia**.

⚠️ `Favorite`, `Pet` y `User` se importan a nivel de módulo a propósito (mismo
motivo que en `test_match_modelo.py`): si el modelo solo se importara dentro de
un test, `Base.metadata` podría no tener la tabla cuando la fixture `db_session`
hace `create_all`, y el fallo saldría como un `no such table` intermitente según
el orden de colección de pytest.
"""

import pytest
from sqlalchemy import UniqueConstraint
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import configure_mappers

from reencuentro_api.models.favorite import Favorite
from reencuentro_api.models.pet import Pet
from reencuentro_api.models.user import User


def _usuario(db_session, email: str, nombre: str) -> int:
    """Devuelve el **id**, no la instancia: los tests hacen `expunge_all()` para
    releer de verdad desde la DB, y un `User` desprendido explota con
    `DetachedInstanceError` al pedirle cualquier atributo después."""
    user = User(nombre=nombre, email=email, ciudad="Armenia")
    db_session.add(user)
    db_session.flush()
    return user.id


def _mascota(db_session, publicador_id: int, nombre: str = "Nala") -> int:
    """Mascota de **rescatista individual**: `Pet.user_id` es quien la publicó.
    Es la mitad del cruce que persigue este archivo."""
    pet = Pet(
        user_id=publicador_id,
        nombre=nombre,
        especie="perro",
        sexo="hembra",
        edad_meses=24,
        tamano="mediano",
        energia="media",
        historia="Rescatada tras el terremoto.",
        zona="armenia",
    )
    db_session.add(pet)
    db_session.flush()
    return pet.id


@pytest.fixture()
def adoptante(db_session) -> int:
    """Quien mira el catálogo y guarda la mascota: el `user_id` de `favorites`."""
    return _usuario(db_session, "adoptante@example.com", "Adoptante de prueba")


@pytest.fixture()
def publicador(db_session) -> int:
    """Quien publicó la mascota: el `user_id` de `pets`, que NO es este."""
    return _usuario(db_session, "publicador@example.com", "Rescatista que publica")


# --- Round-trip --------------------------------------------------------------


def test_un_favorito_se_guarda_con_su_fecha(db_session, adoptante, publicador):
    """La existencia de la fila **es** la señal (mismo criterio que `HomeProfile`):
    no hay columna de estado que pueda quedar desincronizada con la realidad.
    `creado_en` lo pone Python, no la DB — la migración va sin `DEFAULT`."""
    pet_id = _mascota(db_session, publicador)

    db_session.add(Favorite(user_id=adoptante, pet_id=pet_id))
    db_session.commit()
    db_session.expunge_all()

    guardado = db_session.query(Favorite).one()
    assert guardado.user_id == adoptante
    assert guardado.pet_id == pet_id
    assert guardado.creado_en is not None


# --- Un favorito por (adoptante, mascota) ------------------------------------


def test_dos_favoritos_iguales_violan_el_unique(db_session, adoptante, publicador):
    """`uq_favorite_user_pet` es la garantía real de la idempotencia del POST:
    `adopta-v1` la resolvía solo con un select previo en el router, y en
    serverless dos requests del mismo dedo corren de verdad a la vez y los dos
    pueden ver ese select vacío. El endpoint del paso 2 hará igual el select (para
    responder 200 en vez de un error), pero quien lo garantiza es esta fila."""
    pet_id = _mascota(db_session, publicador)
    db_session.add(Favorite(user_id=adoptante, pet_id=pet_id))
    db_session.commit()

    db_session.add(Favorite(user_id=adoptante, pet_id=pet_id))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_el_unique_se_llama_uq_favorite_user_pet():
    """El nombre no es cosmético: **viaja a la migración** escrita a mano y es el
    que buscará la verificación post-migración en `pg_constraint`. Si alguien lo
    renombra en el modelo, el anti-drift de `AD-07-favorites.sql` tiene que
    enterarse — por eso el nombre se asevera aquí y allá."""
    uniques = {
        constraint.name: [columna.name for columna in constraint.columns]
        for constraint in Favorite.__table__.constraints
        if isinstance(constraint, UniqueConstraint)
    }

    assert "uq_favorite_user_pet" in uniques, f"Uniques declarados: {sorted(uniques)}"
    assert uniques["uq_favorite_user_pet"] == ["user_id", "pet_id"]


def test_el_mismo_adoptante_puede_guardar_dos_mascotas(db_session, adoptante, publicador):
    """El unique es por par, no por persona: la pantalla de favoritas del paso 5
    no tendría sentido si solo cupiera una."""
    primera = _mascota(db_session, publicador, nombre="Nala")
    segunda = _mascota(db_session, publicador, nombre="Copito")

    db_session.add(Favorite(user_id=adoptante, pet_id=primera))
    db_session.add(Favorite(user_id=adoptante, pet_id=segunda))
    db_session.commit()
    db_session.expunge_all()

    assert db_session.query(Favorite).count() == 2


# --- La colisión más peligrosa del portado -----------------------------------


def test_user_id_del_favorito_es_quien_mira_no_quien_publico(db_session, adoptante, publicador):
    """`Favorite.user_id` es **quien mira**; `Pet.user_id` es **quien publica**.
    Las dos son claves foráneas a `users.id`, así que ninguna base de datos avisa
    si se cruzan: el síntoma sería que a quien publica le aparezcan sus propias
    mascotas como "mis favoritas", o que la lista de una persona muestre lo que
    guardó otra."""
    pet_id = _mascota(db_session, publicador)

    db_session.add(Favorite(user_id=adoptante, pet_id=pet_id))
    db_session.commit()
    db_session.expunge_all()

    guardado = db_session.query(Favorite).one()
    assert guardado.user_id == adoptante
    assert guardado.user_id != publicador
    assert db_session.get(Pet, pet_id).user_id == publicador


# --- Guard de la trampa del portado ------------------------------------------


def test_importar_la_app_no_rompe_la_configuracion_de_los_mappers():
    """Ningún modelo de este stack declara `relationship()` salvo
    `Report.fotos_adicionales`. Reponer una `back_populates` contra `User` o `Pet`
    —que aquí no tienen el atributo del otro lado— rompe el **import de toda la
    app**, no un endpoint: `InvalidRequestError` salta al configurar los mappers.
    Es exactamente lo que tumbó el arranque entero al portar `HomeProfile`.

    `configure_mappers()` es lo que fuerza el error: sin esa llamada la
    configuración es perezosa y el fallo aparecería en el primer request real.
    """
    from reencuentro_api.main import app

    configure_mappers()

    assert app.title
    assert not hasattr(Favorite, "user")
    assert not hasattr(Favorite, "pet")
