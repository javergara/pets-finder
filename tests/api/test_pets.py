"""Mascotas en adopción (AD-01): modelo `Pet`, schemas y endpoints de `/api/pets`.

Cubre el invariante del CHECK a nivel de DB, las reglas del `model_validator` de
`PetIn`, la publicación por HTTP (paso 5) y las lecturas del catálogo (paso 6:
listado con filtros, resumen de adopciones y ficha).

⚠️ `Pet` se importa a nivel de módulo a propósito: el fixture `db_session` hace
`create_all` con lo que esté registrado en `Base.metadata` en ese instante, y un
import perezoso produce un `no such table: pets` intermitente según el orden de
colección de pytest.
"""

from contextlib import contextmanager
from datetime import date, datetime

import pytest
from pydantic import ValidationError
from sqlalchemy import event
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


# --- Lecturas del catálogo: GET "" / GET /adopciones / GET /{pet_id} (paso 6) --


def _sembrar_catalogo(db_session, otro_usuario, organizacion) -> dict[str, Pet]:
    """Catálogo variado: mascotas de organización y de rescatista, mezcla de
    especie/tamaño/energía/sexo/zona y los tres estados.

    `publicado_en` va explícito para que el orden del listado sea determinista.
    """
    mascotas = {
        "canela": _pet(
            organizacion_id=organizacion.id,
            nombre="Canela",
            especie="perro",
            sexo="hembra",
            tamano="mediano",
            energia="media",
            zona="Armenia",
            publicado_en=datetime(2026, 8, 14, 9, 0),
        ),
        "mishi": _pet(
            organizacion_id=organizacion.id,
            nombre="Mishi",
            especie="gato",
            sexo="macho",
            tamano="pequeño",
            energia="baja",
            zona="Pereira",
            publicado_en=datetime(2026, 8, 13, 9, 0),
        ),
        "rocky": _pet(
            user_id=otro_usuario.id,
            telefono_contacto="3105558899",
            nombre="Rocky",
            especie="perro",
            sexo="macho",
            tamano="grande",
            energia="alta",
            zona="Armenia",
            publicado_en=datetime(2026, 8, 12, 9, 0),
        ),
        "nube": _pet(
            user_id=otro_usuario.id,
            telefono_contacto="3105558899",
            nombre="Nube",
            especie="gato",
            sexo="hembra",
            tamano="pequeño",
            energia="media",
            zona="Cali",
            estado="en_proceso",
            publicado_en=datetime(2026, 8, 11, 9, 0),
        ),
        "duque": _pet(
            organizacion_id=organizacion.id,
            nombre="Duque",
            especie="perro",
            sexo="macho",
            tamano="grande",
            energia="media",
            zona="Armenia",
            estado="adoptado",
            adoptado_en=datetime(2026, 8, 13, 18, 0),
            publicado_en=datetime(2026, 8, 10, 9, 0),
        ),
    }
    db_session.add_all(mascotas.values())
    db_session.commit()
    return mascotas


def _nombres(respuesta) -> list[str]:
    return [m["nombre"] for m in respuesta.json()]


@contextmanager
def _contar_consultas(session):
    """Cuenta las sentencias SQL reales que salen por el engine del test.

    Es la red contra el N+1 del catálogo: sin las dos queries batch con `IN`,
    cada mascota de la página añadiría un round-trip por su publicador.
    """
    sentencias: list[str] = []
    engine = session.get_bind()

    def _registrar(conn, cursor, statement, parameters, context, executemany):
        sentencias.append(statement)

    event.listen(engine, "before_cursor_execute", _registrar)
    try:
        yield sentencias
    finally:
        event.remove(engine, "before_cursor_execute", _registrar)


def test_listado_filtra_por_especie(client, db_session, otro_usuario, organizacion):
    _sembrar_catalogo(db_session, otro_usuario, organizacion)

    assert sorted(_nombres(client.get("/api/pets?especie=perro"))) == ["Canela", "Rocky"]
    assert _nombres(client.get("/api/pets?especie=gato")) == ["Mishi"]


