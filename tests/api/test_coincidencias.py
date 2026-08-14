import math
from datetime import date

import pytest

from reencuentro_api.models.report import Report
from reencuentro_api.models.user import User
from reencuentro_api.services.coincidencias import (
    PESO_DIAS,
    UMBRAL_ALTO,
    UMBRAL_MEDIO,
    UMBRAL_MISMA_IMAGEN,
    banda_de_parecido,
    ordenar_coincidencias,
    similitud_coseno,
)


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

    assert [c for c, _, _ in resultado] == [cerca, lejos]
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


# --- Parecido visual (ADR 0012) ---
#
# Vectores escritos a mano, nunca inferencia: estos tests verifican la LÓGICA de
# combinación, no la calidad del modelo (eso se calibró aparte, contra las fotos
# reales de producción). Corren sin red y sin torch.

PIPELINE = "yolos-tiny+dinov2-animal-id/v1"


def _vector(*, similitud=None) -> list[float]:
    """Vector unitario de 384 dims. Con `similitud`, forma ese coseno exacto
    contra el vector base (dos ejes ortogonales: cos²+sin²=1)."""
    vector = [0.0] * 384
    if similitud is None:
        vector[0] = 1.0
    else:
        vector[0] = similitud
        vector[1] = math.sqrt(1 - similitud**2)
    return vector


def _con_vector(similitud=None, modelo=PIPELINE, **overrides) -> Report:
    return _reporte(embedding=_vector(similitud=similitud), embedding_modelo=modelo, **overrides)


def test_sin_embeddings_el_orden_es_identico_al_de_antes_del_adr_0012():
    """Propiedad clave: `cercania` es monótona decreciente del puntaje viejo,
    así que sin vectores el ranking no cambia en absoluto."""
    perdido = _reporte()
    candidatos = [
        _reporte(tipo="encontrado", lat=4.575, lng=-75.640),
        _reporte(tipo="encontrado", lat=4.541, lng=-75.681),
        _reporte(tipo="encontrado", fecha_evento=date(2026, 8, 20)),
        _reporte(tipo="encontrado", lat=4.560, lng=-75.660, fecha_evento=date(2026, 8, 12)),
    ]

    resultado = ordenar_coincidencias(perdido, candidatos)

    puntaje_viejo = [
        distancia + PESO_DIAS * abs((perdido.fecha_evento - c.fecha_evento).days)
        for c, distancia, _ in resultado
    ]
    assert puntaje_viejo == sorted(puntaje_viejo), "el orden histórico se rompió"
    assert all(similitud is None for _c, _d, similitud in resultado)


def test_otra_zona_entra_solo_con_parecido_suficiente():
    perdido = _con_vector()
    parecida = _con_vector(similitud=0.95, tipo="encontrado", zona="Pereira", lat=4.81, lng=-75.70)
    distinta = _con_vector(similitud=0.30, tipo="encontrado", zona="Pereira", lat=4.81, lng=-75.70)

    resultado = ordenar_coincidencias(perdido, [parecida, distinta])

    assert [c for c, _, _ in resultado] == [parecida]


def test_un_parecido_fuerte_de_otra_zona_le_gana_a_uno_pegado_pero_distinto():
    """Es el caso que la heurística sola no podía resolver: la mascota que
    apareció en la ciudad vecina."""
    perdido = _con_vector()
    pegado_pero_distinto = _con_vector(similitud=0.10, tipo="encontrado", lat=4.5401, lng=-75.6801)
    lejano_pero_igual = _con_vector(
        similitud=0.99, tipo="encontrado", zona="Pereira", lat=4.81, lng=-75.70
    )

    resultado = ordenar_coincidencias(perdido, [pegado_pero_distinto, lejano_pero_igual])

    assert resultado[0][0] is lejano_pero_igual


def test_el_parecido_nunca_hunde_a_un_candidato():
    """Un parecido bajo es ausencia de evidencia, no evidencia en contra: no
    puede dejar a un candidato por debajo de otro sin foto en la misma posición."""
    perdido = _con_vector()
    con_foto_distinta = _con_vector(similitud=0.05, tipo="encontrado", lat=4.541, lng=-75.681)
    sin_foto = _reporte(tipo="encontrado", lat=4.575, lng=-75.640)

    resultado = ordenar_coincidencias(perdido, [sin_foto, con_foto_distinta])

    assert (
        resultado[0][0] is con_foto_distinta
    ), "el más cercano sigue primero pese al parecido bajo"


def test_vectores_de_pipelines_distintos_no_se_comparan():
    perdido = _con_vector()
    otro_pipeline = _con_vector(
        similitud=0.99, modelo="pipeline-viejo/v0", tipo="encontrado", lat=4.545, lng=-75.678
    )

    resultado = ordenar_coincidencias(perdido, [otro_pipeline])

    assert resultado[0][2] is None, "espacios vectoriales distintos: mezclarlos sería un bug mudo"


