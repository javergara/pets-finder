from sqlalchemy import func, select

from adopta_api.models.favorite import Favorite
from adopta_api.models.home_profile import HomeProfile
from adopta_api.models.match import Match
from adopta_api.models.pet import Pet
from adopta_api.models.shelter import Shelter
from adopta_api.models.swipe import Swipe
from adopta_api.models.user import User


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
        estado="disponible",
    )
    defaults.update(overrides)
    pet = Pet(**defaults)
    db_session.add(pet)
    db_session.commit()
    db_session.refresh(pet)
    return pet


def _crear_usuario(db_session, **overrides):
    defaults = dict(nombre="Ana", email="ana@example.co", ciudad="Bogotá")
    defaults.update(overrides)
    user = User(**defaults)
    db_session.add(user)
    db_session.flush()
    return user


def _crear_home_profile(db_session, user, **overrides):
    defaults = dict(
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
    defaults.update(overrides)
    home = HomeProfile(**defaults)
    db_session.add(home)
    db_session.commit()
    return home


# --- POST /api/users/{user_id}/favorites --------------------------------------


def test_marcar_favorito_nuevo_devuelve_201(client, db_session):
    shelter = _crear_shelter(db_session)
    pet = _crear_pet(db_session, shelter)
    user = _crear_usuario(db_session)

    respuesta = client.post(f"/api/users/{user.id}/favorites", json={"pet_id": pet.id})

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["id"] == pet.id
    assert cuerpo["es_favorito"] is True

    persistido = db_session.execute(
        select(Favorite).where(Favorite.user_id == user.id, Favorite.pet_id == pet.id)
    ).scalar_one_or_none()
    assert persistido is not None


def test_marcar_favorito_dos_veces_es_idempotente(client, db_session):
    shelter = _crear_shelter(db_session)
    pet = _crear_pet(db_session, shelter)
    user = _crear_usuario(db_session)

    primera = client.post(f"/api/users/{user.id}/favorites", json={"pet_id": pet.id})
    segunda = client.post(f"/api/users/{user.id}/favorites", json={"pet_id": pet.id})

    assert primera.status_code == 201
    assert segunda.status_code == 200

    total = db_session.execute(
        select(func.count())
        .select_from(Favorite)
        .where(Favorite.user_id == user.id, Favorite.pet_id == pet.id)
    ).scalar_one()
    assert total == 1


def test_marcar_favorito_usuario_inexistente_devuelve_404(client, db_session):
    shelter = _crear_shelter(db_session)
    pet = _crear_pet(db_session, shelter)

    respuesta = client.post("/api/users/9999/favorites", json={"pet_id": pet.id})

    assert respuesta.status_code == 404
    assert "9999" in respuesta.json()["detail"]


def test_marcar_favorito_mascota_inexistente_devuelve_404(client, db_session):
    user = _crear_usuario(db_session)

    respuesta = client.post(f"/api/users/{user.id}/favorites", json={"pet_id": 9999})

    assert respuesta.status_code == 404
    assert "9999" in respuesta.json()["detail"]


# --- DELETE /api/users/{user_id}/favorites/{pet_id} ---------------------------


def test_desmarcar_favorito_existente_devuelve_204_y_borra(client, db_session):
    shelter = _crear_shelter(db_session)
    pet = _crear_pet(db_session, shelter)
    user = _crear_usuario(db_session)
    client.post(f"/api/users/{user.id}/favorites", json={"pet_id": pet.id})

    respuesta = client.delete(f"/api/users/{user.id}/favorites/{pet.id}")

    assert respuesta.status_code == 204
    persistido = db_session.execute(
        select(Favorite).where(Favorite.user_id == user.id, Favorite.pet_id == pet.id)
    ).scalar_one_or_none()
    assert persistido is None


def test_desmarcar_favorito_inexistente_devuelve_204_igual(client, db_session):
    shelter = _crear_shelter(db_session)
    pet = _crear_pet(db_session, shelter)
    user = _crear_usuario(db_session)

    respuesta = client.delete(f"/api/users/{user.id}/favorites/{pet.id}")

    assert respuesta.status_code == 204


# --- GET /api/users/{user_id}/favorites ----------------------------------------


def test_listar_favoritos_devuelve_mascotas_con_es_favorito_true(client, db_session):
    shelter = _crear_shelter(db_session)
    pet1 = _crear_pet(db_session, shelter, nombre="Firulais")
    pet2 = _crear_pet(db_session, shelter, nombre="Michi")
    user = _crear_usuario(db_session)
    client.post(f"/api/users/{user.id}/favorites", json={"pet_id": pet1.id})
    client.post(f"/api/users/{user.id}/favorites", json={"pet_id": pet2.id})

    respuesta = client.get(f"/api/users/{user.id}/favorites")

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert len(cuerpo) == 2
    assert all(m["es_favorito"] is True for m in cuerpo)
    nombres = {m["nombre"] for m in cuerpo}
    assert nombres == {"Firulais", "Michi"}


def test_listar_favoritos_usuario_inexistente_devuelve_404(client, db_session):
    respuesta = client.get("/api/users/9999/favorites")

    assert respuesta.status_code == 404
    assert "9999" in respuesta.json()["detail"]


def test_listar_favoritos_sin_favoritos_devuelve_200_vacio(client, db_session):
    user = _crear_usuario(db_session)

    respuesta = client.get(f"/api/users/{user.id}/favorites")

    assert respuesta.status_code == 200
    assert respuesta.json() == []


def test_obtener_mascota_no_favoriteada_devuelve_es_favorito_false(client, db_session):
    shelter = _crear_shelter(db_session)
    pet = _crear_pet(db_session, shelter)
    user = _crear_usuario(db_session)
    _crear_home_profile(db_session, user)

    respuesta = client.get(f"/api/pets/{pet.id}?user_id={user.id}")

    assert respuesta.status_code == 200
    assert respuesta.json()["es_favorito"] is False


# --- Regresión crítica: favoritos es independiente de Swipe/Match -------------


def test_mascota_favoriteada_sigue_en_el_deck(client, db_session):
    shelter = _crear_shelter(db_session)
    pet = _crear_pet(db_session, shelter)
    user = _crear_usuario(db_session)
    _crear_home_profile(db_session, user)

    client.post(f"/api/users/{user.id}/favorites", json={"pet_id": pet.id})

    respuesta = client.get(f"/api/pets?user_id={user.id}")

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert len(cuerpo) == 1
    assert cuerpo[0]["id"] == pet.id
    assert cuerpo[0]["es_favorito"] is True


def test_marcar_favorito_no_crea_swipe_ni_match(client, db_session):
    shelter = _crear_shelter(db_session)
    pet = _crear_pet(db_session, shelter)
    user = _crear_usuario(db_session)

    client.post(f"/api/users/{user.id}/favorites", json={"pet_id": pet.id})

    total_swipes = db_session.execute(
        select(func.count())
        .select_from(Swipe)
        .where(Swipe.user_id == user.id, Swipe.pet_id == pet.id)
    ).scalar_one()
    total_matches = db_session.execute(
        select(func.count())
        .select_from(Match)
        .where(Match.user_id == user.id, Match.pet_id == pet.id)
    ).scalar_one()

    assert total_swipes == 0
    assert total_matches == 0
