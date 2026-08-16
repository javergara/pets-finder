"""Lecturas de solicitudes de adopción (AD-05 paso 2).

`GET /api/solicitudes` (exactamente uno de `adoptante_id`/`organizacion_id`/
`publicador_id`) y `GET /api/solicitudes/{id}` con `solicitante_id`.

La matriz de estados y acciones ya está cubierta caso por caso en
`test_solicitudes_service.py` (función pura, sin HTTP): aquí se prueba **el
contrato HTTP** — quién puede ver qué, en qué orden, con cuántas consultas y sin
filtrar el motivo del descarte.

⚠️ **Ningún cuerpo de respuesta puede contener `motivo_descarte`.** Es la nota
interna del publicador; el adoptante nunca la ve (ADR 0002, docstring de
`models/match.py`). Dos casos lo vigilan por texto crudo — no por campo—, porque
un schema nuevo podría reintroducirlo dentro de un objeto anidado.

⚠️ Los modelos se importan a nivel de módulo a propósito: el fixture
`db_session` hace `create_all` con lo que esté registrado en `Base.metadata` en
ese instante, y un import perezoso produce un `no such table` intermitente según
el orden de colección de pytest.
"""

from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from typing import get_args

import pytest
from sqlalchemy import event

from reencuentro_api.models.home_profile import HomeProfile
from reencuentro_api.models.match import Match
from reencuentro_api.models.organizacion import Organizacion
from reencuentro_api.models.pet import Pet
from reencuentro_api.models.user import User
from reencuentro_api.schemas.solicitud import AccionSolicitud, EstadoSolicitud
from reencuentro_api.services.solicitudes import ESTADOS_SOLICITUD, ORDEN_ACCIONES

MENSAJE_403 = "Solo el adoptante o quien publicó la mascota pueden ver esta solicitud"


