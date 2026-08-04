from datetime import datetime, timedelta, timezone

import pytest

from adopta_api.models.home_profile import HomeProfile
from adopta_api.models.match import Match
from adopta_api.models.pet import Pet
from adopta_api.models.shelter import Shelter
from adopta_api.models.user import User
from adopta_api.services.geo import distancia_km
from adopta_api.services.solicitudes import calcular_etiqueta_solicitud


def _crear_shelter(db_session, **overrides):
    defaults = dict(nombre="Refugio Huellas", ciudad="Bogotá", tiempo_respuesta_horas=12)
    defaults.update(overrides)
    shelter = Shelter(**defaults)
    db_session.add(shelter)
    db_session.flush()
    return shelter


def _crear_pet(db_session, shelter, **overrides):
    defaults = dict(
        shelter_id=shelter.id,
        nombre="Firulais",
        especie="perro",
        raza="Criollo",
        sexo="macho",
        edad_meses=24,
        tamano="mediano",
        energia="media",
        historia="Un perro encantador.",
        tags=[],
        fotos=["/media/pet_1.jpg"],
        apto_ninos=True,
        apto_perros=True,
        apto_gatos=True,
    )
    defaults.update(overrides)
    pet = Pet(**defaults)
    db_session.add(pet)
    db_session.flush()
    return pet


def _crear_match(db_session, adoptante, pet, shelter, estado="solicitado", motivo_descarte=None):
    match = Match(
        user_id=adoptante.id,
        pet_id=pet.id,
        shelter_id=shelter.id,
        estado=estado,
        motivo_descarte=motivo_descarte,
    )
    db_session.add(match)
    db_session.commit()
    db_session.refresh(match)
    return match


def _post_accion(client, shelter_id, match_id, endpoint, body=None):
    url = f"/api/shelters/{shelter_id}/solicitudes/{match_id}/{endpoint}"
    if body is None:
        return client.post(url)
    return client.post(url, json=body)


def _crear_adoptante_con_home(db_session, nombre="Ana", email="ana@example.co", bio="Amo perros."):
    user = User(nombre=nombre, email=email, ciudad="Bogotá", bio=bio)
    db_session.add(user)
    db_session.flush()

    home = HomeProfile(
        user_id=user.id,
        vivienda="casa",
        espacio_exterior="patio",
        personas_en_casa=2,
        tiene_ninos=False,
        tiene_otros_perros=False,
        tiene_otros_gatos=False,
        horas_fuera_dia=4,
        experiencia_previa="algo",
        presupuesto_mensual_cop=150_000,
        preferencia_especies=[],
        preferencia_tamanos=[],
        preferencia_energia="media",
    )
    db_session.add(home)
    db_session.flush()
    return user, home


# --- GET /api/shelters (feature 14-shelter-map) -----------------------------


def test_listar_refugios_mapa_sin_refugios_devuelve_200_vacio(client, db_session):
    respuesta = client.get("/api/shelters")

    assert respuesta.status_code == 200
    assert respuesta.json() == []


def test_listar_refugios_mapa_cuenta_solo_mascotas_disponibles(client, db_session):
    shelter = _crear_shelter(db_session)
    disponible_1 = _crear_pet(db_session, shelter, nombre="Firulais", estado="disponible")
    disponible_2 = _crear_pet(db_session, shelter, nombre="Toby", estado="disponible")
    _crear_pet(db_session, shelter, nombre="Rocky", estado="adoptado")

    respuesta = client.get("/api/shelters")

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert len(cuerpo) == 1
    refugio = cuerpo[0]
    assert refugio["mascotas_disponibles"] == 2
    nombres = {m["nombre"] for m in refugio["mascotas"]}
    assert nombres == {disponible_1.nombre, disponible_2.nombre}
    assert "Rocky" not in nombres


def test_listar_refugios_mapa_sin_user_id_distancia_es_null(client, db_session):
    _crear_shelter(db_session, lat=4.65, lng=-74.05)
    _crear_shelter(db_session, nombre="Refugio B", lat=None, lng=None)

    respuesta = client.get("/api/shelters")

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert len(cuerpo) == 2
    assert all(refugio["distancia_km"] is None for refugio in cuerpo)


