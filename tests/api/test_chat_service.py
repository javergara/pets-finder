"""Tests de `adopta_api.services.chat` (patrón `test_solicitudes_service.py`,
fixture `db_session`, sin cliente HTTP).

Cobertura del `ConnectionManager` (`services/chat_manager.py`): se prueba aquí
con un mock simple de `WebSocket` (solo necesita `accept`/`send_json` async)
porque `conectar`/`desconectar`/`difundir` no tocan la DB ni dependen de un
WebSocket real. `pytest-asyncio` no está entre las dependencias de dev del
proyecto (`requirements-dev.txt`) y no se agrega solo para esto: los métodos
async del manager se ejercitan con `asyncio.run(...)` dentro de tests
`def` normales, sin necesidad de un plugin nuevo. La cobertura de integración
real end-to-end (handshake HTTP real, cierre por ownership inválido,
aislamiento entre hilos vía conexiones reales) queda para
`tests/api/test_chat.py` en el paso 3, que es donde de verdad se puede
ejercitar el ciclo de vida completo de una conexión.
"""

import asyncio

from adopta_api.models.chat import Message, Thread
from adopta_api.models.home_profile import HomeProfile
from adopta_api.models.match import Match
from adopta_api.models.pet import Pet
from adopta_api.models.shelter import Shelter
from adopta_api.models.user import User
from adopta_api.services.chat import obtener_o_crear_thread
from adopta_api.services.chat_manager import ConnectionManager


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


# --- obtener_o_crear_thread ----------------------------------------------------


def test_obtener_o_crear_thread_primera_vez_crea_thread_y_mensaje_sistema(db_session):
    shelter = _crear_shelter(db_session, nombre="Refugio Patitas")
    pet = _crear_pet(db_session, shelter, nombre="Luna")
    adoptante, _ = _crear_adoptante_con_home(db_session)
    match = _crear_match(db_session, adoptante, pet, shelter)

    thread = obtener_o_crear_thread(db_session, match)

    assert thread.id is not None
    assert thread.match_id == match.id

    mensajes = db_session.query(Message).filter(Message.thread_id == thread.id).all()
    assert len(mensajes) == 1
    assert mensajes[0].autor_tipo == "sistema"
    assert "Luna" in mensajes[0].texto
    assert "Refugio Patitas" in mensajes[0].texto


def test_obtener_o_crear_thread_segunda_llamada_es_idempotente(db_session):
    shelter = _crear_shelter(db_session)
    pet = _crear_pet(db_session, shelter)
    adoptante, _ = _crear_adoptante_con_home(db_session)
    match = _crear_match(db_session, adoptante, pet, shelter)

    thread_1 = obtener_o_crear_thread(db_session, match)
    thread_2 = obtener_o_crear_thread(db_session, match)

    assert thread_1.id == thread_2.id
    assert db_session.query(Thread).filter(Thread.match_id == match.id).count() == 1

    mensajes = db_session.query(Message).filter(Message.thread_id == thread_1.id).all()
    assert len(mensajes) == 1


def test_obtener_o_crear_thread_dos_matches_distintos_tienen_hilos_separados(db_session):
    shelter = _crear_shelter(db_session)
    pet_a = _crear_pet(db_session, shelter, nombre="Rocky")
    pet_b = _crear_pet(db_session, shelter, nombre="Nala")
    adoptante, _ = _crear_adoptante_con_home(db_session)
    match_a = _crear_match(db_session, adoptante, pet_a, shelter)
    match_b = _crear_match(db_session, adoptante, pet_b, shelter)

    thread_a = obtener_o_crear_thread(db_session, match_a)
    thread_b = obtener_o_crear_thread(db_session, match_b)

    assert thread_a.id != thread_b.id


# --- ConnectionManager -----------------------------------------------------------
# Se usa un mock simple (solo `accept`/`send_json` async) en vez de un WebSocket real
# de FastAPI: conectar/desconectar/difundir no tocan la DB ni dependen del protocolo
# real, así que basta con verificar el manejo de la lista en memoria. El ciclo de vida
# de una conexión real (handshake HTTP, cierre por ownership) se cubre en el paso 3.


class _WebSocketFalso:
    def __init__(self, falla_al_enviar: bool = False):
        self.aceptado = False
        self.mensajes_recibidos: list[dict] = []
        self._falla_al_enviar = falla_al_enviar

    async def accept(self):
        self.aceptado = True

    async def send_json(self, payload: dict):
        if self._falla_al_enviar:
            raise RuntimeError("conexión cerrada")
        self.mensajes_recibidos.append(payload)


def test_connection_manager_conectar_acepta_y_registra():
    manager = ConnectionManager()
    ws = _WebSocketFalso()

    asyncio.run(manager.conectar(1, ws))

    assert ws.aceptado is True
    assert ws in manager._conexiones[1]


def test_connection_manager_desconectar_limpia_entrada_vacia():
    manager = ConnectionManager()
    ws = _WebSocketFalso()
    asyncio.run(manager.conectar(1, ws))

    manager.desconectar(1, ws)

    assert 1 not in manager._conexiones


def test_connection_manager_desconectar_match_desconocido_no_lanza():
    manager = ConnectionManager()
    ws = _WebSocketFalso()
    manager.desconectar(999, ws)  # no debe lanzar aunque nunca se conectó


def test_connection_manager_difundir_llega_a_todas_las_conexiones_del_hilo():
    manager = ConnectionManager()
    ws_1 = _WebSocketFalso()
    ws_2 = _WebSocketFalso()

    async def _escenario():
        await manager.conectar(1, ws_1)
        await manager.conectar(1, ws_2)
        await manager.difundir(1, {"texto": "hola"})

    asyncio.run(_escenario())

    assert ws_1.mensajes_recibidos == [{"texto": "hola"}]
    assert ws_2.mensajes_recibidos == [{"texto": "hola"}]


def test_connection_manager_difundir_no_llega_a_otro_hilo():
    manager = ConnectionManager()
    ws_hilo_1 = _WebSocketFalso()
    ws_hilo_2 = _WebSocketFalso()

    async def _escenario():
        await manager.conectar(1, ws_hilo_1)
        await manager.conectar(2, ws_hilo_2)
        await manager.difundir(1, {"texto": "solo para el hilo 1"})

    asyncio.run(_escenario())

    assert ws_hilo_1.mensajes_recibidos == [{"texto": "solo para el hilo 1"}]
    assert ws_hilo_2.mensajes_recibidos == []


def test_connection_manager_difundir_ignora_fallo_de_una_conexion_y_sigue_con_las_demas():
    manager = ConnectionManager()
    ws_rota = _WebSocketFalso(falla_al_enviar=True)
    ws_sana = _WebSocketFalso()

    async def _escenario():
        await manager.conectar(1, ws_rota)
        await manager.conectar(1, ws_sana)
        await manager.difundir(1, {"texto": "hola"})  # no debe lanzar pese a ws_rota

    asyncio.run(_escenario())

    assert ws_sana.mensajes_recibidos == [{"texto": "hola"}]
