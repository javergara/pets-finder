"""Tests de integración HTTP + WebSocket de `routers/chat.py` (patrón
`test_shelters.py`, fixture `client`). Cobertura del `acceptance` de
`11-chat` correspondiente al paso 3: creación lazy del hilo vía REST, envío/
recepción en tiempo real vía WS, aislamiento entre hilos, y cierre por
ownership inválido.
"""

import queue

import pytest
from fastapi import WebSocketDisconnect

from adopta_api.models.home_profile import HomeProfile
from adopta_api.models.match import Match
from adopta_api.models.pet import Pet
from adopta_api.models.shelter import Shelter
from adopta_api.models.user import User


def _crear_shelter(db_session, **overrides):
    defaults = dict(nombre="Refugio Huellas", ciudad="Bogotá", tiempo_respuesta_horas=12)
    defaults.update(overrides)
    shelter = Shelter(**defaults)
    db_session.add(shelter)
    db_session.flush()
    return shelter


def _crear_pet(db_session, shelter, **overrides):
    defaults = dict(
        shelter_id=shelter.id,
        nombre="Firulais",
        especie="perro",
        raza="Criollo",
        sexo="macho",
        edad_meses=24,
        tamano="mediano",
        energia="media",
        historia="Un perro encantador.",
        tags=[],
        fotos=["/media/pet_1.jpg"],
        apto_ninos=True,
        apto_perros=True,
        apto_gatos=True,
    )
    defaults.update(overrides)
    pet = Pet(**defaults)
    db_session.add(pet)
    db_session.flush()
    return pet


def _crear_adoptante_con_home(db_session, nombre="Ana", email="ana@example.co"):
    user = User(nombre=nombre, email=email, ciudad="Bogotá", bio="Amo perros.")
    db_session.add(user)
    db_session.flush()

    home = HomeProfile(
        user_id=user.id,
        vivienda="casa",
        espacio_exterior="patio",
        personas_en_casa=2,
        tiene_ninos=False,
        tiene_otros_perros=False,
        tiene_otros_gatos=False,
        horas_fuera_dia=4,
        experiencia_previa="algo",
        presupuesto_mensual_cop=150_000,
        preferencia_especies=[],
        preferencia_tamanos=[],
        preferencia_energia="media",
    )
    db_session.add(home)
    db_session.flush()
    return user, home


def _crear_match(db_session, adoptante, pet, shelter, estado="solicitado"):
    match = Match(user_id=adoptante.id, pet_id=pet.id, shelter_id=shelter.id, estado=estado)
    db_session.add(match)
    db_session.commit()
    db_session.refresh(match)
    return match


def _crear_escenario(db_session, nombre_pet="Luna", nombre_shelter="Refugio Patitas"):
    shelter = _crear_shelter(db_session, nombre=nombre_shelter)
    pet = _crear_pet(db_session, shelter, nombre=nombre_pet)
    adoptante, _home = _crear_adoptante_con_home(db_session, nombre="Ana", email="ana@example.co")
    match = _crear_match(db_session, adoptante, pet, shelter)
    return shelter, pet, adoptante, match


def _ws_url(match_id: int, rol: str, participant_id: int) -> str:
    campo = "user_id" if rol == "adoptante" else "shelter_id"
    return f"/ws/matches/{match_id}/thread?rol={rol}&{campo}={participant_id}"


# --- GET /api/matches/{match_id}/thread -------------------------------------


def test_obtener_thread_primera_vez_crea_hilo_y_mensaje_sistema(client, db_session):
    _shelter, _pet, _adoptante, match = _crear_escenario(
        db_session, nombre_pet="Luna", nombre_shelter="Refugio Patitas"
    )

    response = client.get(f"/api/matches/{match.id}/thread")

    assert response.status_code == 200
    body = response.json()
    assert body["thread"]["match_id"] == match.id
    assert len(body["mensajes"]) == 1
    assert body["mensajes"][0]["autor_tipo"] == "sistema"
    assert "Luna" in body["mensajes"][0]["texto"]
    assert "Refugio Patitas" in body["mensajes"][0]["texto"]


def test_obtener_thread_segunda_llamada_no_duplica(client, db_session):
    _shelter, _pet, _adoptante, match = _crear_escenario(db_session)

    primera = client.get(f"/api/matches/{match.id}/thread").json()
    segunda = client.get(f"/api/matches/{match.id}/thread").json()

    assert primera["thread"]["id"] == segunda["thread"]["id"]
    assert len(segunda["mensajes"]) == 1


