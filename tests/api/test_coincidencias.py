from datetime import date

import pytest

from reencuentro_api.models.report import Report
from reencuentro_api.models.user import User
from reencuentro_api.services.coincidencias import PESO_DIAS, ordenar_coincidencias


def _reporte(**overrides) -> Report:
    datos = dict(
        user_id=1,
        tipo="perdido",
        especie="perro",
        descripcion="d",
        zona="Armenia",
        lat=4.540,
        lng=-75.680,
        fecha_evento=date(2026, 8, 10),
        telefono_contacto="300",
        estado="activo",
    )
    datos.update(overrides)
    return Report(**datos)


# --- Función pura ---


def test_filtra_solo_el_tipo_opuesto_misma_especie_zona_y_activos():
    perdido = _reporte()
    candidatos = [
        _reporte(tipo="encontrado", lat=4.545, lng=-75.678),  # válido
        _reporte(tipo="perdido"),  # mismo tipo: fuera
        _reporte(tipo="encontrado", especie="gato"),  # otra especie: fuera
        _reporte(tipo="encontrado", zona="Pereira", lat=4.81, lng=-75.70),  # otra zona: fuera
        _reporte(tipo="encontrado", estado="reunido"),  # ya reunido: fuera
    ]

    resultado = ordenar_coincidencias(perdido, candidatos)

    assert len(resultado) == 1
    assert resultado[0][0].tipo == "encontrado"


def test_ordena_por_distancia_con_fechas_iguales():
    perdido = _reporte()
    cerca = _reporte(tipo="encontrado", lat=4.541, lng=-75.681)
    lejos = _reporte(tipo="encontrado", lat=4.575, lng=-75.640)

    resultado = ordenar_coincidencias(perdido, [lejos, cerca])

    assert [c for c, _ in resultado] == [cerca, lejos]
    # La distancia devuelta es la geográfica real, creciente.
    assert resultado[0][1] < resultado[1][1]


def test_la_diferencia_de_fechas_penaliza_como_medio_km_por_dia():
    perdido = _reporte()
    # Mismo punto pero 10 días después: puntaje 0 + 0.5*10 = 5.
    mismo_punto_lejos_en_tiempo = _reporte(tipo="encontrado", fecha_evento=date(2026, 8, 20))
    # A ~2 km el mismo día: puntaje ~2 — debe ganar pese a estar más lejos.
    cerca_en_tiempo = _reporte(tipo="encontrado", lat=4.558, lng=-75.680)

    resultado = ordenar_coincidencias(perdido, [mismo_punto_lejos_en_tiempo, cerca_en_tiempo])

    assert resultado[0][0] is cerca_en_tiempo
    assert PESO_DIAS == 0.5


def test_funciona_en_ambas_direcciones():
    encontrado = _reporte(tipo="encontrado", lat=4.545, lng=-75.678)
    perdido = _reporte()

    resultado = ordenar_coincidencias(encontrado, [perdido])

    assert len(resultado) == 1
    assert resultado[0][0].tipo == "perdido"


# --- Endpoint de integración ---


@pytest.fixture()
def par_sembrado(db_session):
    """Replica el par de coincidencia obvia del seed: Rocky perdido ↔ perro
    encontrado a ~600 m y 1 día en Armenia, más ruido que no debe aparecer."""
    user = User(nombre="Ana", email="ana@example.co", ciudad="Armenia")
    db_session.add(user)
    db_session.flush()

    rocky = _reporte(user_id=user.id, nombre_mascota="Rocky")
    encontrado = _reporte(
        user_id=user.id,
        tipo="encontrado",
        situacion="conmigo",
        lat=4.545,
        lng=-75.678,
        fecha_evento=date(2026, 8, 11),
    )
    gato_otro_lado = _reporte(user_id=user.id, tipo="encontrado", especie="gato", situacion="vista")
    db_session.add_all([rocky, encontrado, gato_otro_lado])
    db_session.commit()
    return rocky, encontrado


def test_endpoint_devuelve_el_par_sembrado_con_distancia(client, par_sembrado):
    rocky, encontrado = par_sembrado

    respuesta = client.get(f"/api/reports/{rocky.id}/coincidencias")

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert len(cuerpo) == 1
    assert cuerpo[0]["id"] == encontrado.id
    assert cuerpo[0]["tipo"] == "encontrado"
    # ~600 m entre (4.540,-75.680) y (4.545,-75.678).
    assert 0.3 < cuerpo[0]["distancia_km"] < 1.0


def test_endpoint_reporte_inexistente_devuelve_404(client, db_session):
    respuesta = client.get("/api/reports/9999/coincidencias")

    assert respuesta.status_code == 404
    assert "9999" in respuesta.json()["detail"]


# --- Razones explicables (feature 37) ---


def test_razones_basicas_especie_zona_distancia_y_dias():
    from reencuentro_api.services.coincidencias import razones_coincidencia

    perdido = _reporte()
    candidato = _reporte(tipo="encontrado", fecha_evento=date(2026, 8, 12))

    razones = razones_coincidencia(perdido, candidato, 0.62)

    assert razones == ["mismo perro", "misma zona (Armenia)", "a 0.62 km", "2 días de diferencia"]


def test_razones_mismo_dia_color_y_tamano():
    from reencuentro_api.services.coincidencias import razones_coincidencia

    perdido = _reporte(color="Negro", tamano="mediano")
    candidato = _reporte(tipo="encontrado", color="Negro", tamano="mediano")

    razones = razones_coincidencia(perdido, candidato, 0.1)

    assert "el mismo día" in razones
    assert "mismo color" in razones
    assert "mismo tamaño" in razones


def test_razones_color_distinto_u_otro_no_se_afirma():
    from reencuentro_api.services.coincidencias import razones_coincidencia

    con_distinto = razones_coincidencia(
        _reporte(color="Negro"), _reporte(tipo="encontrado", color="Blanco"), 0.5
    )
    con_otro = razones_coincidencia(
        _reporte(color="Otro"), _reporte(tipo="encontrado", color="Otro"), 0.5
    )

    assert all("color" not in r for r in con_distinto)
    assert all("color" not in r for r in con_otro)


def test_endpoint_incluye_las_razones(client, par_sembrado):
    rocky, encontrado = par_sembrado

    cuerpo = client.get(f"/api/reports/{rocky.id}/coincidencias").json()

    razones = cuerpo[0]["razones"]
    assert "mismo perro" in razones
    assert "misma zona (Armenia)" in razones
    assert "1 día de diferencia" in razones
    assert any(r.startswith("a 0.") for r in razones)
