"""Tests de integración de filtros de descubrimiento sobre GET /api/pets.

Complementa tests/api/test_filters_service.py (unitarios, sin DB) probando
que routers/pets.py conecta correctamente query params -> FiltrosDeck ->
aplicar_filtros, con lat/lng reales de User/Pet en la base de datos de test.
"""

from adopta_api.models.home_profile import HomeProfile
from adopta_api.models.pet import Pet
from adopta_api.models.shelter import Shelter
from adopta_api.models.user import User

# Coordenadas de barrios de Bogotá (mismas usadas en test_geo.py / test_filters_service.py).
USAQUEN = (4.6946, -74.0307)
CHAPINERO = (4.6486, -74.0629)  # ~6.24 km de Usaquén
KENNEDY = (4.6280, -74.1497)  # ~15.1 km de Usaquén


def _crear_shelter(db_session) -> Shelter:
    shelter = Shelter(nombre="Refugio Test", ciudad="Bogotá", tiempo_respuesta_horas=12)
    db_session.add(shelter)
    db_session.flush()
    return shelter


def _crear_usuario(db_session, lat: float | None = None, lng: float | None = None) -> User:
    user = User(nombre="Ana", email="ana@example.co", lat=lat, lng=lng)
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
    return user


def _crear_pet(db_session, shelter: Shelter, nombre: str, **overrides) -> Pet:
    base = dict(
        shelter_id=shelter.id,
        nombre=nombre,
        especie="perro",
        raza="Criolla",
        sexo="macho",
        edad_meses=24,
        tamano="mediano",
        energia="media",
        historia="Una mascota encantadora.",
        tags=[],
        fotos=["/media/pet.jpg"],
        apto_ninos=True,
        apto_perros=True,
        apto_gatos=True,
    )
    base.update(overrides)
    pet = Pet(**base)
    db_session.add(pet)
    db_session.commit()
    return pet


def test_filtro_especie(client, db_session):
    shelter = _crear_shelter(db_session)
    _perro = _crear_pet(db_session, shelter, "Firulais", especie="perro")
    gato = _crear_pet(db_session, shelter, "Michi", especie="gato")

    respuesta = client.get("/api/pets?especie=gato")

    assert respuesta.status_code == 200
    assert [p["id"] for p in respuesta.json()] == [gato.id]


def test_filtro_tamano(client, db_session):
    shelter = _crear_shelter(db_session)
    _pequeno = _crear_pet(db_session, shelter, "Chico", tamano="pequeño")
    grande = _crear_pet(db_session, shelter, "Grandote", tamano="grande")

    respuesta = client.get("/api/pets?tamano=grande")

    assert respuesta.status_code == 200
    assert [p["id"] for p in respuesta.json()] == [grande.id]


def test_filtro_energia(client, db_session):
    shelter = _crear_shelter(db_session)
    _tranquilo = _crear_pet(db_session, shelter, "Tranquilo", energia="baja")
    activo = _crear_pet(db_session, shelter, "Activo", energia="alta")

    respuesta = client.get("/api/pets?energia=alta")

    assert respuesta.status_code == 200
    assert [p["id"] for p in respuesta.json()] == [activo.id]


def test_filtro_edad_categoria(client, db_session):
    shelter = _crear_shelter(db_session)
    cachorro = _crear_pet(db_session, shelter, "Cachorro", edad_meses=5)
    _adulto = _crear_pet(db_session, shelter, "Adulto", edad_meses=48)

    respuesta = client.get("/api/pets?edad_categoria=cachorro")

    assert respuesta.status_code == 200
    assert [p["id"] for p in respuesta.json()] == [cachorro.id]


def test_filtro_apto_ninos(client, db_session):
    shelter = _crear_shelter(db_session)
    apto = _crear_pet(db_session, shelter, "AptoNinos", apto_ninos=True)
    _no_apto = _crear_pet(db_session, shelter, "NoAptoNinos", apto_ninos=False)

    respuesta = client.get("/api/pets?apto_ninos=true")

    assert respuesta.status_code == 200
    assert [p["id"] for p in respuesta.json()] == [apto.id]


