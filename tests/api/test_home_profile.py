"""Contrato HTTP del perfil de hogar (AD-04 paso 2).

`PUT`/`GET /api/users/{user_id}/home-profile`. El **modelo** ya estaba cubierto
por `test_home_profile_modelo.py` (AD-03 paso 2) y aquí no se re-litiga: esto
prueba el upsert real, la autoría y el catálogo de respuestas por HTTP.

⚠️ `User` y `HomeProfile` se importan a nivel de módulo a propósito: el fixture
`db_session` hace `create_all` con lo que esté registrado en `Base.metadata` en
ese instante, y un import perezoso produce un `no such table` intermitente según
el orden de colección de pytest.
"""

import pytest
from sqlalchemy import func, select

from reencuentro_api.models.home_profile import HomeProfile
from reencuentro_api.models.user import User

MENSAJE_403_GET = "Solo puedes consultar tu propio perfil de hogar"


@pytest.fixture()
def usuario(db_session):
    user = User(nombre="Ana", email="ana@example.co", ciudad="Armenia")
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture()
def tercero(db_session):
    """Otra persona con cuenta: quien intenta espiar, y a quien se espía."""
    user = User(nombre="Lucía", email="lucia@example.co", ciudad="Pereira")
    db_session.add(user)
    db_session.commit()
    return user


def _payload(user_id: int, **overrides) -> dict:
    datos = {
        "user_id": user_id,
        "vivienda": "casa",
        "espacio_exterior": "patio",
        "personas_en_casa": 3,
        "tiene_ninos": False,
        "tiene_otros_perros": False,
        "tiene_otros_gatos": True,
        "horas_fuera_dia": 6,
        "experiencia_previa": "algo",
        "presupuesto_mensual_cop": 200_000,
        "preferencia_especies": ["perro", "gato"],
        "preferencia_tamanos": ["mediano"],
        "preferencia_energia": "media",
    }
    datos.update(overrides)
    return datos


def _filas(db_session) -> int:
    return db_session.execute(select(func.count()).select_from(HomeProfile)).scalar_one()


# --- PUT: crear y actualizar la misma fila (acceptance 1) ----------------------


