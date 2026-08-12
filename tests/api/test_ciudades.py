import re
from pathlib import Path

from reencuentro_api.services.ciudades import COLOMBIA, ZONA_OTRO, ZONAS, zona_valida


def test_cada_zona_contiene_su_propio_centro():
    for nombre, caja in ZONAS.items():
        assert caja["lat_min"] <= caja["centro_lat"] <= caja["lat_max"], nombre
        assert caja["lng_min"] <= caja["centro_lng"] <= caja["lng_max"], nombre


def test_colombia_contiene_todas_las_zonas():
    for nombre, caja in ZONAS.items():
        assert COLOMBIA["lat_min"] <= caja["lat_min"], nombre
        assert caja["lat_max"] <= COLOMBIA["lat_max"], nombre
        assert COLOMBIA["lng_min"] <= caja["lng_min"], nombre
        assert caja["lng_max"] <= COLOMBIA["lng_max"], nombre


def test_zona_valida_acepta_las_conocidas_y_otro():
    for nombre in ZONAS:
        assert zona_valida(nombre)
    assert zona_valida(ZONA_OTRO)


def test_zona_valida_rechaza_desconocidas():
    assert not zona_valida("Palmira")
    assert not zona_valida("")
    assert not zona_valida("armenia")  # sensible a mayúsculas: el frontend manda la clave exacta


def test_las_zonas_son_las_del_pivot_mas_medellin():
    # Las 6 del pivot + Medellín (feature 26, benchmark de Reúne Mascotas).
    assert set(ZONAS) == {"Armenia", "Pereira", "Manizales", "Cali", "Quibdó", "Bogotá", "Medellín"}


def test_zonas_en_sync_con_el_frontend():
    """El duplicado consciente de lib/ciudades.ts debe coincidir número a número.

    Es el test comparativo que docs pedían desde el pivot: al tocar una zona hay
    que cambiar backend Y frontend — este test truena si se olvida uno.
    """
    ts = (Path(__file__).parents[2] / "src" / "web" / "src" / "lib" / "ciudades.ts").read_text()
    claves = {
        "latMin": "lat_min",
        "latMax": "lat_max",
        "lngMin": "lng_min",
        "lngMax": "lng_max",
        "centroLat": "centro_lat",
        "centroLng": "centro_lng",
    }
    for nombre, caja in ZONAS.items():
        bloque = re.search(re.escape(nombre) + r":\s*\{(.*?)\}", ts, re.S)
        assert bloque, f"la zona {nombre} no existe en lib/ciudades.ts"
        for clave_ts, clave_py in claves.items():
            valor = re.search(clave_ts + r":\s*(-?\d+(?:\.\d+)?)", bloque.group(1))
            assert valor, f"{nombre}.{clave_ts} no está en lib/ciudades.ts"
            assert float(valor.group(1)) == caja[clave_py], f"{nombre}.{clave_ts} desincronizado"
