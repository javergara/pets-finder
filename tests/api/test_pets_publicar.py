"""Publicar, editar y despublicar mascotas en adopción (AD-02).

`tests/api/test_pets.py` cubre el alta y las lecturas de AD-01; aquí vive lo que
escribe sobre una mascota ya publicada: `PUT /api/pets/{id}` (paso 1),
`DELETE /api/pets/{id}` (paso 2) y el puente con un reporte de "encontrada"
(paso 3).

⚠️ `Pet`, `Organizacion` y `User` se importan a nivel de módulo a propósito: el
fixture `db_session` hace `create_all` con lo que esté registrado en
`Base.metadata` en ese instante, y un import perezoso produce un `no such table:
pets` intermitente según el orden de colección de pytest.
"""

from datetime import datetime

import pytest

from reencuentro_api.models.organizacion import Organizacion
from reencuentro_api.models.pet import Pet
from reencuentro_api.models.user import User


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
        "publicado_en": datetime(2026, 8, 14, 9, 0),
    }
    campos.update(overrides)
    return Pet(**campos)


def _guardar(db_session, **overrides) -> Pet:
    pet = _pet(**overrides)
    db_session.add(pet)
    db_session.commit()
    return pet


# --- PUT /api/pets/{pet_id} (paso 1) -------------------------------------------


def test_editar_como_autor_de_la_organizacion_devuelve_200(
    client, db_session, organizacion, usuario
):
    pet = _guardar(db_session, organizacion_id=organizacion.id)

    respuesta = client.put(
        f"/api/pets/{pet.id}",
        json={"user_id": usuario.id, "nombre": "Canelita", "historia": "Ya está esterilizada."},
    )

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["nombre"] == "Canelita"
    assert cuerpo["publicador"]["tipo"] == "organizacion"

    # Contra la DB, no solo contra la respuesta: lo que importa es que quedó guardado.
    db_session.expire_all()
    guardada = db_session.get(Pet, pet.id)
    assert guardada.nombre == "Canelita"
    assert guardada.historia == "Ya está esterilizada."


