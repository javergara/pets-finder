"""Tests unitarios puros de `reencuentro_api.services.solicitudes` (sin DB, sin HTTP).

Los 14 casos de `validar_transicion`/`calcular_etiqueta_solicitud` vienen portados
de `tests/api/test_solicitudes_service.py` de la era Adopta (`adopta-v1`). Lo que
AD-05 añade es la cuarta acción (`aprobar`), `acciones_disponibles` —que el
backend calcula para que el frontend no reimplemente la matriz— y el guard de
vocabulario del final del archivo.

⚠️ La matriz se recorre siempre desde `ESTADOS_SOLICITUD` y `TRANSICIONES_VALIDAS`
del propio módulo, nunca desde una lista copiada aquí: con una lista local,
añadirle un estado al servicio pasaría sin que ningún test se entere — que es
exactamente el accidente contra el que existe este archivo.

Los tests de integración HTTP (`GET /api/solicitudes`, las cuatro acciones) son
de los pasos 2 y 3 y viven en `test_solicitudes.py`.
"""

import re
from datetime import datetime, timedelta, timezone

import pytest

from reencuentro_api.services.solicitudes import (
    ACCION_LEGIBLE,
    ESTADO_LEGIBLE,
    ESTADOS_SOLICITUD,
    ESTADOS_TERMINALES,
    MOTIVO_ADOPTADA_POR_OTRA,
    ORDEN_ACCIONES,
    TRANSICIONES_VALIDAS,
    TransicionInvalidaError,
    acciones_disponibles,
    calcular_etiqueta_solicitud,
    mensaje_solicitudes_vivas,
    validar_transicion,
)

# --- validar_transicion -------------------------------------------------------


@pytest.mark.parametrize("accion", sorted(TRANSICIONES_VALIDAS))
@pytest.mark.parametrize("estado", ESTADOS_SOLICITUD)
def test_validar_transicion_matriz_completa(estado, accion):
    """5 estados x 4 acciones = 20 combinaciones: válidas no lanzan, inválidas sí."""
    if estado in TRANSICIONES_VALIDAS[accion]:
        # No debe lanzar.
        validar_transicion(estado, accion)
    else:
        with pytest.raises(TransicionInvalidaError) as exc_info:
            validar_transicion(estado, accion)
        assert str(exc_info.value)


def test_validar_transicion_agendar_visita_valida_desde_solicitado():
    validar_transicion("solicitado", "agendar-visita")


def test_validar_transicion_agendar_visita_valida_desde_en_revision():
    validar_transicion("en_revision", "agendar-visita")


def test_validar_transicion_pedir_informacion_invalida_desde_en_revision():
    """Pedir información dos veces no es un paso adelante: ya se pidió.

    El `match` va contra la constante de copy, no contra `"en_revision"`: ese
    texto se le muestra tal cual a una persona (llega como `detail` de un 409) y
    el nombre interno del estado no le dice nada. Comparar contra la constante
    —y no contra la frase escrita a mano aquí— deja el copy con una sola fuente.
    """
    with pytest.raises(TransicionInvalidaError, match=re.escape(ESTADO_LEGIBLE["en_revision"])):
        validar_transicion("en_revision", "pedir-informacion")


def test_validar_transicion_descartar_valida_desde_visita_agendada():
    validar_transicion("visita_agendada", "descartar")


@pytest.mark.parametrize("accion", sorted(TRANSICIONES_VALIDAS))
def test_validar_transicion_estados_terminales_siempre_invalida(accion):
    """Los estados terminales (`adoptado`, `cerrado`) no están en ningún set de
    `TRANSICIONES_VALIDAS`: cualquier acción sobre ellos lanza siempre."""
    for estado_terminal in ("adoptado", "cerrado"):
        with pytest.raises(TransicionInvalidaError):
            validar_transicion(estado_terminal, accion)


# --- `aprobar`: la acción que no existía en `adopta-v1` ------------------------


def test_aprobar_valido_desde_los_tres_estados():
    """Se puede aprobar en cualquier punto del proceso, incluido el primero: hay
    adopciones que se cierran en la primera llamada y obligar a pasar por
    `en_revision` sería burocracia inventada por el software."""
    for estado in ("solicitado", "en_revision", "visita_agendada"):
        validar_transicion(estado, "aprobar")


