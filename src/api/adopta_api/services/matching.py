"""Registrar un swipe y, si es 'like', crear el match de inmediato.

Ver docs/decisions/0002-mecanica-match-no-mutuo.md: el match no requiere
ninguna acción del refugio, se crea en el mismo request que el swipe.
"""

from sqlalchemy.orm import Session

from ..models.match import Match
from ..models.pet import Pet
from ..models.swipe import Swipe


def registrar_swipe(session: Session, user_id: int, pet_id: int, direccion: str) -> Swipe:
    swipe = Swipe(user_id=user_id, pet_id=pet_id, direccion=direccion)
    session.add(swipe)

    if direccion == "like":
        pet = session.get(Pet, pet_id)
        match = Match(
            user_id=user_id, pet_id=pet_id, shelter_id=pet.shelter_id, estado="solicitado"
        )
        session.add(match)

    session.commit()
    session.refresh(swipe)
    return swipe