def test_filtro_apto_perros(client, db_session):
    shelter = _crear_shelter(db_session)
    apto = _crear_pet(db_session, shelter, "AptoPerros", apto_perros=True)
    _no_apto = _crear_pet(db_session, shelter, "NoAptoPerros", apto_perros=False)

    respuesta = client.get("/api/pets?apto_perros=true")

    assert respuesta.status_code == 200
    assert [p["id"] for p in respuesta.json()] == [apto.id]


def test_filtro_apto_gatos(client, db_session):
    shelter = _crear_shelter(db_session)
    apto = _crear_pet(db_session, shelter, "AptoGatos", apto_gatos=True)
    _no_apto = _crear_pet(db_session, shelter, "NoAptoGatos", apto_gatos=False)

    respuesta = client.get("/api/pets?apto_gatos=true")

    assert respuesta.status_code == 200
    assert [p["id"] for p in respuesta.json()] == [apto.id]


def test_filtro_distancia_km_excluye_lo_lejano(client, db_session):
    shelter = _crear_shelter(db_session)
    usuario = _crear_usuario(db_session, lat=USAQUEN[0], lng=USAQUEN[1])
    cerca = _crear_pet(db_session, shelter, "Cerca", lat=CHAPINERO[0], lng=CHAPINERO[1])
    _lejos = _crear_pet(db_session, shelter, "Lejos", lat=KENNEDY[0], lng=KENNEDY[1])

    respuesta = client.get(f"/api/pets?user_id={usuario.id}&distancia_km=10")

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert [p["id"] for p in cuerpo] == [cerca.id]
    assert cuerpo[0]["distancia_km"] is not None


def test_combinacion_de_dos_filtros(client, db_session):
    shelter = _crear_shelter(db_session)
    coincide = _crear_pet(db_session, shelter, "Coincide", especie="perro", tamano="grande")
    _falla_especie = _crear_pet(
        db_session, shelter, "FallaEspecie", especie="gato", tamano="grande"
    )
    _falla_tamano = _crear_pet(
        db_session, shelter, "FallaTamano", especie="perro", tamano="pequeño"
    )

    respuesta = client.get("/api/pets?especie=perro&tamano=grande")

    assert respuesta.status_code == 200
    assert [p["id"] for p in respuesta.json()] == [coincide.id]


def test_default_distancia_15km_implicito(client, db_session):
    shelter = _crear_shelter(db_session)
    usuario = _crear_usuario(db_session, lat=USAQUEN[0], lng=USAQUEN[1])
    cerca = _crear_pet(db_session, shelter, "Cerca", lat=CHAPINERO[0], lng=CHAPINERO[1])
    _lejos = _crear_pet(db_session, shelter, "Lejos", lat=KENNEDY[0], lng=KENNEDY[1])  # ~15.1km

    # Sin enviar distancia_km explícito: debe comportarse como si fuera 15.0.
    respuesta = client.get(f"/api/pets?user_id={usuario.id}")

    assert respuesta.status_code == 200
    assert [p["id"] for p in respuesta.json()] == [cerca.id]


def test_distancia_no_excluye_cuando_falta_lat_lng_del_usuario(client, db_session):
    shelter = _crear_shelter(db_session)
    usuario = _crear_usuario(db_session, lat=None, lng=None)
    lejos = _crear_pet(db_session, shelter, "Lejos", lat=KENNEDY[0], lng=KENNEDY[1])

    respuesta = client.get(f"/api/pets?user_id={usuario.id}&distancia_km=1")

    assert respuesta.status_code == 200
    assert [p["id"] for p in respuesta.json()] == [lejos.id]


def test_distancia_no_excluye_cuando_falta_lat_lng_de_la_mascota(client, db_session):
    shelter = _crear_shelter(db_session)
    usuario = _crear_usuario(db_session, lat=USAQUEN[0], lng=USAQUEN[1])
    sin_coordenadas = _crear_pet(db_session, shelter, "SinCoordenadas", lat=None, lng=None)

    respuesta = client.get(f"/api/pets?user_id={usuario.id}&distancia_km=1")

    assert respuesta.status_code == 200
    assert [p["id"] for p in respuesta.json()] == [sin_coordenadas.id]
