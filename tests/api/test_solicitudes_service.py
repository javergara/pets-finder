"""Tests unitarios puros de `adopta_api.services.solicitudes` (sin DB, sin cliente HTTP).

Cubre `validar_transicion`/`TransicionInvalidaError` y las 6 ramas de
`calcular_etiqueta_solicitud`. Los tests de integración HTTP de la feature 09
(`GET /api/shelters/{id}/solicitudes...`) siguen en `test_shelters.py`.
"""

from datetime import datetime, timedelta, timezone

import pytest

from adopta_api.services.solicitudes import (
    TRANSICIONES_VALIDAS,
    TransicionInvalidaError,
    calcular_etiqueta_solicitud,
    validar_transicion,
)

ESTADOS = ["solicitado", "en_revision", "visita_agendada", "adoptado", "cerrado"]


# --- validar_transicion -------------------------------------------------------


@pytest.mark.parametrize("accion", sorted(TRANSICIONES_VALIDAS))
@pytest.mark.parametrize("estado", ESTADOS)
def test_validar_transicion_matriz_completa(estado, accion):
    """5 estados x 3 acciones = 15 combinaciones: válidas no lanzan, inválidas sí."""
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
    with pytest.raises(TransicionInvalidaError, match="en_revision"):
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
    """`en_revision` etiqueta siempre "En revisión", sin importar los días transcurridos:
    a diferencia de `solicitado`, no cae en la rama de "Sin responder · N días"."""
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
    """Regresión: creado_en puede venir naive (sin tzinfo) al leerlo de SQLite."""
    ahora = datetime(2026, 8, 10, tzinfo=timezone.utc)
    creado_en_naive = datetime(2026, 8, 5)  # sin tzinfo
    assert creado_en_naive.tzinfo is None

    resultado = calcular_etiqueta_solicitud("solicitado", creado_en_naive, ahora=ahora)

    assert resultado == "Sin responder · 5 días"