def test_obtener_thread_404_match_inexistente(client, db_session):
    response = client.get("/api/matches/9999/thread")

    assert response.status_code == 404
    assert "9999" in response.json()["detail"]


# --- WS /ws/matches/{match_id}/thread ---------------------------------------


def test_ws_mensaje_se_persiste_y_llega_al_otro_lado(client, db_session):
    shelter, _pet, adoptante, match = _crear_escenario(db_session)

    with client.websocket_connect(_ws_url(match.id, "adoptante", adoptante.id)) as ws_adoptante:
        with client.websocket_connect(_ws_url(match.id, "refugio", shelter.id)) as ws_refugio:
            ws_adoptante.send_json({"texto": "hola, ¿puedo visitar mañana?"})

            recibido_refugio = ws_refugio.receive_json()
            assert recibido_refugio["autor_tipo"] == "adoptante"
            assert recibido_refugio["texto"] == "hola, ¿puedo visitar mañana?"

            # El remitente también recibe su propio mensaje vía difusión (mismo
            # canal para todas las conexiones activas del hilo, confirmación
            # implícita de entrega).
            recibido_propio = ws_adoptante.receive_json()
            assert recibido_propio["texto"] == "hola, ¿puedo visitar mañana?"

    from adopta_api.models.chat import Message, Thread

    thread = db_session.query(Thread).filter(Thread.match_id == match.id).one()
    mensajes = db_session.query(Message).filter(Message.thread_id == thread.id).all()
    # 1 mensaje de sistema (creado por la conexión, que llama obtener_o_crear_thread)
    # + 1 mensaje del adoptante.
    assert len(mensajes) == 2
    mensaje_adoptante = [m for m in mensajes if m.autor_tipo == "adoptante"][0]
    assert mensaje_adoptante.texto == "hola, ¿puedo visitar mañana?"
    assert thread.ultimo_mensaje_en == mensaje_adoptante.creado_en


def test_ws_aislamiento_entre_hilos_de_matches_distintos(client, db_session):
    shelter_a = _crear_shelter(db_session, nombre="Refugio A")
    pet_a = _crear_pet(db_session, shelter_a, nombre="Rocky")
    adoptante, _home = _crear_adoptante_con_home(db_session, nombre="Ana", email="ana@example.co")
    match_a = _crear_match(db_session, adoptante, pet_a, shelter_a)

    shelter_b = _crear_shelter(db_session, nombre="Refugio B")
    pet_b = _crear_pet(db_session, shelter_b, nombre="Nala")
    match_b = _crear_match(db_session, adoptante, pet_b, shelter_b)

    with client.websocket_connect(_ws_url(match_a.id, "adoptante", adoptante.id)) as ws_a:
        with client.websocket_connect(_ws_url(match_b.id, "adoptante", adoptante.id)) as ws_b:
            ws_a.send_json({"texto": "solo para el hilo A"})

            # Sincroniza contra la propia difusión del hilo A (el remitente
            # recibe su propio mensaje) antes de verificar que el hilo B no
            # recibió nada -- el ConnectionManager solo difunde a conexiones
            # del mismo match_id, así que no hay condición de carrera real,
            # pero esto además prueba que el servidor terminó de procesar el
            # mensaje antes de la aserción.
            recibido_a = ws_a.receive_json()
            assert recibido_a["texto"] == "solo para el hilo A"

            with pytest.raises(queue.Empty):
                ws_b._send_queue.get(timeout=0.2)


def test_ws_ownership_invalida_cierra_conexion(client, db_session):
    _shelter, _pet, adoptante, match = _crear_escenario(db_session)
    otro_user_id = adoptante.id + 1

    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client.websocket_connect(_ws_url(match.id, "adoptante", otro_user_id)):
            pass
    assert exc_info.value.code == 1008


def test_ws_ownership_invalida_shelter_cierra_conexion(client, db_session):
    shelter, _pet, _adoptante, match = _crear_escenario(db_session)
    otro_shelter_id = shelter.id + 1

    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client.websocket_connect(_ws_url(match.id, "refugio", otro_shelter_id)):
            pass
    assert exc_info.value.code == 1008


def test_ws_match_inexistente_cierra_conexion(client, db_session):
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client.websocket_connect(_ws_url(9999, "adoptante", 1)):
            pass
    assert exc_info.value.code == 1008
