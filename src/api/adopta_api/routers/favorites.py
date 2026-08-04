"""Favoritos (feature 13-favorites): guardar mascotas sin hacer swipe definitivo,
para revisar después.

Independiente de `Swipe` a propósito: marcar/desmarcar un favorito nunca inserta
una fila en `swipes`, nunca pasa por `services/matching.py` ni crea un `Match`, y
nunca excluye la mascota del deck (`routers/pets.py::listar_mascotas` solo filtra
por `Swipe.pet_id`; ver docstring de `models/favorite.py`). Mismo criterio de
nesting que `routers/sponsorships.py`: router propio bajo `/api`, registrado en
`main.py` junto a los demás.
"""

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.favorite import Favorite
from ..models.pet import Pet
from ..models.user import User
from ..schemas.favorite import FavoriteIn
from ..schemas.pet import PetOut
from ..services.db import get_session
from .pets import _pet_out

router = APIRouter(prefix="/api", tags=["favorites"])


@router.post("/users/{user_id}/favorites", response_model=PetOut)
def marcar_favorito(
    user_id: int, payload: FavoriteIn, response: Response, session: Session = Depends(get_session)
) -> PetOut:
    """Idempotente: si el favorito ya existía, 200 sin duplicar la fila; si es
    nuevo, 201. Sin `UniqueConstraint` de esquema -- la idempotencia se garantiza
    aquí con un `select` previo (mismo criterio que `guardar_home_profile`)."""
    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(404, f"El usuario {user_id} no existe")

    pet = session.get(Pet, payload.pet_id)
    if pet is None:
        raise HTTPException(404, f"La mascota {payload.pet_id} no existe")

    favorito = session.execute(
        select(Favorite).where(Favorite.user_id == user_id, Favorite.pet_id == payload.pet_id)
    ).scalar_one_or_none()

    if favorito is None:
        favorito = Favorite(user_id=user_id, pet_id=payload.pet_id)
        session.add(favorito)
        session.commit()
        response.status_code = status.HTTP_201_CREATED
    else:
        response.status_code = status.HTTP_200_OK

    return _pet_out(pet, home=None, favoritos={payload.pet_id})


@router.delete("/users/{user_id}/favorites/{pet_id}", status_code=status.HTTP_204_NO_CONTENT)
def desmarcar_favorito(user_id: int, pet_id: int, session: Session = Depends(get_session)) -> None:
    """Idempotente: 204 exista o no la fila -- nunca 404 por "no estaba marcada".

    No valida que `user_id`/`pet_id` existan como entidades: es una operación de
    "asegurar que no esté marcado", que tiene sentido pedir aunque el estado ya
    sea el deseado (decisión documentada, no un olvido).
    """
    favorito = session.execute(
        select(Favorite).where(Favorite.user_id == user_id, Favorite.pet_id == pet_id)
    ).scalar_one_or_none()

    if favorito is not None:
        session.delete(favorito)
        session.commit()


@router.get("/users/{user_id}/favorites", response_model=list[PetOut])
def listar_favoritos(user_id: int, session: Session = Depends(get_session)) -> list[PetOut]:
    """Lista vacía (200, no 404) si el usuario no tiene favoritos. No exige
    `HomeProfile` -- favoritos no depende de `home` por decisión de producto."""
    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(404, f"El usuario {user_id} no existe")

    pet_ids = set(
        session.execute(select(Favorite.pet_id).where(Favorite.user_id == user_id)).scalars()
    )
    if not pet_ids:
        return []

    pets = session.execute(select(Pet).where(Pet.id.in_(pet_ids))).scalars().all()
    return [_pet_out(pet, home=None, favoritos=pet_ids) for pet in pets]
