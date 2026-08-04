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


def test_obtener_perfil_apadrinamientos_es_cero_sin_sponsorships(client, db_session):
    """`apadrinamientos` es un count real de `Sponsorship.activo` (feature
    12-sponsorship): con cero apadrinamientos creados, el conteo real da 0 -- no es
    un valor fijo. Ver `test_sponsorships.py` para la regresión con datos reales."""
    _shelter, _pet, user = _seed_usuario_con_matches(db_session, con_home_profile=True)

    respuesta = client.get(f"/api/users/{user.id}")

    assert respuesta.json()["metricas"]["apadrinamientos"] == 0


def test_registrar_usuario_crea_sin_home_profile_y_metricas_en_cero(client, db_session):
    respuesta = client.post(
        "/api/users",
        json={
            "nombre": "Camila",
            "email": "camila@example.co",
            "ciudad": "Bogotá",
            "barrio": "Usaquén",
        },
    )

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["nombre"] == "Camila"
    assert cuerpo["email"] == "camila@example.co"
    assert cuerpo["home_profile"] is None
    assert cuerpo["metricas"] == {
        "matches_activos": 0,
        "visitas_agendadas": 0,
        "apadrinamientos": 0,
    }


def test_registrar_usuario_con_email_duplicado_devuelve_409_en_espanol(client, db_session):
    _shelter, _pet, user = _seed_usuario_con_matches(db_session, con_home_profile=False)

    respuesta = client.post(
        "/api/users",
        json={"nombre": "Otra Ana", "email": user.email},
    )

    assert respuesta.status_code == 409
    detalle = respuesta.json()["detail"]
    assert user.email in detalle
    assert "Ya existe una cuenta" in detalle


def test_registrar_usuario_es_recuperable_via_get(client, db_session):
    respuesta_creacion = client.post(
        "/api/users",
        json={"nombre": "Diego", "email": "diego@example.co", "barrio": "Chapinero"},
    )
    user_id = respuesta_creacion.json()["id"]

    respuesta_get = client.get(f"/api/users/{user_id}")

    assert respuesta_get.status_code == 200
    cuerpo = respuesta_get.json()
    assert cuerpo["nombre"] == "Diego"
    assert cuerpo["email"] == "diego@example.co"
    assert cuerpo["ciudad"] == "Bogotá"
    assert cuerpo["barrio"] == "Chapinero"
    assert cuerpo["home_profile"] is None


def _home_profile_payload(**overrides):
    payload = {
        "vivienda": "casa",
        "espacio_exterior": "patio",
        "personas_en_casa": 2,
        "tiene_ninos": True,
        "tiene_otros_perros": False,
        "tiene_otros_gatos": False,
        "horas_fuera_dia": 4,
        "experiencia_previa": "algo",
        "presupuesto_mensual_cop": 150_000,
        "preferencia_especies": [],
        "preferencia_tamanos": [],
        "preferencia_energia": "media",
    }
    payload.update(overrides)
    return payload


def test_guardar_home_profile_lo_crea_cuando_no_existe(client, db_session):
    _shelter, _pet, user = _seed_usuario_con_matches(db_session, con_home_profile=False)

    respuesta = client.put(f"/api/users/{user.id}/home-profile", json=_home_profile_payload())

    assert respuesta.status_code == 200
    assert respuesta.json()["vivienda"] == "casa"
    assert respuesta.json()["tiene_ninos"] is True

    respuesta_get = client.get(f"/api/users/{user.id}")
    assert respuesta_get.json()["home_profile"] is not None
    assert respuesta_get.json()["home_profile"]["horas_fuera_dia"] == 4


def test_guardar_home_profile_reemplaza_si_ya_existe(client, db_session):
    _shelter, _pet, user = _seed_usuario_con_matches(db_session, con_home_profile=True)

    respuesta = client.put(
        f"/api/users/{user.id}/home-profile",
        json=_home_profile_payload(tiene_ninos=False),
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["tiene_ninos"] is False

    respuesta_get = client.get(f"/api/users/{user.id}")
    assert respuesta_get.json()["home_profile"]["tiene_ninos"] is False

    # No debe crear una segunda fila: sigue habiendo un único HomeProfile para el usuario.
    homes = db_session.query(HomeProfile).filter(HomeProfile.user_id == user.id).all()
    assert len(homes) == 1


def test_guardar_home_profile_usuario_inexistente_devuelve_404(client, db_session):
    respuesta = client.put("/api/users/9999/home-profile", json=_home_profile_payload())

    assert respuesta.status_code == 404
    assert "9999" in respuesta.json()["detail"]


def test_guardar_home_profile_recalcula_afinidad_de_inmediato(client, db_session):
    """Regresión ADR 0003: sin HomeProfile, GET /api/pets da 404; tras el PUT, calcula
    afinidad al vuelo y refleja de inmediato un cambio de campo (tiene_ninos)."""
    shelter = Shelter(nombre="Refugio Afinidad", ciudad="Bogotá", tiempo_respuesta_horas=12)
    db_session.add(shelter)
    db_session.flush()

    pet = Pet(
        shelter_id=shelter.id,
        nombre="Toby",
        especie="perro",
        raza="Criollo",
        sexo="macho",
        edad_meses=24,
        tamano="mediano",
        energia="media",
        historia="Un perro encantador.",
        tags=[],
        fotos=["/media/pet_toby.jpg"],
        apto_ninos=False,
        apto_perros=True,
        apto_gatos=True,
    )
    db_session.add(pet)

    user = User(nombre="Laura", email="laura@example.co", ciudad="Bogotá")
    db_session.add(user)
    db_session.commit()

    # Sin HomeProfile: 404 en español, comportamiento existente que no se toca.
    respuesta_sin_home = client.get(f"/api/pets?user_id={user.id}")
    assert respuesta_sin_home.status_code == 404
    assert "HomeProfile" in respuesta_sin_home.json()["detail"]

    client.put(
        f"/api/users/{user.id}/home-profile",
        json=_home_profile_payload(tiene_ninos=True),
    )

    respuesta_con_ninos = client.get(f"/api/pets?user_id={user.id}&incluir_incompatibles=true")
    assert respuesta_con_ninos.status_code == 200
    toby_con_ninos = next(p for p in respuesta_con_ninos.json() if p["nombre"] == "Toby")
    assert toby_con_ninos["afinidad"]["incompatible"] is True
    assert toby_con_ninos["afinidad"]["score"] == 0

    client.put(
        f"/api/users/{user.id}/home-profile",
        json=_home_profile_payload(tiene_ninos=False),
    )

    respuesta_sin_ninos = client.get(f"/api/pets?user_id={user.id}")
    assert respuesta_sin_ninos.status_code == 200
    toby_sin_ninos = next(p for p in respuesta_sin_ninos.json() if p["nombre"] == "Toby")
    assert toby_sin_ninos["afinidad"]["incompatible"] is False
    assert toby_sin_ninos["afinidad"]["score"] > 0