def test_listado_filtra_por_tamano(client, db_session, otro_usuario, organizacion):
    _sembrar_catalogo(db_session, otro_usuario, organizacion)

    assert _nombres(client.get("/api/pets?tamano=grande")) == ["Rocky"]
    assert _nombres(client.get("/api/pets?tamano=pequeño")) == ["Mishi"]


def test_listado_filtra_por_energia(client, db_session, otro_usuario, organizacion):
    _sembrar_catalogo(db_session, otro_usuario, organizacion)

    assert _nombres(client.get("/api/pets?energia=baja")) == ["Mishi"]
    assert _nombres(client.get("/api/pets?energia=alta")) == ["Rocky"]


def test_listado_filtra_por_sexo(client, db_session, otro_usuario, organizacion):
    _sembrar_catalogo(db_session, otro_usuario, organizacion)

    assert _nombres(client.get("/api/pets?sexo=hembra")) == ["Canela"]
    assert sorted(_nombres(client.get("/api/pets?sexo=macho"))) == ["Mishi", "Rocky"]


def test_listado_filtra_por_zona(client, db_session, otro_usuario, organizacion):
    _sembrar_catalogo(db_session, otro_usuario, organizacion)

    assert _nombres(client.get("/api/pets?zona=Armenia")) == ["Canela", "Rocky"]
    assert _nombres(client.get("/api/pets?zona=Pereira")) == ["Mishi"]


def test_listado_combina_filtros(client, db_session, otro_usuario, organizacion):
    _sembrar_catalogo(db_session, otro_usuario, organizacion)

    assert _nombres(client.get("/api/pets?especie=perro&zona=Armenia&tamano=grande")) == ["Rocky"]
    assert _nombres(client.get("/api/pets?especie=perro&sexo=hembra&energia=media")) == ["Canela"]
    assert client.get("/api/pets?especie=gato&zona=Armenia").json() == []


def test_listado_excluye_adoptadas_por_defecto(client, db_session, otro_usuario, organizacion):
    """El catálogo muestra lo adoptable: ni las adoptadas ni las en proceso."""
    _sembrar_catalogo(db_session, otro_usuario, organizacion)

    cuerpo = client.get("/api/pets").json()

    assert [m["nombre"] for m in cuerpo] == ["Canela", "Mishi", "Rocky"]
    assert all(m["estado"] == "disponible" for m in cuerpo)


def test_listado_con_estado_todos_incluye_adoptadas_y_en_proceso(
    client, db_session, otro_usuario, organizacion
):
    _sembrar_catalogo(db_session, otro_usuario, organizacion)

    todos = client.get("/api/pets?estado=todos").json()

    # Orden por publicado_en desc, id desc.
    assert [m["nombre"] for m in todos] == ["Canela", "Mishi", "Rocky", "Nube", "Duque"]
    assert _nombres(client.get("/api/pets?estado=en_proceso")) == ["Nube"]
    assert _nombres(client.get("/api/pets?estado=adoptado")) == ["Duque"]


def test_listado_pagina_con_el_total_en_el_header(client, db_session, otro_usuario, organizacion):
    _sembrar_catalogo(db_session, otro_usuario, organizacion)

    pagina1 = client.get("/api/pets?estado=todos&limit=2&offset=0")
    pagina2 = client.get("/api/pets?estado=todos&limit=2&offset=2")
    sin_limit = client.get("/api/pets?estado=todos")

    # El total es el de la consulta SIN paginar, en las tres respuestas.
    assert pagina1.headers["X-Total-Count"] == "5"
    assert pagina2.headers["X-Total-Count"] == "5"
    assert sin_limit.headers["X-Total-Count"] == "5"
    assert len(pagina1.json()) == 2
    # Y el total respeta los filtros: solo 3 disponibles.
    assert client.get("/api/pets?limit=2").headers["X-Total-Count"] == "3"
    # Sin duplicados ni huecos entre páginas.
    assert _nombres(pagina1) + _nombres(pagina2) == _nombres(sin_limit)[:4]


def test_listado_con_limit_invalido_devuelve_422(client, db_session):
    assert client.get("/api/pets?limit=0").status_code == 422
    assert client.get("/api/pets?limit=101").status_code == 422
    assert client.get("/api/pets?offset=-1").status_code == 422


