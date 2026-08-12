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
    assert not zona_valida("Medellín")
    assert not zona_valida("")
    assert not zona_valida("armenia")  # sensible a mayúsculas: el frontend manda la clave exacta


def test_las_seis_zonas_son_las_del_pivot():
    assert set(ZONAS) == {"Armenia", "Pereira", "Manizales", "Cali", "Quibdó", "Bogotá"}
