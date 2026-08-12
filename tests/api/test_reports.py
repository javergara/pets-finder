from datetime import date

import pytest

from reencuentro_api.models.report import Report
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


def _payload_perdido(usuario, **overrides):
    payload = {
        "user_id": usuario.id,
        "tipo": "perdido",
        "especie": "perro",
        "nombre_mascota": "Rocky",
        "descripcion": "Criollo color miel con collar rojo.",
        "zona": "Armenia",
        "barrio": "La Castellana",
        "lat": 4.54,
        "lng": -75.68,
        "fecha_evento": "2026-08-10",
        "telefono_contacto": "3001234567",
    }
    payload.update(overrides)
    return payload


def _payload_encontrado(usuario, **overrides):
    payload = {
        "user_id": usuario.id,
        "tipo": "encontrado",
        "especie": "perro",
        "situacion": "conmigo",
        "descripcion": "Perro color miel, lo tengo resguardado.",
        "zona": "Armenia",
        "lat": 4.545,
        "lng": -75.678,
        "fecha_evento": "2026-08-11",
        "telefono_contacto": "3007654321",
    }
    payload.update(overrides)
    return payload


# --- Creación ---


def test_crear_reporte_perdido_devuelve_201(client, usuario):
    respuesta = client.post("/api/reports", json=_payload_perdido(usuario))

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["tipo"] == "perdido"
    assert cuerpo["nombre_mascota"] == "Rocky"
    assert cuerpo["situacion"] is None
    assert cuerpo["estado"] == "activo"
    assert cuerpo["resuelto_en"] is None


def test_crear_reporte_encontrado_devuelve_201(client, usuario):
    respuesta = client.post("/api/reports", json=_payload_encontrado(usuario))

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["tipo"] == "encontrado"
    assert cuerpo["situacion"] == "conmigo"
    assert cuerpo["nombre_mascota"] is None


def test_crear_reporte_con_usuario_inexistente_devuelve_404(client, db_session):
    payload = _payload_perdido(type("U", (), {"id": 9999})())

    respuesta = client.post("/api/reports", json=payload)

    assert respuesta.status_code == 404
    assert "9999" in respuesta.json()["detail"]


# --- Validación condicional (422) ---


def test_encontrado_sin_situacion_devuelve_422(client, usuario):
    payload = _payload_encontrado(usuario)
    del payload["situacion"]

    respuesta = client.post("/api/reports", json=payload)

    assert respuesta.status_code == 422
    assert "situacion" in str(respuesta.json())


def test_perdido_con_situacion_devuelve_422(client, usuario):
    respuesta = client.post("/api/reports", json=_payload_perdido(usuario, situacion="conmigo"))

    assert respuesta.status_code == 422


def test_encontrado_con_nombre_mascota_devuelve_422(client, usuario):
    respuesta = client.post(
        "/api/reports", json=_payload_encontrado(usuario, nombre_mascota="Rocky")
    )

    assert respuesta.status_code == 422


def test_zona_desconocida_devuelve_422(client, usuario):
    respuesta = client.post("/api/reports", json=_payload_perdido(usuario, zona="Medellín"))

    assert respuesta.status_code == 422
    assert "Zona desconocida" in str(respuesta.json())


def test_zona_otro_sin_ciudad_texto_devuelve_422(client, usuario):
    respuesta = client.post("/api/reports", json=_payload_perdido(usuario, zona="Otro"))

    assert respuesta.status_code == 422
    assert "ciudad_texto" in str(respuesta.json())


def test_zona_otro_con_ciudad_texto_devuelve_201(client, usuario):
    respuesta = client.post(
        "/api/reports",
        json=_payload_perdido(usuario, zona="Otro", ciudad_texto="Ibagué", lat=4.44, lng=-75.24),
    )

    assert respuesta.status_code == 201
    assert respuesta.json()["ciudad_texto"] == "Ibagué"


def test_telefono_vacio_devuelve_422(client, usuario):
    respuesta = client.post("/api/reports", json=_payload_perdido(usuario, telefono_contacto="  "))

    assert respuesta.status_code == 422


# --- Listado y filtros ---