def test_listado_filtra_por_organizacion_y_por_rescatista_sin_confundirlos(
    client, db_session, usuario, otro_usuario, organizacion
):
    """`user_id` en el listado es **el rescatista que publicó**, nunca el
    adoptante que mira (en `adopta-v1` significaba lo contrario).

    `usuario` es quien registró la organización: sus mascotas cuelgan de ella,
    así que filtrar por `user_id=usuario.id` no devuelve ninguna.
    """
    _sembrar_catalogo(db_session, otro_usuario, organizacion)

    de_la_organizacion = client.get(f"/api/pets?organizacion_id={organizacion.id}")
    del_rescatista = client.get(f"/api/pets?user_id={otro_usuario.id}")

    assert _nombres(de_la_organizacion) == ["Canela", "Mishi"]
    assert _nombres(del_rescatista) == ["Rocky"]
    assert "Rocky" not in _nombres(de_la_organizacion)
    assert {"Canela", "Mishi"}.isdisjoint(_nombres(del_rescatista))
    # Quien registró la organización no publica "a su nombre" ninguna mascota.
    assert client.get(f"/api/pets?user_id={usuario.id}").json() == []
    # Combinables con el estado, para el panel de la organización (AD-02).
    assert _nombres(client.get(f"/api/pets?organizacion_id={organizacion.id}&estado=todos")) == [
        "Canela",
        "Mishi",
        "Duque",
    ]


def test_listado_trae_el_publicador_de_cada_mascota(
    client, db_session, usuario, otro_usuario, organizacion
):
    _sembrar_catalogo(db_session, otro_usuario, organizacion)

    por_nombre = {m["nombre"]: m["publicador"] for m in client.get("/api/pets").json()}

    assert por_nombre["Canela"]["tipo"] == "organizacion"
    assert por_nombre["Canela"]["id"] == organizacion.id
    assert por_nombre["Canela"]["nombre"] == "Fundación Huellitas del Quindío"
    assert por_nombre["Rocky"]["tipo"] == "rescatista"
    assert por_nombre["Rocky"]["id"] == otro_usuario.id
    assert por_nombre["Rocky"]["nombre"] == "Carlos"


def test_listado_no_hace_una_consulta_por_publicador(client, db_session):
    """Anti-N+1: el número de consultas NO crece con el tamaño de la página.

    Son siempre 4 — el total, las mascotas, y **una** query con `IN` por cada
    tabla de publicador — aunque cada mascota tenga un publicador distinto. Con
    `session.get` por mascota serían 2 + N: contra el pooler de Supabase, ~40
    round-trips por página.
    """
    for n in range(6):
        rescatista = User(nombre=f"Rescatista {n}", email=f"r{n}@example.co", ciudad="Armenia")
        db_session.add(rescatista)
        db_session.flush()
        fundacion = Organizacion(
            user_id=rescatista.id,
            tipo="fundacion",
            nombre=f"Fundación {n}",
            descripcion="Rescate tras el sismo.",
            zona="Armenia",
            direccion="Cra 14 #10-25",
            lat=4.535,
            lng=-75.68,
            telefono_contacto="3001112233",
        )
        db_session.add(fundacion)
        db_session.flush()
        db_session.add(_pet(organizacion_id=fundacion.id, nombre=f"Fundada {n}"))
        db_session.add(
            _pet(user_id=rescatista.id, telefono_contacto="3105558899", nombre=f"Rescatada {n}")
        )
    db_session.commit()

    # El identity map de la sesión del fixture escondería el N+1 (en producción
    # cada request abre su propia sesión): se vacía antes de contar para que las
    # consultas por publicador sean visibles de verdad.
    db_session.expunge_all()
    with _contar_consultas(db_session) as pagina_corta:
        assert len(client.get("/api/pets?limit=3").json()) == 3

    db_session.expunge_all()
    with _contar_consultas(db_session) as pagina_completa:
        assert len(client.get("/api/pets").json()) == 12

    assert len(pagina_corta) == 4
    assert len(pagina_completa) == 4


