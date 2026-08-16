"""Swipes del deck de descubrimiento (AD-03): `POST /api/swipes`.

⚠️ **`user_id` es el ADOPTANTE** que mira el deck, no quien publicó la mascota
(`Pet.user_id`). Las dos son FK a `users.id`, así que un cruce no lo detecta
ninguna base de datos: ver el docstring de `models/swipe.py`.

Desde **AD-05** el swipe-derecha hace dos cosas: registra el gesto y crea la
**solicitud de adopción** (`matches`). Es un solo endpoint porque en el producto
es un solo gesto — pedir la mascota *es* deslizar a la derecha— y porque partirlo
en dos peticiones dejaría swipes sin solicitud en cuanto la segunda fallara. Lo
que el publicador hace después con esa solicitud vive en `routers/solicitudes.py`.
"""

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..models.match import Match
from ..models.pet import Pet
from ..models.swipe import Swipe
from ..models.user import User
from ..schemas.pet import PetResumenOut
from ..schemas.solicitud import SolicitudResumenOut
from ..schemas.swipe import SwipeIn, SwipeOut
from ..services.db import get_session
from ..services.solicitudes import calcular_etiqueta_solicitud

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


def _solicitud_existente(session: Session, user_id: int, pet_id: int) -> Match | None:
    """La solicitud que esa persona ya tiene sobre esa mascota, si la hay.

    Gemela de `_swipe_existente` y por el mismo motivo: `uq_match_user_pet` es el
    segundo `UniqueConstraint` que puede rechazar el insert, y hace falta poder
    reconsultar después del `rollback()`.
    """
    return session.execute(
        select(Match).where(Match.user_id == user_id, Match.pet_id == pet_id)
    ).scalar_one_or_none()


def _texto_o_none(valor: str | None) -> str | None:
    """`""` y `"   "` son "no escribió nada", no un texto.

    Sin esto, el detalle de la solicitud le pintaría al publicador una cita vacía
    atribuida al adoptante, indistinguible de un mensaje que se perdió por el
    camino. La columna es `nullable`: que lo diga el dato.
    """
    limpio = (valor or "").strip()
    return limpio or None


def _nueva_solicitud(payload: SwipeIn) -> Match:
    """La solicitud que nace del "me interesa", sin tocar la sesión.

    `estado` y `creado_en` los pone el modelo (`solicitado` y el ahora en UTC):
    repetirlos aquí sería una segunda fuente de verdad para el estado inicial.
    """
    return Match(
        # ⚠️ El ADOPTANTE, igual que en el swipe (ver `models/match.py`).
        user_id=payload.user_id,
        pet_id=payload.pet_id,
        mensaje=_texto_o_none(payload.mensaje),
        telefono_contacto=_texto_o_none(payload.telefono_contacto),
    )


def _resumen_solicitud(match: Match | None, pet: Pet) -> SolicitudResumenOut | None:
    if match is None:
        return None
    return SolicitudResumenOut(
        id=match.id,
        estado=match.estado,
        etiqueta=calcular_etiqueta_solicitud(match.estado, match.creado_en),
        creado_en=match.creado_en,
        pet=PetResumenOut.model_validate(pet),
    )


def _swipe_out(swipe: Swipe, match: Match | None, pet: Pet) -> SwipeOut:
    """La respuesta completa: el swipe del ORM más la solicitud armada a mano.

    `solicitud` se asigna después del `model_validate` porque `Swipe` no tiene
    ese atributo —no hay `relationship()` entre `swipes` y `matches`, a
    propósito— y `from_attributes` no puede inventarlo.
    """
    salida = SwipeOut.model_validate(swipe)
    salida.solicitud = _resumen_solicitud(match, pet)
    return salida


