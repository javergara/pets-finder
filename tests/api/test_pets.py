"""Mascotas en adopción (AD-01): modelo `Pet`, schemas y `POST /api/pets`.

Las lecturas (`GET`) llegan en el paso 6 del plan; aquí se ejercitan el
invariante del CHECK a nivel de DB, las reglas del `model_validator` de `PetIn`
y la publicación por HTTP.

⚠️ `Pet` se importa a nivel de módulo a propósito: el fixture `db_session` hace
`create_all` con lo que esté registrado en `Base.metadata` en ese instante, y un
import perezoso produce un `no such table: pets` intermitente según el orden de
colección de pytest.
"""

from datetime import date, datetime

import pytest
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from reencuentro_api.models.organizacion import Organizacion
from reencuentro_api.models.pet import Pet
from reencuentro_api.models.report import Report
from reencuentro_api.models.user import User
from reencuentro_api.routers import pets as router_pets
from reencuentro_api.schemas.pet import PetIn


@pytest.fixture()
def usuario(db_session):
    user = User(nombre="Ana", email="ana@example.co", ciudad="Armenia")
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture()
def otro_usuario(db_session):
    user = User(nombre="Carlos", email="carlos@example.co", ciudad="Pereira")
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture()
def reporte(db_session, usuario):
    """Un "encontrado" que nadie reclamó: el puente hacia adopción (AD-02)."""
    report = Report(
        user_id=usuario.id,
        tipo="encontrado",
        especie="perro",
        descripcion="Perra encontrada cerca del Parque Sucre, la tengo conmigo.",
        zona="Armenia",
        lat=4.535,
        lng=-75.68,
        situacion="conmigo",
        fecha_evento=date(2026, 8, 11),
        telefono_contacto="3001112233",
    )
    db_session.add(report)
    db_session.commit()
    return report


@pytest.fixture()
def organizacion(db_session, usuario):
    org = Organizacion(
        user_id=usuario.id,
        tipo="fundacion",
        nombre="Fundación Huellitas del Quindío",
        descripcion="Rescatamos mascotas afectadas por el sismo.",
        zona="Armenia",
        direccion="Cra 14 #10-25",
        lat=4.535,
        lng=-75.68,
        telefono_contacto="3001112233",
    )
    db_session.add(org)
    db_session.commit()
    return org


def _pet(**overrides) -> Pet:
    campos = {
        "nombre": "Canela",
        "especie": "perro",
        "sexo": "hembra",
        "edad_meses": 18,
        "tamano": "mediano",
        "energia": "media",
        "historia": "Rescatada en Armenia tras el sismo, busca hogar.",
        "zona": "Armenia",
    }
    campos.update(overrides)
    return Pet(**campos)


def _payload(**overrides) -> dict:
    payload = {
        "user_id": 1,
        "organizacion_id": 7,
        "nombre": "Canela",
        "especie": "perro",
        "sexo": "hembra",
        "tamano": "mediano",
        "energia": "media",
        "edad_meses": 18,
        "historia": "Rescatada en Armenia tras el sismo, busca hogar.",
        "zona": "Armenia",
    }
    payload.update(overrides)
    return payload


# --- Modelo: el CHECK de publicador exclusivo (invariante de DB) ---------------


def test_pet_con_organizacion_y_rescatista_viola_el_check(db_session, usuario, organizacion):
    db_session.add(_pet(organizacion_id=organizacion.id, user_id=usuario.id))

    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_pet_sin_organizacion_ni_rescatista_viola_el_check(db_session):
    db_session.add(_pet())

    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_pet_de_organizacion_se_guarda_con_los_defaults(db_session, organizacion):
    pet = _pet(organizacion_id=organizacion.id)
    db_session.add(pet)
    db_session.commit()

    assert pet.id is not None
    assert pet.user_id is None
    assert pet.report_id is None
    assert pet.estado == "disponible"
    assert pet.fotos == []
    assert pet.tags == []
    assert pet.esterilizado is False
    assert pet.apto_ninos is True
    assert isinstance(pet.publicado_en, datetime)
    assert pet.adoptado_en is None