def test_put_crea_el_perfil_y_la_fila_queda_en_la_base(client, db_session, usuario):
    """El 200 no basta: se lee la fila para comprobar que se persistió de verdad."""
    respuesta = client.put(
        f"/api/users/{usuario.id}/home-profile",
        json=_payload(usuario.id, horas_fuera_dia=9),
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["horas_fuera_dia"] == 9

    db_session.expire_all()
    fila = db_session.get(HomeProfile, usuario.id)
    assert fila is not None
    assert fila.vivienda == "casa"
    assert fila.espacio_exterior == "patio"
    assert fila.personas_en_casa == 3
    assert fila.tiene_otros_gatos is True
    assert fila.horas_fuera_dia == 9
    assert fila.experiencia_previa == "algo"
    assert fila.presupuesto_mensual_cop == 200_000
    assert fila.preferencia_especies == ["perro", "gato"]
    assert fila.preferencia_tamanos == ["mediano"]
    assert fila.preferencia_energia == "media"


def test_put_dos_veces_actualiza_la_misma_fila_y_no_crea_otra(client, db_session, usuario):
    """Acceptance 1: guardar dos veces deja **un** perfil, con los valores nuevos.

    Nunca 201 en la creación: el cliente tendría que ramificar entre "crear" y
    "editar" para leer el mismo cuerpo, y el wizard de AD-04 no sabe (ni debe
    saber) si la persona ya había contestado.
    """
    primera = client.put(
        f"/api/users/{usuario.id}/home-profile",
        json=_payload(usuario.id, vivienda="apartamento", horas_fuera_dia=4),
    )
    segunda = client.put(
        f"/api/users/{usuario.id}/home-profile",
        json=_payload(
            usuario.id,
            vivienda="casa",
            horas_fuera_dia=10,
            preferencia_especies=["gato"],
            presupuesto_mensual_cop=350_000,
        ),
    )

    assert primera.status_code == 200
    assert segunda.status_code == 200
    assert _filas(db_session) == 1

    db_session.expire_all()
    fila = db_session.get(HomeProfile, usuario.id)
    assert fila.vivienda == "casa"
    assert fila.horas_fuera_dia == 10
    assert fila.presupuesto_mensual_cop == 350_000
    # La lista JSON se reemplaza entera (no lleva `MutableList`): si el router
    # hiciera `.append`, aquí seguirían las dos especies de la primera llamada.
    assert fila.preferencia_especies == ["gato"]


# --- PUT: autoría y usuario inexistente ----------------------------------------


def test_put_con_user_id_ajeno_en_el_body_es_403_y_no_escribe_nada(
    client, db_session, usuario, tercero
):
    """El `user_id` del body es redundante con el de la ruta a propósito (patrón
    `PetIn`/`OrganizacionUpdate`): comparar ambos es lo que produce el 403."""
    respuesta = client.put(
        f"/api/users/{tercero.id}/home-profile",
        json=_payload(usuario.id),
    )

    assert respuesta.status_code == 403
    assert respuesta.json()["detail"]
    assert _filas(db_session) == 0


def test_put_a_usuario_inexistente_devuelve_404(client, db_session):
    respuesta = client.put("/api/users/9999/home-profile", json=_payload(9999))

    assert respuesta.status_code == 404
    assert "9999" in respuesta.json()["detail"]
    assert _filas(db_session) == 0


# --- PUT: el presupuesto es opcional de verdad ---------------------------------


def test_put_sin_el_campo_presupuesto_lo_guarda_vacio(client, db_session, usuario):
    datos = _payload(usuario.id)
    del datos["presupuesto_mensual_cop"]

    respuesta = client.put(f"/api/users/{usuario.id}/home-profile", json=datos)

    assert respuesta.status_code == 200
    assert respuesta.json()["presupuesto_mensual_cop"] is None
    db_session.expire_all()
    assert db_session.get(HomeProfile, usuario.id).presupuesto_mensual_cop is None


def test_put_con_presupuesto_null_explicito_lo_guarda_vacio(client, db_session, usuario):
    """La otra forma de "no lo dije": el wizard manda el campo con `null` cuando
    la persona lo deja en blanco después de haberlo llenado. Un `Field(ge=0)` sin
    `| None` rechazaría este cuerpo con 422 y el paso quedaría sin salida."""
    respuesta = client.put(
        f"/api/users/{usuario.id}/home-profile",
        json=_payload(usuario.id, presupuesto_mensual_cop=None),
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["presupuesto_mensual_cop"] is None
    db_session.expire_all()
    assert db_session.get(HomeProfile, usuario.id).presupuesto_mensual_cop is None


# --- PUT: catálogo y rangos (422 uno por uno) ----------------------------------


@pytest.mark.parametrize(
    "campo,valor",
    [
        ("vivienda", "finca"),
        ("espacio_exterior", "terraza"),
        ("experiencia_previa", "poquita"),
        ("horas_fuera_dia", 25),
        ("horas_fuera_dia", -1),
        ("personas_en_casa", 0),
        ("preferencia_energia", "eléctrica"),
        ("preferencia_especies", ["dinosaurio"]),
        ("preferencia_tamanos", ["gigante"]),
        ("presupuesto_mensual_cop", -1),
        ("presupuesto_mensual_cop", 10_000_001),
    ],
)
def test_put_rechaza_valores_fuera_de_catalogo_o_de_rango(
    client, db_session, usuario, campo, valor
):
    respuesta = client.put(
        f"/api/users/{usuario.id}/home-profile",
        json=_payload(usuario.id, **{campo: valor}),
    )

    assert respuesta.status_code == 422, f"{campo}={valor!r} debería ser inválido"
    assert _filas(db_session) == 0


# --- GET: lo propio ------------------------------------------------------------


def test_get_propio_devuelve_las_doce_respuestas(client, db_session, usuario):
    """El cuerpo exacto, campo por campo: es lo que precarga el wizard de AD-04.

    Va como igualdad y no como `in`: si mañana alguien añadiera aquí un dato que
    no es una respuesta del cuestionario, tiene que ser una decisión y no un
    descuido.
    """
    client.put(f"/api/users/{usuario.id}/home-profile", json=_payload(usuario.id))

    respuesta = client.get(f"/api/users/{usuario.id}/home-profile?solicitante_id={usuario.id}")

    assert respuesta.status_code == 200
    assert len(respuesta.json()) == 12
    assert respuesta.json() == {
        "vivienda": "casa",
        "espacio_exterior": "patio",
        "personas_en_casa": 3,
        "tiene_ninos": False,
        "tiene_otros_perros": False,
        "tiene_otros_gatos": True,
        "horas_fuera_dia": 6,
        "experiencia_previa": "algo",
        "presupuesto_mensual_cop": 200_000,
        "preferencia_especies": ["perro", "gato"],
        "preferencia_tamanos": ["mediano"],
        "preferencia_energia": "media",
    }


def test_get_propio_sin_perfil_devuelve_404_en_espanol(client, db_session, usuario):
    """El 404 es la señal de "todavía no contestó el cuestionario": el cliente de
    AD-04 lo mapea a `null` y la pantalla ofrece el wizard vacío."""
    respuesta = client.get(f"/api/users/{usuario.id}/home-profile?solicitante_id={usuario.id}")

    assert respuesta.status_code == 404
    detalle = respuesta.json()["detail"]
    assert "perfil de hogar" in detalle


def test_get_de_un_usuario_inexistente_devuelve_404(client, db_session):
    respuesta = client.get("/api/users/9999/home-profile?solicitante_id=9999")

    assert respuesta.status_code == 404
    assert "9999" in respuesta.json()["detail"]


def test_get_sin_solicitante_id_es_422(client, db_session, usuario):
    """`solicitante_id` es obligatorio: si fuera opcional, omitirlo sería la forma
    trivial de saltarse la comprobación de autoría."""
    client.put(f"/api/users/{usuario.id}/home-profile", json=_payload(usuario.id))

    respuesta = client.get(f"/api/users/{usuario.id}/home-profile")

    assert respuesta.status_code == 422


# --- GET: lo ajeno, en sus dos escenarios --------------------------------------
#
# Van los DOS a propósito. El cuestionario tiene datos del hogar de alguien
# (cuántas personas viven ahí, si hay niños, cuánto puede gastar al mes) y el
# par prueba una propiedad que un solo caso no puede: que desde afuera **no se
# distingue** si esa persona lo completó o no. Con solo el caso "con perfil",
# invertir el orden (404-de-perfil antes que 403) seguiría verde y filtraría esa
# información a cualquiera que pruebe ids.


def test_get_ajeno_es_403_cuando_ese_tercero_si_tiene_perfil(client, db_session, usuario, tercero):
    client.put(f"/api/users/{tercero.id}/home-profile", json=_payload(tercero.id))

    respuesta = client.get(f"/api/users/{tercero.id}/home-profile?solicitante_id={usuario.id}")

    assert respuesta.status_code == 403
    assert respuesta.json()["detail"] == MENSAJE_403_GET


def test_get_ajeno_es_403_tambien_cuando_ese_tercero_no_tiene_perfil(
    client, db_session, usuario, tercero
):
    respuesta = client.get(f"/api/users/{tercero.id}/home-profile?solicitante_id={usuario.id}")

    assert respuesta.status_code == 403
    assert respuesta.json()["detail"] == MENSAJE_403_GET


# --- Orden de rutas: lo que se midió, no lo que se supuso ----------------------
#
# ⚠️ Aquí el orden de declaración **no** decide nada, al revés que en
# `/api/pets/deck` (`test_deck.py`). Medido sobre `router.routes` en esta versión
# de FastAPI: `GET /api/users/{user_id}` compila a `^/api/users/(?P<user_id>
# [^/]+)$`, y `[^/]+` no cruza una barra, así que jamás puede capturar
# `/api/users/1/home-profile` — son tres segmentos contra dos. Con `/deck` sí
# había colisión porque compite por el **mismo** segmento que `{pet_id}`.
# Mover las dos rutas del hogar debajo de la dinámica deja la suite en verde
# (446/446, comprobado). Se declaran arriba igual, por lectura y por costumbre
# del repo, pero ningún test puede fijar ese orden sin mentir.
#
# Lo que el caso de abajo sí fija es el **contrato**: esta ruta devuelve el
# cuestionario y no un `UserOut`.


def test_el_hogar_no_lo_atiende_la_ruta_del_perfil_publico(client, db_session, usuario):
    """El cuerpo del hogar no trae `email` ni `nombre`: no es un perfil público."""
    client.put(f"/api/users/{usuario.id}/home-profile", json=_payload(usuario.id))

    cuerpo = client.get(f"/api/users/{usuario.id}/home-profile?solicitante_id={usuario.id}").json()

    assert "email" not in cuerpo
    assert "nombre" not in cuerpo
    assert cuerpo["vivienda"] == "casa"
