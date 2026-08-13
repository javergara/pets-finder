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
    respuesta = client.post("/api/reports", json=_payload_perdido(usuario, zona="Palmira"))

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
            raza="Criollo / mestizo",
            color="Miel / dorado",
            tamano="mediano",
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
            raza="Siamés",
            color="Gris",
            tamano="pequeño",
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


def test_crear_reporte_con_caracteristicas_las_persiste(client, usuario):
    respuesta = client.post(
        "/api/reports",
        json=_payload_perdido(usuario, raza="Labrador", color="Negro", tamano="grande"),
    )

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["raza"] == "Labrador"
    assert cuerpo["color"] == "Negro"
    assert cuerpo["tamano"] == "grande"


def test_tamano_invalido_devuelve_422(client, usuario):
    respuesta = client.post("/api/reports", json=_payload_perdido(usuario, tamano="gigante"))

    assert respuesta.status_code == 422


def test_listado_filtra_por_raza_color_y_tamano(client, db_session, usuario):
    """Feature 15: los filtros por características son exactos y combinables.
    Los reportes sin características (null, anteriores a la feature) no matchean
    los filtros pero sí aparecen sin ellos."""
    _sembrar_variedad(db_session, usuario)

    por_color = client.get("/api/reports?color=Miel%20%2F%20dorado").json()
    assert len(por_color) == 1
    assert por_color[0]["nombre_mascota"] == "Rocky"

    por_raza = client.get("/api/reports?raza=Siam%C3%A9s").json()
    assert len(por_raza) == 1
    assert por_raza[0]["nombre_mascota"] == "Mishi"

    combinado = client.get("/api/reports?tipo=perdido&tamano=mediano&zona=Armenia").json()
    assert len(combinado) == 1
    assert combinado[0]["nombre_mascota"] == "Rocky"

    # Sin filtros de características, los null siguen apareciendo.
    todos_activos = client.get("/api/reports").json()
    assert len(todos_activos) == 3


def test_listado_filtra_por_user_id(client, db_session, usuario, otro_usuario):
    _sembrar_variedad(db_session, usuario)

    ajenos = client.get(f"/api/reports?user_id={otro_usuario.id}&estado=todos").json()
    propios = client.get(f"/api/reports?user_id={usuario.id}&estado=todos").json()

    assert ajenos == []
    assert len(propios) == 4


# --- Marcar reunido (feature 09) ---


def test_marcar_reunido_transiciona_y_sale_del_listado(client, db_session, usuario):
    reporte = _sembrar_variedad(db_session, usuario)[0]

    respuesta = client.post(f"/api/reports/{reporte.id}/reunido", json={"user_id": usuario.id})

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["estado"] == "reunido"
    assert cuerpo["resuelto_en"] is not None

    # Sale del listado activo por defecto.
    activos = client.get("/api/reports").json()
    assert all(r["id"] != reporte.id for r in activos)


def test_marcar_reunido_por_otro_usuario_devuelve_403_en_espanol(
    client, db_session, usuario, otro_usuario
):
    reporte = _sembrar_variedad(db_session, usuario)[0]

    respuesta = client.post(f"/api/reports/{reporte.id}/reunido", json={"user_id": otro_usuario.id})

    assert respuesta.status_code == 403
    assert "Solo quien creó el reporte" in respuesta.json()["detail"]


def test_marcar_reunido_dos_veces_devuelve_409(client, db_session, usuario):
    reporte = _sembrar_variedad(db_session, usuario)[0]
    client.post(f"/api/reports/{reporte.id}/reunido", json={"user_id": usuario.id})

    respuesta = client.post(f"/api/reports/{reporte.id}/reunido", json={"user_id": usuario.id})

    assert respuesta.status_code == 409
    assert "ya está marcado" in respuesta.json()["detail"]


def test_resumen_reunidos_cuenta_y_lista_los_recientes(client, db_session, usuario):
    reportes = _sembrar_variedad(db_session, usuario)
    # El seed de variedad trae 1 reunido (Firulais); marcamos otro más.
    client.post(f"/api/reports/{reportes[0].id}/reunido", json={"user_id": usuario.id})

    respuesta = client.get("/api/reports/reunidos")

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["total"] == 2
    # El recién marcado (con resuelto_en real) va de primero.
    assert cuerpo["recientes"][0]["id"] == reportes[0].id


def test_la_ruta_literal_reunidos_no_queda_eclipsada_por_report_id(client, db_session):
    """Regresión de la regla de orden: /api/reports/reunidos debe responder 200,
    nunca 422 por parsearse como un report_id inválido."""
    respuesta = client.get("/api/reports/reunidos")

    assert respuesta.status_code == 200
    assert respuesta.json() == {"total": 0, "recientes": []}


# --- Eliminar reporte (feature 18) ---


def test_eliminar_reporte_por_su_autor_devuelve_204_y_desaparece(client, db_session, usuario):
    reporte = _sembrar_variedad(db_session, usuario)[0]

    respuesta = client.delete(f"/api/reports/{reporte.id}?user_id={usuario.id}")

    assert respuesta.status_code == 204
    assert client.get(f"/api/reports/{reporte.id}").status_code == 404
    activos = client.get("/api/reports").json()
    assert all(r["id"] != reporte.id for r in activos)