def test_pet_de_rescatista_se_guarda_sin_organizacion(db_session, usuario):
    pet = _pet(user_id=usuario.id, telefono_contacto="3001112233")
    db_session.add(pet)
    db_session.commit()

    assert pet.organizacion_id is None
    assert pet.user_id == usuario.id
    assert pet.telefono_contacto == "3001112233"


# --- Schemas: el model_validator de PetIn --------------------------------------


def test_petin_con_organizacion_y_rescatista_es_invalido():
    with pytest.raises(ValidationError) as error:
        PetIn(**_payload(organizacion_id=7, rescatista_id=1))

    assert "exactamente uno" in str(error.value)


def test_petin_sin_organizacion_ni_rescatista_es_invalido():
    with pytest.raises(ValidationError) as error:
        PetIn(**_payload(organizacion_id=None))

    assert "exactamente uno" in str(error.value)


def test_petin_con_rescatista_ajeno_es_invalido():
    """`user_id` es quien hace el request; `rescatista_id`, el dueño declarado."""
    with pytest.raises(ValidationError) as error:
        PetIn(
            **_payload(
                organizacion_id=None,
                rescatista_id=2,
                user_id=1,
                telefono_contacto="3001112233",
            )
        )

    assert "a su propio nombre" in str(error.value)


def test_petin_de_rescatista_sin_telefono_es_invalido():
    with pytest.raises(ValidationError) as error:
        PetIn(**_payload(organizacion_id=None, rescatista_id=1, user_id=1))

    assert "teléfono de contacto" in str(error.value)


def test_petin_con_zona_desconocida_es_invalido():
    with pytest.raises(ValidationError) as error:
        PetIn(**_payload(zona="Palmira"))

    assert "Zona desconocida" in str(error.value)


def test_petin_con_zona_otro_sin_ciudad_texto_es_invalido():
    with pytest.raises(ValidationError) as error:
        PetIn(**_payload(zona="Otro"))

    assert "ciudad_texto" in str(error.value)


@pytest.mark.parametrize(
    ("campo", "valor"),
    [
        ("especie", "dragón"),
        ("sexo", "macha"),
        ("tamano", "gigante"),
        ("energia", "altísima"),
    ],
)
def test_petin_con_literal_invalido_es_invalido(campo, valor):
    with pytest.raises(ValidationError):
        PetIn(**_payload(**{campo: valor}))


def test_petin_de_organizacion_valida():
    pet = PetIn(**_payload())

    assert pet.organizacion_id == 7
    assert pet.rescatista_id is None
    assert pet.tags == []
    assert pet.fotos == []
    assert pet.apto_ninos is True


def test_petin_de_rescatista_valida():
    pet = PetIn(
        **_payload(
            organizacion_id=None,
            rescatista_id=1,
            user_id=1,
            telefono_contacto="3001112233",
            zona="Otro",
            ciudad_texto="Tuluá",
        )
    )

    assert pet.rescatista_id == 1
    assert pet.organizacion_id is None
    assert pet.ciudad_texto == "Tuluá"


# --- POST /api/pets (paso 5) ---------------------------------------------------


def test_publicar_mascota_de_organizacion_devuelve_201(client, usuario, organizacion):
    respuesta = client.post(
        "/api/pets",
        json=_payload(user_id=usuario.id, organizacion_id=organizacion.id),
    )

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["organizacion_id"] == organizacion.id
    assert cuerpo["user_id"] is None
    assert cuerpo["nombre"] == "Canela"
    assert cuerpo["estado"] == "disponible"
    assert cuerpo["fotos"] == []
    assert cuerpo["tags"] == []


