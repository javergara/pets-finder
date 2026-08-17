"""Las cuatro acciones sobre una solicitud de adopción (AD-05 paso 3).

`POST /api/solicitudes/{id}/agendar-visita`, `/pedir-informacion`, `/aprobar` y
`/descartar`: lo único de todo el módulo que **escribe**.

Qué se prueba aquí y qué no: la matriz de transiciones caso por caso ya está en
`test_solicitudes_service.py` (función pura, sin HTTP) y las lecturas en
`test_solicitudes.py`. Esto cubre el **efecto observable** de mutar — quién puede,
qué queda en la base, y qué arrastra `aprobar` consigo.

⚠️ **El adoptante recibe 403 en las cuatro.** No es un caso de borde: es el
corazón del ADR 0002. El match no es mutuo, así que quien pidió la mascota no
gestiona nada — ni siquiera su propia solicitud, que sí puede *leer*. Sin este
corte, alguien se aprobaría a sí mismo la adopción con un `POST` a mano.

⚠️ **Las reglas viven en el código, no en la base**: SQLite no fuerza las FK y
tampoco hay constraints de estado, así que cada caso asevera el efecto (la fila,
la mascota, las hermanas) y no solo el código de estado.

⚠️ **`aprobar` cierra las demás con un `UPDATE` masivo y
`synchronize_session=False`**: las instancias ya cargadas en la sesión compartida
del `conftest` no se enteran del cambio. Por eso todas las aserciones sobre filas
hermanas van después de `db_session.expire_all()` (o releídas por HTTP). Sin eso
el test miente en las dos direcciones: puede pasar con una implementación rota y
fallar con la buena.
"""

from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import event

from reencuentro_api.models.home_profile import HomeProfile
from reencuentro_api.models.match import Match
from reencuentro_api.models.organizacion import Organizacion
from reencuentro_api.models.pet import Pet
from reencuentro_api.models.user import User
from reencuentro_api.routers.solicitudes import ACCION_AJENA, ESTADOS_TERMINALES
from reencuentro_api.services.solicitudes import (
    ACCION_LEGIBLE,
    ESTADO_LEGIBLE,
    ESTADOS_SOLICITUD,
    MOTIVO_ADOPTADA_POR_OTRA,
    ORDEN_ACCIONES,
    TRANSICIONES_VALIDAS,
    acciones_disponibles,
)

MOTIVO = "Ya tiene tres perros en un apartamento"


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
        "nombre": "Duque",
        "especie": "perro",
        "raza": "Criolla",
        "sexo": "macho",
        "edad_meses": 18,
        "tamano": "mediano",
        "energia": "media",
        "historia": "Rescatado en Armenia tras el sismo, busca hogar.",
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
        "mensaje": "Tengo patio y tiempo para acompañarlo.",
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
    """Quien publica: el único que puede ejecutar acciones."""
    return _usuario(db_session, "Carlos", "carlos@example.co", ciudad="Pereira")


@pytest.fixture()
def tercero(db_session):
    return _usuario(db_session, "Sofía", "sofia@example.co", ciudad="Manizales")


@pytest.fixture()
def pet(db_session, rescatista):
    return _pet(db_session, user_id=rescatista.id)


@pytest.fixture()
def solicitud(db_session, adoptante, pet):
    return _solicitud(db_session, adoptante.id, pet.id)


def _cuerpo(user_id: int, accion: str) -> dict:
    """El body de cada acción: `descartar` es la única que lleva algo más."""
    cuerpo: dict = {"user_id": user_id}
    if accion == "descartar":
        cuerpo["motivo"] = MOTIVO
    return cuerpo


def _ejecutar(client, solicitud_id: int, accion: str, user_id: int):
    return client.post(f"/api/solicitudes/{solicitud_id}/{accion}", json=_cuerpo(user_id, accion))


