from adopta_api.models.home_profile import HomeProfile
from adopta_api.models.match import Match
from adopta_api.models.pet import Pet
from adopta_api.models.shelter import Shelter
from adopta_api.models.user import User

ESTADOS = ["solicitado", "en_revision", "visita_agendada", "adoptado", "cerrado"]


def _seed_usuario_con_matches(db_session, *, con_home_profile: bool):
    shelter = Shelter(nombre="Refugio Test", ciudad="Bogotá", tiempo_respuesta_horas=12)
    db_session.add(shelter)
    db_session.flush()

    pet = Pet(
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
    db_session.add(pet)

    user = User(nombre="Ana", email="ana@example.co", ciudad="Bogotá", barrio="Chapinero")
    db_session.add(user)
    db_session.flush()

    if con_home_profile:
        home = HomeProfile(
            user_id=user.id,
            vivienda="casa",
            espacio_exterior="patio",
            personas_en_casa=2,
            tiene_ninos=True,
            horas_fuera_dia=4,
            experiencia_previa="algo",
            presupuesto_mensual_cop=150_000,
            preferencia_especies=[],
            preferencia_tamanos=[],
            preferencia_energia="media",
        )
        db_session.add(home)

    for estado in ESTADOS:
        db_session.add(Match(user_id=user.id, pet_id=pet.id, shelter_id=shelter.id, estado=estado))

    db_session.commit()
    return shelter, pet, user


def test_obtener_perfil_calcula_metricas_de_los_5_estados(client, db_session):
    _shelter, _pet, user = _seed_usuario_con_matches(db_session, con_home_profile=True)

    respuesta = client.get(f"/api/users/{user.id}")

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    # matches_activos: todos menos "adoptado"/"cerrado" -> solicitado, en_revision, visita_agendada
    assert cuerpo["metricas"]["matches_activos"] == 3
    # visitas_agendadas: solo el estado "visita_agendada"
    assert cuerpo["metricas"]["visitas_agendadas"] == 1


def test_obtener_perfil_con_home_profile_refleja_datos_reales(client, db_session):
    _shelter, _pet, user = _seed_usuario_con_matches(db_session, con_home_profile=True)

    respuesta = client.get(f"/api/users/{user.id}")

    cuerpo = respuesta.json()
    assert cuerpo["home_profile"] is not None
    assert cuerpo["home_profile"]["vivienda"] == "casa"
    assert cuerpo["home_profile"]["tiene_ninos"] is True
    assert cuerpo["home_profile"]["horas_fuera_dia"] == 4


def test_obtener_perfil_sin_home_profile_devuelve_null_no_404(client, db_session):
    _shelter, _pet, user = _seed_usuario_con_matches(db_session, con_home_profile=False)

    respuesta = client.get(f"/api/users/{user.id}")

    assert respuesta.status_code == 200
    assert respuesta.json()["home_profile"] is None


def test_obtener_perfil_usuario_inexistente_devuelve_404(client, db_session):
    respuesta = client.get("/api/users/9999")

    assert respuesta.status_code == 404
    assert "9999" in respuesta.json()["detail"]


def test_obtener_perfil_apadrinamientos_siempre_cero(client, db_session):
    _shelter, _pet, user = _seed_usuario_con_matches(db_session, con_home_profile=True)

    respuesta = client.get(f"/api/users/{user.id}")

    assert respuesta.json()["metricas"]["apadrinamientos"] == 0