def test_publicar_mascota_de_rescatista_guarda_el_dueno_en_user_id(client, usuario, db_session):
    """La trampa de la colisión: el dueño viaja como `rescatista_id` en el
    payload y tiene que quedar guardado en la columna `Pet.user_id`."""
    respuesta = client.post(
        "/api/pets",
        json=_payload(
            user_id=usuario.id,
            organizacion_id=None,
            rescatista_id=usuario.id,
            telefono_contacto="3001112233",
        ),
    )

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["user_id"] == usuario.id
    assert cuerpo["organizacion_id"] is None

    guardada = db_session.get(Pet, cuerpo["id"])
    assert guardada.user_id == usuario.id
    assert guardada.organizacion_id is None
    assert guardada.telefono_contacto == "3001112233"


def test_publicar_con_ambos_duenos_devuelve_422(client, usuario, organizacion):
    respuesta = client.post(
        "/api/pets",
        json=_payload(
            user_id=usuario.id,
            organizacion_id=organizacion.id,
            rescatista_id=usuario.id,
            telefono_contacto="3001112233",
        ),
    )

    assert respuesta.status_code == 422
    assert "exactamente uno" in str(respuesta.json())


def test_publicar_sin_dueno_devuelve_422(client, usuario):
    respuesta = client.post("/api/pets", json=_payload(user_id=usuario.id, organizacion_id=None))

    assert respuesta.status_code == 422
    assert "exactamente uno" in str(respuesta.json())


def test_publicar_a_nombre_de_otro_rescatista_devuelve_422(client, usuario, otro_usuario):
    respuesta = client.post(
        "/api/pets",
        json=_payload(
            user_id=usuario.id,
            organizacion_id=None,
            rescatista_id=otro_usuario.id,
            telefono_contacto="3001112233",
        ),
    )

    assert respuesta.status_code == 422
    assert "a su propio nombre" in str(respuesta.json())


def test_publicar_como_rescatista_sin_telefono_devuelve_422(client, usuario):
    respuesta = client.post(
        "/api/pets",
        json=_payload(user_id=usuario.id, organizacion_id=None, rescatista_id=usuario.id),
    )

    assert respuesta.status_code == 422
    assert "teléfono de contacto" in str(respuesta.json())


def test_publicar_en_organizacion_inexistente_devuelve_404(client, usuario):
    respuesta = client.post("/api/pets", json=_payload(user_id=usuario.id, organizacion_id=9999))

    assert respuesta.status_code == 404
    assert "9999" in respuesta.json()["detail"]


def test_publicar_con_rescatista_inexistente_devuelve_404(client, db_session):
    respuesta = client.post(
        "/api/pets",
        json=_payload(
            user_id=9999,
            organizacion_id=None,
            rescatista_id=9999,
            telefono_contacto="3001112233",
        ),
    )

    assert respuesta.status_code == 404
    assert "9999" in respuesta.json()["detail"]


def test_publicar_en_organizacion_ajena_devuelve_403(client, organizacion, otro_usuario):
    respuesta = client.post(
        "/api/pets",
        json=_payload(user_id=otro_usuario.id, organizacion_id=organizacion.id),
    )

    assert respuesta.status_code == 403
    assert respuesta.json()["detail"] == (
        "Solo quien registró la organización puede publicar mascotas en adopción"
    )


def test_publicar_con_reporte_inexistente_devuelve_404(client, usuario, organizacion):
    respuesta = client.post(
        "/api/pets",
        json=_payload(user_id=usuario.id, organizacion_id=organizacion.id, report_id=9999),
    )

    assert respuesta.status_code == 404
    assert "9999" in respuesta.json()["detail"]


def test_publicar_dos_veces_el_mismo_reporte_devuelve_409(client, usuario, organizacion, reporte):
    cuerpo = _payload(user_id=usuario.id, organizacion_id=organizacion.id, report_id=reporte.id)

    primera = client.post("/api/pets", json=cuerpo)
    segunda = client.post("/api/pets", json=cuerpo)

    assert primera.status_code == 201
    assert primera.json()["report_id"] == reporte.id
    assert segunda.status_code == 409
    assert segunda.json()["detail"] == "Este reporte ya tiene una mascota publicada en adopción"


