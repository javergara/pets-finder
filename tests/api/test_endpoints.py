from adopta_api.models.home_profile import HomeProfile
from adopta_api.models.pet import Pet
from adopta_api.models.shelter import Shelter
from adopta_api.models.user import User


def _seed_minimo(db_session):
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

    user = User(nombre="Ana", email="ana@example.co")
    db_session.add(user)
    db_session.flush()

    home = HomeProfile(
        user_id=user.id,
        vivienda="casa",
        espacio_exterior="patio",
        personas_en_casa=2,
        horas_fuera_dia=4,
        experiencia_previa="algo",
        presupuesto_mensual_cop=150_000,
        preferencia_especies=[],
        preferencia_tamanos=[],
        preferencia_energia="media",
    )
    db_session.add(home)
    db_session.commit()
    return shelter, pet, user


def test_listar_mascotas(client, db_session):
    _shelter, pet, user = _seed_minimo(db_session)

    respuesta = client.get(f"/api/pets?user_id={user.id}")

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert len(cuerpo) == 1
    assert cuerpo[0]["id"] == pet.id
    assert cuerpo[0]["afinidad"] is not None


def test_swipe_like_crea_match(client, db_session):
    _shelter, pet, user = _seed_minimo(db_session)

    respuesta = client.post(
        "/api/swipes", json={"user_id": user.id, "pet_id": pet.id, "direccion": "like"}
    )

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["match"] is not None
    assert cuerpo["match"]["estado"] == "solicitado"

    matches = client.get(f"/api/matches?user_id={user.id}").json()
    assert len(matches) == 1
    assert matches[0]["pet"]["id"] == pet.id


def test_swipe_pass_no_crea_match(client, db_session):
    _shelter, pet, user = _seed_minimo(db_session)

    respuesta = client.post(
        "/api/swipes", json={"user_id": user.id, "pet_id": pet.id, "direccion": "pass"}
    )

    assert respuesta.status_code == 201
    assert respuesta.json()["match"] is None

    matches = client.get(f"/api/matches?user_id={user.id}").json()
    assert len(matches) == 0


def test_mascota_excluida_tras_swipe(client, db_session):
    _shelter, pet, user = _seed_minimo(db_session)
    client.post("/api/swipes", json={"user_id": user.id, "pet_id": pet.id, "direccion": "pass"})

    respuesta = client.get(f"/api/pets?user_id={user.id}")

    assert respuesta.json() == []


def test_obtener_mascota_incluye_afinidad_y_refugio(client, db_session):
    shelter, pet, user = _seed_minimo(db_session)

    respuesta = client.get(f"/api/pets/{pet.id}?user_id={user.id}")

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["id"] == pet.id
    assert cuerpo["nombre"] == "Firulais"
    assert cuerpo["shelter"]["id"] == shelter.id
    assert cuerpo["afinidad"] is not None
    assert cuerpo["afinidad"]["score"] >= 0


def test_obtener_mascota_sin_user_id_no_calcula_afinidad(client, db_session):
    _shelter, pet, _user = _seed_minimo(db_session)

    respuesta = client.get(f"/api/pets/{pet.id}")

    assert respuesta.status_code == 200
    assert respuesta.json()["afinidad"] is None


def test_obtener_mascota_inexistente_devuelve_404(client, db_session):
    _seed_minimo(db_session)

    respuesta = client.get("/api/pets/9999")

    assert respuesta.status_code == 404
