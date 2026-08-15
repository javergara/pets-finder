"""Modelo `HomeProfile` (AD-03 paso 2): perfil de hogar del adoptante.

Se adelanta de AD-04 a AD-03 por una razón de código, no de preferencia:
`services/afinidad.py` tiene la firma `calcular_afinidad(pet: Pet, home:
HomeProfile)` y no puede existir sin este modelo; y si el deck consultara
`home_profiles` sin que la tabla exista en producción, la ruta respondería 500
(`SKIP_DB_CREATE_ALL=1` no crea nada por su cuenta).

Aquí solo se prueba la **persistencia**: el contrato HTTP (`HomeProfileIn/Out`,
`PUT/GET /api/users/{id}/home-profile`) es de AD-04 y todavía no existe.

⚠️ `HomeProfile` y `User` se importan a nivel de módulo a propósito: si el
modelo solo se importara dentro de un test, `Base.metadata` podría no tener la
tabla cuando la fixture `db_session` hace `create_all`, y el fallo saldría como
un `no such table` intermitente según el orden de colección de pytest.
"""

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import configure_mappers

from reencuentro_api.models.home_profile import HomeProfile
from reencuentro_api.models.user import User


def _usuario(db_session, email: str = "adoptante@example.com") -> int:
    """Devuelve el **id**, no la instancia: los tests hacen `expunge_all()` para
    releer de verdad desde la DB, y un `User` desprendido explota con
    `DetachedInstanceError` al pedirle cualquier atributo después."""
    user = User(nombre="Adoptante de prueba", email=email, ciudad="Armenia")
    db_session.add(user)
    db_session.flush()
    return user.id


def _perfil(user_id: int, **cambios) -> HomeProfile:
    datos = dict(
        vivienda="casa",
        espacio_exterior="patio",
        personas_en_casa=3,
        tiene_ninos=True,
        tiene_otros_perros=False,
        tiene_otros_gatos=True,
        horas_fuera_dia=6,
        experiencia_previa="algo",
        presupuesto_mensual_cop=180_000,
        preferencia_especies=["perro", "gato"],
        preferencia_tamanos=["mediano", "grande"],
        preferencia_energia="media",
    )
    datos.update(cambios)
    return HomeProfile(user_id=user_id, **datos)


# --- Round-trip -------------------------------------------------------------


def test_un_perfil_de_hogar_se_guarda_y_se_recupera_completo(db_session):
    user_id = _usuario(db_session)

    db_session.add(_perfil(user_id))
    db_session.commit()
    db_session.expunge_all()

    guardado = db_session.get(HomeProfile, user_id)
    assert guardado is not None
    assert guardado.user_id == user_id
    assert guardado.vivienda == "casa"
    assert guardado.espacio_exterior == "patio"
    assert guardado.personas_en_casa == 3
    assert guardado.tiene_ninos is True
    assert guardado.tiene_otros_perros is False
    assert guardado.tiene_otros_gatos is True
    assert guardado.horas_fuera_dia == 6
    assert guardado.experiencia_previa == "algo"
    assert guardado.presupuesto_mensual_cop == 180_000
    assert guardado.preferencia_energia == "media"


def test_las_preferencias_sobreviven_al_round_trip_como_listas(db_session):
    """Son columnas JSON: si se guardaran como texto plano volverían como `str`
    y `pet.especie in home.preferencia_especies` haría match por subcadena."""
    user_id = _usuario(db_session)

    db_session.add(
        _perfil(
            user_id,
            preferencia_especies=["gato"],
            preferencia_tamanos=["pequeño", "mediano", "grande"],
        )
    )
    db_session.commit()
    db_session.expunge_all()

    guardado = db_session.get(HomeProfile, user_id)
    assert guardado.preferencia_especies == ["gato"]
    assert guardado.preferencia_tamanos == ["pequeño", "mediano", "grande"]


