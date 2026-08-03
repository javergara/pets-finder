from datetime import datetime, timedelta, timezone

from adopta_api.models.home_profile import HomeProfile
from adopta_api.models.match import Match
from adopta_api.models.pet import Pet
from adopta_api.models.shelter import Shelter
from adopta_api.models.user import User
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
    assert cuerpo[0]["etiqueta"] == "Cuestionario nuevo"
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


def test_calcular_etiqueta_en_revision_viejo_es_sin_responder_con_dias_exactos():
    ahora = datetime(2026, 8, 10, tzinfo=timezone.utc)
    creado_en = ahora - timedelta(days=5)
    assert (
        calcular_etiqueta_solicitud("en_revision", creado_en, ahora=ahora)
        == "Sin responder · 5 días"
    )


def test_calcular_etiqueta_con_creado_en_naive_no_lanza_typeerror():
    """Regresión: creado_en puede venir naive (sin tzinfo) al leerlo de SQLite."""
    ahora = datetime(2026, 8, 10, tzinfo=timezone.utc)
    creado_en_naive = datetime(2026, 8, 5)  # sin tzinfo
    assert creado_en_naive.tzinfo is None

    resultado = calcular_etiqueta_solicitud("solicitado", creado_en_naive, ahora=ahora)

    assert resultado == "Sin responder · 5 días"
