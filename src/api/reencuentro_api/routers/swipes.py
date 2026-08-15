"""Swipes del deck de descubrimiento (AD-03): `POST /api/swipes`.

⚠️ **`user_id` es el ADOPTANTE** que mira el deck, no quien publicó la mascota
(`Pet.user_id`). Las dos son FK a `users.id`, así que un cruce no lo detecta
ninguna base de datos: ver el docstring de `models/swipe.py`.
"""

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..models.pet import Pet
from ..models.swipe import Swipe
from ..models.user import User
from ..schemas.swipe import SwipeIn, SwipeOut
from ..services.db import get_session

router = APIRouter(prefix="/api/swipes", tags=["swipes"])

MASCOTA_YA_ADOPTADA = "Esta mascota ya encontró hogar"


def _swipe_existente(session: Session, user_id: int, pet_id: int) -> Swipe | None:
    """El swipe que esa persona ya hizo sobre esa mascota, si lo hay.

    Lo usan las dos mitades del 200 idempotente: el select previo y el de
    después del `rollback()`. Está aquí, a nivel de módulo, para que el test de
    la carrera pueda dejarlo ciego con un monkeypatch (patrón de
    `_mascota_del_reporte` en `routers/pets.py`).
    """
    return session.execute(
        select(Swipe).where(Swipe.user_id == user_id, Swipe.pet_id == pet_id)
    ).scalar_one_or_none()


@router.post("", response_model=SwipeOut, status_code=status.HTTP_201_CREATED)
def registrar_swipe(
    payload: SwipeIn, response: Response, session: Session = Depends(get_session)
) -> SwipeOut:
    """Registra la decisión del adoptante sobre una mascota del deck.

    Responde **201** la primera vez y **200 el repetido**, con la misma fila y
    sin crear una segunda (patrón de `entrar_o_registrar`, no un 409): un
    doble-tap del gesto en un móvil es un accidente del dedo, no un error del
    usuario, y en AD-05 duplicaría además la solicitud. El repetido **no cambia
    la dirección** ya guardada: pasar de "ahora no" a "me interesa" es una
    decisión de producto (AD-05/AD-07), no un efecto colateral de repetir el
    gesto.

    La idempotencia necesita **las dos cosas**: el select previo, que da la
    respuesta limpia en el caso normal, y el `IntegrityError` atrapado con
    `rollback()`, que es la garantía real. En serverless (ADR 0007) dos requests
    del mismo dedo corren de verdad a la vez y los dos pueden ver el select
    vacío; ahí solo el `UniqueConstraint` decide, y sin atraparlo el usuario
    recibiría un 500 con traza.

    ⚠️ Los 404 salen de comprobaciones **en el código**, no de las FK: SQLite no
    las fuerza (gotcha de AD-02 paso 3), así que confiar en la base dejaría los
    tests en verde y produciría un 500 recién en Postgres. Se valida que las dos
    partes existan antes de mirar el estado de la mascota: "no existe" es una
    respuesta más precisa que "ya encontró hogar" para un id inventado.

    El **409** es solo para `adoptado`: `en_proceso` sigue aceptando swipes
    porque una adopción puede no cuajar (el `PUT` devuelve la mascota a
    `disponible`) y el interés de otra familia es lo que evita empezar de cero.
    El deck ya no muestra ninguna de las dos, pero una carta vieja en pantalla
    sí puede llegar hasta aquí.
    """
    pet = session.get(Pet, payload.pet_id)
    if pet is None:
        raise HTTPException(404, f"La mascota {payload.pet_id} no existe")
    if session.get(User, payload.user_id) is None:
        raise HTTPException(404, f"El usuario {payload.user_id} no existe")
    if pet.estado == "adoptado":
        raise HTTPException(409, MASCOTA_YA_ADOPTADA)

    existente = _swipe_existente(session, payload.user_id, payload.pet_id)
    if existente is not None:
        response.status_code = status.HTTP_200_OK
        return SwipeOut.model_validate(existente)

    # `mensaje` y `telefono_contacto` del payload se descartan a propósito: no
    # son columnas de `swipes`, viven en la solicitud de AD-05 (ver `SwipeIn`).
    swipe = Swipe(
        user_id=payload.user_id,
        pet_id=payload.pet_id,
        direccion=payload.direccion,
    )
    session.add(swipe)
    try:
        session.commit()
    except IntegrityError:
        # Carrera: otro request registró el mismo (adoptante, mascota) entre el
        # select de arriba y este commit. `uq_swipe_user_pet` lo rechazó.
        session.rollback()
        existente = _swipe_existente(session, payload.user_id, payload.pet_id)
        if existente is not None:
            response.status_code = status.HTTP_200_OK
            return SwipeOut.model_validate(existente)
        raise
    session.refresh(swipe)

    return SwipeOut.model_validate(swipe)
