"""Filtros del deck de descubrimiento (AD-03 paso 5).

Función pura sobre `PetOut`: sin DB, sin FastAPI. Los quince primeros casos
vienen de `origin/adopta-v1:tests/api/test_filters_service.py` y fijan que el
port no cambió una línea de lógica; los cuatro últimos son propios de este repo
(`zona`, `tags` y el default de `distancia_km`).

Las coordenadas son las mismas de `tests/api/test_geo.py` — no se inventan
distancias nuevas: Usaquén↔Chapinero ≈ 6.24 km y Usaquén↔Kennedy ≈ 15.1 km ya
están fijadas allí contra el haversine.
"""

from datetime import datetime, timezone

import pytest

from reencuentro_api.schemas.pet import PetOut
from reencuentro_api.services.filtros import FiltrosDeck, aplicar_filtros

# Coordenadas de barrios de Bogotá usadas en tests/api/test_geo.py.
USAQUEN = (4.6946, -74.0307)
CHAPINERO = (4.6486, -74.0629)  # ~6.24 km de Usaquén
KENNEDY = (4.6280, -74.1497)  # ~15.1 km de Usaquén


def _ahora() -> datetime:
    """Naive-UTC, como `publicado_en` en los dos motores (ver `descubrir.py`)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _pet(id_: int, **overrides) -> PetOut:
    base = dict(
        id=id_,
        organizacion_id=1,
        user_id=None,
        report_id=None,
        nombre=f"Mascota{id_}",
        especie="perro",
        raza="Criolla",
        sexo="macho",
        edad_meses=24,
        tamano="mediano",
        energia="media",
        fotos=[],
        historia="Historia de prueba",
        tags=[],
        esterilizado=True,
        vacunas_al_dia=True,
        microchip=True,
        desparasitado=True,
        apto_ninos=True,
        apto_perros=True,
        apto_gatos=True,
        zona="Armenia",
        ciudad_texto=None,
        barrio=None,
        lat=None,
        lng=None,
        telefono_contacto="3001112233",
        estado="disponible",
        publicado_en=_ahora(),
        adoptado_en=None,
        publicador=None,
        afinidad=None,
        distancia_km=None,
    )
    base.update(overrides)
    return PetOut(**base)


# --- Los quince de adopta-v1: la lógica no cambió -------------------------------


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


def test_filtro_edad_categoria_senior_usa_el_umbral_de_descubrir():
    """El corte de "senior" es `EDAD_MESES_SENIOR` (84) importado de
    `descubrir.py`, no un 84 escrito otra vez aquí."""
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
    """Degradación elegante: sin coordenadas del usuario nadie se excluye."""
    pet = _pet(1, lat=KENNEDY[0], lng=KENNEDY[1])

    resultado = aplicar_filtros([pet], FiltrosDeck(distancia_km=1.0), user_lat=None, user_lng=None)

    assert [p.id for p in resultado] == [1]
    assert resultado[0].distancia_km is None


def test_filtro_distancia_no_excluye_cuando_falta_lat_lng_de_la_mascota():
    """Y sin pin de la mascota, tampoco — el caso mayoritario de este repo."""
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


# --- Los cuatro propios de este repo -------------------------------------------


def test_filtro_zona():
    """La zona es el filtro primario de un catálogo colombiano de seis ciudades:
    en `adopta-v1` (una sola ciudad) no existía."""
    pets = [_pet(1, zona="Armenia"), _pet(2, zona="Pereira"), _pet(3, zona="Cali")]

    resultado = aplicar_filtros(
        pets, FiltrosDeck(zona=["Armenia", "Cali"]), user_lat=None, user_lng=None
    )

    assert [p.id for p in resultado] == [1, 3]


def test_filtro_zona_vacio_no_restringe():
    """ "Todo Colombia" se pide con la lista vacía, igual que en el catálogo."""
    pets = [_pet(1, zona="Armenia"), _pet(2, zona="Bogotá")]

    resultado = aplicar_filtros(pets, FiltrosDeck(zona=[]), user_lat=None, user_lng=None)

    assert [p.id for p in resultado] == [1, 2]


def test_filtro_tags():
    """`tags` se filtra aquí, en Python, y no en SQL: la columna es JSON (TEXT en
    SQLite, `json` en Postgres) y ni `LIKE` ni `->>` son portables entre las dos.

    Basta con que la mascota tenga **alguna** de las etiquetas pedidas (OR dentro
    del criterio, como el resto de los filtros de lista).
    """
    pets = [
        _pet(1, tags=["necesita experiencia", "tranquila"]),
        _pet(2, tags=["juguetona"]),
        _pet(3, tags=[]),
    ]

    resultado = aplicar_filtros(
        pets, FiltrosDeck(tags=["tranquila", "sociable"]), user_lat=None, user_lng=None
    )

    assert [p.id for p in resultado] == [1]


def test_sin_distancia_km_no_excluye_nada():
    """El default de `distancia_km` es `None`, no los 15 km de `adopta-v1`.

    Aquel radio venía de un producto urbano de Bogotá donde toda mascota tenía
    coordenadas. Aquí muchas no tienen pin y muchas otras están a más de 15 km de
    quien busca: un default así escondería resultados **en silencio**, sin que
    nadie hubiera pedido filtrar por distancia.
    """
    lejos = _pet(1, lat=KENNEDY[0], lng=KENNEDY[1])
    lejisimos = _pet(2, lat=4.0, lng=-76.5)  # a cientos de km de Usaquén

    resultado = aplicar_filtros(
        [lejos, lejisimos], FiltrosDeck(), user_lat=USAQUEN[0], user_lng=USAQUEN[1]
    )

    assert [p.id for p in resultado] == [1, 2]
    # La distancia se calcula igual: es información, no un filtro.
    assert resultado[0].distancia_km == pytest.approx(15.1, abs=0.5)