def test_aprobar_invalido_desde_adoptado_y_cerrado():
    """Aprobar dos veces volvería a mover `pet.estado` y a cerrar solicitudes ya
    cerradas; aprobar una descartada resucitaría una decisión ya tomada."""
    for estado in ("adoptado", "cerrado"):
        with pytest.raises(TransicionInvalidaError, match=re.escape(ESTADO_LEGIBLE[estado])):
            validar_transicion(estado, "aprobar")


# --- El mensaje del 409 es copy de producto, no identificadores ----------------


def test_el_copy_cubre_exactamente_los_estados_y_las_acciones_reales():
    """Los dos catálogos de copy no pueden quedarse cortos ni sobrar.

    Es el mismo candado que `test_orden_acciones_cubre_toda_la_matriz`: un
    estado nuevo sin su frase reventaría el mensaje del 409 con un `KeyError`
    (500 con traza en vez de un 409 explicado), y una frase huérfana es copy que
    nadie lee y que nadie va a mantener.
    """
    assert set(ESTADO_LEGIBLE) == set(ESTADOS_SOLICITUD)
    assert set(ACCION_LEGIBLE) == set(ORDEN_ACCIONES)


#: Las 11 combinaciones que lanzan, derivadas de la matriz del servicio y no
#: escritas a mano: si mañana cambia, este test cambia con ella.
COMBINACIONES_INVALIDAS = [
    (estado, accion)
    for accion in sorted(TRANSICIONES_VALIDAS)
    for estado in ESTADOS_SOLICITUD
    if estado not in TRANSICIONES_VALIDAS[accion]
]


@pytest.mark.parametrize(("estado", "accion"), COMBINACIONES_INVALIDAS)
def test_ningun_mensaje_de_transicion_invalida_filtra_identificadores(estado, accion):
    """Toda la matriz inválida, comprobada contra `docs/conventions.md` §3.

    El texto viaja como `detail` de un 409 y la pantalla lo muestra tal cual, así
    que es copy de producto: tiene que decir **qué pasó** ("ya no puedes
    confirmar la adopción: esta solicitud ya está cerrada"), nunca el slug de la
    ruta ni el nombre de la columna. Se recorre la matriz entera en vez de un
    caso de ejemplo porque el descuido aparece de a una combinación.
    """
    with pytest.raises(TransicionInvalidaError) as exc_info:
        validar_transicion(estado, accion)

    mensaje = str(exc_info.value)
    assert accion not in mensaje
    assert estado not in mensaje
    # Y dice de verdad qué se intentó y en qué punto está la solicitud.
    assert ACCION_LEGIBLE[accion] in mensaje
    assert ESTADO_LEGIBLE[estado] in mensaje


# --- acciones_disponibles ------------------------------------------------------

ACCIONES_ESPERADAS: dict[str, list[str]] = {
    "solicitado": ["agendar-visita", "pedir-informacion", "aprobar", "descartar"],
    "en_revision": ["agendar-visita", "aprobar", "descartar"],
    "visita_agendada": ["aprobar", "descartar"],
    "adoptado": [],
    "cerrado": [],
}


@pytest.mark.parametrize("estado", ESTADOS_SOLICITUD)
def test_acciones_disponibles_de_un_no_publicador_es_lista_vacia(estado):
    """El adoptante no gestiona su propia solicitud (ADR 0002: el match no es
    mutuo, y quien publicó es el único que decide). Sin este corte, el detalle de
    la solicitud le pintaría al adoptante un botón "Aprobar" sobre su propia
    adopción."""
    assert acciones_disponibles(estado, es_publicador=False) == []


@pytest.mark.parametrize("estado", ESTADOS_SOLICITUD)
def test_acciones_disponibles_por_estado(estado):
    """El orden importa: es el de los botones en `SolicitudDetalle` (paso 7), y
    tiene que ser el de `ORDEN_ACCIONES`, no el de iteración de un dict.

    Recorrer `ESTADOS_SOLICITUD` (y no las claves de `ACCIONES_ESPERADAS`) hace
    que un estado persistido nuevo llegue aquí sin caso y falle en vez de quedar
    sin cobertura.
    """
    assert estado in ACCIONES_ESPERADAS, (
        f"Estado persistido {estado!r} sin caso esperado: si se añadió un estado, "
        "decide qué acciones ofrece antes de que lo decida el orden de un dict"
    )
    assert acciones_disponibles(estado, es_publicador=True) == ACCIONES_ESPERADAS[estado]