def test_listado_acepta_adoptante_id_sin_alterar_la_respuesta(
    client, db_session, otro_usuario, organizacion
):
    """`adoptante_id` ya se acepta para no romper el cliente cuando AD-03/05/07
    lo llenen; en AD-01 no cambia nada de lo que se devuelve."""
    _sembrar_catalogo(db_session, otro_usuario, organizacion)

    con_adoptante = client.get(f"/api/pets?adoptante_id={otro_usuario.id}")

    assert con_adoptante.status_code == 200
    assert con_adoptante.json() == client.get("/api/pets").json()
    assert all(m["afinidad"] is None for m in con_adoptante.json())
    assert all(m["es_favorito"] is False for m in con_adoptante.json())
    assert all(m["ya_solicitada"] is False for m in con_adoptante.json())


def test_adopciones_no_se_parsea_como_pet_id_y_responde_200(client, db_session):
    """Garantía viva del orden literal-antes-que-dinámica: si `GET /adopciones`
    se declarara después de `GET /{pet_id}`, FastAPI intentaría convertir
    "adopciones" en int y respondería 422 (bug que parece "ruta inexistente")."""
    respuesta = client.get("/api/pets/adopciones")

    assert respuesta.status_code != 422
    assert respuesta.status_code == 200
    assert respuesta.json() == {"total": 0, "recientes": []}


def test_resumen_de_adopciones_cuenta_solo_las_adoptadas(
    client, db_session, otro_usuario, organizacion
):
    _sembrar_catalogo(db_session, otro_usuario, organizacion)

    cuerpo = client.get("/api/pets/adopciones").json()

    assert cuerpo["total"] == 1
    assert [m["nombre"] for m in cuerpo["recientes"]] == ["Duque"]
    assert cuerpo["recientes"][0]["estado"] == "adoptado"


def test_resumen_de_adopciones_lista_las_seis_mas_recientes(
    client, db_session, otro_usuario, organizacion
):
    db_session.add_all(
        _pet(
            organizacion_id=organizacion.id,
            nombre=f"Adoptada {n}",
            estado="adoptado",
            adoptado_en=datetime(2026, 8, 1 + n, 12, 0),
        )
        for n in range(8)
    )
    db_session.add(_pet(organizacion_id=organizacion.id, nombre="Disponible"))
    db_session.commit()

    cuerpo = client.get("/api/pets/adopciones").json()

    assert cuerpo["total"] == 8
    assert len(cuerpo["recientes"]) == 6
    # Las más recientes primero (adoptado_en desc).
    assert [m["nombre"] for m in cuerpo["recientes"]] == [f"Adoptada {n}" for n in range(7, 1, -1)]


def test_detalle_de_mascota_de_organizacion_trae_su_publicador(
    client, db_session, otro_usuario, organizacion
):
    canela = _sembrar_catalogo(db_session, otro_usuario, organizacion)["canela"]

    respuesta = client.get(f"/api/pets/{canela.id}")

    assert respuesta.status_code == 200
    publicador = respuesta.json()["publicador"]
    assert publicador["tipo"] == "organizacion"
    assert publicador["id"] == organizacion.id
    assert publicador["nombre"] == "Fundación Huellitas del Quindío"
    # Sin teléfono propio, la mascota se contacta por el de la organización.
    assert publicador["telefono_contacto"] == "3001112233"
    assert publicador["zona"] == "Armenia"


def test_detalle_de_mascota_de_rescatista_trae_su_telefono(
    client, db_session, otro_usuario, organizacion
):
    """El `User` no tiene teléfono: el del rescatista sale de `Pet.telefono_contacto`."""
    rocky = _sembrar_catalogo(db_session, otro_usuario, organizacion)["rocky"]

    respuesta = client.get(f"/api/pets/{rocky.id}")

    assert respuesta.status_code == 200
    publicador = respuesta.json()["publicador"]
    assert publicador["tipo"] == "rescatista"
    assert publicador["id"] == otro_usuario.id
    assert publicador["nombre"] == "Carlos"
    assert publicador["telefono_contacto"] == "3105558899"


def test_detalle_de_mascota_inexistente_devuelve_404(client, db_session):
    respuesta = client.get("/api/pets/9999")

    assert respuesta.status_code == 404
    assert respuesta.json()["detail"] == "La mascota 9999 no existe"