@contextmanager
def _contar_filas_actualizadas(session):
    """Cuenta **filas** de `matches` actualizadas, no sentencias.

    ⚠️ Contar sentencias no sirve para lo que este archivo tiene que vigilar: al
    hacer flush, SQLAlchemy agrupa los `UPDATE` de varias instancias con las
    mismas columnas en un solo `executemany`, así que un bucle sobre N hermanas
    saldría también como **una** sentencia y el test pasaría con la
    implementación que quiere prohibir. Por eso, cuando la ejecución es
    `executemany`, cada juego de parámetros cuenta como una fila.
    """
    filas: list[int] = []
    engine = session.get_bind()

    def _registrar(conn, cursor, statement, parameters, context, executemany):
        if statement.strip().upper().startswith("UPDATE MATCHES"):
            filas.append(len(parameters) if executemany else 1)

    event.listen(engine, "before_cursor_execute", _registrar)
    try:
        yield filas
    finally:
        event.remove(engine, "before_cursor_execute", _registrar)


# --- Candado: los terminales son los estados sin ninguna acción ----------------


def test_los_estados_terminales_son_los_que_no_admiten_ninguna_accion():
    """`ESTADOS_TERMINALES` viaja dentro de un `NOT IN` de SQL (el cierre masivo
    de `aprobar`), así que está escrito a mano en el router. Este candado exige
    que siga siendo exactamente el conjunto de estados desde los que ya no se
    avanza: si mañana aparece un sexto estado terminal y nadie lo añade aquí,
    aprobar una solicitud le pisaría el motivo a una adopción ya cerrada.
    """
    sin_acciones = {
        estado for estado in ESTADOS_SOLICITUD if not acciones_disponibles(estado, True)
    }

    assert set(ESTADOS_TERMINALES) == sin_acciones == {"adoptado", "cerrado"}


# --- Las cuatro acciones desde un estado válido --------------------------------


@pytest.mark.parametrize(
    ("accion", "estado_inicial", "estado_final", "etiqueta", "acciones_despues"),
    [
        (
            "agendar-visita",
            "solicitado",
            "visita_agendada",
            "Visita agendada",
            ["aprobar", "descartar"],
        ),
        (
            "pedir-informacion",
            "solicitado",
            "en_revision",
            "En revisión",
            ["agendar-visita", "aprobar", "descartar"],
        ),
        ("aprobar", "visita_agendada", "adoptado", "Adopción cerrada", []),
        ("descartar", "en_revision", "cerrado", "Solicitud cerrada", []),
    ],
)
def test_cada_accion_deja_el_estado_la_etiqueta_y_la_fecha_que_le_tocan(
    client,
    db_session,
    adoptante,
    rescatista,
    pet,
    accion,
    estado_inicial,
    estado_final,
    etiqueta,
    acciones_despues,
):
    """La respuesta es el detalle ya actualizado, no un 204 mudo.

    Devolver el detalle completo evita el `GET` inmediato que haría la pantalla
    tras cada botón, y sobre todo devuelve `acciones_disponibles` recalculadas:
    quien decide qué botones quedan es el backend (ADR 0002, decisión 2 del
    líder), y la pantalla del paso 7 no puede reimplementar la matriz.
    """
    _home(db_session, adoptante.id)
    solicitud = _solicitud(db_session, adoptante.id, pet.id, estado=estado_inicial)

    respuesta = _ejecutar(client, solicitud.id, accion, rescatista.id)

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["estado"] == estado_final
    assert cuerpo["etiqueta"] == etiqueta
    assert cuerpo["acciones_disponibles"] == acciones_despues
    assert cuerpo["actualizado_en"] is not None
    # Es el detalle, no el resumen: la pantalla sigue mostrando con qué se decidió.
    assert cuerpo["mensaje"] == "Tengo patio y tiempo para acompañarlo."
    assert cuerpo["home_profile"]["vivienda"] == "casa"

    db_session.expire_all()
    guardada = db_session.get(Match, solicitud.id)
    assert guardada.estado == estado_final
    assert guardada.actualizado_en is not None


def test_la_fecha_de_actualizacion_nace_nula_y_solo_la_pone_la_accion(
    client, db_session, rescatista, solicitud
):
    """`actualizado_en` es lo que distingue "todavía nadie la miró" de "ya la
    gestioné": si naciera con la fecha de creación, la lista del publicador no
    podría separar las dos cosas."""
    assert solicitud.actualizado_en is None

    antes = _ahora()
    _ejecutar(client, solicitud.id, "agendar-visita", rescatista.id)

    db_session.expire_all()
    guardada = db_session.get(Match, solicitud.id)
    assert guardada.actualizado_en >= antes - timedelta(seconds=5)
    assert guardada.creado_en < guardada.actualizado_en


