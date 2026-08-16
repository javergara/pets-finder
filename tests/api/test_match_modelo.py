"""Modelo `Match` (AD-05 paso 1): la solicitud de adopción, persistida.

La tabla **se sigue llamando `matches`** —es el nombre que traen las migraciones
del backlog y el del ADR 0002—, pero en la API, en el copy y en las pantallas se
llama siempre **"solicitud"**. Quien busque "match" en el producto no lo va a
encontrar: vive en el esquema, no en la interfaz.

Aquí solo se prueba la **persistencia**: el contrato HTTP (`SolicitudOut`, las
cuatro acciones) es de los pasos 2 y 3 y todavía no existe.

⚠️ `Match`, `Pet` y `User` se importan a nivel de módulo a propósito (mismo
motivo que en `test_home_profile_modelo.py`): si el modelo solo se importara
dentro de un test, `Base.metadata` podría no tener la tabla cuando la fixture
`db_session` hace `create_all`, y el fallo saldría como un `no such table`
intermitente según el orden de colección de pytest.
"""

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import configure_mappers

from reencuentro_api.models.match import Match
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
    """Quien mira el deck y hace el swipe-derecha: el `user_id` de `matches`."""
    return _usuario(db_session, "adoptante@example.com", "Adoptante de prueba")


@pytest.fixture()
def publicador(db_session) -> int:
    """Quien publicó la mascota y gestiona la solicitud: el `user_id` de `pets`."""
    return _usuario(db_session, "publicador@example.com", "Rescatista que publica")


# --- Round-trip --------------------------------------------------------------


def test_una_solicitud_se_guarda_con_sus_defaults(db_session, adoptante, publicador):
    """El swipe-derecha (paso 4) creará la fila con lo mínimo: adoptante, mascota
    y nada más. Todo lo demás lo pone el modelo."""
    pet_id = _mascota(db_session, publicador)

    db_session.add(Match(user_id=adoptante, pet_id=pet_id))
    db_session.commit()
    db_session.expunge_all()

    guardada = db_session.query(Match).one()
    assert guardada.user_id == adoptante
    assert guardada.pet_id == pet_id
    assert guardada.estado == "solicitado"
    assert guardada.creado_en is not None
    assert guardada.actualizado_en is None, "solo se llena cuando el publicador actúa"
    assert guardada.mensaje is None
    assert guardada.telefono_contacto is None
    assert guardada.motivo_descarte is None


def test_el_mensaje_y_el_telefono_del_adoptante_sobreviven_al_round_trip(
    db_session, adoptante, publicador
):
    """Las dos columnas entran ya en AD-05 aunque las use AD-06 (contacto por
    WhatsApp): así esa feature no necesita un `ALTER TABLE` y se ahorra una
    ventana de migración autorizada. El teléfono es del adoptante —el modelo
    `User` no tiene ninguno— y lo deja al swipear."""
    pet_id = _mascota(db_session, publicador)

    db_session.add(
        Match(
            user_id=adoptante,
            pet_id=pet_id,
            mensaje="Tengo patio y trabajo desde casa.",
            telefono_contacto="3001234567",
        )
    )
    db_session.commit()
    db_session.expunge_all()

    guardada = db_session.query(Match).one()
    assert guardada.mensaje == "Tengo patio y trabajo desde casa."
    assert guardada.telefono_contacto == "3001234567"


# --- Una solicitud por (adoptante, mascota) ----------------------------------


def test_no_se_puede_solicitar_dos_veces_la_misma_mascota(db_session, adoptante, publicador):
    """`uq_match_user_pet` es la garantía real de la idempotencia que pide el
    acceptance: en serverless dos requests del mismo dedo corren de verdad a la
    vez y los dos pueden ver vacío el select previo del endpoint."""
    pet_id = _mascota(db_session, publicador)
    db_session.add(Match(user_id=adoptante, pet_id=pet_id))
    db_session.commit()

    db_session.add(Match(user_id=adoptante, pet_id=pet_id))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_el_mismo_adoptante_puede_solicitar_dos_mascotas(db_session, adoptante, publicador):
    """El unique es por par, no por persona: alguien que busca compañía mira
    varias fichas y puede interesarse en más de una."""
    primera = _mascota(db_session, publicador, nombre="Nala")
    segunda = _mascota(db_session, publicador, nombre="Copito")

    db_session.add(Match(user_id=adoptante, pet_id=primera))
    db_session.add(Match(user_id=adoptante, pet_id=segunda))
    db_session.commit()
    db_session.expunge_all()

    assert db_session.query(Match).count() == 2


