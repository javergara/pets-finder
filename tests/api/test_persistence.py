from adopta_api.models.home_profile import HomeProfile
from adopta_api.models.match import Match
from adopta_api.models.pet import Pet
from adopta_api.models.shelter import Shelter
from adopta_api.models.swipe import Swipe
from adopta_api.models.user import User


def _make_pet(shelter_id: int, **overrides) -> Pet:
    base = dict(
        shelter_id=shelter_id,
        nombre="Firulais",
        especie="perro",
        raza="Criollo",
        sexo="macho",
        edad_meses=24,
        tamano="mediano",
        energia="media",
        historia="Un perro encantador.",
        apto_ninos=True,
        apto_perros=True,
        apto_gatos=True,
    )
    base.update(overrides)
    return Pet(**base)


def test_crea_y_lee_las_seis_entidades(db_session):
    shelter = Shelter(nombre="Refugio de prueba", ciudad="Bogotá")
    db_session.add(shelter)
    db_session.flush()

    pet = _make_pet(shelter.id)
    db_session.add(pet)

    user = User(nombre="Test User", email="test@example.co")
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
        preferencia_energia="media",
    )
    db_session.add(home)
    db_session.flush()

    swipe = Swipe(user_id=user.id, pet_id=pet.id, direccion="like")
    db_session.add(swipe)

    match = Match(user_id=user.id, pet_id=pet.id, shelter_id=shelter.id)
    db_session.add(match)
    db_session.commit()

    assert db_session.get(Shelter, shelter.id).nombre == "Refugio de prueba"
    assert db_session.get(Pet, pet.id).nombre == "Firulais"
    assert db_session.get(User, user.id).email == "test@example.co"
    assert db_session.get(HomeProfile, user.id).vivienda == "casa"
    assert db_session.get(Swipe, swipe.id).direccion == "like"
    assert db_session.get(Match, match.id).estado == "solicitado"