def test_listar_refugios_mapa_con_user_id_calcula_distancia_km(client, db_session):
    user = User(
        nombre="Ana", email="ana-mapa@example.co", ciudad="Bogotá", lat=4.6946, lng=-74.0307
    )
    db_session.add(user)
    _crear_shelter(db_session, lat=4.6486, lng=-74.0629)
    db_session.commit()

    respuesta = client.get(f"/api/shelters?user_id={user.id}")

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert len(cuerpo) == 1
    esperado = distancia_km(4.6946, -74.0307, 4.6486, -74.0629)
    assert cuerpo[0]["distancia_km"] == pytest.approx(esperado)


def test_listar_refugios_mapa_user_id_inexistente_devuelve_404(client, db_session):
    respuesta = client.get("/api/shelters?user_id=9999")

    assert respuesta.status_code == 404
    assert "9999" in respuesta.json()["detail"]


# --- GET /api/shelters/{id} -------------------------------------------------


def test_obtener_refugio_calcula_metricas(client, db_session):
    shelter = _crear_shelter(db_session, adopciones_cerradas=7)
    pet1 = _crear_pet(db_session, shelter, nombre="Firulais")
    pet2 = _crear_pet(db_session, shelter, nombre="Toby")
    adoptante, _home = _crear_adoptante_con_home(db_session)

    ahora = datetime.now(timezone.utc).replace(tzinfo=None)
    hace_2_meses = (ahora.replace(day=1) - timedelta(days=45)).replace(tzinfo=None)

    # Dentro del mes actual, distintos estados.
    db_session.add(
        Match(
            user_id=adoptante.id,
            pet_id=pet1.id,
            shelter_id=shelter.id,
            estado="solicitado",
            creado_en=ahora,
        )
    )
    db_session.add(
        Match(
            user_id=adoptante.id,
            pet_id=pet2.id,
            shelter_id=shelter.id,
            estado="visita_agendada",
            creado_en=ahora,
        )
    )
    # Fuera del mes actual: no debe contar para interesados_este_mes.
    db_session.add(
        Match(
            user_id=adoptante.id,
            pet_id=pet1.id,
            shelter_id=shelter.id,
            estado="cerrado",
            creado_en=hace_2_meses,
        )
    )
    db_session.commit()

    respuesta = client.get(f"/api/shelters/{shelter.id}")

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["nombre"] == "Refugio Huellas"
    metricas = cuerpo["metricas"]
    assert metricas["mascotas_publicadas"] == 2
    assert metricas["interesados_este_mes"] == 2
    assert metricas["visitas_agendadas"] == 1
    assert metricas["adopciones_cerradas"] == 7
    assert metricas["apadrinamientos_recaudados_cop"] == 0


def test_obtener_refugio_inexistente_devuelve_404(client, db_session):
    respuesta = client.get("/api/shelters/9999")

    assert respuesta.status_code == 404
    assert "9999" in respuesta.json()["detail"]


# --- GET /api/shelters/{id}/solicitudes -------------------------------------


def test_listar_solicitudes_vacia_sin_matches_no_es_404(client, db_session):
    shelter = _crear_shelter(db_session)
    _crear_pet(db_session, shelter)

    respuesta = client.get(f"/api/shelters/{shelter.id}/solicitudes")

    assert respuesta.status_code == 200
    assert respuesta.json() == []


def test_listar_solicitudes_inexistente_devuelve_404(client, db_session):
    respuesta = client.get("/api/shelters/9999/solicitudes")

    assert respuesta.status_code == 404
    assert "9999" in respuesta.json()["detail"]