def _solicitud_del_swipe_previo(session: Session, swipe: Swipe, payload: SwipeIn) -> Match | None:
    """La solicitud de un swipe que ya estaba, creándola solo si falta.

    Dos casos, los dos reales:

    - **El gesto repetido** (el doble-tap del dedo en un móvil): devuelve la
      solicitud que ya había, sin pisarle el mensaje. Reenviar el gesto no puede
      borrarle a quien publica el texto que estaba leyendo.
    - **El swipe huérfano**: las filas que dejó AD-03, cuando el "me interesa"
      todavía no creaba nada. Sin esto, esas personas seguirían swipeando a la
      derecha sin que su solicitud llegue jamás a nadie.

    Manda la dirección **guardada**, no la del payload: el repetido no cambia el
    `pass` a `like` (decisión de AD-03), así que tampoco puede crear la solicitud
    por la puerta de atrás.
    """
    if swipe.direccion != "like":
        return None

    solicitud = _solicitud_existente(session, payload.user_id, payload.pet_id)
    if solicitud is not None:
        return solicitud

    solicitud = _nueva_solicitud(payload)
    session.add(solicitud)
    try:
        session.commit()
    except IntegrityError:
        # Otro request creó la solicitud entre el select de arriba y este commit:
        # `uq_match_user_pet` lo rechazó. Misma receta que el swipe.
        session.rollback()
        solicitud = _solicitud_existente(session, payload.user_id, payload.pet_id)
        if solicitud is None:
            raise
        return solicitud
    session.refresh(solicitud)
    return solicitud


@router.post("", response_model=SwipeOut, status_code=status.HTTP_201_CREATED)
def registrar_swipe(
    payload: SwipeIn, response: Response, session: Session = Depends(get_session)
) -> SwipeOut:
    """Registra la decisión del adoptante sobre una mascota del deck.

    Un **`like` crea además la solicitud de adopción** (`matches`) copiando el
    `mensaje` y el `telefono_contacto` del payload; un `pass` no crea nada y
    devuelve `solicitud: null`.

    ⚠️ **Las dos filas viajan en el MISMO `commit()`.** Con dos commits, un fallo
    en el segundo dejaría un swipe sin solicitud: el deck no volvería a mostrar
    esa mascota (ya está swipeada) y la familia quedaría esperando una respuesta
    que nadie va a ver nunca. Esa media escritura es invisible desde la UI, que es
    lo que la hace peligrosa.

    Responde **201** la primera vez y **200 el repetido**, con la misma fila y
    sin crear una segunda (patrón de `entrar_o_registrar`, no un 409): un
    doble-tap del gesto en un móvil es un accidente del dedo, no un error del
    usuario, y duplicaría además la solicitud —quien publica vería a la misma
    familia dos veces en su panel—. El repetido **no cambia la dirección** ya
    guardada ni el mensaje ya enviado: pasar de "ahora no" a "me interesa" es una
    decisión de producto (AD-07), no un efecto colateral de repetir el gesto.

    La idempotencia necesita **las dos cosas**: el select previo, que da la
    respuesta limpia en el caso normal, y el `IntegrityError` atrapado con
    `rollback()`, que es la garantía real. En serverless (ADR 0007) dos requests
    del mismo dedo corren de verdad a la vez y los dos pueden ver el select
    vacío; ahí solo el `UniqueConstraint` decide, y sin atraparlo el usuario
    recibiría un 500 con traza. Desde AD-05 hay **dos** constraints que pueden
    saltar —`uq_swipe_user_pet` y `uq_match_user_pet`— y el `except` cubre a los
    dos: la respuesta idempotente se rearma reconsultando las dos tablas.

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
        return _swipe_out(existente, _solicitud_del_swipe_previo(session, existente, payload), pet)

    # `mensaje` y `telefono_contacto` no son columnas de `swipes`: van en la
    # solicitud de al lado (ver `SwipeIn`).
    swipe = Swipe(
        user_id=payload.user_id,
        pet_id=payload.pet_id,
        direccion=payload.direccion,
    )
    session.add(swipe)
    solicitud = _nueva_solicitud(payload) if payload.direccion == "like" else None
    if solicitud is not None:
        session.add(solicitud)
    try:
        # Un solo commit para las dos filas: ver el aviso del docstring.
        session.commit()
    except IntegrityError:
        # Carrera: otro request registró el mismo (adoptante, mascota) entre el
        # select de arriba y este commit. Lo rechazó `uq_swipe_user_pet` o
        # `uq_match_user_pet` —da igual cuál—: el rollback deshace las dos filas
        # y se responde con lo que dejó el request que ganó.
        session.rollback()
        existente = _swipe_existente(session, payload.user_id, payload.pet_id)
        if existente is not None:
            response.status_code = status.HTTP_200_OK
            return _swipe_out(
                existente, _solicitud_del_swipe_previo(session, existente, payload), pet
            )
        raise
    session.refresh(swipe)
    if solicitud is not None:
        session.refresh(solicitud)

    return _swipe_out(swipe, solicitud, pet)