# --- Autorización: solo quien publicó ------------------------------------------


@pytest.mark.parametrize("accion", ORDEN_ACCIONES)
def test_el_adoptante_no_puede_ejecutar_ninguna_accion(
    client, db_session, adoptante, solicitud, accion
):
    """El corazón del ADR 0002: el match no es mutuo.

    Que la solicitud sea suya le da derecho a **leerla** (hay un test de eso en
    `test_solicitudes.py`), no a moverla. Sin este 403 cualquiera se aprobaría a
    sí mismo la adopción con un `POST` a mano — el `acciones_disponibles: []` que
    recibe su pantalla es una cortesía de UI, no una barrera.
    """
    respuesta = _ejecutar(client, solicitud.id, accion, adoptante.id)

    assert respuesta.status_code == 403
    assert respuesta.json()["detail"] == ACCION_AJENA

    db_session.expire_all()
    assert db_session.get(Match, solicitud.id).estado == "solicitado"
    assert db_session.get(Match, solicitud.id).actualizado_en is None


@pytest.mark.parametrize("accion", ORDEN_ACCIONES)
def test_un_tercero_no_puede_ejecutar_ninguna_accion(
    client, db_session, tercero, pet, solicitud, accion
):
    """Los ids son secuenciales y adivinables: sin este corte, cualquiera cierra
    las solicitudes de una fundación ajena."""
    respuesta = _ejecutar(client, solicitud.id, accion, tercero.id)

    assert respuesta.status_code == 403

    db_session.expire_all()
    assert db_session.get(Match, solicitud.id).estado == "solicitado"
    assert db_session.get(Pet, pet.id).estado == "disponible"


def test_el_copy_del_403_tampoco_nombra_identificadores_internos():
    """El otro `detail` que ve una persona al pulsar un botón (`conventions.md` §3).

    Lo mira quien no publicó la mascota —incluido quien la pidió, que es el caso
    frecuente— y ya estaba escrito como copy de producto: este caso lo fija para
    que siga siéndolo. La aserción se deriva de los catálogos del servicio, no de
    una lista escrita a mano, para que un estado o una acción nueva entren aquí
    solos.
    """
    assert not any(accion in ACCION_AJENA for accion in ORDEN_ACCIONES)
    assert not any(estado in ACCION_AJENA for estado in ESTADOS_SOLICITUD)
    assert "user_id" not in ACCION_AJENA


def test_el_autor_de_la_organizacion_si_puede(client, db_session, adoptante, rescatista):
    """La autoría sale de `_dueno_user_id` (importado de `routers/pets.py`): quien
    registró la fundación gestiona sus mascotas aunque `Pet.user_id` sea nulo."""
    organizacion = _organizacion(db_session, rescatista.id)
    pet = _pet(db_session, organizacion_id=organizacion.id, nombre="Nala")
    solicitud = _solicitud(db_session, adoptante.id, pet.id)

    respuesta = _ejecutar(client, solicitud.id, "agendar-visita", rescatista.id)

    assert respuesta.status_code == 200
    assert respuesta.json()["estado"] == "visita_agendada"


def test_una_mascota_de_organizacion_eliminada_no_autoriza_a_nadie(
    client, db_session, adoptante, rescatista
):
    """`_dueno_user_id` devuelve `None` cuando la organización ya no existe
    (feature 32, y SQLite no fuerza las FK): entonces **nadie** queda autorizado,
    en vez de un 500 o —peor— de autorizar de más."""
    organizacion = _organizacion(db_session, rescatista.id)
    pet = _pet(db_session, organizacion_id=organizacion.id, nombre="Nala")
    solicitud = _solicitud(db_session, adoptante.id, pet.id)
    db_session.delete(organizacion)
    db_session.commit()

    respuesta = _ejecutar(client, solicitud.id, "aprobar", rescatista.id)

    assert respuesta.status_code == 403
    db_session.expire_all()
    assert db_session.get(Match, solicitud.id).estado == "solicitado"