def test_eliminar_reporte_ajeno_devuelve_403_en_espanol(client, db_session, usuario, otro_usuario):
    reporte = _sembrar_variedad(db_session, usuario)[0]

    respuesta = client.delete(f"/api/reports/{reporte.id}?user_id={otro_usuario.id}")

    assert respuesta.status_code == 403
    assert respuesta.json()["detail"] == "Solo quien creó el reporte puede eliminarlo"
    # El reporte sigue existiendo intacto.
    assert client.get(f"/api/reports/{reporte.id}").status_code == 200


def test_eliminar_reporte_inexistente_devuelve_404(client, db_session, usuario):
    respuesta = client.delete(f"/api/reports/999?user_id={usuario.id}")

    assert respuesta.status_code == 404


# --- Conteos por tipo (feature 34) ---


def test_conteos_cuenta_solo_activos_por_tipo(client, db_session, usuario):
    _sembrar_variedad(db_session, usuario)

    respuesta = client.get("/api/reports/conteos")

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    # El seed de variedad: 2 perdidos + 1 encontrado activos; el perdido reunido
    # (Firulais) NO cuenta.
    assert cuerpo == {"perdidos": 2, "encontrados": 1}


def test_conteos_ruta_literal_no_eclipsada(client, db_session):
    """Nunca 422 por parsearse "conteos" como report_id (regla de orden)."""
    respuesta = client.get("/api/reports/conteos")

    assert respuesta.status_code == 200
    assert respuesta.json() == {"perdidos": 0, "encontrados": 0}


# --- Edición completa (feature 29) ---


def test_editar_caracteristicas_fecha_y_pin(client, db_session, usuario):
    reporte = _sembrar_variedad(db_session, usuario)[0]

    respuesta = client.put(
        f"/api/reports/{reporte.id}",
        json={
            "user_id": usuario.id,
            "raza": "Labrador",
            "color": "Negro",
            "tamano": "grande",
            "barrio": "Corregido",
            "fecha_evento": "2026-08-09",
            "lat": 4.55,
            "lng": -75.7,
            "foto_url": "/media/uploads/nueva.jpg",
        },
    )

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["raza"] == "Labrador"
    assert cuerpo["color"] == "Negro"
    assert cuerpo["tamano"] == "grande"
    assert cuerpo["barrio"] == "Corregido"
    assert cuerpo["fecha_evento"] == "2026-08-09"
    assert cuerpo["lat"] == 4.55 and cuerpo["lng"] == -75.7
    assert cuerpo["foto_url"] == "/media/uploads/nueva.jpg"
    # Lo no enviado queda intacto.
    assert cuerpo["nombre_mascota"] == "Rocky"
    assert cuerpo["zona"] == "Armenia"


def test_editar_tamano_invalido_devuelve_422(client, db_session, usuario):
    reporte = _sembrar_variedad(db_session, usuario)[0]

    respuesta = client.put(
        f"/api/reports/{reporte.id}", json={"user_id": usuario.id, "tamano": "gigante"}
    )

    assert respuesta.status_code == 422


# --- Búsqueda y paginación (feature 30) ---


def test_busqueda_q_en_nombre_descripcion_barrio_y_ciudad(client, db_session, usuario):
    _sembrar_variedad(db_session, usuario)

    # Nombre, case-insensitive.
    assert [r["nombre_mascota"] for r in client.get("/api/reports?q=rOcKy").json()] == ["Rocky"]
    # Descripción (todas las del seed de variedad dicen "d") + combinable con tipo.
    assert len(client.get("/api/reports?q=d&tipo=encontrado").json()) == 1
    # Sin coincidencias.
    assert client.get("/api/reports?q=inexistente").json() == []


def test_paginacion_con_orden_estable_y_total_en_header(client, db_session, usuario):
    _sembrar_variedad(db_session, usuario)

    pagina1 = client.get("/api/reports?limit=2&offset=0")
    pagina2 = client.get("/api/reports?limit=2&offset=2")

    assert pagina1.headers["X-Total-Count"] == "3"
    assert len(pagina1.json()) == 2
    ids_paginados = [r["id"] for r in pagina1.json()] + [r["id"] for r in pagina2.json()]
    # Mismo orden que el listado completo: sin duplicados ni huecos entre páginas.
    completo = [r["id"] for r in client.get("/api/reports").json()]
    assert ids_paginados == completo


def test_sin_limit_la_respuesta_sigue_completa_con_total(client, db_session, usuario):
    _sembrar_variedad(db_session, usuario)

    respuesta = client.get("/api/reports")

    assert len(respuesta.json()) == 3
    assert respuesta.headers["X-Total-Count"] == "3"


def test_limit_invalido_devuelve_422(client, db_session):
    assert client.get("/api/reports?limit=0").status_code == 422
    assert client.get("/api/reports?limit=101").status_code == 422
    assert client.get("/api/reports?offset=-1").status_code == 422
