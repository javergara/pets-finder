import pytest

from adopta_api.models.pet import Pet
from adopta_api.models.shelter import Shelter
from adopta_api.models.sponsorship import Sponsorship
from adopta_api.models.user import User
from adopta_api.routers.sponsorships import META_MENSUAL_COP


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
    # commit (no solo flush): expira los atributos en memoria y fuerza releerlos de
    # SQLite en la siguiente consulta, que los devuelve naive -- mismo criterio que
    # `es_dificil_de_ubicar`/`routers/shelters.py` esperan (ver su comentario sobre
    # datetimes naive al leer de SQLite).
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


def _crear_sponsorship(db_session, user, pet, **overrides):
    defaults = dict(user_id=user.id, pet_id=pet.id, monto_cop=50_000, periodicidad="mensual")
    defaults.update(overrides)
    sponsorship = Sponsorship(**defaults)
    db_session.add(sponsorship)
    db_session.commit()
    db_session.refresh(sponsorship)
    return sponsorship


# --- GET /api/pets/necesitan-apoyo -------------------------------------------


def test_necesita_apoyo_filtra_por_es_dificil_de_ubicar(client, db_session):
    shelter = _crear_shelter(db_session)
    senior = _crear_pet(db_session, shelter, nombre="Viejo Sabio", edad_meses=90)
    con_tag = _crear_pet(
        db_session, shelter, nombre="Necesita Cariño", tags=["necesita experiencia"]
    )
    normal = _crear_pet(db_session, shelter, nombre="Cachorro Normal", edad_meses=12)

    respuesta = client.get("/api/pets/necesitan-apoyo")

    assert respuesta.status_code == 200
    nombres = {m["nombre"] for m in respuesta.json()}
    assert senior.nombre in nombres
    assert con_tag.nombre in nombres
    assert normal.nombre not in nombres


def test_necesita_apoyo_lista_vacia_sin_calificar_no_es_404(client, db_session):
    shelter = _crear_shelter(db_session)
    _crear_pet(db_session, shelter, nombre="Cachorro Normal", edad_meses=12)

    respuesta = client.get("/api/pets/necesitan-apoyo")

    assert respuesta.status_code == 200
    assert respuesta.json() == []


def test_necesita_apoyo_excluye_no_disponibles(client, db_session):
    shelter = _crear_shelter(db_session)
    _crear_pet(db_session, shelter, nombre="Senior Adoptado", edad_meses=90, estado="adoptado")

    respuesta = client.get("/api/pets/necesitan-apoyo")

    assert respuesta.status_code == 200
    assert respuesta.json() == []


def test_necesita_apoyo_porcentaje_cubierto_con_cero_apadrinamientos(client, db_session):
    shelter = _crear_shelter(db_session)
    _crear_pet(db_session, shelter, nombre="Viejo Sabio", edad_meses=90)

    respuesta = client.get("/api/pets/necesitan-apoyo")

    cuerpo = respuesta.json()
    assert len(cuerpo) == 1
    assert cuerpo[0]["monto_recaudado_cop"] == 0
    assert cuerpo[0]["porcentaje_cubierto"] == 0


def test_necesita_apoyo_porcentaje_cubierto_con_un_apadrinamiento(client, db_session):
    shelter = _crear_shelter(db_session)
    pet = _crear_pet(db_session, shelter, nombre="Viejo Sabio", edad_meses=90)
    user = _crear_usuario(db_session)
    _crear_sponsorship(db_session, user, pet, monto_cop=round(META_MENSUAL_COP / 2))

    respuesta = client.get("/api/pets/necesitan-apoyo")

    cuerpo = respuesta.json()
    assert cuerpo[0]["monto_recaudado_cop"] == round(META_MENSUAL_COP / 2)
    assert cuerpo[0]["porcentaje_cubierto"] == 50


def test_necesita_apoyo_porcentaje_cubierto_tope_100(client, db_session):
    shelter = _crear_shelter(db_session)
    pet = _crear_pet(db_session, shelter, nombre="Viejo Sabio", edad_meses=90)
    user = _crear_usuario(db_session)
    _crear_sponsorship(db_session, user, pet, monto_cop=META_MENSUAL_COP)
    _crear_sponsorship(db_session, user, pet, monto_cop=META_MENSUAL_COP)

    respuesta = client.get("/api/pets/necesitan-apoyo")

    cuerpo = respuesta.json()
    assert cuerpo[0]["monto_recaudado_cop"] == META_MENSUAL_COP * 2
    assert cuerpo[0]["porcentaje_cubierto"] == 100


def test_necesita_apoyo_ignora_sponsorship_inactivo(client, db_session):
    shelter = _crear_shelter(db_session)
    pet = _crear_pet(db_session, shelter, nombre="Viejo Sabio", edad_meses=90)
    user = _crear_usuario(db_session)
    _crear_sponsorship(db_session, user, pet, monto_cop=META_MENSUAL_COP, activo=False)

    respuesta = client.get("/api/pets/necesitan-apoyo")

    cuerpo = respuesta.json()
    assert cuerpo[0]["monto_recaudado_cop"] == 0
    assert cuerpo[0]["porcentaje_cubierto"] == 0


# --- POST /api/sponsorships ---------------------------------------------------