def test_dos_adoptantes_pueden_solicitar_la_misma_mascota(db_session, adoptante, publicador):
    """Es el caso que hace falta para el cierre masivo del paso 3: aprobar una
    solicitud cierra las demás de esa mascota. Sin varias solicitudes por mascota
    ese código no tendría nada que cerrar."""
    otro_adoptante = _usuario(db_session, "otra@example.com", "Otra adoptante")
    pet_id = _mascota(db_session, publicador)

    db_session.add(Match(user_id=adoptante, pet_id=pet_id))
    db_session.add(Match(user_id=otro_adoptante, pet_id=pet_id))
    db_session.commit()
    db_session.expunge_all()

    assert db_session.query(Match).count() == 2


# --- La colisión más peligrosa del portado -----------------------------------


def test_user_id_del_match_es_el_adoptante_no_el_publicador(db_session, adoptante, publicador):
    """`Match.user_id` es **quien pide adoptar**; `Pet.user_id` es **quien
    publicó**. Las dos son claves foráneas a `users.id`, así que ninguna base de
    datos avisa si se cruzan: el síntoma sería que el panel del publicador le
    muestre sus propias solicitudes, o que el adoptante gestione la mascota de
    otro."""
    pet_id = _mascota(db_session, publicador)

    db_session.add(Match(user_id=adoptante, pet_id=pet_id))
    db_session.commit()
    db_session.expunge_all()

    guardada = db_session.query(Match).one()
    assert guardada.user_id == adoptante
    assert guardada.user_id != publicador
    assert db_session.get(Pet, pet_id).user_id == publicador


def test_el_modelo_no_arrastra_shelter_id_ni_una_columna_de_afinidad():
    """Dos cosas que el `Match` de `adopta-v1` sí tenía y aquí no se portan:

    - `shelter_id`: los refugios ya no existen (una mascota cuelga de una
      organización **o** de un rescatista) y el dueño se resuelve por join a
      `pets`. Duplicarlo aquí repetiría el XOR de `ck_pets_publicador_exclusivo`
      en una segunda tabla y quedaría rancio si una mascota cambia de dueño.
    - Cualquier columna de afinidad: el score se calcula al vuelo (ADR 0003), y
      persistirlo lo dejaría mintiendo en cuanto el adoptante edite su hogar.
    """
    columnas = {columna.name for columna in Match.__table__.columns}

    assert "shelter_id" not in columnas
    assert "organizacion_id" not in columnas
    assert not [nombre for nombre in columnas if "afinidad" in nombre]


def test_motivo_descarte_admite_un_texto_de_500_caracteres(db_session, adoptante, publicador):
    """El tope declarado (`String(500)`, `varchar(500)` en Postgres) tiene que dar
    para el motivo más largo que el publicador pueda escribir. SQLite no fuerza la
    longitud, así que lo que prueba este caso es el round-trip completo del texto;
    quien lo hace cumplir de verdad es la migración, y el anti-drift la vigila."""
    pet_id = _mascota(db_session, publicador)
    motivo = "á" * 500

    db_session.add(
        Match(user_id=adoptante, pet_id=pet_id, estado="cerrado", motivo_descarte=motivo)
    )
    db_session.commit()
    db_session.expunge_all()

    guardada = db_session.query(Match).one()
    assert guardada.motivo_descarte == motivo
    assert len(guardada.motivo_descarte) == 500


# --- Guard de la trampa del portado ------------------------------------------


def test_importar_la_app_no_rompe_la_configuracion_de_los_mappers():
    """Ningún modelo de este stack declara `relationship()` salvo
    `Report.fotos_adicionales`. Reponer la que tenía `adopta-v1` (`user`, `pet`,
    `shelter` con `back_populates`) rompe el **import de toda la app**, no un
    endpoint: los `back_populates` apuntan a atributos que `User` y `Pet` no
    tienen aquí y `InvalidRequestError` salta al configurar los mappers. Es
    exactamente lo que tumbó el arranque entero en el paso 2 de AD-03.

    `configure_mappers()` es lo que fuerza el error: sin esa llamada la
    configuración es perezosa y el fallo aparecería en el primer request real.
    """
    from reencuentro_api.main import app

    configure_mappers()

    assert app.title
    assert not hasattr(Match, "user")
    assert not hasattr(Match, "pet")