@pytest.mark.parametrize("accion", ORDEN_ACCIONES)
def test_una_solicitud_inexistente_es_404(client, db_session, rescatista, accion):
    respuesta = _ejecutar(client, 9999, accion, rescatista.id)

    assert respuesta.status_code == 404
    assert "9999" in respuesta.json()["detail"]


def test_sin_user_id_en_el_body_es_422(client, db_session, solicitud):
    """`user_id` es toda la autorización que hay (ADR 0005, sin contraseñas): si
    fuera opcional, omitirlo sería la forma más fácil de saltarse el 403."""
    respuesta = client.post(f"/api/solicitudes/{solicitud.id}/agendar-visita", json={})

    assert respuesta.status_code == 422


# --- 409: la matriz completa ----------------------------------------------------

COMBINACIONES_INVALIDAS = [
    (accion, estado)
    for accion in ORDEN_ACCIONES
    for estado in ESTADOS_SOLICITUD
    if estado not in TRANSICIONES_VALIDAS[accion]
]


@pytest.mark.parametrize(("accion", "estado"), COMBINACIONES_INVALIDAS)
def test_toda_transicion_invalida_es_409_y_no_muta_nada(
    client, db_session, adoptante, rescatista, pet, accion, estado
):
    """Las 11 combinaciones imposibles, generadas de `TRANSICIONES_VALIDAS`.

    Se derivan del servicio en vez de escribirse a mano para que ninguna quede
    sin probar si mañana cambia la matriz. Los dos estados terminales
    (`adoptado`, `cerrado`) entran aquí por construcción: no aparecen en ningún
    set, así que las cuatro acciones sobre ellos son 409.

    Que el estado no cambie importa tanto como el código: un 409 que igual
    hubiera escrito dejaría la solicitud en un estado que la matriz prohíbe.
    """
    solicitud = _solicitud(db_session, adoptante.id, pet.id, estado=estado)

    respuesta = _ejecutar(client, solicitud.id, accion, rescatista.id)

    assert respuesta.status_code == 409
    # El `detail` se le muestra tal cual a quien pulsó el botón (la pantalla lo
    # pinta en su `role="alert"`), así que es copy de producto y no un código:
    # dice qué se intentó y en qué punto está la solicitud, sin el slug de la
    # ruta ni el nombre del estado que guarda la columna (`conventions.md` §3).
    detalle = respuesta.json()["detail"]
    assert ACCION_LEGIBLE[accion] in detalle
    assert ESTADO_LEGIBLE[estado] in detalle
    assert accion not in detalle
    assert estado not in detalle

    db_session.expire_all()
    guardada = db_session.get(Match, solicitud.id)
    assert guardada.estado == estado
    assert guardada.actualizado_en is None


@pytest.mark.parametrize("estado", ESTADOS_TERMINALES)
def test_aprobar_una_solicitud_terminal_no_toca_la_mascota_ni_a_las_hermanas(
    client, db_session, adoptante, otro_adoptante, rescatista, pet, estado
):
    """El 409 corta **antes** del efecto en cadena de `aprobar`.

    Es el caso que más caro sale si se cuela: una solicitud ya cerrada volvería a
    marcar la mascota como adoptada y cerraría de nuevo a todas las hermanas, con
    un motivo que ya no es cierto.
    """
    terminal = _solicitud(db_session, adoptante.id, pet.id, estado=estado)
    hermana = _solicitud(db_session, otro_adoptante.id, pet.id)

    respuesta = _ejecutar(client, terminal.id, "aprobar", rescatista.id)

    assert respuesta.status_code == 409
    db_session.expire_all()
    assert db_session.get(Pet, pet.id).estado == "disponible"
    assert db_session.get(Pet, pet.id).adoptado_en is None
    assert db_session.get(Match, hermana.id).estado == "solicitado"


# --- Descartar: el motivo es obligatorio y se guarda recortado ------------------


@pytest.mark.parametrize("motivo", ["", "   ", "\n\t "])
def test_descartar_sin_motivo_real_es_422(client, db_session, rescatista, solicitud, motivo):
    """`min_length=1` no alcanza: `"   "` mide 3 y no dice nada. El publicador
    siempre deja constancia de por qué cierra una solicitud."""
    respuesta = client.post(
        f"/api/solicitudes/{solicitud.id}/descartar",
        json={"user_id": rescatista.id, "motivo": motivo},
    )

    assert respuesta.status_code == 422

    db_session.expire_all()
    assert db_session.get(Match, solicitud.id).estado == "solicitado"


