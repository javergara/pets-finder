"""Página HTML para bots de redes (feature 21, ADR 0009): og tags por reporte."""

from datetime import date

import pytest

from reencuentro_api.models.report import Report
from reencuentro_api.models.user import User


@pytest.fixture()
def reporte(db_session):
    user = User(nombre="Ana", email="ana@example.co", ciudad="Armenia")
    db_session.add(user)
    db_session.commit()
    r = Report(
        user_id=user.id,
        tipo="perdido",
        especie="perro",
        nombre_mascota="Rocky",
        descripcion='Criollo color miel con collar rojo & pañoleta "verde".',
        foto_url="/media/uploads/abc.jpg",
        zona="Armenia",
        lat=4.54,
        lng=-75.68,
        fecha_evento=date(2026, 8, 10),
        telefono_contacto="3001234567",
    )
    db_session.add(r)
    db_session.commit()
    return r


def test_pagina_de_reporte_lleva_los_og_tags(client, reporte):
    respuesta = client.get(f"/reporte/{reporte.id}")

    assert respuesta.status_code == 200
    assert respuesta.headers["content-type"].startswith("text/html")
    html = respuesta.text
    assert '<meta property="og:title" content="Rocky — Se perdió en Armenia">' in html
    assert 'og:site_name" content="Pet Finder Col"' in html
    # La foto relativa se vuelve absoluta con el dominio del sitio.
    assert (
        '<meta property="og:image" content="https://petfinder-col.com/media/uploads/abc.jpg">'
        in html
    )
    assert (
        '<meta property="og:url" content="https://petfinder-col.com/reporte/'
        f'{reporte.id}">' in html
    )
    # La descripción con caracteres especiales queda escapada, no rompe el HTML.
    assert "&amp;" in html and "&quot;verde&quot;" in html


def test_pagina_sin_foto_omite_og_image(client, db_session, reporte):
    reporte.foto_url = None
    db_session.commit()

    html = client.get(f"/reporte/{reporte.id}").text

    assert "og:image" not in html
    assert 'og:title" content="Rocky' in html


def test_pagina_con_foto_absoluta_la_usa_tal_cual(client, db_session, reporte):
    reporte.foto_url = "https://cdn.example.com/foto.jpg"
    db_session.commit()

    html = client.get(f"/reporte/{reporte.id}").text

    assert '<meta property="og:image" content="https://cdn.example.com/foto.jpg">' in html


def test_pagina_de_reporte_inexistente_devuelve_404(client, db_session):
    assert client.get("/reporte/999").status_code == 404
