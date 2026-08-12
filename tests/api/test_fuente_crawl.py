"""Feature crawler (ADR 0009): procedencia `fuente` + `crawl_metadata`.

Cubre el contrato nuevo del POST /api/reports:
- fuente "manual" por defecto, con las reglas de siempre (teléfono obligatorio).
- fuente "crawl": metadata obligatoria, teléfono opcional si hay un camino de
  contacto alternativo (url_post o autor_handle del post original).
"""

import pytest

from reencuentro_api.models.user import User


@pytest.fixture()
def usuario(db_session):
    user = User(nombre="Ana", email="ana@example.co", ciudad="Armenia")
    db_session.add(user)
    db_session.commit()
    return user


def _payload_crawl(usuario, **overrides):
    payload = {
        "user_id": usuario.id,
        "tipo": "encontrado",
        "especie": "perro",
        "situacion": "vista",
        "descripcion": "Perrita pequeña con pañoleta, vista cerca del parque del Perro.",
        "zona": "Cali",
        "lat": 3.452,
        "lng": -76.532,
        "fecha_evento": "2026-08-11",
        "fuente": "crawl",
        "crawl_metadata": {
            "plataforma": "instagram",
            "url_post": "https://www.instagram.com/p/ABC123/",
            "autor_handle": "rescate.cali",
            "fecha_post": "2026-08-11",
            "modelo_extraccion": "llamaextract",
            "confianza": 0.87,
            "indice_mascota": 0,
            "total_mascotas": 1,
        },
    }
    payload.update(overrides)
    return payload


def test_manual_por_defecto_sin_metadata(client, usuario):
    """Un reporte del formulario de siempre sale con fuente 'manual' y sin metadata."""
    respuesta = client.post(
        "/api/reports",
        json={
            "user_id": usuario.id,
            "tipo": "perdido",
            "especie": "perro",
            "nombre_mascota": "Rocky",
            "descripcion": "Criollo color miel con collar rojo.",
            "zona": "Armenia",
            "lat": 4.54,
            "lng": -75.68,
            "fecha_evento": "2026-08-10",
            "telefono_contacto": "3001234567",
        },
    )
    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["fuente"] == "manual"
    assert cuerpo["crawl_metadata"] is None


def test_crawl_sin_telefono_crea_y_devuelve_metadata(client, usuario):
    respuesta = client.post("/api/reports", json=_payload_crawl(usuario))
    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["fuente"] == "crawl"
    assert cuerpo["telefono_contacto"] is None
    assert cuerpo["crawl_metadata"]["url_post"] == "https://www.instagram.com/p/ABC123/"
    assert cuerpo["crawl_metadata"]["autor_handle"] == "rescate.cali"
    assert cuerpo["crawl_metadata"]["indice_mascota"] == 0

    # Y el detalle lo devuelve igual (roundtrip completo por la columna JSON).
    detalle = client.get(f"/api/reports/{cuerpo['id']}").json()
    assert detalle["crawl_metadata"] == cuerpo["crawl_metadata"]


def test_crawl_sin_metadata_es_422(client, usuario):
    payload = _payload_crawl(usuario)
    del payload["crawl_metadata"]
    respuesta = client.post("/api/reports", json=payload)
    assert respuesta.status_code == 422
    assert "crawl_metadata" in respuesta.text


def test_crawl_sin_telefono_ni_origen_es_422(client, usuario):
    """Solo la red, sin url ni handle ni teléfono: no hay forma de contactar."""
    payload = _payload_crawl(usuario, crawl_metadata={"plataforma": "instagram"})
    respuesta = client.post("/api/reports", json=payload)
    assert respuesta.status_code == 422
    assert "camino de contacto" in respuesta.text


def test_crawl_solo_con_handle_es_valido(client, usuario):
    """El pantallazo a veces solo deja legible la cuenta: eso basta como contacto."""
    payload = _payload_crawl(
        usuario, crawl_metadata={"plataforma": "facebook", "autor_handle": "rescates.armenia"}
    )
    respuesta = client.post("/api/reports", json=payload)
    assert respuesta.status_code == 201
    assert respuesta.json()["crawl_metadata"]["autor_handle"] == "rescates.armenia"


