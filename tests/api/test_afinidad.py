"""Afinidad adoptante ↔ mascota (AD-03 paso 3).

Función pura: sin DB, sin FastAPI. Los `Pet`/`HomeProfile` se construyen
transitorios (nunca se hace `add`/`commit`), que es exactamente como los usa el
deck antes de serializar.

Los cuatro primeros casos vienen de `origin/adopta-v1:tests/api/test_affinity.py`
y fijan que los pesos y las reglas duras NO cambiaron con el port. El resto son
nuevos: las razones legibles (acceptance de AD-03), el presupuesto opcional y la
dirección de la dependencia entre servicios.
"""

import inspect
import re

from reencuentro_api.models.home_profile import HomeProfile
from reencuentro_api.models.pet import Pet
from reencuentro_api.services import afinidad as modulo_afinidad
from reencuentro_api.services.afinidad import calcular_afinidad


def _pet(**overrides) -> Pet:
    """Mascota transitoria con los campos obligatorios del modelo de este repo.

    `zona`, `sexo` e `historia` no existían en `adopta-v1` y aquí son columnas
    NOT NULL, así que viajan siempre aunque la afinidad no los mire.
    """
    base = dict(
        nombre="Duque",
        especie="perro",
        sexo="macho",
        tamano="grande",
        energia="alta",
        edad_meses=30,
        historia="Rescatado tras el terremoto.",
        tags=[],
        apto_ninos=True,
        apto_perros=True,
        apto_gatos=True,
        zona="Armenia",
    )
    base.update(overrides)
    return Pet(**base)


def _home(**overrides) -> HomeProfile:
    base = dict(
        vivienda="casa",
        espacio_exterior="jardin",
        tiene_ninos=False,
        tiene_otros_perros=False,
        tiene_otros_gatos=False,
        horas_fuera_dia=3,
        experiencia_previa="mucha",
        presupuesto_mensual_cop=300_000,
        preferencia_especies=["perro"],
        preferencia_tamanos=["grande"],
        preferencia_energia="alta",
    )
    base.update(overrides)
    return HomeProfile(**base)


# --- Los cuatro de adopta-v1: pesos y reglas duras intactos -----------------


def test_alta_afinidad():
    pet = _pet()
    home = _home()

    resultado = calcular_afinidad(pet, home)

    assert not resultado.incompatible
    assert resultado.score >= 85
    assert resultado.explicacion


def test_baja_afinidad():
    pet = _pet(nombre="Rex", edad_meses=100, tags=["necesita experiencia"])
    home = _home(
        vivienda="apartamento",
        espacio_exterior="ninguno",
        horas_fuera_dia=10,
        experiencia_previa="ninguna",
        presupuesto_mensual_cop=50_000,
        preferencia_especies=["gato"],
        preferencia_tamanos=["pequeño"],
        preferencia_energia="baja",
    )

    resultado = calcular_afinidad(pet, home)

    assert not resultado.incompatible
    assert resultado.score <= 40


def test_regla_dura_ninos():
    pet = _pet(nombre="Bella", tamano="pequeño", energia="media", edad_meses=36, apto_ninos=False)
    home = _home(
        espacio_exterior="patio",
        tiene_ninos=True,
        horas_fuera_dia=5,
        experiencia_previa="algo",
        presupuesto_mensual_cop=150_000,
        preferencia_especies=[],
        preferencia_tamanos=[],
        preferencia_energia="media",
    )

    resultado = calcular_afinidad(pet, home)

    assert resultado.incompatible
    assert resultado.score == 0
    assert "niños" in resultado.explicacion


def test_regla_dura_gatos():
    pet = _pet(
        nombre="Simón",
        especie="gato",
        tamano="mediano",
        edad_meses=14,
        apto_perros=False,
        apto_gatos=False,
    )
    home = _home(
        tiene_otros_gatos=True,
        horas_fuera_dia=5,
        experiencia_previa="algo",
        presupuesto_mensual_cop=150_000,
        preferencia_especies=[],
        preferencia_tamanos=[],
        preferencia_energia="media",
    )

    resultado = calcular_afinidad(pet, home)

    assert resultado.incompatible
    assert resultado.score == 0
    assert "gatos" in resultado.explicacion