def test_descartar_guarda_el_motivo_recortado(client, db_session, rescatista, solicitud):
    """Se lee de la fila y no de la respuesta a propósito: el motivo **nunca**
    sale en ningún cuerpo (contrato de privacidad de `schemas/solicitud.py`)."""
    respuesta = client.post(
        f"/api/solicitudes/{solicitud.id}/descartar",
        json={"user_id": rescatista.id, "motivo": f"  {MOTIVO}  "},
    )

    assert respuesta.status_code == 200
    assert "motivo_descarte" not in respuesta.text
    assert "tres perros" not in respuesta.text

    db_session.expire_all()
    guardada = db_session.get(Match, solicitud.id)
    assert guardada.estado == "cerrado"
    assert guardada.motivo_descarte == MOTIVO


# --- Aprobar: la mascota y las demás solicitudes -------------------------------


def test_aprobar_marca_la_mascota_como_adoptada(client, db_session, rescatista, pet, solicitud):
    """El acceptance 3 no pide una franja nueva (ya existe desde AD-01): pide que
    aprobar empuje la mascota hasta ella, y eso son `estado` + `adoptado_en`."""
    respuesta = _ejecutar(client, solicitud.id, "aprobar", rescatista.id)

    assert respuesta.status_code == 200
    db_session.expire_all()
    guardada = db_session.get(Pet, pet.id)
    assert guardada.estado == "adoptado"
    assert guardada.adoptado_en is not None
    # La tarjeta que viaja en la respuesta ya refleja el estado nuevo.
    assert respuesta.json()["pet"]["estado"] == "adoptado"


def test_aprobar_cierra_las_demas_solicitudes_de_esa_mascota(
    client, db_session, adoptante, otro_adoptante, rescatista, tercero, pet
):
    """Una mascota se adopta una vez: dejar abiertas las demás sería mandar a
    varias familias a esperar por algo que ya no puede pasar.

    Las que ya estaban en un estado terminal **no se pisan**: cerrarlas otra vez
    reescribiría el motivo real que dejó el publicador, y sobre una `adoptado`
    diría "fue adoptada por otra familia" justo en la solicitud que sí se adoptó.
    Y las de **otras** mascotas no se tocan en absoluto: el `WHERE` va por
    `pet_id`, no por publicador.
    """
    elegida = _solicitud(db_session, adoptante.id, pet.id, estado="visita_agendada")
    en_espera = _solicitud(db_session, otro_adoptante.id, pet.id)
    en_revision = _solicitud(db_session, tercero.id, pet.id, estado="en_revision")
    ya_cerrada = _solicitud(
        db_session,
        _usuario(db_session, "Diego", "diego@example.co").id,
        pet.id,
        estado="cerrado",
        motivo_descarte="No respondió al mensaje",
    )
    ya_adoptada = _solicitud(
        db_session,
        _usuario(db_session, "Elena", "elena@example.co").id,
        pet.id,
        estado="adoptado",
    )
    otra_pet = _pet(db_session, user_id=rescatista.id, nombre="Nala")
    ajena = _solicitud(db_session, otro_adoptante.id, otra_pet.id)

    respuesta = _ejecutar(client, elegida.id, "aprobar", rescatista.id)

    assert respuesta.status_code == 200
    db_session.expire_all()

    for cerrada_ahora in (en_espera, en_revision):
        fila = db_session.get(Match, cerrada_ahora.id)
        assert fila.estado == "cerrado"
        assert fila.motivo_descarte == MOTIVO_ADOPTADA_POR_OTRA
        assert fila.actualizado_en is not None

    assert db_session.get(Match, ya_cerrada.id).motivo_descarte == "No respondió al mensaje"
    assert db_session.get(Match, ya_cerrada.id).actualizado_en is None
    assert db_session.get(Match, ya_adoptada.id).estado == "adoptado"
    assert db_session.get(Match, ya_adoptada.id).motivo_descarte is None

    assert db_session.get(Match, ajena.id).estado == "solicitado"
    assert db_session.get(Pet, otra_pet.id).estado == "disponible"