def test_listar_solicitudes_ordenada_con_afinidad_y_etiqueta(client, db_session):
    shelter = _crear_shelter(db_session)
    pet = _crear_pet(db_session, shelter)
    adoptante, _home = _crear_adoptante_con_home(db_session)

    ahora = datetime.now(timezone.utc).replace(tzinfo=None)
    hace_3_dias = ahora - timedelta(days=3)
    hace_1_hora = ahora - timedelta(hours=1)

    match_viejo = Match(
        user_id=adoptante.id,
        pet_id=pet.id,
        shelter_id=shelter.id,
        estado="solicitado",
        creado_en=hace_3_dias,
    )
    match_reciente = Match(
        user_id=adoptante.id,
        pet_id=pet.id,
        shelter_id=shelter.id,
        estado="en_revision",
        creado_en=hace_1_hora,
    )
    db_session.add_all([match_viejo, match_reciente])
    db_session.commit()

    respuesta = client.get(f"/api/shelters/{shelter.id}/solicitudes")

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert len(cuerpo) == 2
    # Orden: creado_en desc -> el más reciente primero.
    assert cuerpo[0]["id"] == match_reciente.id
    assert cuerpo[0]["etiqueta"] == "En revisión"
    assert cuerpo[1]["id"] == match_viejo.id
    assert cuerpo[1]["etiqueta"] == "Sin responder · 3 días"
    assert cuerpo[0]["adoptante"]["nombre"] == "Ana"
    assert cuerpo[0]["pet"]["nombre"] == pet.nombre
    assert "score" in cuerpo[0]["afinidad"]


def test_listar_solicitudes_excluye_match_sin_home_profile(client, db_session):
    shelter = _crear_shelter(db_session)
    pet = _crear_pet(db_session, shelter)
    # Adoptante SIN HomeProfile (caso defensivo, no debería pasar en producción).
    user_sin_home = User(nombre="Sin Home", email="sinhome@example.co")
    db_session.add(user_sin_home)
    db_session.flush()
    db_session.add(Match(user_id=user_sin_home.id, pet_id=pet.id, shelter_id=shelter.id))
    db_session.commit()

    respuesta = client.get(f"/api/shelters/{shelter.id}/solicitudes")

    assert respuesta.status_code == 200
    assert respuesta.json() == []


# --- GET /api/shelters/{id}/solicitudes/{match_id} --------------------------


def test_obtener_solicitud_detalle_completo(client, db_session):
    shelter = _crear_shelter(db_session)
    pet = _crear_pet(db_session, shelter)
    adoptante, home = _crear_adoptante_con_home(db_session, bio="Me encantan los animales.")

    match = Match(user_id=adoptante.id, pet_id=pet.id, shelter_id=shelter.id)
    db_session.add(match)
    db_session.commit()

    respuesta = client.get(f"/api/shelters/{shelter.id}/solicitudes/{match.id}")

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["id"] == match.id
    assert cuerpo["bio"] == "Me encantan los animales."
    assert cuerpo["home_profile"]["vivienda"] == home.vivienda
    assert cuerpo["home_profile"]["horas_fuera_dia"] == home.horas_fuera_dia


def test_obtener_solicitud_refugio_inexistente_devuelve_404(client, db_session):
    respuesta = client.get("/api/shelters/9999/solicitudes/1")

    assert respuesta.status_code == 404
    assert "9999" in respuesta.json()["detail"]


def test_obtener_solicitud_match_inexistente_devuelve_404(client, db_session):
    shelter = _crear_shelter(db_session)

    respuesta = client.get(f"/api/shelters/{shelter.id}/solicitudes/9999")

    assert respuesta.status_code == 404


def test_obtener_solicitud_de_otro_refugio_devuelve_404(client, db_session):
    shelter_a = _crear_shelter(db_session, nombre="Refugio A")
    shelter_b = _crear_shelter(db_session, nombre="Refugio B")
    pet_a = _crear_pet(db_session, shelter_a)
    adoptante, _home = _crear_adoptante_con_home(db_session)

    match_de_a = Match(user_id=adoptante.id, pet_id=pet_a.id, shelter_id=shelter_a.id)
    db_session.add(match_de_a)
    db_session.commit()

    # El match pertenece a shelter_a, no a shelter_b: no debe filtrarse.
    respuesta = client.get(f"/api/shelters/{shelter_b.id}/solicitudes/{match_de_a.id}")

    assert respuesta.status_code == 404


# --- services/solicitudes.py::calcular_etiqueta_solicitud (unitario, sin DB) ---


def test_calcular_etiqueta_visita_agendada():
    ahora = datetime(2026, 8, 3, tzinfo=timezone.utc)
    assert calcular_etiqueta_solicitud("visita_agendada", ahora, ahora=ahora) == "Visita agendada"


def test_calcular_etiqueta_adoptado():
    ahora = datetime(2026, 8, 3, tzinfo=timezone.utc)
    assert calcular_etiqueta_solicitud("adoptado", ahora, ahora=ahora) == "Adopción cerrada"