def test_crear_apadrinamiento_exitoso(client, db_session):
    shelter = _crear_shelter(db_session)
    pet = _crear_pet(db_session, shelter)
    user = _crear_usuario(db_session)

    respuesta = client.post(
        "/api/sponsorships",
        json={
            "user_id": user.id,
            "pet_id": pet.id,
            "monto_cop": 70_000,
            "periodicidad": "mensual",
        },
    )

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["monto_cop"] == 70_000
    assert cuerpo["periodicidad"] == "mensual"
    assert cuerpo["activo"] is True
    assert cuerpo["pet"]["nombre"] == pet.nombre

    persistido = db_session.get(Sponsorship, cuerpo["id"])
    assert persistido is not None
    assert persistido.activo is True
    assert persistido.monto_cop == 70_000


def test_crear_apadrinamiento_usuario_inexistente_devuelve_404(client, db_session):
    shelter = _crear_shelter(db_session)
    pet = _crear_pet(db_session, shelter)

    respuesta = client.post(
        "/api/sponsorships",
        json={"user_id": 9999, "pet_id": pet.id, "monto_cop": 30_000, "periodicidad": "unico"},
    )

    assert respuesta.status_code == 404
    assert "9999" in respuesta.json()["detail"]


def test_crear_apadrinamiento_mascota_inexistente_devuelve_404(client, db_session):
    user = _crear_usuario(db_session)

    respuesta = client.post(
        "/api/sponsorships",
        json={"user_id": user.id, "pet_id": 9999, "monto_cop": 30_000, "periodicidad": "unico"},
    )

    assert respuesta.status_code == 404
    assert "9999" in respuesta.json()["detail"]


@pytest.mark.parametrize("monto_cop", [0, -1, -100])
def test_crear_apadrinamiento_monto_no_positivo_devuelve_422(client, db_session, monto_cop):
    shelter = _crear_shelter(db_session)
    pet = _crear_pet(db_session, shelter)
    user = _crear_usuario(db_session)

    respuesta = client.post(
        "/api/sponsorships",
        json={
            "user_id": user.id,
            "pet_id": pet.id,
            "monto_cop": monto_cop,
            "periodicidad": "mensual",
        },
    )

    assert respuesta.status_code == 422


def test_crear_apadrinamiento_periodicidad_invalida_devuelve_422(client, db_session):
    shelter = _crear_shelter(db_session)
    pet = _crear_pet(db_session, shelter)
    user = _crear_usuario(db_session)

    respuesta = client.post(
        "/api/sponsorships",
        json={
            "user_id": user.id,
            "pet_id": pet.id,
            "monto_cop": 30_000,
            "periodicidad": "semanal",
        },
    )

    assert respuesta.status_code == 422


# --- GET /api/users/{user_id}/sponsorships ------------------------------------


def test_listar_apadrinamientos_usuario_incluye_activos_e_inactivos(client, db_session):
    shelter = _crear_shelter(db_session)
    pet = _crear_pet(db_session, shelter)
    user = _crear_usuario(db_session)
    _crear_sponsorship(db_session, user, pet, monto_cop=30_000, activo=True)
    _crear_sponsorship(db_session, user, pet, monto_cop=50_000, activo=False)

    respuesta = client.get(f"/api/users/{user.id}/sponsorships")

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert len(cuerpo) == 2


def test_listar_apadrinamientos_novedad_solo_si_activo(client, db_session):
    shelter = _crear_shelter(db_session)
    pet = _crear_pet(db_session, shelter)
    user = _crear_usuario(db_session)
    _crear_sponsorship(db_session, user, pet, monto_cop=30_000, activo=True)
    _crear_sponsorship(db_session, user, pet, monto_cop=50_000, activo=False)

    respuesta = client.get(f"/api/users/{user.id}/sponsorships")

    cuerpo = respuesta.json()
    activo = next(s for s in cuerpo if s["activo"])
    inactivo = next(s for s in cuerpo if not s["activo"])
    assert activo["novedad"] is not None
    assert pet.nombre in activo["novedad"]
    assert inactivo["novedad"] is None


def test_listar_apadrinamientos_usuario_inexistente_devuelve_404(client, db_session):
    respuesta = client.get("/api/users/9999/sponsorships")

    assert respuesta.status_code == 404
    assert "9999" in respuesta.json()["detail"]


# --- Regresión explícita: features 07/09 dejan de estar fijas en 0 -----------


def test_apadrinamiento_activo_refleja_en_metricas_usuario(client, db_session):
    shelter = _crear_shelter(db_session)
    pet = _crear_pet(db_session, shelter)
    user = _crear_usuario(db_session)
    _crear_sponsorship(db_session, user, pet, monto_cop=30_000, activo=True)

    respuesta = client.get(f"/api/users/{user.id}")

    assert respuesta.status_code == 200
    assert respuesta.json()["metricas"]["apadrinamientos"] >= 1


def test_apadrinamiento_activo_refleja_en_metricas_refugio(client, db_session):
    shelter = _crear_shelter(db_session)
    pet = _crear_pet(db_session, shelter)
    user = _crear_usuario(db_session)
    _crear_sponsorship(db_session, user, pet, monto_cop=30_000, activo=True)
    _crear_sponsorship(db_session, user, pet, monto_cop=999_999, activo=False)

    respuesta = client.get(f"/api/shelters/{shelter.id}")

    assert respuesta.status_code == 200
    assert respuesta.json()["metricas"]["apadrinamientos_recaudados_cop"] == 30_000