def test_editar_como_rescatista_dueno_devuelve_200(client, db_session, otro_usuario):
    pet = _guardar(db_session, user_id=otro_usuario.id, telefono_contacto="3105558899")

    respuesta = client.put(
        f"/api/pets/{pet.id}",
        json={"user_id": otro_usuario.id, "energia": "alta", "esterilizado": True},
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["publicador"]["tipo"] == "rescatista"

    db_session.expire_all()
    guardada = db_session.get(Pet, pet.id)
    assert guardada.energia == "alta"
    assert guardada.esterilizado is True


def test_editar_mascota_de_organizacion_ajena_devuelve_403(
    client, db_session, organizacion, otro_usuario
):
    pet = _guardar(db_session, organizacion_id=organizacion.id)

    respuesta = client.put(
        f"/api/pets/{pet.id}", json={"user_id": otro_usuario.id, "nombre": "Robada"}
    )

    assert respuesta.status_code == 403
    assert respuesta.json()["detail"] == "Solo quien publicó la mascota puede editarla"

    db_session.expire_all()
    assert db_session.get(Pet, pet.id).nombre == "Canela"


def test_editar_mascota_de_rescatista_ajeno_devuelve_403(client, db_session, usuario, otro_usuario):
    pet = _guardar(db_session, user_id=otro_usuario.id, telefono_contacto="3105558899")

    respuesta = client.put(f"/api/pets/{pet.id}", json={"user_id": usuario.id, "nombre": "Robada"})

    assert respuesta.status_code == 403
    assert respuesta.json()["detail"] == "Solo quien publicó la mascota puede editarla"


def test_editar_mascota_de_organizacion_eliminada_devuelve_403(
    client, db_session, organizacion, usuario
):
    """Sin dueño no queda nadie autorizado: `_dueno_user_id` devuelve `None` y
    eso tiene que ser un 403 en español, nunca un 500 (la organización se puede
    eliminar —feature 32— y SQLite no fuerza las FK)."""
    pet = _guardar(db_session, organizacion_id=organizacion.id)
    db_session.delete(organizacion)
    db_session.commit()

    respuesta = client.put(
        f"/api/pets/{pet.id}", json={"user_id": usuario.id, "nombre": "Huérfana"}
    )

    assert respuesta.status_code == 403
    assert respuesta.json()["detail"] == "Solo quien publicó la mascota puede editarla"


def test_editar_mascota_inexistente_devuelve_404(client, db_session, usuario):
    respuesta = client.put("/api/pets/9999", json={"user_id": usuario.id, "nombre": "Fantasma"})

    assert respuesta.status_code == 404
    assert respuesta.json()["detail"] == "La mascota 9999 no existe"


def test_fotos_y_tags_se_reemplazan_como_lista_completa(client, db_session, organizacion, usuario):
    """La guarda contra la mutación in-place: `pet.fotos.append(...)` no se
    persiste (las columnas JSON no llevan `MutableList`), así que la lista tiene
    que reasignarse entera. Un re-fetch es lo único que lo detecta."""
    pet = _guardar(
        db_session,
        organizacion_id=organizacion.id,
        fotos=["/media/uploads/vieja1.jpg", "/media/uploads/vieja2.jpg"],
        tags=["tímida", "necesita experiencia"],
    )

    respuesta = client.put(
        f"/api/pets/{pet.id}",
        json={
            "user_id": usuario.id,
            "fotos": ["/media/uploads/nueva.jpg"],
            "tags": ["juguetona"],
        },
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["fotos"] == ["/media/uploads/nueva.jpg"]
    assert respuesta.json()["tags"] == ["juguetona"]

    db_session.expire_all()
    guardada = db_session.get(Pet, pet.id)
    assert guardada.fotos == ["/media/uploads/nueva.jpg"]
    assert guardada.tags == ["juguetona"]

    # Y sobrevive a una lectura nueva por HTTP, no solo al objeto en memoria.
    cuerpo = client.get(f"/api/pets/{pet.id}").json()
    assert cuerpo["fotos"] == ["/media/uploads/nueva.jpg"]
    assert cuerpo["tags"] == ["juguetona"]


def test_marcar_adoptada_pone_la_fecha_y_la_saca_del_catalogo(
    client, db_session, organizacion, usuario
):
    pet = _guardar(db_session, organizacion_id=organizacion.id)

    respuesta = client.put(
        f"/api/pets/{pet.id}", json={"user_id": usuario.id, "estado": "adoptado"}
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["estado"] == "adoptado"
    assert respuesta.json()["adoptado_en"] is not None

    db_session.expire_all()
    assert db_session.get(Pet, pet.id).adoptado_en is not None

    adopciones = client.get("/api/pets/adopciones").json()
    assert adopciones["total"] == 1
    assert [m["nombre"] for m in adopciones["recientes"]] == ["Canela"]
    assert [m["nombre"] for m in client.get("/api/pets").json()] == []


def test_volver_a_disponible_limpia_la_fecha_de_adopcion(client, db_session, organizacion, usuario):
    """Una adopción que no cuajó: la mascota vuelve al catálogo y deja de contar
    en la franja de esperanza. Si `adoptado_en` se quedara, el resumen mentiría."""
    pet = _guardar(
        db_session,
        organizacion_id=organizacion.id,
        estado="adoptado",
        adoptado_en=datetime(2026, 8, 14, 18, 0),
    )

    respuesta = client.put(
        f"/api/pets/{pet.id}", json={"user_id": usuario.id, "estado": "disponible"}
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["adoptado_en"] is None

    db_session.expire_all()
    assert db_session.get(Pet, pet.id).adoptado_en is None

    assert client.get("/api/pets/adopciones").json() == {"total": 0, "recientes": []}
    assert [m["nombre"] for m in client.get("/api/pets").json()] == ["Canela"]


def test_pasar_a_en_proceso_tambien_limpia_la_fecha(client, db_session, organizacion, usuario):
    pet = _guardar(
        db_session,
        organizacion_id=organizacion.id,
        estado="adoptado",
        adoptado_en=datetime(2026, 8, 14, 18, 0),
    )

    respuesta = client.put(
        f"/api/pets/{pet.id}", json={"user_id": usuario.id, "estado": "en_proceso"}
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["adoptado_en"] is None

    db_session.expire_all()
    assert db_session.get(Pet, pet.id).adoptado_en is None


def test_zona_y_publicador_del_body_no_cambian_nada(
    client, db_session, organizacion, usuario, otro_usuario
):
    """`PetUpdate` no declara `zona`, `ciudad_texto` ni el publicador a
    propósito: mudar una mascota de dueño o de zona cambiaría su encuadre en el
    mapa y en las coincidencias. Si llegan en el body, se ignoran."""
    pet = _guardar(db_session, organizacion_id=organizacion.id, ciudad_texto=None)

    respuesta = client.put(
        f"/api/pets/{pet.id}",
        json={
            "user_id": usuario.id,
            "nombre": "Canelita",
            "zona": "Bogotá",
            "ciudad_texto": "Chía",
            "organizacion_id": 9999,
            "rescatista_id": otro_usuario.id,
        },
    )

    assert respuesta.status_code == 200

    db_session.expire_all()
    guardada = db_session.get(Pet, pet.id)
    assert guardada.nombre == "Canelita"
    assert guardada.zona == "Armenia"
    assert guardada.ciudad_texto is None
    assert guardada.organizacion_id == organizacion.id
    assert guardada.user_id is None


def test_editar_con_estado_invalido_devuelve_422(client, db_session, organizacion, usuario):
    pet = _guardar(db_session, organizacion_id=organizacion.id)

    respuesta = client.put(
        f"/api/pets/{pet.id}", json={"user_id": usuario.id, "estado": "regalada"}
    )

    assert respuesta.status_code == 422

    db_session.expire_all()
    assert db_session.get(Pet, pet.id).estado == "disponible"
