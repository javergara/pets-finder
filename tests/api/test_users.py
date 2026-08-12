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


def test_email_existente_entra_a_la_cuenta_en_vez_de_409(client, db_session):
    """Regresión del bug de producción: la sesión vive en localStorage; si se
    pierde, el mismo formulario debe DEVOLVER la cuenta existente (200) para
    volver a entrar — antes respondía 409 y el usuario quedaba bloqueado."""
    user = User(nombre="Ana", email="ana@example.co", ciudad="Pereira")
    db_session.add(user)
    db_session.commit()

    respuesta = client.post(
        "/api/users",
        json={"nombre": "Otro Nombre", "email": "ana@example.co"},
    )

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["id"] == user.id
    # Entrar no edita el perfil: conserva el nombre original.
    assert cuerpo["nombre"] == "Ana"
    # Y no creó una fila nueva.
    assert db_session.query(User).count() == 1


def test_el_email_se_normaliza_a_minusculas(client, db_session):
    creacion = client.post("/api/users", json={"nombre": "Ana", "email": "Ana@Example.co"})
    assert creacion.status_code == 201
    assert creacion.json()["email"] == "ana@example.co"

    # Reingresar con otra capitalización entra a la misma cuenta.
    reingreso = client.post("/api/users", json={"nombre": "Ana", "email": "ANA@example.CO"})
    assert reingreso.status_code == 200
    assert reingreso.json()["id"] == creacion.json()["id"]


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