def test_carrera_por_el_mismo_reporte_devuelve_409(
    client, usuario, organizacion, reporte, monkeypatch
):
    """El select previo ciego (como en una carrera real entre dos requests): el
    índice único de `report_id` es quien rechaza el insert, y sin atrapar el
    `IntegrityError` eso sería un 500 con traza en vez de un 409 de producto."""
    cuerpo = _payload(user_id=usuario.id, organizacion_id=organizacion.id, report_id=reporte.id)
    assert client.post("/api/pets", json=cuerpo).status_code == 201

    consulta_real = router_pets._mascota_del_reporte
    llamadas = []

    def _ciego_la_primera_vez(session, report_id):
        llamadas.append(report_id)
        return None if len(llamadas) == 1 else consulta_real(session, report_id)

    monkeypatch.setattr(router_pets, "_mascota_del_reporte", _ciego_la_primera_vez)

    respuesta = client.post("/api/pets", json=cuerpo)

    assert respuesta.status_code == 409
    assert respuesta.json()["detail"] == "Este reporte ya tiene una mascota publicada en adopción"
    # El select previo Y el de después del rollback: la segunda consulta es la
    # que convierte el error de DB en el mensaje de producto.
    assert len(llamadas) == 2


@pytest.mark.parametrize(
    ("campo", "valor"),
    [
        ("especie", "dragón"),
        ("sexo", "macha"),
        ("tamano", "gigante"),
        ("energia", "altísima"),
    ],
)
def test_publicar_con_literal_invalido_devuelve_422(client, usuario, organizacion, campo, valor):
    respuesta = client.post(
        "/api/pets",
        json=_payload(user_id=usuario.id, organizacion_id=organizacion.id, **{campo: valor}),
    )

    assert respuesta.status_code == 422


def test_publicar_con_zona_desconocida_devuelve_422(client, usuario, organizacion):
    respuesta = client.post(
        "/api/pets",
        json=_payload(user_id=usuario.id, organizacion_id=organizacion.id, zona="Palmira"),
    )

    assert respuesta.status_code == 422
    assert "Zona desconocida" in str(respuesta.json())


def test_publicar_con_zona_otro_sin_ciudad_texto_devuelve_422(client, usuario, organizacion):
    respuesta = client.post(
        "/api/pets",
        json=_payload(user_id=usuario.id, organizacion_id=organizacion.id, zona="Otro"),
    )

    assert respuesta.status_code == 422
    assert "ciudad_texto" in str(respuesta.json())


# --- Helper de autoría, que reusan las lecturas (paso 6) y AD-02 ---------------


def test_dueno_de_mascota_de_organizacion_es_quien_la_registro(db_session, usuario, organizacion):
    pet = _pet(organizacion_id=organizacion.id)
    db_session.add(pet)
    db_session.commit()

    assert router_pets._dueno_user_id(db_session, pet) == usuario.id


def test_dueno_de_mascota_de_rescatista_es_el_rescatista(db_session, usuario):
    pet = _pet(user_id=usuario.id, telefono_contacto="3001112233")
    db_session.add(pet)
    db_session.commit()

    assert router_pets._dueno_user_id(db_session, pet) == usuario.id


def test_dueno_de_mascota_con_organizacion_borrada_es_nadie(db_session, organizacion):
    """Si la organización se elimina (feature 32), la mascota queda sin nadie
    que pueda gestionarla — mejor eso que un 500 o un 403 que autorice de más."""
    pet = _pet(organizacion_id=organizacion.id)
    db_session.add(pet)
    db_session.commit()
    db_session.delete(organizacion)
    db_session.commit()

    assert router_pets._dueno_user_id(db_session, pet) is None
