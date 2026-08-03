import pytest

from adopta_api.services.geo import distancia_km

# Coordenadas de barrios de Bogotá usadas en scripts/seed.py (BARRIO_COORDS).
USAQUEN = (4.6946, -74.0307)
CHAPINERO = (4.6486, -74.0629)
KENNEDY = (4.6280, -74.1497)


def test_distancia_cero_entre_el_mismo_punto():
    assert distancia_km(*USAQUEN, *USAQUEN) == 0.0


def test_distancia_entre_usaquen_y_chapinero_es_aproximadamente_6_2_km():
    # Distancia real en línea recta entre esos dos barrios de Bogotá.
    assert distancia_km(*USAQUEN, *CHAPINERO) == pytest.approx(6.24, abs=0.5)


def test_distancia_entre_usaquen_y_kennedy_es_aproximadamente_15_km():
    assert distancia_km(*USAQUEN, *KENNEDY) == pytest.approx(15.1, abs=0.5)


def test_distancia_es_simetrica():
    assert distancia_km(*USAQUEN, *CHAPINERO) == distancia_km(*CHAPINERO, *USAQUEN)


def test_distancia_no_es_negativa_ni_absurda_para_puntos_cercanos():
    # Dos puntos separados por ~0.01 grados (~1 km) no pueden dar miles de km.
    resultado = distancia_km(4.6946, -74.0307, 4.7046, -74.0307)
    assert 0 < resultado < 5