def test_aprobar_cierra_las_demas_con_una_sola_query(
    client, db_session, adoptante, rescatista, pet
):
    """El cierre en cadena **no puede crecer** con el número de solicitudes.

    Un bucle que recorra las hermanas es una escritura por familia interesada, y
    cada una es un round-trip contra el pooler de Supabase dentro de la misma
    transacción — justo el momento en que más caro sale. Con el `UPDATE` masivo
    son siempre dos filas tocadas: la aprobada y la sentencia de cierre.

    ⚠️ Se cuentan **filas**, no sentencias: al hacer flush, SQLAlchemy agrupa los
    `UPDATE` de varias instancias con las mismas columnas en un solo
    `executemany`, así que contando sentencias un bucle también daría "una" y este
    test pasaría con la implementación que existe para prohibir.
    """
    una = _solicitud(db_session, adoptante.id, pet.id, estado="visita_agendada")
    _solicitud(db_session, _usuario(db_session, "H1", "h1@example.co").id, pet.id)

    with _contar_filas_actualizadas(db_session) as con_una_hermana:
        assert _ejecutar(client, una.id, "aprobar", rescatista.id).status_code == 200

    otra_pet = _pet(db_session, user_id=rescatista.id, nombre="Nala")
    cuatro = _solicitud(db_session, adoptante.id, otra_pet.id, estado="visita_agendada")
    for n in range(4):
        hermano = _usuario(db_session, f"Hermana {n}", f"hermana{n}@example.co")
        _solicitud(db_session, hermano.id, otra_pet.id)

    with _contar_filas_actualizadas(db_session) as con_cuatro_hermanas:
        assert _ejecutar(client, cuatro.id, "aprobar", rescatista.id).status_code == 200

    db_session.expire_all()
    cerradas = [
        m
        for m in db_session.query(Match).filter(Match.pet_id == otra_pet.id).all()
        if m.estado == "cerrado"
    ]
    assert len(cerradas) == 4  # el efecto sí ocurrió: no es un conteo sobre la nada
    assert sum(con_una_hermana) == sum(con_cuatro_hermanas) == 2


# --- De extremo a extremo: la mascota sale del catálogo y sube a la franja ------


def test_tras_aprobar_la_mascota_deja_el_catalogo_y_entra_en_las_adopciones(
    client, db_session, rescatista, pet, solicitud
):
    """El recorrido completo del acceptance 3, por HTTP y sin tocar la sesión:
    `GET /api/pets` filtra por `estado=disponible` y `/api/pets/adopciones` es la
    franja de celebración."""
    catalogo_antes = client.get("/api/pets").json()
    assert [p["id"] for p in catalogo_antes] == [pet.id]
    assert client.get("/api/pets/adopciones").json()["total"] == 0

    assert _ejecutar(client, solicitud.id, "aprobar", rescatista.id).status_code == 200

    assert client.get("/api/pets").json() == []
    adopciones = client.get("/api/pets/adopciones").json()
    assert adopciones["total"] == 1
    assert [p["id"] for p in adopciones["recientes"]] == [pet.id]


def test_el_adoptante_de_una_cerrada_no_ve_el_motivo_en_su_detalle(
    client, db_session, adoptante, otro_adoptante, rescatista, pet
):
    """Quien no se quedó con la mascota ve que su solicitud está cerrada, no por
    qué (ADR 0002). Se compara contra el **texto crudo** porque el motivo podría
    reaparecer anidado dentro de cualquier objeto de un schema compartido."""
    elegida = _solicitud(db_session, adoptante.id, pet.id, estado="visita_agendada")
    descartada = _solicitud(db_session, otro_adoptante.id, pet.id)

    assert _ejecutar(client, elegida.id, "aprobar", rescatista.id).status_code == 200

    respuesta = client.get(
        f"/api/solicitudes/{descartada.id}?solicitante_id={otro_adoptante.id}",
    )

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["estado"] == "cerrado"
    assert cuerpo["etiqueta"] == "Solicitud cerrada"
    assert cuerpo["acciones_disponibles"] == []
    assert "motivo_descarte" not in respuesta.text
    assert MOTIVO_ADOPTADA_POR_OTRA not in respuesta.text
