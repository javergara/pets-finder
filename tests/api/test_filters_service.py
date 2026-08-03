from datetime import datetime, timezone

import pytest

from adopta_api.schemas.pet import PetOut
from adopta_api.services.filters import FiltrosDeck, aplicar_filtros

AHORA = datetime.now(timezone.utc).replace(tzinfo=None)

# Coordenadas de barrios de Bogotá usadas en scripts/seed.py / test_geo.py.
USAQUEN = (4.6946, -74.0307)
CHAPINERO = (4.6486, -74.0629)  # ~6.24 km de Usaquén
KENNEDY = (4.6280, -74.1497)  # ~15.1 km de Usaquén


def _pet(id_: int, **overrides) -> PetOut:
    base = dict(
        id=id_,
        shelter_id=1,
        nombre=f"Mascota{id_}",
        especie="perro",
        raza="Criolla",
        sexo="macho",
        edad_meses=24,
        tamano="mediano",
        energia="media",
        fotos=[],
        historia="",
        tags=[],
        esterilizado=True,
        vacunas_al_dia=True,
        microchip=True,
        desparasitado=True,
        apto_ninos=True,
        apto_perros=True,
        apto_gatos=True,
        estado="disponible",
        publicado_en=AHORA,
        shelter=None,
        afinidad=None,
        lat=None,
        lng=None,
        distancia_km=None,
    )
    base.update(overrides)
    return PetOut(**base)


def test_sin_filtros_devuelve_todas_las_mascotas_sin_cambios():
    pets = [_pet(1), _pet(2), _pet(3)]

    resultado = aplicar_filtros(pets, FiltrosDeck(), user_lat=None, user_lng=None)

    assert [p.id for p in resultado] == [1, 2, 3]


def test_filtro_especie():
    pets = [_pet(1, especie="perro"), _pet(2, especie="gato")]

    resultado = aplicar_filtros(pets, FiltrosDeck(especie=["gato"]), user_lat=None, user_lng=None)

    assert [p.id for p in resultado] == [2]


def test_filtro_tamano():
    pets = [_pet(1, tamano="pequeño"), _pet(2, tamano="grande")]

    resultado = aplicar_filtros(pets, FiltrosDeck(tamano=["grande"]), user_lat=None, user_lng=None)

    assert [p.id for p in resultado] == [2]


def test_filtro_energia():
    pets = [_pet(1, energia="baja"), _pet(2, energia="alta")]

    resultado = aplicar_filtros(pets, FiltrosDeck(energia=["alta"]), user_lat=None, user_lng=None)

    assert [p.id for p in resultado] == [2]


def test_filtro_edad_categoria_cachorro():
    pets = [_pet(1, edad_meses=5), _pet(2, edad_meses=50)]

    resultado = aplicar_filtros(
        pets, FiltrosDeck(edad_categoria=["cachorro"]), user_lat=None, user_lng=None
    )

    assert [p.id for p in resultado] == [1]


def test_filtro_edad_categoria_joven():
    pets = [_pet(1, edad_meses=12), _pet(2, edad_meses=35), _pet(3, edad_meses=36)]

    resultado = aplicar_filtros(
        pets, FiltrosDeck(edad_categoria=["joven"]), user_lat=None, user_lng=None
    )

    assert sorted(p.id for p in resultado) == [1, 2]


def test_filtro_edad_categoria_adulto():
    pets = [_pet(1, edad_meses=36), _pet(2, edad_meses=83), _pet(3, edad_meses=84)]

    resultado = aplicar_filtros(
        pets, FiltrosDeck(edad_categoria=["adulto"]), user_lat=None, user_lng=None
    )

    assert sorted(p.id for p in resultado) == [1, 2]


def test_filtro_edad_categoria_senior_usa_umbral_de_deck():
    pets = [_pet(1, edad_meses=83), _pet(2, edad_meses=84), _pet(3, edad_meses=120)]

    resultado = aplicar_filtros(
        pets, FiltrosDeck(edad_categoria=["senior"]), user_lat=None, user_lng=None
    )

    assert sorted(p.id for p in resultado) == [2, 3]


def test_filtro_apto_ninos():
    pets = [_pet(1, apto_ninos=True), _pet(2, apto_ninos=False)]

    resultado = aplicar_filtros(pets, FiltrosDeck(apto_ninos=True), user_lat=None, user_lng=None)

    assert [p.id for p in resultado] == [1]


def test_filtro_apto_perros():
    pets = [_pet(1, apto_perros=True), _pet(2, apto_perros=False)]

    resultado = aplicar_filtros(pets, FiltrosDeck(apto_perros=True), user_lat=None, user_lng=None)

    assert [p.id for p in resultado] == [1]


def test_filtro_apto_gatos():
    pets = [_pet(1, apto_gatos=True), _pet(2, apto_gatos=False)]

    resultado = aplicar_filtros(pets, FiltrosDeck(apto_gatos=True), user_lat=None, user_lng=None)

    assert [p.id for p in resultado] == [1]


def test_filtro_distancia_excluye_lo_lejano_y_asigna_distancia_km():
    cerca = _pet(1, lat=CHAPINERO[0], lng=CHAPINERO[1])
    lejos = _pet(2, lat=KENNEDY[0], lng=KENNEDY[1])

    resultado = aplicar_filtros(
        [cerca, lejos],
        FiltrosDeck(distancia_km=10.0),
        user_lat=USAQUEN[0],
        user_lng=USAQUEN[1],
    )

    assert [p.id for p in resultado] == [1]
    assert resultado[0].distancia_km == pytest.approx(6.24, abs=0.5)


def test_filtro_distancia_no_excluye_cuando_falta_lat_lng_del_usuario():
    pet = _pet(1, lat=KENNEDY[0], lng=KENNEDY[1])

    resultado = aplicar_filtros([pet], FiltrosDeck(distancia_km=1.0), user_lat=None, user_lng=None)

    assert [p.id for p in resultado] == [1]
    assert resultado[0].distancia_km is None


def test_filtro_distancia_no_excluye_cuando_falta_lat_lng_de_la_mascota():
    pet = _pet(1, lat=None, lng=None)

    resultado = aplicar_filtros(
        [pet],
        FiltrosDeck(distancia_km=1.0),
        user_lat=USAQUEN[0],
        user_lng=USAQUEN[1],
    )

    assert [p.id for p in resultado] == [1]
    assert resultado[0].distancia_km is None


def test_combinacion_de_varios_filtros():
    coincide = _pet(
        1,
        especie="perro",
        tamano="grande",
        apto_ninos=True,
        lat=CHAPINERO[0],
        lng=CHAPINERO[1],
    )
    falla_especie = _pet(
        2,
        especie="gato",
        tamano="grande",
        apto_ninos=True,
        lat=CHAPINERO[0],
        lng=CHAPINERO[1],
    )
    falla_tamano = _pet(
        3,
        especie="perro",
        tamano="pequeño",
        apto_ninos=True,
        lat=CHAPINERO[0],
        lng=CHAPINERO[1],
    )
    falla_distancia = _pet(
        4,
        especie="perro",
        tamano="grande",
        apto_ninos=True,
        lat=KENNEDY[0],
        lng=KENNEDY[1],
    )

    filtros = FiltrosDeck(especie=["perro"], tamano=["grande"], apto_ninos=True, distancia_km=10.0)
    resultado = aplicar_filtros(
        [coincide, falla_especie, falla_tamano, falla_distancia],
        filtros,
        user_lat=USAQUEN[0],
        user_lng=USAQUEN[1],
    )

    assert [p.id for p in resultado] == [1]