def test_facebook_acepta_grupo_y_hace_roundtrip(client, usuario):
    """La variante de Facebook de la unión discriminada lleva el nombre del grupo."""
    payload = _payload_crawl(
        usuario,
        crawl_metadata={
            "plataforma": "facebook",
            "autor_handle": "maria.rescates",
            "grupo": "Mascotas Perdidas Cali",
        },
    )
    respuesta = client.post("/api/reports", json=payload)
    assert respuesta.status_code == 201
    assert respuesta.json()["crawl_metadata"]["grupo"] == "Mascotas Perdidas Cali"


def test_url_post_no_http_es_422(client, usuario):
    """url_post se renderiza como href en la UI y el POST es público: solo http(s)."""
    payload = _payload_crawl(
        usuario,
        crawl_metadata={"plataforma": "desconocida", "url_post": "javascript:alert(1)"},
    )
    respuesta = client.post("/api/reports", json=payload)
    assert respuesta.status_code == 422
    assert "URL http(s) absoluta" in respuesta.text


def test_whatsapp_acepta_nombre_grupo(client, usuario):
    """Las cadenas de WhatsApp no tienen url_post: el grupo es la pista de origen."""
    payload = _payload_crawl(
        usuario,
        crawl_metadata={
            "plataforma": "whatsapp",
            "autor_handle": "3001234567",
            "nombre_grupo": "Mascotas Eje Cafetero",
        },
    )
    respuesta = client.post("/api/reports", json=payload)
    assert respuesta.status_code == 201
    assert respuesta.json()["crawl_metadata"]["nombre_grupo"] == "Mascotas Eje Cafetero"


def test_grupo_fuera_de_facebook_es_422(client, usuario):
    """extra='forbid': un campo de otra variante no se descarta en silencio."""
    payload = _payload_crawl(
        usuario,
        crawl_metadata={
            "plataforma": "instagram",
            "autor_handle": "rescate.cali",
            "grupo": "Mascotas Perdidas Cali",
        },
    )
    respuesta = client.post("/api/reports", json=payload)
    assert respuesta.status_code == 422


def test_manual_con_metadata_es_422(client, usuario):
    respuesta = client.post(
        "/api/reports",
        json=_payload_crawl(usuario, fuente="manual", telefono_contacto="3001234567"),
    )
    assert respuesta.status_code == 422
    assert "solo aplica a reportes con fuente 'crawl'" in respuesta.text


def test_manual_sin_telefono_sigue_siendo_422(client, usuario):
    """La regla de siempre no se relaja: el formulario exige teléfono."""
    payload = _payload_crawl(usuario, fuente="manual")
    del payload["crawl_metadata"]
    respuesta = client.post("/api/reports", json=payload)
    assert respuesta.status_code == 422
    assert "teléfono de contacto es obligatorio" in respuesta.text


def test_idempotency_id_repetido_devuelve_el_mismo_reporte(client, usuario):
    """Retry seguro del crawler: mismo idempotency_id → 200 con el reporte ya
    creado, nunca un duplicado."""
    payload = _payload_crawl(usuario, idempotency_id="https://instagram.com/p/ABC/#0")

    primera = client.post("/api/reports", json=payload)
    assert primera.status_code == 201

    segunda = client.post("/api/reports", json=payload)
    assert segunda.status_code == 200
    assert segunda.json()["id"] == primera.json()["id"]

    listado = client.get("/api/reports").json()
    assert len(listado) == 1


def test_sin_idempotency_id_cada_post_crea_un_reporte(client, usuario):
    """El formulario manual no manda la clave: el comportamiento de siempre."""
    payload = _payload_crawl(usuario)
    assert client.post("/api/reports", json=payload).status_code == 201
    assert client.post("/api/reports", json=payload).status_code == 201
    assert len(client.get("/api/reports").json()) == 2


def test_listado_incluye_fuente(client, usuario):
    client.post("/api/reports", json=_payload_crawl(usuario))
    listado = client.get("/api/reports").json()
    assert len(listado) == 1
    assert listado[0]["fuente"] == "crawl"