def test_la_misma_foto_no_cuenta_como_parecido():
    """El crawler saca N mascotas de un mismo pantallazo (ADR 0010 §6): ahí un
    coseno de 1.0 dice 'es la misma imagen', no 'es la misma mascota'."""
    perdido = _con_vector(foto_url="https://bucket/post.jpg")
    mismo_pantallazo = _con_vector(
        similitud=1.0, tipo="encontrado", foto_url="https://bucket/post.jpg"
    )

    resultado = ordenar_coincidencias(perdido, [mismo_pantallazo])

    assert resultado[0][2] is None


def test_bandas_de_parecido():
    assert banda_de_parecido(0.95) == "alto"
    assert banda_de_parecido(UMBRAL_ALTO) == "alto"
    assert banda_de_parecido(0.85) == "medio"
    assert banda_de_parecido(UMBRAL_MEDIO) == "medio"
    assert banda_de_parecido(0.79) is None, "por debajo del umbral no se le dice nada al usuario"
    assert banda_de_parecido(None) is None


def test_endpoint_expone_la_banda_y_nunca_el_vector(client, db_session):
    user = User(nombre="Ana", email="ana@example.co", ciudad="Armenia")
    db_session.add(user)
    db_session.flush()
    perdido = _con_vector(user_id=user.id)
    encontrado = _con_vector(
        similitud=0.97,
        user_id=user.id,
        tipo="encontrado",
        situacion="conmigo",
        lat=4.545,
        lng=-75.678,
    )
    db_session.add_all([perdido, encontrado])
    db_session.commit()

    cuerpo = client.get(f"/api/reports/{perdido.id}/coincidencias").json()

    assert cuerpo[0]["parecido_foto"] == "alto"
    assert "embedding" not in cuerpo[0], "384 floats no tienen por qué viajar al cliente"


def test_admision_cruzada_en_el_umbral_exacto():
    """El borde donde la admisión (>=) y el bono (>) se separan a propósito:
    en UMBRAL_MEDIO justo el candidato entra, pero todavía no gana nada."""
    perdido = _con_vector()
    en_el_umbral = _con_vector(
        similitud=UMBRAL_MEDIO, tipo="encontrado", zona="Pereira", lat=4.81, lng=-75.70
    )
    justo_debajo = _con_vector(
        similitud=UMBRAL_MEDIO - 0.01, tipo="encontrado", zona="Pereira", lat=4.81, lng=-75.70
    )

    resultado = ordenar_coincidencias(perdido, [en_el_umbral, justo_debajo])

    assert [c for c, _, _ in resultado] == [en_el_umbral]


def test_similitud_coseno_bordes():
    """Los vectores salen de una columna JSON: nada de lo raro debe reventar."""
    base = _vector()
    assert similitud_coseno(base, base) == pytest.approx(1.0)
    assert similitud_coseno(None, base) is None
    assert similitud_coseno([], base) is None
    assert similitud_coseno([1.0, 0.0], base) is None, "longitudes distintas no se comparan"
    assert similitud_coseno(["a"] * 384, base) is None, "JSON no numérico no puede dar un 500"
    assert similitud_coseno(base, [None] * 384) is None


def test_una_foto_ajena_re_subida_no_se_cuela_al_primer_puesto():
    """Sin auth (ADR 0005 §4) cualquiera puede bajar la foto pública de un
    reporte perdido, re-subirla —lo que le da una URL NUEVA— y publicar un
    'encontrado' que quedaría clavado de primero. Se detecta por vector."""
    perdido = _con_vector(foto_url="https://bucket/original.jpg")
    impostor = _con_vector(
        similitud=1.0,
        tipo="encontrado",
        foto_url="https://bucket/copia-re-subida.jpg",  # otra URL, misma imagen
        zona="Bogotá",
        lat=4.65,
        lng=-74.10,
    )
    rescatista_real = _con_vector(similitud=0.20, tipo="encontrado", lat=4.5401, lng=-75.6801)

    resultado = ordenar_coincidencias(perdido, [impostor, rescatista_real])

    assert resultado[0][0] is rescatista_real, "el impostor no puede desplazar al rescatista real"
    assert impostor not in [c for c, _, _ in resultado], "sin zona ni parecido, ni siquiera entra"


def test_el_verdadero_positivo_real_sigue_pasando_el_guardia():
    """El guardia de 'misma imagen' no puede tragarse un reencuentro de verdad:
    el verdadero positivo medido en la calibración fue 0.997."""
    perdido = _con_vector()
    reencuentro = _con_vector(similitud=0.997, tipo="encontrado", lat=4.545, lng=-75.678)

    resultado = ordenar_coincidencias(perdido, [reencuentro])

    assert resultado[0][2] == pytest.approx(0.997, abs=1e-6)
    assert 0.997 < UMBRAL_MISMA_IMAGEN
