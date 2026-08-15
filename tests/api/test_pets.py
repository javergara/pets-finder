"""Mascotas en adopción (AD-01): modelo `Pet` y schemas.

El router llega en los pasos 5-6 del plan; aquí solo se ejercitan el invariante
del CHECK a nivel de DB y las reglas del `model_validator` de `PetIn`.

⚠️ `Pet` se importa a nivel de módulo a propósito: el fixture `db_session` hace
`create_all` con lo que esté registrado en `Base.metadata` en ese instante, y un
import perezoso produce un `no such table: pets` intermitente según el orden de
colección de pytest.
"""

from datetime import datetime

import pytest
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from reencuentro_api.models.organizacion import Organizacion
from reencuentro_api.models.pet import Pet
from reencuentro_api.models.user import User
from reencuentro_api.schemas.pet import PetIn


@pytest.fixture()
def usuario(db_session):
    user = User(nombre="Ana", email="ana@example.co", ciudad="Armenia")
    db_session.add(user)
    db_session.commit()
    return user


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