def test_una_lista_de_preferencias_vacia_se_guarda_vacia(db_session):
    """`_score_preferencia` de `services/afinidad.py` (paso 3) trata la lista
    vacía como "sin preferencia" (100), no como "no le sirve ninguna": tiene que
    volver `[]` y no `None`."""
    user_id = _usuario(db_session)

    db_session.add(_perfil(user_id, preferencia_especies=[], preferencia_tamanos=[]))
    db_session.commit()
    db_session.expunge_all()

    guardado = db_session.get(HomeProfile, user_id)
    assert guardado.preferencia_especies == []
    assert guardado.preferencia_tamanos == []


# --- `user_id` es la PK: un perfil por persona -------------------------------


def test_user_id_es_la_llave_primaria_y_no_admite_dos_perfiles(db_session):
    """Sin `id` propio: la existencia de la fila *es* la señal de "cuestionario
    completo", y guardar de nuevo tiene que reemplazar, nunca duplicar (el
    upsert de AD-04 se apoya en esto)."""
    user_id = _usuario(db_session)
    db_session.add(_perfil(user_id))
    db_session.commit()

    db_session.add(_perfil(user_id, vivienda="apartamento"))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_el_perfil_se_edita_reemplazando_la_misma_fila(db_session):
    user_id = _usuario(db_session)
    db_session.add(_perfil(user_id))
    db_session.commit()

    guardado = db_session.get(HomeProfile, user_id)
    guardado.vivienda = "apartamento"
    guardado.preferencia_especies = ["gato"]
    db_session.commit()
    db_session.expunge_all()

    assert db_session.query(HomeProfile).count() == 1
    releido = db_session.get(HomeProfile, user_id)
    assert releido.vivienda == "apartamento"
    assert releido.preferencia_especies == ["gato"]


def test_dos_usuarios_distintos_tienen_cada_uno_su_perfil(db_session):
    ana_id = _usuario(db_session, "ana@example.com")
    carlos_id = _usuario(db_session, "carlos@example.com")

    db_session.add(_perfil(ana_id, vivienda="casa"))
    db_session.add(_perfil(carlos_id, vivienda="apartamento"))
    db_session.commit()
    db_session.expunge_all()

    assert db_session.get(HomeProfile, ana_id).vivienda == "casa"
    assert db_session.get(HomeProfile, carlos_id).vivienda == "apartamento"


# --- El presupuesto es opcional ---------------------------------------------


def test_el_presupuesto_mensual_puede_quedar_vacio(db_session):
    """Decisión de producto: pedir un presupuesto mensual en COP en plena
    emergencia añade fricción y tono equivocado. Quien no lo dé conserva el
    resto de su perfil, y `afinidad.py` degrada a solo-experiencia."""
    user_id = _usuario(db_session)

    db_session.add(_perfil(user_id, presupuesto_mensual_cop=None))
    db_session.commit()
    db_session.expunge_all()

    guardado = db_session.get(HomeProfile, user_id)
    assert guardado.presupuesto_mensual_cop is None
    assert guardado.experiencia_previa == "algo"


# --- Guard de la trampa del portado -----------------------------------------


def test_importar_la_app_no_rompe_la_configuracion_de_los_mappers():
    """El `HomeProfile` de `adopta-v1` declara
    `user: Mapped["User"] = relationship(back_populates="home_profile")`, y el
    `User` de este repo **no tiene ese atributo**: al configurar los mappers
    salta `InvalidRequestError` y falla el **import de toda la app**, no solo un
    endpoint. Por eso la relación se borró al portar (ningún modelo de este
    stack declara relaciones salvo `Report.fotos_adicionales`).

    `configure_mappers()` es lo que fuerza el error: sin esa llamada la
    configuración es perezosa y el fallo aparecería en el primer request real.
    """
    from reencuentro_api.main import app

    configure_mappers()

    assert app.title
    assert not hasattr(HomeProfile, "user")
