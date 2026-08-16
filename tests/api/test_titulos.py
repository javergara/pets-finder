"""Título auto-compuesto para reportes sin nombre (feature 36) y para mascotas
en adopción sin nombre (AD-08 paso 2).

Los casos de `titulo_pet` son deliberadamente **los mismos** que los de su espejo
`tituloMascota` en `src/web/src/lib/adopcion.test.ts`: son dos implementaciones
de la misma regla en dos lenguajes y no hay candado automático que las ate, así
que lo único que queda es que un humano pueda contrastarlas a ojo en un minuto.
"""

from datetime import date

import pytest

from reencuentro_api.models.pet import Pet
from reencuentro_api.models.report import Report
from reencuentro_api.models.user import User
from reencuentro_api.services.titulos import titulo_pet, titulo_reporte


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


# ── Mascotas en adopción (AD-08) ─────────────────────────────────────────────
# Mismos cuatro casos que `tituloMascota` en `lib/adopcion.test.ts`, en el mismo
# orden: el que cambie uno de los dos lados tiene que ver el otro al lado.


def _mascota(**overrides) -> Pet:
    datos = {
        "user_id": 1,
        "nombre": "Nala",
        "especie": "perro",
        "sexo": "hembra",
        "edad_meses": 18,
        "tamano": "mediano",
        "energia": "media",
        "raza": None,
        "historia": "Rescatada en Armenia tras el sismo, busca hogar.",
        "zona": "Armenia",
    }
    datos.update(overrides)
    return Pet(**datos)


def test_el_nombre_de_la_mascota_manda_cuando_lo_tiene():
    assert titulo_pet(_mascota(nombre="Nala", raza="Labrador")) == "Nala"


def test_sin_nombre_compone_especie_tamano_raza():
    assert titulo_pet(_mascota(nombre="", raza="Labrador")) == "Perro mediano labrador"


def test_sin_raza_no_deja_huecos_ni_cuelga_el_separador():
    assert titulo_pet(_mascota(nombre="", raza=None)) == "Perro mediano"
    # El nombre en blanco cuenta como ausente: `nombre` es obligatorio en la DB,
    # pero un formulario puede mandar espacios y "  " en la vista previa se ve rota.
    assert titulo_pet(_mascota(nombre="   ", especie="gato", tamano="pequeño")) == "Gato pequeño"


def test_la_raza_otra_no_aporta_senas():
    assert titulo_pet(_mascota(nombre="", raza="Otra")) == "Perro mediano"


def test_el_tamano_va_crudo_no_la_etiqueta_de_la_ui():
    """`tamano` se interpola tal cual viene de la columna ("mediano"), no como la
    etiqueta que pinta la UI ("Mediana"). Es lo que ya hace `titulo_reporte` y lo
    que hace `tituloMascota`; escribir "Perro Mediana labrador" sería el bug."""
    assert titulo_pet(_mascota(nombre="", tamano="grande")) == "Perro grande"
    assert titulo_pet(_mascota(nombre="", especie="otro")) == "Otro animal mediano"
