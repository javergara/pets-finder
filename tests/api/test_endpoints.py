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


def test_publicar_mascota_devuelve_201_con_campos_reflejados(client, db_session):
    shelter, _pet, _user = _seed_minimo(db_session)

    payload = {
        "shelter_id": shelter.id,
        "nombre": "Luna",
        "especie": "gato",
        "raza": "Siames",
        "sexo": "hembra",
        "edad_meses": 8,
        "tamano": "pequeño",
        "energia": "baja",
        "historia": "Una gata tranquila que ama dormir al sol.",
        "tags": ["tranquila", "cariñosa"],
        "esterilizado": True,
        "vacunas_al_dia": True,
        "microchip": True,
        "desparasitado": True,
        "apto_ninos": False,
        "apto_perros": False,
        "apto_gatos": True,
        "fotos": ["/media/luna_1.jpg"],
    }

    respuesta = client.post("/api/pets", json=payload)

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["shelter_id"] == shelter.id
    assert cuerpo["nombre"] == "Luna"
    assert cuerpo["especie"] == "gato"
    assert cuerpo["raza"] == "Siames"
    assert cuerpo["sexo"] == "hembra"
    assert cuerpo["edad_meses"] == 8
    assert cuerpo["tamano"] == "pequeño"
    assert cuerpo["energia"] == "baja"
    assert cuerpo["historia"] == payload["historia"]
    assert cuerpo["tags"] == ["tranquila", "cariñosa"]
    assert cuerpo["esterilizado"] is True
    assert cuerpo["vacunas_al_dia"] is True
    assert cuerpo["microchip"] is True
    assert cuerpo["desparasitado"] is True
    assert cuerpo["apto_ninos"] is False
    assert cuerpo["apto_perros"] is False
    assert cuerpo["apto_gatos"] is True
    assert cuerpo["fotos"] == ["/media/luna_1.jpg"]
    assert cuerpo["estado"] == "disponible"


def test_publicar_mascota_aplica_defaults_documentados(client, db_session):
    shelter, _pet, _user = _seed_minimo(db_session)

    payload = {
        "shelter_id": shelter.id,
        "nombre": "Max",
        "especie": "perro",
        "raza": "Criollo",
        "sexo": "macho",
        "edad_meses": 36,
        "tamano": "grande",
        "energia": "alta",
        "historia": "Un perro juguetón que necesita espacio.",
    }

    respuesta = client.post("/api/pets", json=payload)

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["tags"] == []
    assert cuerpo["fotos"] == []
    assert cuerpo["esterilizado"] is False
    assert cuerpo["vacunas_al_dia"] is False
    assert cuerpo["microchip"] is False
    assert cuerpo["desparasitado"] is False
    assert cuerpo["apto_ninos"] is True
    assert cuerpo["apto_perros"] is True
    assert cuerpo["apto_gatos"] is True
    assert cuerpo["estado"] == "disponible"


def test_publicar_mascota_shelter_inexistente_devuelve_404_y_no_inserta(client, db_session):
    _seed_minimo(db_session)

    payload = {
        "shelter_id": 9999,
        "nombre": "Rocky",
        "especie": "perro",
        "raza": "Criollo",
        "sexo": "macho",
        "edad_meses": 12,
        "tamano": "mediano",
        "energia": "media",
        "historia": "Un perro amistoso.",
    }

    respuesta = client.post("/api/pets", json=payload)

    assert respuesta.status_code == 404
    assert "9999" in respuesta.json()["detail"]

    mascotas = client.get("/api/pets").json()
    assert all(mascota["nombre"] != "Rocky" for mascota in mascotas)