def _sembrar_variedad(db_session, usuario):
    reportes = [
        Report(
            user_id=usuario.id,
            tipo="perdido",
            especie="perro",
            nombre_mascota="Rocky",
            descripcion="d",
            zona="Armenia",
            lat=4.54,
            lng=-75.68,
            fecha_evento=date(2026, 8, 10),
            telefono_contacto="300",
        ),
        Report(
            user_id=usuario.id,
            tipo="encontrado",
            especie="perro",
            situacion="conmigo",
            descripcion="d",
            zona="Armenia",
            lat=4.545,
            lng=-75.678,
            fecha_evento=date(2026, 8, 11),
            telefono_contacto="300",
        ),
        Report(
            user_id=usuario.id,
            tipo="perdido",
            especie="gato",
            nombre_mascota="Mishi",
            descripcion="d",
            zona="Pereira",
            lat=4.81,
            lng=-75.70,
            fecha_evento=date(2026, 8, 9),
            telefono_contacto="300",
        ),
        Report(
            user_id=usuario.id,
            tipo="perdido",
            especie="perro",
            nombre_mascota="Firulais",
            descripcion="d",
            zona="Armenia",
            lat=4.55,
            lng=-75.69,
            fecha_evento=date(2026, 8, 12),
            telefono_contacto="300",
            estado="reunido",
        ),
    ]
    db_session.add_all(reportes)
    db_session.commit()
    return reportes


def test_listado_excluye_reunidos_por_defecto(client, db_session, usuario):
    _sembrar_variedad(db_session, usuario)

    respuesta = client.get("/api/reports")

    cuerpo = respuesta.json()
    assert len(cuerpo) == 3
    assert all(r["estado"] == "activo" for r in cuerpo)


def test_listado_ordena_por_fecha_evento_descendente(client, db_session, usuario):
    _sembrar_variedad(db_session, usuario)

    respuesta = client.get("/api/reports")

    fechas = [r["fecha_evento"] for r in respuesta.json()]
    assert fechas == sorted(fechas, reverse=True)


def test_listado_filtra_por_tipo_especie_y_zona(client, db_session, usuario):
    _sembrar_variedad(db_session, usuario)

    solo_perdidos = client.get("/api/reports?tipo=perdido").json()
    assert {r["tipo"] for r in solo_perdidos} == {"perdido"}

    solo_gatos = client.get("/api/reports?especie=gato").json()
    assert len(solo_gatos) == 1
    assert solo_gatos[0]["nombre_mascota"] == "Mishi"

    solo_pereira = client.get("/api/reports?zona=Pereira").json()
    assert len(solo_pereira) == 1
    assert solo_pereira[0]["zona"] == "Pereira"


def test_listado_estado_reunido_y_todos(client, db_session, usuario):
    _sembrar_variedad(db_session, usuario)

    reunidos = client.get("/api/reports?estado=reunido").json()
    assert len(reunidos) == 1
    assert reunidos[0]["nombre_mascota"] == "Firulais"

    todos = client.get("/api/reports?estado=todos").json()
    assert len(todos) == 4


# --- Detalle y edición ---


def test_obtener_reporte_inexistente_devuelve_404(client, db_session):
    respuesta = client.get("/api/reports/9999")

    assert respuesta.status_code == 404
    assert "9999" in respuesta.json()["detail"]


def test_editar_reporte_por_su_autor(client, db_session, usuario):
    reporte = _sembrar_variedad(db_session, usuario)[0]

    respuesta = client.put(
        f"/api/reports/{reporte.id}",
        json={"user_id": usuario.id, "descripcion": "Actualizada: visto cerca del parque."},
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["descripcion"] == "Actualizada: visto cerca del parque."
    # Los campos no enviados no cambian.
    assert respuesta.json()["nombre_mascota"] == "Rocky"


def test_editar_reporte_ajeno_devuelve_403_en_espanol(client, db_session, usuario, otro_usuario):
    reporte = _sembrar_variedad(db_session, usuario)[0]

    respuesta = client.put(
        f"/api/reports/{reporte.id}",
        json={"user_id": otro_usuario.id, "descripcion": "intruso"},
    )

    assert respuesta.status_code == 403
    assert "Solo quien creó el reporte" in respuesta.json()["detail"]
