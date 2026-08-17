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

from datetime import date, datetime

import pytest

from reencuentro_api.models.organizacion import Organizacion
from reencuentro_api.models.pet import Pet
from reencuentro_api.models.report import Report
from reencuentro_api.models.user import User
from reencuentro_api.routers import pets as pets_router
from reencuentro_api.routers import reports as reports_router


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


@pytest.fixture()
def reporte(db_session, usuario):
    """Un "encontrado" que el autor tiene consigo: el puente hacia adopción.

    Trae foto propia porque el caso delicado del `DELETE` es justo ese: si la
    mascota nació de este reporte, sus fotos **son** las del reporte, que sigue
    vivo en la app.
    """
    report = Report(
        user_id=usuario.id,
        tipo="encontrado",
        especie="perro",
        descripcion="Perra encontrada cerca del Parque Sucre, la tengo conmigo.",
        foto_url="/media/uploads/reporte-principal.jpg",
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


# --- DELETE /api/pets/{pet_id} (paso 2) ----------------------------------------
#
# ⚠️ Lo que pasa cuando la mascota YA tiene swipes, favoritos o solicitudes vive
# en `tests/api/test_despublicar_rastros.py`, no aquí: esos casos necesitan una
# base con `PRAGMA foreign_keys=ON` y el `db_session` de este archivo —el del
# conftest— no fuerza las FK. Con FK encendidas, varios tests de abajo caerían a
# propósito (`..._de_organizacion_eliminada_devuelve_403` borra una organización
# con una mascota colgando).


@pytest.fixture()
def fotos_borradas(monkeypatch):
    """Lista-espía sobre `borrar_foto`, con las URLs en el orden en que se pidió
    borrarlas (patrón de `tests/api/test_borrado_fotos.py`).

    Sin espía estos tests no valdrían nada: `borrar_foto` **nunca lanza** (es
    tolerante a fallos por diseño, feature 20), así que un 204 sale igual de
    limpio borrando las fotos que no debía. Se parchea el nombre importado en el
    router —que es al que llega la llamada—, no el de `reencuentro_api.media`.
    """
    llamadas: list[str] = []
    monkeypatch.setattr(pets_router, "borrar_foto", llamadas.append)
    return llamadas


def _payload_publicar(**overrides) -> dict:
    payload = {
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


def test_despublicar_como_autor_de_la_organizacion_devuelve_204(
    client, db_session, organizacion, usuario
):
    pet = _guardar(db_session, organizacion_id=organizacion.id)

    respuesta = client.delete(f"/api/pets/{pet.id}?user_id={usuario.id}")

    assert respuesta.status_code == 204
    assert client.get(f"/api/pets/{pet.id}").status_code == 404
    assert client.get("/api/pets").json() == []

    db_session.expire_all()
    assert db_session.get(Pet, pet.id) is None


def test_despublicar_como_rescatista_dueno_devuelve_204(client, db_session, otro_usuario):
    pet = _guardar(db_session, user_id=otro_usuario.id, telefono_contacto="3105558899")

    respuesta = client.delete(f"/api/pets/{pet.id}?user_id={otro_usuario.id}")

    assert respuesta.status_code == 204

    db_session.expire_all()
    assert db_session.get(Pet, pet.id) is None


def test_despublicar_mascota_ajena_devuelve_403_y_no_borra_nada(
    client, db_session, organizacion, otro_usuario, fotos_borradas
):
    pet = _guardar(db_session, organizacion_id=organizacion.id, fotos=["/media/uploads/canela.jpg"])

    respuesta = client.delete(f"/api/pets/{pet.id}?user_id={otro_usuario.id}")

    assert respuesta.status_code == 403
    assert respuesta.json()["detail"] == "Solo quien publicó la mascota puede despublicarla"
    # Ni la fila ni las fotos: el 403 tiene que cortar antes de tocar el bucket.
    assert fotos_borradas == []

    db_session.expire_all()
    assert db_session.get(Pet, pet.id) is not None


def test_despublicar_mascota_de_rescatista_ajeno_devuelve_403(
    client, db_session, usuario, otro_usuario
):
    pet = _guardar(db_session, user_id=otro_usuario.id, telefono_contacto="3105558899")

    respuesta = client.delete(f"/api/pets/{pet.id}?user_id={usuario.id}")

    assert respuesta.status_code == 403

    db_session.expire_all()
    assert db_session.get(Pet, pet.id) is not None


def test_despublicar_mascota_de_organizacion_eliminada_devuelve_403(
    client, db_session, organizacion, usuario
):
    """Mismo criterio que el `PUT`: `_dueno_user_id` devuelve `None` cuando la
    organización ya no existe (se puede eliminar, feature 32) y entonces no queda
    nadie autorizado — 403 en español, jamás un 500."""
    pet = _guardar(db_session, organizacion_id=organizacion.id)
    db_session.delete(organizacion)
    db_session.commit()

    respuesta = client.delete(f"/api/pets/{pet.id}?user_id={usuario.id}")

    assert respuesta.status_code == 403
    assert respuesta.json()["detail"] == "Solo quien publicó la mascota puede despublicarla"


def test_despublicar_mascota_inexistente_devuelve_404(client, db_session, usuario):
    respuesta = client.delete(f"/api/pets/9999?user_id={usuario.id}")

    assert respuesta.status_code == 404
    assert respuesta.json()["detail"] == "La mascota 9999 no existe"


def test_despublicar_borra_una_vez_cada_foto_propia(
    client, db_session, organizacion, usuario, fotos_borradas
):
    """Mascota publicada desde cero (`report_id is None`): sus fotos son suyas y
    no las usa nadie más, así que se van con ella."""
    fotos = [
        "/media/uploads/canela-1.jpg",
        "https://abc123.supabase.co/storage/v1/object/public/fotos/canela-2.jpg",
        "/media/uploads/canela-3.jpg",
    ]
    pet = _guardar(db_session, organizacion_id=organizacion.id, fotos=fotos)

    respuesta = client.delete(f"/api/pets/{pet.id}?user_id={usuario.id}")

    assert respuesta.status_code == 204
    assert fotos_borradas == fotos


def test_despublicar_mascota_que_vino_de_un_reporte_no_borra_sus_fotos(
    client, db_session, usuario, reporte, fotos_borradas
):
    """El punto delicado del paso: esas fotos son **del reporte**, que sigue vivo.

    Borrarlas dejaría el reporte con imágenes rotas en producción. Y como
    `borrar_foto` no lanza, el 204 saldría igual de verde: la única forma de
    detectarlo es contar las llamadas.
    """
    pet = _guardar(
        db_session,
        user_id=usuario.id,
        telefono_contacto="3001112233",
        report_id=reporte.id,
        fotos=[reporte.foto_url],
    )

    respuesta = client.delete(f"/api/pets/{pet.id}?user_id={usuario.id}")

    assert respuesta.status_code == 204
    assert fotos_borradas == []

    # La mascota se fue; el reporte y su foto siguen enteros.
    assert client.get(f"/api/pets/{pet.id}").status_code == 404
    cuerpo = client.get(f"/api/reports/{reporte.id}").json()
    assert cuerpo["foto_url"] == "/media/uploads/reporte-principal.jpg"
    assert cuerpo["fotos"] == ["/media/uploads/reporte-principal.jpg"]


def test_tras_despublicar_el_mismo_reporte_se_puede_volver_a_publicar(
    client, db_session, usuario, reporte
):
    """El `unique` de `report_id` se libera al borrar la fila: quien se arrepiente
    de despublicar puede volver a dar en adopción el mismo encontrado (201, no el
    409 de "este reporte ya tiene una mascota publicada")."""
    primera = client.post(
        "/api/pets",
        json=_payload_publicar(
            user_id=usuario.id,
            rescatista_id=usuario.id,
            telefono_contacto="3001112233",
            report_id=reporte.id,
        ),
    )
    assert primera.status_code == 201

    assert (
        client.delete(f"/api/pets/{primera.json()['id']}?user_id={usuario.id}").status_code == 204
    )

    segunda = client.post(
        "/api/pets",
        json=_payload_publicar(
            user_id=usuario.id,
            rescatista_id=usuario.id,
            telefono_contacto="3001112233",
            report_id=reporte.id,
        ),
    )

    assert segunda.status_code == 201
    assert segunda.json()["report_id"] == reporte.id


# --- El puente reporte encontrado ↔ adopción (paso 3) --------------------------

MENSAJE_NO_ES_ENCONTRADA_CONMIGO = (
    "Solo se puede dar en adopción una mascota encontrada que tengas contigo"
)
MENSAJE_NO_ES_TU_REPORTE = "Solo quien publicó el reporte puede darla en adopción"
MENSAJE_REPORTE_CON_MASCOTA = (
    "Este reporte tiene una mascota publicada en adopción: despublícala primero"
)


@pytest.fixture()
def reporte_perdido(db_session, usuario):
    report = Report(
        user_id=usuario.id,
        tipo="perdido",
        especie="perro",
        nombre_mascota="Rocky",
        descripcion="Se perdió cerca del Parque Sucre.",
        zona="Armenia",
        lat=4.535,
        lng=-75.68,
        fecha_evento=date(2026, 8, 11),
        telefono_contacto="3001112233",
    )
    db_session.add(report)
    db_session.commit()
    return report


@pytest.fixture()
def reporte_vista(db_session, usuario):
    """Un "encontrado" que quien reportó **no** tiene consigo: la vio y no pudo
    atraparla. No hay nada que dar en adopción — la mascota anda suelta."""
    report = Report(
        user_id=usuario.id,
        tipo="encontrado",
        especie="gato",
        descripcion="Gato atigrado rondando el barrio, no me dejó acercarme.",
        zona="Armenia",
        lat=4.535,
        lng=-75.68,
        situacion="vista",
        fecha_evento=date(2026, 8, 11),
        telefono_contacto="3001112233",
    )
    db_session.add(report)
    db_session.commit()
    return report


@pytest.fixture()
def fotos_borradas_del_reporte(monkeypatch):
    """El mismo espía del `DELETE` de mascotas, pero sobre `routers/reports.py`.

    Aquí es lo único que puede detectar el bug del orden: si el 409 se
    comprobara **después** de `borrar_foto`, el endpoint respondería igual de
    "correcto" con 409 habiéndose llevado ya las fotos del usuario del bucket, y
    sin borrar el reporte. `borrar_foto` no lanza, así que el status no delata
    nada.
    """
    llamadas: list[str | None] = []
    monkeypatch.setattr(reports_router, "borrar_foto", llamadas.append)
    return llamadas


def _publicar_desde(client, usuario, reporte):
    return client.post(
        "/api/pets",
        json=_payload_publicar(
            user_id=usuario.id,
            rescatista_id=usuario.id,
            telefono_contacto="3001112233",
            report_id=reporte.id,
        ),
    )


def test_publicar_desde_un_encontrado_propio_enlaza_el_reporte(
    client, db_session, usuario, reporte
):
    respuesta = _publicar_desde(client, usuario, reporte)

    assert respuesta.status_code == 201
    assert respuesta.json()["report_id"] == reporte.id

    db_session.expire_all()
    guardada = db_session.get(Pet, respuesta.json()["id"])
    assert guardada.report_id == reporte.id


def test_publicar_desde_un_reporte_perdido_devuelve_422(
    client, db_session, usuario, reporte_perdido
):
    """Una mascota perdida es de alguien que la está buscando: darla en adopción
    sería justo lo contrario del producto."""
    respuesta = _publicar_desde(client, usuario, reporte_perdido)

    assert respuesta.status_code == 422
    assert respuesta.json()["detail"] == MENSAJE_NO_ES_ENCONTRADA_CONMIGO

    db_session.expire_all()
    assert db_session.query(Pet).count() == 0


def test_publicar_desde_un_encontrado_solo_visto_devuelve_422(
    client, db_session, usuario, reporte_vista
):
    respuesta = _publicar_desde(client, usuario, reporte_vista)

    assert respuesta.status_code == 422
    assert respuesta.json()["detail"] == MENSAJE_NO_ES_ENCONTRADA_CONMIGO

    db_session.expire_all()
    assert db_session.query(Pet).count() == 0


def test_publicar_desde_un_reporte_ajeno_devuelve_403(client, db_session, otro_usuario, reporte):
    """El reporte es de `usuario` y quien publica es `otro_usuario`: aunque la
    mascota encontrada esté "conmigo", no es su mascota la que se está dando."""
    respuesta = _publicar_desde(client, otro_usuario, reporte)

    assert respuesta.status_code == 403
    assert respuesta.json()["detail"] == MENSAJE_NO_ES_TU_REPORTE

    db_session.expire_all()
    assert db_session.query(Pet).count() == 0


def test_reporte_ajeno_y_ademas_perdido_devuelve_422_no_403(
    client, db_session, otro_usuario, reporte_perdido
):
    """Fija la **precedencia**: primero se valida qué clase de reporte es y solo
    después de quién. Si el orden se invirtiera, este caso respondería 403 y el
    mensaje sugeriría que basta con ser el autor para dar en adopción una
    mascota perdida."""
    respuesta = _publicar_desde(client, otro_usuario, reporte_perdido)

    assert respuesta.status_code == 422
    assert respuesta.json()["detail"] == MENSAJE_NO_ES_ENCONTRADA_CONMIGO


def test_publicar_dos_veces_desde_el_mismo_reporte_devuelve_409(client, usuario, reporte):
    assert _publicar_desde(client, usuario, reporte).status_code == 201

    segunda = _publicar_desde(client, usuario, reporte)

    assert segunda.status_code == 409
    assert segunda.json()["detail"] == "Este reporte ya tiene una mascota publicada en adopción"


def test_el_detalle_del_reporte_expone_la_mascota_en_adopcion(client, usuario, reporte):
    creada = _publicar_desde(client, usuario, reporte)
    assert creada.status_code == 201

    cuerpo = client.get(f"/api/reports/{reporte.id}").json()

    assert cuerpo["adopcion_pet_id"] == creada.json()["id"]


def test_el_detalle_de_un_reporte_sin_adopcion_lo_deja_en_none(client, reporte):
    cuerpo = client.get(f"/api/reports/{reporte.id}").json()

    assert cuerpo["adopcion_pet_id"] is None


def test_el_listado_de_reportes_nunca_calcula_la_mascota_en_adopcion(client, usuario, reporte):
    """Guarda anti-N+1: el campo existe en el contrato pero el listado (y con él
    el mapa) lo deja SIEMPRE en `None`. Llenarlo aquí costaría una query por
    reporte contra el pooler de Supabase, y ninguna vista de lista lo usa."""
    assert _publicar_desde(client, usuario, reporte).status_code == 201

    listado = client.get("/api/reports").json()

    assert [r["id"] for r in listado] == [reporte.id]
    assert "adopcion_pet_id" in listado[0]
    assert listado[0]["adopcion_pet_id"] is None


def test_eliminar_un_reporte_con_mascota_enlazada_devuelve_409_sin_tocar_las_fotos(
    client, db_session, usuario, reporte, fotos_borradas_del_reporte
):
    """Sin esta guarda el `DELETE` reventaría con `IntegrityError` (la FK de
    `pets.report_id`) → 500 con traza. Y el 409 tiene que ir **antes** de borrar
    las fotos: si no, el usuario pierde las imágenes y encima el reporte sigue
    ahí."""
    assert _publicar_desde(client, usuario, reporte).status_code == 201

    respuesta = client.delete(f"/api/reports/{reporte.id}?user_id={usuario.id}")

    assert respuesta.status_code == 409
    assert respuesta.json()["detail"] == MENSAJE_REPORTE_CON_MASCOTA
    assert fotos_borradas_del_reporte == []

    db_session.expire_all()
    assert db_session.get(Report, reporte.id) is not None
    cuerpo = client.get(f"/api/reports/{reporte.id}").json()
    assert cuerpo["foto_url"] == "/media/uploads/reporte-principal.jpg"
    assert cuerpo["fotos"] == ["/media/uploads/reporte-principal.jpg"]


def test_tras_despublicar_la_mascota_el_reporte_si_se_elimina(client, db_session, usuario, reporte):
    creada = _publicar_desde(client, usuario, reporte)
    assert creada.status_code == 201
    assert client.delete(f"/api/pets/{creada.json()['id']}?user_id={usuario.id}").status_code == 204

    respuesta = client.delete(f"/api/reports/{reporte.id}?user_id={usuario.id}")

    assert respuesta.status_code == 204

    db_session.expire_all()
    assert db_session.get(Report, reporte.id) is None