# --- Razones legibles (acceptance de AD-03) --------------------------------


def test_devuelve_al_menos_dos_razones():
    resultado = calcular_afinidad(_pet(), _home())

    # `tuple`, no `list`: el dataclass es frozen y una lista sería mutable.
    assert isinstance(resultado.razones, tuple)
    assert len(resultado.razones) >= 2
    assert all(isinstance(razon, str) and razon.strip() for razon in resultado.razones)


def test_razones_citan_energia_y_vivienda():
    pet = _pet(nombre="Nube", tamano="pequeño", energia="media")
    home = _home(
        vivienda="apartamento",
        espacio_exterior="ninguno",
        horas_fuera_dia=6,
        preferencia_especies=[],
        preferencia_tamanos=[],
        preferencia_energia="media",
    )

    razones = calcular_afinidad(pet, home).razones
    texto = " | ".join(razones).lower()

    assert "energía" in texto
    assert "apartamento" in texto
    assert "6 horas fuera al día" in texto


def test_razones_mencionan_la_convivencia_que_el_hogar_necesita():
    pet = _pet(nombre="Luna", energia="media", apto_ninos=True, apto_gatos=True)
    home = _home(
        tiene_ninos=True,
        tiene_otros_gatos=True,
        horas_fuera_dia=5,
        preferencia_energia="media",
    )

    texto = " | ".join(calcular_afinidad(pet, home).razones).lower()

    assert "niños" in texto
    assert "gatos" in texto


def test_incompatible_tiene_score_cero_y_al_menos_una_razon():
    pet = _pet(nombre="Bonita", apto_ninos=False)
    home = _home(tiene_ninos=True)

    resultado = calcular_afinidad(pet, home)

    assert resultado.incompatible
    assert resultado.score == 0
    # Basta una: la tarjeta se excluye del deck, no se argumenta a favor.
    assert len(resultado.razones) >= 1
    assert "niños" in " | ".join(resultado.razones).lower()


# --- Presupuesto opcional --------------------------------------------------


def test_sin_presupuesto_usa_solo_experiencia():
    """Sin la guarda, `None >= costo_estimado` es un TypeError que revienta el deck.

    Mascota difícil (energía alta → dificultad 3) con un hogar sin experiencia
    (nivel 1): score de experiencia = 100 - (3-1)*40 = 20. Con presupuesto de
    sobra el bloque promedia (20+100)/2 = 60; sin presupuesto vale 20 pelado.
    Sobre el resto de scores en 100, eso da 88 contra 94.
    """
    pet = _pet(nombre="Rex")  # energía alta → dificultad 3
    sin_presupuesto = _home(experiencia_previa="ninguna", presupuesto_mensual_cop=None)
    con_presupuesto = _home(experiencia_previa="ninguna", presupuesto_mensual_cop=300_000)

    resultado_sin = calcular_afinidad(pet, sin_presupuesto)
    resultado_con = calcular_afinidad(pet, con_presupuesto)

    assert resultado_sin.score == 88
    assert resultado_con.score == 94
    assert not resultado_sin.incompatible


# --- El score y las razones dependen del hogar (acceptance 2 de AD-04) -----


# Los dos hogares que se comparan en los dos casos de abajo. Solo cambian las
# tres respuestas que el cuestionario de AD-04 pesa más: vivienda + espacio,
# rutina y experiencia. Todo lo demás sale del `_home()` base, para que la
# diferencia de score no venga de una preferencia suelta.
def _hogar_apretado() -> HomeProfile:
    return _home(
        vivienda="apartamento",
        espacio_exterior="ninguno",
        horas_fuera_dia=10,
        experiencia_previa="ninguna",
    )


def _hogar_holgado() -> HomeProfile:
    return _home(
        vivienda="casa",
        espacio_exterior="patio",
        horas_fuera_dia=4,
        experiencia_previa="mucha",
    )


