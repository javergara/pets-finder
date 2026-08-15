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


# --- Dirección de la dependencia entre servicios ---------------------------


def test_afinidad_no_importa_descubrir():
    """`afinidad` trabaja sobre modelos; `descubrir`, sobre schemas.

    Importar `EDAD_MESES_SENIOR` desde `descubrir.py` para no repetir el 84
    invertiría la capa (`afinidad → descubrir → schemas.pet`). El literal se
    repite a propósito; el regex tolera que un comentario nombre el módulo.
    """
    fuente = inspect.getsource(modulo_afinidad)

    assert re.search(r"^\s*from\s+\.descubrir|^\s*import\s+.*descubrir", fuente, re.M) is None
