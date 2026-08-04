"""Creación lazy e idempotente del `Thread` de un match (ADR 0004).

`services/matching.py::registrar_swipe` sigue siendo el único lugar donde se crea
un `Match` -- este servicio no se llama desde ahí. Se llama tanto desde el
endpoint REST (`GET /api/matches/{match_id}/thread`) como desde el handler del
WebSocket (`WS /ws/matches/{match_id}/thread`), en `routers/chat.py`.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.chat import Message, Thread
from ..models.match import Match
from ..models.pet import Pet
from ..models.shelter import Shelter


def obtener_o_crear_thread(session: Session, match: Match) -> Thread:
    """Devuelve el `Thread` del match, creándolo (con su mensaje de sistema)
    si es la primera vez. Idempotente: llamadas siguientes sobre el mismo
    match no duplican el mensaje de sistema."""
    thread = session.execute(select(Thread).where(Thread.match_id == match.id)).scalar_one_or_none()
    if thread is not None:
        return thread

    pet = session.get(Pet, match.pet_id)
    shelter = session.get(Shelter, match.shelter_id)

    thread = Thread(match_id=match.id)
    session.add(thread)
    session.flush()  # asigna thread.id, necesario para el Message

    mensaje_sistema = Message(
        thread_id=thread.id,
        autor_tipo="sistema",
        texto=(
            f"Se abrió esta conversación porque hiciste match con {pet.nombre} "
            f"de {shelter.nombre}. Recuerden coordinar la visita presencial "
            "antes de la entrega."
        ),
    )
    session.add(mensaje_sistema)
    session.commit()
    session.refresh(thread)
    return thread