def test_orden_acciones_cubre_toda_la_matriz():
    """`ORDEN_ACCIONES` existe solo para fijar el orden de los botones; si alguien
    añade una acción a `TRANSICIONES_VALIDAS` y olvida la tupla, esa acción
    desaparecería de la UI sin dar ningún error."""
    assert set(ORDEN_ACCIONES) == set(TRANSICIONES_VALIDAS)
    assert len(ORDEN_ACCIONES) == len(TRANSICIONES_VALIDAS), "ORDEN_ACCIONES repite una acción"


# --- calcular_etiqueta_solicitud -----------------------------------------------


def test_calcular_etiqueta_visita_agendada():
    ahora = datetime(2026, 8, 3, tzinfo=timezone.utc)
    assert calcular_etiqueta_solicitud("visita_agendada", ahora, ahora=ahora) == "Visita agendada"


def test_calcular_etiqueta_adoptado():
    ahora = datetime(2026, 8, 3, tzinfo=timezone.utc)
    assert calcular_etiqueta_solicitud("adoptado", ahora, ahora=ahora) == "Adopción cerrada"


def test_calcular_etiqueta_cerrado():
    ahora = datetime(2026, 8, 3, tzinfo=timezone.utc)
    assert calcular_etiqueta_solicitud("cerrado", ahora, ahora=ahora) == "Solicitud cerrada"


def test_calcular_etiqueta_en_revision_reciente_es_en_revision():
    ahora = datetime(2026, 8, 3, tzinfo=timezone.utc)
    creado_en = ahora - timedelta(hours=1)
    assert calcular_etiqueta_solicitud("en_revision", creado_en, ahora=ahora) == "En revisión"


def test_calcular_etiqueta_en_revision_viejo_es_en_revision():
    """`en_revision` etiqueta siempre "En revisión", sin importar los días
    transcurridos: a diferencia de `solicitado`, no cae en "Sin responder · N días"."""
    ahora = datetime(2026, 8, 10, tzinfo=timezone.utc)
    creado_en = ahora - timedelta(days=5)
    assert calcular_etiqueta_solicitud("en_revision", creado_en, ahora=ahora) == "En revisión"


def test_calcular_etiqueta_solicitado_reciente_es_cuestionario_nuevo():
    ahora = datetime(2026, 8, 3, tzinfo=timezone.utc)
    creado_en = ahora - timedelta(hours=5)
    assert calcular_etiqueta_solicitud("solicitado", creado_en, ahora=ahora) == "Cuestionario nuevo"


def test_calcular_etiqueta_solicitado_viejo_es_sin_responder_con_dias_exactos():
    ahora = datetime(2026, 8, 10, tzinfo=timezone.utc)
    creado_en = ahora - timedelta(days=5)
    assert (
        calcular_etiqueta_solicitud("solicitado", creado_en, ahora=ahora)
        == "Sin responder · 5 días"
    )


def test_calcular_etiqueta_con_creado_en_naive_no_lanza_typeerror():
    """Regresión: `creado_en` vuelve naive de la DB (la columna es `timestamp
    without time zone` también en Postgres, ver `migrations/AD-05-matches.sql`),
    aunque se haya guardado con `datetime.now(timezone.utc)`. Sin la
    normalización previa, la resta explota con `TypeError: can't subtract
    offset-naive and offset-aware datetimes` — en producción, no solo en SQLite."""
    ahora = datetime(2026, 8, 10, tzinfo=timezone.utc)
    creado_en_naive = datetime(2026, 8, 5)  # sin tzinfo
    assert creado_en_naive.tzinfo is None

    resultado = calcular_etiqueta_solicitud("solicitado", creado_en_naive, ahora=ahora)

    assert resultado == "Sin responder · 5 días"


# --- El guard de vocabulario ---------------------------------------------------