def test_calcular_etiqueta_cerrado():
    ahora = datetime(2026, 8, 3, tzinfo=timezone.utc)
    assert calcular_etiqueta_solicitud("cerrado", ahora, ahora=ahora) == "Solicitud cerrada"


def test_calcular_etiqueta_solicitado_reciente_es_cuestionario_nuevo():
    ahora = datetime(2026, 8, 3, tzinfo=timezone.utc)
    creado_en = ahora - timedelta(hours=5)
    assert calcular_etiqueta_solicitud("solicitado", creado_en, ahora=ahora) == "Cuestionario nuevo"


def test_calcular_etiqueta_en_revision_viejo_es_en_revision():
    ahora = datetime(2026, 8, 10, tzinfo=timezone.utc)
    creado_en = ahora - timedelta(days=5)
    assert calcular_etiqueta_solicitud("en_revision", creado_en, ahora=ahora) == "En revisión"


def test_calcular_etiqueta_con_creado_en_naive_no_lanza_typeerror():
    """Regresión: creado_en puede venir naive (sin tzinfo) al leerlo de SQLite."""
    ahora = datetime(2026, 8, 10, tzinfo=timezone.utc)
    creado_en_naive = datetime(2026, 8, 5)  # sin tzinfo
    assert creado_en_naive.tzinfo is None

    resultado = calcular_etiqueta_solicitud("solicitado", creado_en_naive, ahora=ahora)

    assert resultado == "Sin responder · 5 días"


# --- POST .../agendar-visita, .../pedir-informacion, .../descartar (feature 10) ---


@pytest.mark.parametrize(
    "endpoint,estado_inicial,estado_esperado",
    [
        ("agendar-visita", "solicitado", "visita_agendada"),
        ("agendar-visita", "en_revision", "visita_agendada"),
        ("pedir-informacion", "solicitado", "en_revision"),
        ("descartar", "solicitado", "cerrado"),
        ("descartar", "en_revision", "cerrado"),
        ("descartar", "visita_agendada", "cerrado"),
    ],
)
def test_transicion_valida_actualiza_estado_y_persiste(
    client, db_session, endpoint, estado_inicial, estado_esperado
):
    shelter = _crear_shelter(db_session)
    pet = _crear_pet(db_session, shelter)
    adoptante, _home = _crear_adoptante_con_home(db_session)
    match = _crear_match(db_session, adoptante, pet, shelter, estado=estado_inicial)

    body = {"motivo": "No cumple con el espacio requerido."} if endpoint == "descartar" else None
    respuesta = _post_accion(client, shelter.id, match.id, endpoint, body)

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["id"] == match.id
    assert cuerpo["estado"] == estado_esperado

    db_session.refresh(match)
    assert match.estado == estado_esperado
    if endpoint == "descartar":
        assert match.motivo_descarte == "No cumple con el espacio requerido."
    else:
        assert match.motivo_descarte is None


def test_descartar_recorta_espacios_del_motivo(client, db_session):
    shelter = _crear_shelter(db_session)
    pet = _crear_pet(db_session, shelter)
    adoptante, _home = _crear_adoptante_con_home(db_session)
    match = _crear_match(db_session, adoptante, pet, shelter, estado="solicitado")

    respuesta = _post_accion(
        client,
        shelter.id,
        match.id,
        "descartar",
        {"motivo": "   No cumple con el espacio requerido.   "},
    )

    assert respuesta.status_code == 200
    db_session.refresh(match)
    assert match.motivo_descarte == "No cumple con el espacio requerido."


@pytest.mark.parametrize("motivo", ["", "   ", "\n\t"])
def test_descartar_con_motivo_vacio_o_solo_espacios_devuelve_422(client, db_session, motivo):
    shelter = _crear_shelter(db_session)
    pet = _crear_pet(db_session, shelter)
    adoptante, _home = _crear_adoptante_con_home(db_session)
    match = _crear_match(db_session, adoptante, pet, shelter, estado="solicitado")

    respuesta = _post_accion(client, shelter.id, match.id, "descartar", {"motivo": motivo})

    assert respuesta.status_code == 422
    db_session.refresh(match)
    assert match.estado == "solicitado"
    assert match.motivo_descarte is None