def test_dos_hogares_distintos_dan_scores_distintos_a_la_misma_mascota():
    """La afinidad es del par (mascota, hogar), no una nota fija de la mascota.

    Es lo que le faltaba al acceptance de AD-04: los tests de AD-03 miran
    siempre **un** hogar, así que un `calcular_afinidad` que ignorara el perfil
    y devolviera una constante los pasaría todos.

    Los números son exactos a propósito. Con `!=` bastaría con que el cálculo
    variara por cualquier motivo —incluido uno equivocado— y aquí se está
    fijando la ponderación real: Duque es un perro grande de mucha energía, así
    que el apartamento sin espacio, las 10 horas fuera y la falta de experiencia
    lo hunden (energía 0, tamaño 40, experiencia 20) mientras que la casa con
    patio y 4 horas fuera lo dejan perfecto.
    """
    pet = _pet()  # perro grande, energía alta, 30 meses

    apretado = calcular_afinidad(pet, _hogar_apretado())
    holgado = calcular_afinidad(pet, _hogar_holgado())

    assert apretado.score == 52
    assert holgado.score == 100
    assert apretado.score < holgado.score
    assert not apretado.incompatible and not holgado.incompatible


def test_las_razones_cambian_con_las_respuestas_del_hogar():
    """Y cada juego de razones cita **sus** respuestas, no las del otro hogar.

    Sin esta parte, un `_razones()` que escribiera las horas o la vivienda a
    mano (o que leyera las del hogar equivocado) seguiría devolviendo tuplas
    distintas —el score las separa igual— y pasaría inadvertido.
    """
    pet = _pet()

    razones_apretado = calcular_afinidad(pet, _hogar_apretado()).razones
    razones_holgado = calcular_afinidad(pet, _hogar_holgado()).razones

    assert razones_apretado != razones_holgado

    texto_apretado = " | ".join(razones_apretado).lower()
    texto_holgado = " | ".join(razones_holgado).lower()

    assert "10 horas fuera al día" in texto_apretado
    assert "tu apartamento" in texto_apretado
    assert "4 horas fuera al día" not in texto_apretado
    assert "tu casa" not in texto_apretado

    assert "4 horas fuera al día" in texto_holgado
    assert "tu casa" in texto_holgado
    assert "10 horas fuera al día" not in texto_holgado
    assert "tu apartamento" not in texto_holgado


# --- Dirección de la dependencia entre servicios ---------------------------


def test_afinidad_no_importa_descubrir():
    """`afinidad` trabaja sobre modelos; `descubrir`, sobre schemas.

    Importar `EDAD_MESES_SENIOR` desde `descubrir.py` para no repetir el 84
    invertiría la capa (`afinidad → descubrir → schemas.pet`). El literal se
    repite a propósito; el regex tolera que un comentario nombre el módulo.
    """
    fuente = inspect.getsource(modulo_afinidad)

    assert re.search(r"^\s*from\s+\.descubrir|^\s*import\s+.*descubrir", fuente, re.M) is None


def test_el_umbral_senior_es_el_mismo_en_afinidad_y_descubrir():
    """El precio de repetir el 84: hay que impedir que los dos se separen.

    El test de arriba prohíbe el import; este prohíbe el drift, que es el otro
    lado de la misma decisión. Desde `tests/` sí se pueden importar los dos
    módulos a la vez —el test no es una capa de la app, así que no invierte
    nada— y por eso la deuda que dejó abierta el revisor de AD-03 se salda aquí.

    No basta con comparar el literal: se ejercita el borde real de
    `_dificultad_mascota`, que es donde el umbral tiene efecto. 84 meses (7
    años justos) todavía es una mascota fácil de ubicar; 85 ya suma dificultad
    y exige más experiencia al hogar.
    """
    from reencuentro_api.services.afinidad import _dificultad_mascota
    from reencuentro_api.services.descubrir import EDAD_MESES_SENIOR

    assert EDAD_MESES_SENIOR == 84

    # Energía media y sin etiquetas: así la dificultad la decide solo la edad.
    assert _dificultad_mascota(_pet(energia="media", edad_meses=84)) == 1
    assert _dificultad_mascota(_pet(energia="media", edad_meses=85)) == 2
