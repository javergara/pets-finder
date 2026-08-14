"""Landing por zona con SEO (feature 46)."""

from datetime import date

import pytest

from reencuentro_api.models.report import Report
from reencuentro_api.models.user import User


@pytest.fixture()
def sembrado(db_session):
    user = User(nombre="Ana", email="ana@example.co", ciudad="Cali")
    db_session.add(user)
    db_session.flush()

    def _r(**overrides):
        datos = dict(
            user_id=user.id,
            tipo="perdido",
            especie="perro",
            descripcion="d",
            zona="Cali",
            lat=3.45,
            lng=-76.53,
            fecha_evento=date(2026, 8, 10),
            telefono_contacto="300",
            estado="activo",
        )
        datos.update(overrides)
        return Report(**datos)

    db_session.add_all(
        [
            _r(),
            _r(),
            _r(tipo="encontrado", situacion="conmigo"),
            _r(zona="Armenia"),
            _r(estado="reunido"),
        ]
    )
    db_session.commit()


def test_conteos_por_zona_y_globales(client, sembrado):
    cali = client.get("/api/reports/conteos", params={"zona": "Cali"}).json()
    todos = client.get("/api/reports/conteos").json()

    assert cali == {"perdidos": 2, "encontrados": 1}
    assert todos == {"perdidos": 3, "encontrados": 1}


def test_pagina_de_bots_de_zona_lleva_og_propios(client, sembrado):
    r = client.get("/cali")

    assert r.status_code == 200
    html = r.text
    assert '<meta property="og:title" content="Mascotas perdidas y encontradas en Cali">' in html
    assert "busca a 2 mascotas perdidas y cuida 1 encontradas en Cali" in html
    assert 'og:url" content="https://petfinder-col.com/cali"' in html


def test_todos_los_slugs_responden_y_uno_desconocido_no(client):
    for slug in ("cali", "armenia", "pereira", "manizales", "quibdo", "bogota", "medellin"):
        assert client.get(f"/{slug}").status_code == 200, slug
    # Un slug desconocido no tiene ruta registrada: la API no lo atiende.
    assert client.get("/narnia").status_code == 404