# Matriz completa de transiciones inválidas: terminal (adoptado/cerrado) -> cualquier
# acción; visita_agendada -> agendar-visita/pedir-informacion; en_revision ->
# pedir-informacion. Ver `services/solicitudes.py::TRANSICIONES_VALIDAS`.
TRANSICIONES_INVALIDAS = [
    ("agendar-visita", "visita_agendada"),
    ("agendar-visita", "adoptado"),
    ("agendar-visita", "cerrado"),
    ("pedir-informacion", "en_revision"),
    ("pedir-informacion", "visita_agendada"),
    ("pedir-informacion", "adoptado"),
    ("pedir-informacion", "cerrado"),
    ("descartar", "adoptado"),
    ("descartar", "cerrado"),
]


@pytest.mark.parametrize("endpoint,estado_inicial", TRANSICIONES_INVALIDAS)
def test_transicion_invalida_devuelve_409_y_no_muta_estado(
    client, db_session, endpoint, estado_inicial
):
    shelter = _crear_shelter(db_session)
    pet = _crear_pet(db_session, shelter)
    adoptante, _home = _crear_adoptante_con_home(db_session)
    match = _crear_match(db_session, adoptante, pet, shelter, estado=estado_inicial)

    body = {"motivo": "Motivo cualquiera."} if endpoint == "descartar" else None
    respuesta = _post_accion(client, shelter.id, match.id, endpoint, body)

    assert respuesta.status_code == 409
    detalle = respuesta.json()["detail"]
    assert detalle
    assert estado_inicial in detalle

    db_session.refresh(match)
    assert match.estado == estado_inicial


@pytest.mark.parametrize("endpoint", ["agendar-visita", "pedir-informacion", "descartar"])
def test_accion_refugio_inexistente_devuelve_404(client, db_session, endpoint):
    body = {"motivo": "x"} if endpoint == "descartar" else None
    respuesta = _post_accion(client, 9999, 1, endpoint, body)

    assert respuesta.status_code == 404
    assert "9999" in respuesta.json()["detail"]


@pytest.mark.parametrize("endpoint", ["agendar-visita", "pedir-informacion", "descartar"])
def test_accion_match_inexistente_devuelve_404(client, db_session, endpoint):
    shelter = _crear_shelter(db_session)

    body = {"motivo": "x"} if endpoint == "descartar" else None
    respuesta = _post_accion(client, shelter.id, 9999, endpoint, body)

    assert respuesta.status_code == 404


@pytest.mark.parametrize("endpoint", ["agendar-visita", "pedir-informacion", "descartar"])
def test_accion_match_de_otro_refugio_devuelve_404(client, db_session, endpoint):
    shelter_a = _crear_shelter(db_session, nombre="Refugio A")
    shelter_b = _crear_shelter(db_session, nombre="Refugio B")
    pet_a = _crear_pet(db_session, shelter_a)
    adoptante, _home = _crear_adoptante_con_home(db_session)
    match_de_a = _crear_match(db_session, adoptante, pet_a, shelter_a, estado="solicitado")

    body = {"motivo": "x"} if endpoint == "descartar" else None
    respuesta = _post_accion(client, shelter_b.id, match_de_a.id, endpoint, body)

    assert respuesta.status_code == 404


def test_get_matches_adoptante_no_expone_motivo_descarte(client, db_session):
    """`motivo_descarte` se persiste (ver tests de arriba) pero nunca debe filtrarse al
    adoptante: ni `schemas/match.py::MatchWithPetOut` ni el router de matches lo
    exponen. Este test lee la respuesta JSON real de `GET /api/matches`, no solo el
    schema en abstracto, para confirmarlo en el contrato HTTP efectivo."""
    shelter = _crear_shelter(db_session)
    pet = _crear_pet(db_session, shelter)
    adoptante, _home = _crear_adoptante_con_home(db_session)
    _crear_match(
        db_session, adoptante, pet, shelter, estado="cerrado", motivo_descarte="Motivo interno."
    )

    respuesta = client.get(f"/api/matches?user_id={adoptante.id}")

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert len(cuerpo) == 1
    for elemento in cuerpo:
        assert "motivo_descarte" not in elemento
