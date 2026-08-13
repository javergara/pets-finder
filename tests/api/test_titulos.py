"""Título auto-compuesto para reportes sin nombre (feature 36)."""

from datetime import date

import pytest

from reencuentro_api.models.report import Report
from reencuentro_api.models.user import User
from reencuentro_api.services.titulos import titulo_reporte


def _reporte(**overrides) -> Report:
    datos = {
        "user_id": 1,
        "tipo": "perdido",
        "especie": "perro",
        "nombre_mascota": None,
        "tamano": None,
        "color": None,
        "descripcion": "x",
        "zona": "Armenia",
        "lat": 4.54,
        "lng": -75.68,
        "fecha_evento": date(2026, 8, 10),
        "telefono_contacto": "3001234567",
    }
    datos.update(overrides)
    return Report(**datos)


def test_con_nombre_el_nombre_manda():
    assert titulo_reporte(_reporte(nombre_mascota="Rocky", color="Negro")) == "Rocky"


def test_sin_nombre_compone_especie_tamano_color():
    assert titulo_reporte(_reporte(tamano="mediano", color="Café")) == "Perro mediano café"


def test_omite_atributos_ausentes_sin_huecos():
    assert titulo_reporte(_reporte()) == "Perro"
    assert titulo_reporte(_reporte(especie="gato", color="Atigrado")) == "Gato atigrado"
    assert titulo_reporte(_reporte(tamano="grande")) == "Perro grande"


def test_color_otro_no_aporta_senas():
    assert titulo_reporte(_reporte(tamano="pequeño", color="Otro")) == "Perro pequeño"


@pytest.fixture()
def reporte_sin_nombre(db_session):
    user = User(nombre="Ana", email="ana2@example.co", ciudad="Armenia")
    db_session.add(user)
    db_session.commit()
    r = _reporte(user_id=user.id, tamano="mediano", color="Café")
    db_session.add(r)
    db_session.commit()
    return r


def test_og_tags_usan_el_titulo_compuesto(client, reporte_sin_nombre):
    html = client.get(f"/reporte/{reporte_sin_nombre.id}").text

    assert 'og:title" content="Perro mediano café — Se perdió en Armenia"' in html
