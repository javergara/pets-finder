from adopta_api.models.home_profile import HomeProfile
from adopta_api.models.pet import Pet
from adopta_api.services.affinity import calcular_afinidad


def test_alta_afinidad():
    pet = Pet(
        nombre="Duque",
        especie="perro",
        tamano="grande",
        energia="alta",
        edad_meses=30,
        tags=[],
        apto_ninos=True,
        apto_perros=True,
        apto_gatos=True,
    )
    home = HomeProfile(
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

    resultado = calcular_afinidad(pet, home)

    assert not resultado.incompatible
    assert resultado.score >= 85
    assert resultado.explicacion


def test_baja_afinidad():
    pet = Pet(
        nombre="Rex",
        especie="perro",
        tamano="grande",
        energia="alta",
        edad_meses=100,
        tags=["necesita experiencia"],
        apto_ninos=True,
        apto_perros=True,
        apto_gatos=True,
    )
    home = HomeProfile(
        vivienda="apartamento",
        espacio_exterior="ninguno",
        tiene_ninos=False,
        tiene_otros_perros=False,
        tiene_otros_gatos=False,
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
    pet = Pet(
        nombre="Bella",
        especie="perro",
        tamano="pequeño",
        energia="media",
        edad_meses=36,
        tags=[],
        apto_ninos=False,
        apto_perros=True,
        apto_gatos=True,
    )
    home = HomeProfile(
        vivienda="casa",
        espacio_exterior="patio",
        tiene_ninos=True,
        tiene_otros_perros=False,
        tiene_otros_gatos=False,
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
    pet = Pet(
        nombre="Simón",
        especie="gato",
        tamano="mediano",
        energia="alta",
        edad_meses=14,
        tags=[],
        apto_ninos=True,
        apto_perros=False,
        apto_gatos=False,
    )
    home = HomeProfile(
        vivienda="casa",
        espacio_exterior="jardin",
        tiene_ninos=False,
        tiene_otros_perros=False,
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
