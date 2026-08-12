from reencuentro_api.models.user import User


def test_registrar_usuario_devuelve_201_con_el_perfil(client, db_session):
    respuesta = client.post(
        "/api/users",
        json={
            "nombre": "Camila",
            "email": "camila@example.co",
            "ciudad": "Armenia",
            "barrio": "La Castellana",
        },
    )

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["nombre"] == "Camila"
    assert cuerpo["email"] == "camila@example.co"
    assert cuerpo["ciudad"] == "Armenia"
    assert cuerpo["barrio"] == "La Castellana"


def test_registrar_usuario_con_email_duplicado_devuelve_409_en_espanol(client, db_session):
    user = User(nombre="Ana", email="ana@example.co", ciudad="Pereira")
    db_session.add(user)
    db_session.commit()

    respuesta = client.post(
        "/api/users",
        json={"nombre": "Otra Ana", "email": "ana@example.co"},
    )

    assert respuesta.status_code == 409
    detalle = respuesta.json()["detail"]
    assert "ana@example.co" in detalle
    assert "Ya existe una cuenta" in detalle


def test_registrar_usuario_es_recuperable_via_get(client, db_session):
    respuesta_creacion = client.post(
        "/api/users",
        json={"nombre": "Diego", "email": "diego@example.co", "barrio": "Cuba"},
    )
    user_id = respuesta_creacion.json()["id"]

    respuesta_get = client.get(f"/api/users/{user_id}")

    assert respuesta_get.status_code == 200
    cuerpo = respuesta_get.json()
    assert cuerpo["nombre"] == "Diego"
    assert cuerpo["email"] == "diego@example.co"
    assert cuerpo["ciudad"] == "Armenia"
    assert cuerpo["barrio"] == "Cuba"


def test_obtener_perfil_usuario_inexistente_devuelve_404(client, db_session):
    respuesta = client.get("/api/users/9999")

    assert respuesta.status_code == 404
    assert "9999" in respuesta.json()["detail"]