def test_ningun_estado_persistido_cae_al_branch_de_solicitado():
    """La trampa más silenciosa del portado: la rama de "solicitado" es el `else`
    de la función, así que **cualquier estado que nadie contemple aterriza ahí**.

    Inventar un estado `"aprobado"` (la palabra que el backlog usa en prosa, ver
    la nota de vigencia del ADR 0002) no rompería nada visible: la solicitud
    mostraría *"Sin responder · 5 días"* sobre una adopción ya cerrada, y el
    publicador creería que le queda trabajo por hacer.

    Dos aserciones, porque miden cosas distintas: que ningún estado distinto de
    `solicitado` use el texto de esa rama, y que las cinco etiquetas sean
    **distintas entre sí** — dos estados con la misma etiqueta serían
    indistinguibles en pantalla aunque ninguno cayera en el `else`.
    """
    ahora = datetime(2026, 8, 15, tzinfo=timezone.utc)
    creado_en = ahora - timedelta(days=5)

    etiquetas = {
        estado: calcular_etiqueta_solicitud(estado, creado_en, ahora=ahora)
        for estado in ESTADOS_SOLICITUD
    }

    for estado, etiqueta in etiquetas.items():
        if estado == "solicitado":
            continue
        assert etiqueta != "Cuestionario nuevo", (
            f"El estado {estado!r} cae en la rama de 'solicitado': "
            "o falta su branch en calcular_etiqueta_solicitud, o el estado no existe"
        )
        assert not etiqueta.startswith("Sin responder"), (
            f"El estado {estado!r} cae en la rama de 'solicitado' y muestra "
            f"{etiqueta!r} sobre una solicitud que ya avanzó"
        )

    assert len(set(etiquetas.values())) == len(
        ESTADOS_SOLICITUD
    ), f"Dos estados comparten etiqueta y son indistinguibles en pantalla: {etiquetas}"


def test_las_acciones_no_son_estados():
    """`aprobar` y `descartar` son nombres de acción HTTP (`POST
    /api/solicitudes/{id}/aprobar`), nunca valores de `Match.estado`: llevan a
    `adoptado` y `cerrado`. El ADR 0002 lo dice con todas las letras."""
    assert set(ORDEN_ACCIONES).isdisjoint(ESTADOS_SOLICITUD)
    assert "aprobado" not in ESTADOS_SOLICITUD
    assert "descartado" not in ESTADOS_SOLICITUD


def test_los_estados_terminales_viven_en_el_servicio_y_son_los_que_no_avanzan():
    """AD-09 bajó `ESTADOS_TERMINALES` del router al servicio porque
    `despublicar_mascota` necesita la misma frontera (y `routers/solicitudes.py`
    ya importa de `.pets`, así que la vuelta habría sido circular).

    El candado no es dónde vive, sino que siga significando lo mismo: terminal =
    ninguna acción disponible. Si mañana aparece un sexto estado sin acciones y
    nadie lo añade aquí, una mascota con solicitudes en ese estado bloquearía
    para siempre su despublicación con un 409 que nadie puede resolver.
    """
    sin_acciones = {
        estado for estado in ESTADOS_SOLICITUD if not acciones_disponibles(estado, True)
    }
    assert set(ESTADOS_TERMINALES) == sin_acciones == {"adoptado", "cerrado"}


def test_el_409_de_despublicar_concuerda_en_singular_y_en_plural():
    """El mensaje lo lee quien pulsó "Despublicar": tiene que decir cuántas
    conversaciones abiertas lo bloquean y qué hacer con ellas. Un "1 solicitudes
    abiertas" delata que nadie lo leyó antes de mandarlo a producción."""
    assert mensaje_solicitudes_vivas(1) == (
        "Esta mascota tiene 1 solicitud de adopción abierta: "
        "ciérrala antes de despublicar a la mascota"
    )
    assert mensaje_solicitudes_vivas(3) == (
        "Esta mascota tiene 3 solicitudes de adopción abiertas: "
        "ciérralas antes de despublicar a la mascota"
    )
    # La salida va nombrada, no solo el problema: sin esto el 409 sería un "no se
    # puede" seco y quien lo recibe no sabría por dónde seguir.
    for cuantas in (1, 2, 7):
        assert "cierra" in mensaje_solicitudes_vivas(cuantas).replace("é", "e")


def test_el_motivo_de_cierre_automatico_es_copy_de_producto():
    """El texto que recibe quien no se quedó con la mascota cuando otra solicitud
    se aprueba (paso 3). Vive en el servicio y no incrustado en el router para
    que el test del cierre masivo compare contra la misma constante — y porque es
    copy: se lee en español y no culpa a nadie."""
    assert MOTIVO_ADOPTADA_POR_OTRA == "La mascota fue adoptada por otra familia"