def _ahora() -> datetime:
    """UTC naive, como lo devuelve la columna (`timestamp without time zone`)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


# --- Siembra -------------------------------------------------------------------


def _usuario(db_session, nombre: str, email: str, **overrides) -> User:
    campos = {"nombre": nombre, "email": email, "ciudad": "Armenia"}
    campos.update(overrides)
    user = User(**campos)
    db_session.add(user)
    db_session.commit()
    return user


def _organizacion(db_session, user_id: int, nombre: str = "Fundación Huellas") -> Organizacion:
    organizacion = Organizacion(
        user_id=user_id,
        tipo="fundacion",
        nombre=nombre,
        descripcion="Rescate tras el sismo.",
        zona="Armenia",
        direccion="Cra 14 #10-25",
        lat=4.535,
        lng=-75.68,
        telefono_contacto="3001112233",
    )
    db_session.add(organizacion)
    db_session.commit()
    return organizacion


def _pet(db_session, **overrides) -> Pet:
    campos = {
        "nombre": "Canela",
        "especie": "perro",
        "raza": "Criolla",
        "sexo": "hembra",
        "edad_meses": 18,
        "tamano": "mediano",
        "energia": "media",
        "historia": "Rescatada en Armenia tras el sismo, busca hogar.",
        "zona": "Armenia",
    }
    campos.update(overrides)
    if campos.get("user_id") is not None:
        campos.setdefault("telefono_contacto", "3105558899")
    pet = Pet(**campos)
    db_session.add(pet)
    db_session.commit()
    return pet


def _home(db_session, user_id: int, **overrides) -> HomeProfile:
    campos = {
        "user_id": user_id,
        "vivienda": "casa",
        "espacio_exterior": "patio",
        "personas_en_casa": 2,
        "tiene_ninos": False,
        "tiene_otros_perros": False,
        "tiene_otros_gatos": False,
        "horas_fuera_dia": 6,
        "experiencia_previa": "algo",
        "presupuesto_mensual_cop": 200_000,
        "preferencia_especies": ["perro"],
        "preferencia_tamanos": ["mediano"],
        "preferencia_energia": "media",
    }
    campos.update(overrides)
    home = HomeProfile(**campos)
    db_session.add(home)
    db_session.commit()
    return home


def _solicitud(db_session, adoptante_id: int, pet_id: int, **overrides) -> Match:
    campos = {
        "user_id": adoptante_id,  # ⚠️ el ADOPTANTE, no quien publicó
        "pet_id": pet_id,
        "estado": "solicitado",
        "mensaje": "Tengo patio y tiempo para acompañarla.",
        "telefono_contacto": "3125557788",
        "creado_en": _ahora() - timedelta(days=1),
    }
    campos.update(overrides)
    match = Match(**campos)
    db_session.add(match)
    db_session.commit()
    return match


@pytest.fixture()
def adoptante(db_session):
    return _usuario(db_session, "Ana", "ana@example.co", bio="Vivo con mi hija en Armenia.")


@pytest.fixture()
def otro_adoptante(db_session):
    return _usuario(db_session, "Lucía", "lucia@example.co", ciudad="Pereira")


@pytest.fixture()
def rescatista(db_session):
    """Quien publica: NO es quien pide la mascota."""
    return _usuario(db_session, "Carlos", "carlos@example.co", ciudad="Pereira")


@pytest.fixture()
def tercero(db_session):
    """Alguien sin nada que ver con la solicitud: el que recibe el 403."""
    return _usuario(db_session, "Sofía", "sofia@example.co", ciudad="Manizales")


@contextmanager
def _contar_consultas(session):
    """Cuenta las sentencias SQL reales que salen por el engine del test."""
    sentencias: list[str] = []
    engine = session.get_bind()

    def _registrar(conn, cursor, statement, parameters, context, executemany):
        sentencias.append(statement)

    event.listen(engine, "before_cursor_execute", _registrar)
    try:
        yield sentencias
    finally:
        event.remove(engine, "before_cursor_execute", _registrar)


# --- Candado: los Literal del schema no pueden separarse del servicio ----------


def test_los_estados_del_literal_son_los_del_servicio():
    """`EstadoSolicitud` es el contrato HTTP de `ESTADOS_SOLICITUD`.

    Si alguien añade un estado en el servicio y no aquí, la respuesta con ese
    estado revienta al serializar; si lo añade aquí y no allá (el `"aprobado"`
    que prohíbe la decisión 1 del líder), el schema legitima un estado que
    `calcular_etiqueta_solicitud` trata como "solicitado".
    """
    assert set(get_args(EstadoSolicitud)) == set(ESTADOS_SOLICITUD)


def test_las_acciones_del_literal_son_las_del_servicio():
    """Mismo candado para `acciones_disponibles`: lo que el backend puede
    devolver es exactamente lo que el frontend sabe pintar."""
    assert set(get_args(AccionSolicitud)) == set(ORDEN_ACCIONES)


# --- Lista por adoptante (lo que ve quien pidió la mascota) --------------------


def test_lista_por_adoptante_en_orden_y_sin_acciones(client, db_session, adoptante, rescatista):
    """Orden `creado_en desc, id desc` y **`acciones_disponibles` siempre vacío**.

    Para el adoptante el match no es mutuo (ADR 0002): quien publicó es el único
    que decide, así que su pantalla no puede recibir ni un botón. La siembra va
    de la más antigua a la más nueva para que el orden natural de inserción sea
    justo el inverso del esperado.
    """
    ahora = _ahora()
    for nombre, dias in (("Canela", 3), ("Rocky", 2), ("Luna", 1)):
        pet = _pet(db_session, user_id=rescatista.id, nombre=nombre)
        _solicitud(db_session, adoptante.id, pet.id, creado_en=ahora - timedelta(days=dias))

    respuesta = client.get(f"/api/solicitudes?adoptante_id={adoptante.id}")

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert [s["pet"]["nombre"] for s in cuerpo] == ["Luna", "Rocky", "Canela"]
    assert all(s["acciones_disponibles"] == [] for s in cuerpo)
    assert all(s["estado"] == "solicitado" for s in cuerpo)
    # La etiqueta la calcula el servicio: 3 días sin respuesta ya no es "nueva".
    assert cuerpo[0]["etiqueta"] == "Cuestionario nuevo"
    assert cuerpo[-1]["etiqueta"] == "Sin responder · 3 días"
    assert cuerpo[0]["publicador"]["tipo"] == "rescatista"
    assert cuerpo[0]["adoptante"] == {"id": adoptante.id, "nombre": "Ana"}


def test_el_adoptante_no_ve_las_solicitudes_de_otro(
    client, db_session, adoptante, otro_adoptante, rescatista
):
    pet = _pet(db_session, user_id=rescatista.id)
    _solicitud(db_session, otro_adoptante.id, pet.id)

    cuerpo = client.get(f"/api/solicitudes?adoptante_id={adoptante.id}").json()

    assert cuerpo == []


def test_el_resumen_del_adoptante_no_expone_su_email(client, db_session, adoptante, rescatista):
    """`AdoptanteResumen` es `{id, nombre}`: el correo es la credencial de acceso
    de todo el producto (ADR 0005, entrar-o-registrar sin contraseña)."""
    pet = _pet(db_session, user_id=rescatista.id)
    _solicitud(db_session, adoptante.id, pet.id)

    respuesta = client.get(f"/api/solicitudes?publicador_id={rescatista.id}")

    assert set(respuesta.json()[0]["adoptante"]) == {"id", "nombre"}
    assert "ana@example.co" not in respuesta.text


# --- Lista por organización (el panel de la fundación) -------------------------


def test_lista_por_organizacion_trae_las_acciones_del_publicador(
    client, db_session, adoptante, rescatista
):
    """Las cuatro acciones, en el orden de `ORDEN_ACCIONES`, sobre `solicitado`.

    Las calcula el backend para quien consulta: en `adopta-v1` la pantalla
    reimplementaba la matriz a mano y las dos fuentes de verdad se separaban.
    """
    organizacion = _organizacion(db_session, rescatista.id)
    pet = _pet(db_session, organizacion_id=organizacion.id, nombre="Nala")
    _solicitud(db_session, adoptante.id, pet.id)

    cuerpo = client.get(f"/api/solicitudes?organizacion_id={organizacion.id}").json()

    assert len(cuerpo) == 1
    assert cuerpo[0]["acciones_disponibles"] == list(ORDEN_ACCIONES)
    assert cuerpo[0]["pet"]["nombre"] == "Nala"
    assert cuerpo[0]["publicador"]["tipo"] == "organizacion"


def test_la_solicitud_de_otra_organizacion_no_aparece(
    client, db_session, adoptante, otro_adoptante, rescatista, tercero
):
    mia = _organizacion(db_session, rescatista.id, nombre="Fundación Huellas")
    ajena = _organizacion(db_session, tercero.id, nombre="Fundación Patitas")
    pet_mia = _pet(db_session, organizacion_id=mia.id, nombre="Nala")
    pet_ajena = _pet(db_session, organizacion_id=ajena.id, nombre="Tomás")
    _solicitud(db_session, adoptante.id, pet_mia.id)
    _solicitud(db_session, otro_adoptante.id, pet_ajena.id)

    cuerpo = client.get(f"/api/solicitudes?organizacion_id={mia.id}").json()

    assert [s["pet"]["nombre"] for s in cuerpo] == ["Nala"]


def test_una_solicitud_en_estado_terminal_no_ofrece_acciones(
    client, db_session, adoptante, rescatista
):
    """`adoptado` y `cerrado` no aparecen en ningún set de `TRANSICIONES_VALIDAS`,
    así que el publicador tampoco recibe botones sobre ellas."""
    organizacion = _organizacion(db_session, rescatista.id)
    pet = _pet(db_session, organizacion_id=organizacion.id, estado="adoptado")
    _solicitud(db_session, adoptante.id, pet.id, estado="adoptado")

    cuerpo = client.get(f"/api/solicitudes?organizacion_id={organizacion.id}").json()

    assert cuerpo[0]["acciones_disponibles"] == []
    assert cuerpo[0]["etiqueta"] == "Adopción cerrada"


# --- Lista por publicador: las DOS vías ----------------------------------------


def test_lista_por_rescatista(client, db_session, adoptante, rescatista):
    pet = _pet(db_session, user_id=rescatista.id, nombre="Duque")
    _solicitud(db_session, adoptante.id, pet.id)

    cuerpo = client.get(f"/api/solicitudes?publicador_id={rescatista.id}").json()

    assert [s["pet"]["nombre"] for s in cuerpo] == ["Duque"]
    assert cuerpo[0]["acciones_disponibles"] == list(ORDEN_ACCIONES)


def test_publicador_id_trae_sus_mascotas_y_las_de_sus_organizaciones(
    client, db_session, adoptante, otro_adoptante, rescatista, tercero
):
    """ "Las que recibí" es una sola lista, no dos.

    Quien registró una fundación **y además** publicó a su nombre tendría que
    mirar en dos sitios distintos si `publicador_id` cubriera solo una vía, y la
    pantalla mentiría sin dar ningún error. Mismo criterio que `_dueno_user_id`.
    """
    ahora = _ahora()
    organizacion = _organizacion(db_session, rescatista.id)
    pet_organizacion = _pet(db_session, organizacion_id=organizacion.id, nombre="Nala")
    pet_propia = _pet(db_session, user_id=rescatista.id, nombre="Duque")
    ajena = _organizacion(db_session, tercero.id, nombre="Fundación Patitas")
    pet_ajena = _pet(db_session, organizacion_id=ajena.id, nombre="Tomás")

    _solicitud(db_session, adoptante.id, pet_organizacion.id, creado_en=ahora - timedelta(days=2))
    _solicitud(db_session, otro_adoptante.id, pet_propia.id, creado_en=ahora - timedelta(days=1))
    _solicitud(db_session, adoptante.id, pet_ajena.id)

    cuerpo = client.get(f"/api/solicitudes?publicador_id={rescatista.id}").json()

    assert [s["pet"]["nombre"] for s in cuerpo] == ["Duque", "Nala"]
    assert all(s["acciones_disponibles"] for s in cuerpo)


# --- Exactamente uno de los tres filtros (422 a mano) --------------------------


def test_sin_ningun_filtro_es_422(client, db_session):
    """FastAPI no sabe expresar "exactamente uno de tres": sin este guard la ruta
    devolvería **todas** las solicitudes de la app a cualquiera."""
    respuesta = client.get("/api/solicitudes")

    assert respuesta.status_code == 422
    assert "exactamente uno" in respuesta.json()["detail"]


@pytest.mark.parametrize(
    "query",
    [
        "adoptante_id=1&organizacion_id=1",
        "adoptante_id=1&publicador_id=1",
        "organizacion_id=1&publicador_id=1",
        "adoptante_id=1&organizacion_id=1&publicador_id=1",
    ],
)
def test_dos_filtros_a_la_vez_son_422(client, db_session, query):
    """Combinarlos no es "más específico": son tres preguntas distintas y el
    router tendría que inventar cuál gana."""
    respuesta = client.get(f"/api/solicitudes?{query}")

    assert respuesta.status_code == 422


# --- 404 y lista vacía ---------------------------------------------------------


@pytest.mark.parametrize(
    "filtro",
    ["adoptante_id=9999", "organizacion_id=9999", "publicador_id=9999"],
)
def test_filtro_inexistente_es_404(client, db_session, filtro):
    """Un id que no existe es un dato equivocado, no una lista vacía: devolver
    `[]` dejaría a la pantalla diciendo "todavía nadie te ha escrito"."""
    respuesta = client.get(f"/api/solicitudes?{filtro}")

    assert respuesta.status_code == 404
    assert "9999" in respuesta.json()["detail"]


def test_sin_solicitudes_devuelve_lista_vacia(client, db_session, adoptante, rescatista):
    """Una fundación recién registrada legítimamente no tiene ninguna: 200 con
    `[]`, nunca 404 (mismo criterio que `listar_necesidades`)."""
    organizacion = _organizacion(db_session, rescatista.id)

    for filtro in (
        f"adoptante_id={adoptante.id}",
        f"organizacion_id={organizacion.id}",
        f"publicador_id={rescatista.id}",
    ):
        respuesta = client.get(f"/api/solicitudes?{filtro}")
        assert respuesta.status_code == 200
        assert respuesta.json() == []


# --- Detalle -------------------------------------------------------------------


def test_detalle_para_el_publicador_trae_el_cuestionario_y_el_contacto(
    client, db_session, adoptante, rescatista
):
    """Es el contenido principal de la pantalla del publicador (ADR 0002): sin el
    cuestionario no hay nada con qué decidir."""
    _home(db_session, adoptante.id, horas_fuera_dia=9, vivienda="apartamento")
    pet = _pet(db_session, user_id=rescatista.id, nombre="Duque")
    solicitud = _solicitud(db_session, adoptante.id, pet.id)

    respuesta = client.get(
        f"/api/solicitudes/{solicitud.id}?solicitante_id={rescatista.id}",
    )

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["id"] == solicitud.id
    assert cuerpo["mensaje"] == "Tengo patio y tiempo para acompañarla."
    assert cuerpo["telefono_contacto"] == "3125557788"
    assert cuerpo["bio"] == "Vivo con mi hija en Armenia."
    assert cuerpo["home_profile"]["vivienda"] == "apartamento"
    assert cuerpo["home_profile"]["horas_fuera_dia"] == 9
    assert cuerpo["afinidad"]["score"] > 0
    assert len(cuerpo["afinidad"]["razones"]) >= 2
    assert cuerpo["acciones_disponibles"] == list(ORDEN_ACCIONES)
    assert cuerpo["actualizado_en"] is None


def test_detalle_para_el_autor_de_la_organizacion(client, db_session, adoptante, rescatista):
    """La autoría sale de `_dueno_user_id`, importado de `routers/pets.py`: quien
    registró la fundación gestiona sus mascotas aunque `Pet.user_id` sea nulo."""
    organizacion = _organizacion(db_session, rescatista.id)
    pet = _pet(db_session, organizacion_id=organizacion.id, nombre="Nala")
    solicitud = _solicitud(db_session, adoptante.id, pet.id)

    respuesta = client.get(f"/api/solicitudes/{solicitud.id}?solicitante_id={rescatista.id}")

    assert respuesta.status_code == 200
    assert respuesta.json()["acciones_disponibles"] == list(ORDEN_ACCIONES)


def test_detalle_para_el_propio_adoptante_no_trae_acciones(
    client, db_session, adoptante, rescatista
):
    """Puede ver su solicitud (es suya) pero no gestionar nada (ADR 0002)."""
    _home(db_session, adoptante.id)
    pet = _pet(db_session, user_id=rescatista.id)
    solicitud = _solicitud(db_session, adoptante.id, pet.id)

    respuesta = client.get(f"/api/solicitudes/{solicitud.id}?solicitante_id={adoptante.id}")

    assert respuesta.status_code == 200
    assert respuesta.json()["acciones_disponibles"] == []


def test_detalle_para_un_tercero_es_403(client, db_session, adoptante, rescatista, tercero):
    """Un id secuencial es adivinable: sin este corte, cualquiera leería el
    cuestionario completo y el teléfono de una persona ajena."""
    _home(db_session, adoptante.id)
    pet = _pet(db_session, user_id=rescatista.id)
    solicitud = _solicitud(db_session, adoptante.id, pet.id)

    respuesta = client.get(f"/api/solicitudes/{solicitud.id}?solicitante_id={tercero.id}")

    assert respuesta.status_code == 403
    assert respuesta.json()["detail"] == MENSAJE_403
    assert "3125557788" not in respuesta.text


def test_detalle_sin_solicitante_id_es_422(client, db_session, adoptante, rescatista):
    """`solicitante_id` es requerido: sin él no hay a quién autorizar."""
    pet = _pet(db_session, user_id=rescatista.id)
    solicitud = _solicitud(db_session, adoptante.id, pet.id)

    assert client.get(f"/api/solicitudes/{solicitud.id}").status_code == 422


def test_detalle_de_una_solicitud_inexistente_es_404(client, db_session, rescatista):
    respuesta = client.get(f"/api/solicitudes/9999?solicitante_id={rescatista.id}")

    assert respuesta.status_code == 404
    assert "9999" in respuesta.json()["detail"]


# --- Sin perfil de hogar: 200 con `afinidad: null` -----------------------------


def test_sin_perfil_de_hogar_la_afinidad_viaja_en_null(client, db_session, adoptante, rescatista):
    """Al revés que `adopta-v1`, que devolvía 404 en el detalle y **saltaba la
    fila** en la lista: la solicitud desaparecía del panel sin ningún error, y
    quien no completó el cuestionario quedaba invisible para el publicador.

    Aquí el cuestionario es opcional (AD-04): la solicitud se ve igual, con
    `afinidad` y `home_profile` en `null`.
    """
    pet = _pet(db_session, user_id=rescatista.id)
    solicitud = _solicitud(db_session, adoptante.id, pet.id)

    lista = client.get(f"/api/solicitudes?publicador_id={rescatista.id}")
    detalle = client.get(f"/api/solicitudes/{solicitud.id}?solicitante_id={rescatista.id}")

    assert lista.status_code == 200
    assert len(lista.json()) == 1
    assert lista.json()[0]["afinidad"] is None
    assert detalle.status_code == 200
    assert detalle.json()["afinidad"] is None
    assert detalle.json()["home_profile"] is None


# --- El contrato de privacidad: `motivo_descarte` no sale nunca ----------------


def test_la_lista_no_expone_el_motivo_del_descarte(client, db_session, adoptante, rescatista):
    """Se compara contra el **texto crudo** de la respuesta, no contra las claves
    del primer nivel: el motivo podría reaparecer anidado dentro de cualquier
    objeto (`pet`, `adoptante`) si alguien lo añade a un schema compartido."""
    _home(db_session, adoptante.id)
    pet = _pet(db_session, user_id=rescatista.id)
    _solicitud(
        db_session,
        adoptante.id,
        pet.id,
        estado="cerrado",
        motivo_descarte="Ya tiene tres perros en un apartamento",
    )

    respuesta = client.get(f"/api/solicitudes?publicador_id={rescatista.id}")

    assert respuesta.status_code == 200
    assert "motivo_descarte" not in respuesta.text
    assert "tres perros" not in respuesta.text


def test_el_detalle_no_expone_el_motivo_del_descarte(client, db_session, adoptante, rescatista):
    """Ni siquiera al publicador que lo escribió: no hay pantalla que lo lea, y
    exponerlo sería un salto a un solo `solicitante_id` de distancia del
    adoptante descartado."""
    _home(db_session, adoptante.id)
    pet = _pet(db_session, user_id=rescatista.id)
    solicitud = _solicitud(
        db_session,
        adoptante.id,
        pet.id,
        estado="cerrado",
        motivo_descarte="Ya tiene tres perros en un apartamento",
    )

    for solicitante_id in (rescatista.id, adoptante.id):
        respuesta = client.get(f"/api/solicitudes/{solicitud.id}?solicitante_id={solicitante_id}")
        assert respuesta.status_code == 200
        assert "motivo_descarte" not in respuesta.text
        assert "tres perros" not in respuesta.text


# --- Anti-N+1 y orden estable --------------------------------------------------


def _sembrar_solicitudes_con_entidades_distintas(db_session, publicador, desde: int, pares: int):
    """Dos solicitudes por iteración, **sin compartir ninguna entidad**.

    Cada una cuelga de una mascota propia, de un adoptante propio con su propio
    perfil de hogar, y de un publicador distinto: una organización nueva (todas
    del mismo dueño, que es lo que hace que `publicador_id` las recoja) y el
    rescatista.
    """
    for n in range(desde, desde + pares):
        organizacion = _organizacion(db_session, publicador.id, nombre=f"Fundación {n}")
        pet_organizacion = _pet(db_session, organizacion_id=organizacion.id, nombre=f"Nala {n}")
        pet_propia = _pet(db_session, user_id=publicador.id, nombre=f"Duque {n}")
        for sufijo, pet in (("a", pet_organizacion), ("b", pet_propia)):
            adoptante = _usuario(db_session, f"Adoptante {n}{sufijo}", f"a{n}{sufijo}@example.co")
            _home(db_session, adoptante.id)
            _solicitud(db_session, adoptante.id, pet.id)


def test_el_listado_no_hace_una_consulta_por_solicitud(client, db_session, rescatista):
    """Anti-N+1: el número de consultas NO crece con el número de solicitudes.

    ⚠️ **Lo que hace real a este test es que ninguna fila comparta entidad con
    otra** —mascota, publicador, adoptante ni perfil de hogar—, no el
    `expunge_all()`. Medido por mutación en AD-03 paso 7 y corregido en
    `memory/memory.md`: con `session.get` por fila el conteo crece y queda rojo,
    pero si todas las filas cuelgan del mismo publicador vuelve a ser constante y
    el test **pasa igual**, porque dentro de un mismo request el identity map
    responde el segundo `get` de la misma fila sin tocar la base.

    Por eso las organizaciones son distintas por fila aunque todas tengan el
    mismo dueño: con una sola organización, el `IN` de una fila escondería el
    N+1 de los publicadores.
    """
    publicador_id = rescatista.id
    _sembrar_solicitudes_con_entidades_distintas(db_session, rescatista, desde=0, pares=1)

    db_session.expunge_all()
    with _contar_consultas(db_session) as consultas_cortas:
        cuerpo_corto = client.get(f"/api/solicitudes?publicador_id={publicador_id}").json()

    rescatista = db_session.get(User, publicador_id)
    _sembrar_solicitudes_con_entidades_distintas(db_session, rescatista, desde=1, pares=2)

    db_session.expunge_all()
    with _contar_consultas(db_session) as consultas_largas:
        cuerpo_largo = client.get(f"/api/solicitudes?publicador_id={publicador_id}").json()

    assert len(cuerpo_corto) == 2
    assert len(cuerpo_largo) == 6
    assert all(s["publicador"] is not None for s in cuerpo_largo)
    assert all(s["afinidad"] is not None for s in cuerpo_largo)
    assert len({s["adoptante"]["id"] for s in cuerpo_largo}) == 6
    # El usuario del filtro, las solicitudes, y un lote por tipo de entidad:
    # mascotas, organizaciones, usuarios publicadores, adoptantes y hogares.
    assert len(consultas_cortas) == len(consultas_largas) == 7


def test_dos_llamadas_seguidas_devuelven_el_mismo_orden(client, db_session, rescatista):
    """El desempate por `id desc` no es cosmético: en Postgres el orden de base es
    arbitrario y dos solicitudes creadas en el mismo segundo (el swipe de dos
    personas a la vez) podrían intercambiarse entre dos recargas — la misma
    corrección que necesitó el deck.
    """
    momento = _ahora() - timedelta(days=1)
    for n in range(4):
        pet = _pet(db_session, user_id=rescatista.id, nombre=f"Mascota {n}")
        adoptante = _usuario(db_session, f"Adoptante {n}", f"a{n}@example.co")
        _solicitud(db_session, adoptante.id, pet.id, creado_en=momento)

    url = f"/api/solicitudes?publicador_id={rescatista.id}"
    primera = [s["pet"]["nombre"] for s in client.get(url).json()]
    segunda = [s["pet"]["nombre"] for s in client.get(url).json()]

    assert primera == segunda
    # Empatadas en `creado_en`, desempata el id descendente: la última primero.
    assert primera == [f"Mascota {n}" for n in reversed(range(4))]
