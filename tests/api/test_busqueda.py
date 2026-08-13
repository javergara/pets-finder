"""Busca a tu mascota (feature 38): parecido explicable sin AI."""

from datetime import date

import pytest

from reencuentro_api.models.report import Report
from reencuentro_api.models.user import User
from reencuentro_api.services.busqueda import (
    ConsultaBusqueda,
    buscar_parecidos,
    puntuar_reporte,
)


def _reporte(**overrides) -> Report:
    datos = dict(
        user_id=1,
        tipo="encontrado",
        especie="perro",
        situacion="conmigo",
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


# --- Función pura ---


def test_parecido_es_relativo_a_los_criterios_dados():
    consulta = ConsultaBusqueda(especie="perro", zona="Cali")

    parecido, razones = puntuar_reporte(consulta, _reporte())

    # Un solo criterio dado y cumplido → 100%, no 25/100.
    assert parecido == 100
    assert razones == ["misma zona (Cali)"]


def test_atributos_pesan_y_los_no_cumplidos_bajan_el_parecido():
    consulta = ConsultaBusqueda(especie="perro", zona="Cali", color="Negro", tamano="mediano")
    candidato = _reporte(color="Negro", tamano="grande")

    parecido, razones = puntuar_reporte(consulta, candidato)

    # zona (25) + color (20) de un máximo 60 → 75%.
    assert parecido == 75
    assert "mismo color (negro)" in razones
    assert all("tamaño" not in r for r in razones)


def test_senas_coinciden_sin_tildes_ni_mayusculas():
    consulta = ConsultaBusqueda(especie="perro", senas="Collar ROJO y mancha café")
    candidato = _reporte(descripcion="Tiene un collar rojo, es color cafe con blanco")

    parecido, razones = puntuar_reporte(consulta, candidato)

    # "collar", "rojo" y "cafe" coinciden pese a tildes/mayúsculas; "mancha" no:
    # 3 de 4 señas → 75%.
    assert parecido == 75
    assert any(r.startswith("señas en común:") for r in razones)


def test_sin_ningun_criterio_el_parecido_es_cero():
    parecido, razones = puntuar_reporte(ConsultaBusqueda(especie="perro"), _reporte())

    assert parecido == 0
    assert razones == []


def test_buscar_filtra_especie_y_ordena_por_parecido():
    consulta = ConsultaBusqueda(especie="perro", zona="Cali", color="Negro")
    candidatos = [
        _reporte(id=1, zona="Armenia", color="Negro"),
        _reporte(id=2, zona="Cali", color="Negro"),
        _reporte(id=3, especie="gato", zona="Cali", color="Negro"),
        _reporte(id=4, zona="Cali", color="Blanco"),
    ]

    resultado = buscar_parecidos(consulta, candidatos)

    assert [r.id for r, _, _ in resultado] == [2, 4, 1]  # gato fuera; 100 > 55 > 44
    assert [p for _, p, _ in resultado] == [100, 56, 44]


# --- Endpoint ---


@pytest.fixture()
def sembrados(db_session):
    user = User(nombre="Ana", email="ana@example.co", ciudad="Cali")
    db_session.add(user)
    db_session.flush()
    encontrado = _reporte(
        user_id=user.id, descripcion="Perro con collar rojo en el parque", color="Negro"
    )
    perdido = _reporte(
        user_id=user.id, tipo="perdido", situacion=None, nombre_mascota="Rocky", color="Negro"
    )
    reunido = _reporte(user_id=user.id, estado="reunido", color="Negro")
    db_session.add_all([encontrado, perdido, reunido])
    db_session.commit()
    return encontrado, perdido


def test_endpoint_busca_solo_el_tipo_pedido_y_activos(client, sembrados):
    encontrado, perdido = sembrados

    respuesta = client.get(
        "/api/reports/busqueda",
        params={"especie": "perro", "tipo": "encontrado", "color": "Negro", "zona": "Cali"},
    )

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    # Solo el encontrado activo: el perdido es de otro tipo y el reunido no está activo.
    assert [r["id"] for r in cuerpo] == [encontrado.id]
    assert cuerpo[0]["parecido"] == 100
    assert "misma zona (Cali)" in cuerpo[0]["razones"]


def test_endpoint_valida_el_tipo(client):
    assert (
        client.get(
            "/api/reports/busqueda", params={"especie": "perro", "tipo": "reunido"}
        ).status_code
        == 422
    )
