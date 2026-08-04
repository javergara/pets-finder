"""Mensajería adoptante<->refugio (feature 11-chat, ADR 0004).

Dos endpoints, mismo hilo:
- `GET /api/matches/{match_id}/thread`: historial completo (REST, un solo
  request). Sirve a ambos lados del match -- el hilo pertenece al match, no
  a un rol, mismo criterio que el propio `Match` (ver `routers/matches.py` y
  `routers/shelters.py`, que exponen el mismo `Match` desde dos ángulos).
- `WS /ws/matches/{match_id}/thread`: canal de mensajes nuevos desde el
  momento de conexión -- NO reenvía historial, el frontend ya lo cargó por
  el `GET` anterior.

Identidad por query param en el WS (`rol`/`user_id`/`shelter_id`): no hay
headers/cookies de sesión en este proyecto y los navegadores no permiten
headers custom en el handshake WebSocket. `autor_tipo` de cada mensaje se
estampa siempre desde el `rol` de la conexión, nunca desde el payload del
cliente -- identidad siempre del path/query, nunca del body, mismo criterio
del resto de la API (p. ej. `shelter_id` en `shelters.py`).
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.chat import Message, Thread
from ..models.match import Match
from ..schemas.chat import MessageOut, ThreadConMensajesOut, ThreadOut
from ..services.chat import obtener_o_crear_thread
from ..services.chat_manager import connection_manager
from ..services.db import get_session

router = APIRouter(tags=["chat"])


@router.get("/api/matches/{match_id}/thread", response_model=ThreadConMensajesOut)
def obtener_thread(match_id: int, session: Session = Depends(get_session)) -> ThreadConMensajesOut:
    """Historial completo de un hilo, creándolo (con su mensaje de sistema)
    si es la primera vez que se pide -- ver
    `services/chat.py::obtener_o_crear_thread` (idempotente)."""
    match = session.get(Match, match_id)
    if match is None:
        raise HTTPException(404, f"El match {match_id} no existe")

    thread = obtener_o_crear_thread(session, match)
    mensajes = (
        session.execute(
            select(Message).where(Message.thread_id == thread.id).order_by(Message.creado_en.asc())
        )
        .scalars()
        .all()
    )
    return ThreadConMensajesOut(
        thread=ThreadOut.model_validate(thread),
        mensajes=[MessageOut.model_validate(mensaje) for mensaje in mensajes],
    )


def _sesion_factory(websocket: WebSocket):
    """Devuelve la factory de sesión que hay que usar para abrir sesiones
    cortas dentro del handler del WS -- respeta
    `app.dependency_overrides[get_session]` (con el que `tests/api/conftest.py`
    inyecta la sesión SQLite en memoria del test) en vez de ir directo a
    `SessionLocal`, que apuntaría siempre a la DB de producción/dev
    (`data/app.db`) sin importar qué sesión esté usando el test.

    Necesario porque un endpoint WS no puede usar `Depends(get_session)`
    para abrir una sesión nueva por cada mensaje entrante: `Depends` solo se
    resuelve una vez, al conectar, y viviría toda la conexión -- exactamente
    el patrón "sesión por conexión" que el plan descarta a favor de "sesión
    por mensaje" (ver docstring de `services/chat.py` y el plan en
    `progress/current.md`)."""
    return websocket.app.dependency_overrides.get(get_session, get_session)


def _validar_ownership(rol: str, user_id: int | None, shelter_id: int | None, match: Match) -> bool:
    if rol == "adoptante":
        return user_id is not None and user_id == match.user_id
    if rol == "refugio":
        return shelter_id is not None and shelter_id == match.shelter_id
    return False


@router.websocket("/ws/matches/{match_id}/thread")
async def ws_thread(
    websocket: WebSocket,
    match_id: int,
    rol: str,
    user_id: int | None = None,
    shelter_id: int | None = None,
) -> None:
    """Nota de diseño sobre `accept()`: NO se llama `websocket.accept()`
    manualmente en el router -- `connection_manager.conectar()` ya lo hace
    (ver su docstring), y llamar `accept()` dos veces sobre el mismo socket
    revienta con un `AssertionError` en Starlette. Mientras el match/ownership
    no se validaron, el socket se mantiene sin aceptar: `websocket.close(...)`
    sobre un socket todavía no aceptado es un rechazo de handshake válido a
    nivel ASGI (equivalente a un 404/403 antes de "contestar"), así que no
    hace falta aceptar primero para poder cerrar con `code=1008`.
    """
    factory = _sesion_factory(websocket)

    sesion_generador = factory()
    session = next(sesion_generador)
    try:
        match = session.get(Match, match_id)
        if match is None or not _validar_ownership(rol, user_id, shelter_id, match):
            await websocket.close(code=1008)
            return
        obtener_o_crear_thread(session, match)
    finally:
        try:
            next(sesion_generador)
        except StopIteration:
            pass

    await connection_manager.conectar(match_id, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            texto = (data or {}).get("texto") or ""
            if not texto:
                continue

            mensaje_generador = factory()
            mensaje_session = next(mensaje_generador)
            try:
                thread = mensaje_session.execute(
                    select(Thread).where(Thread.match_id == match_id)
                ).scalar_one()
                ahora = datetime.now(timezone.utc)
                mensaje = Message(thread_id=thread.id, autor_tipo=rol, texto=texto, creado_en=ahora)
                mensaje_session.add(mensaje)
                thread.ultimo_mensaje_en = ahora
                mensaje_session.commit()
                mensaje_session.refresh(mensaje)
                payload = MessageOut.model_validate(mensaje).model_dump(mode="json")
            finally:
                try:
                    next(mensaje_generador)
                except StopIteration:
                    pass

            await connection_manager.difundir(match_id, payload)
    except WebSocketDisconnect:
        pass
    finally:
        connection_manager.desconectar(match_id, websocket)
