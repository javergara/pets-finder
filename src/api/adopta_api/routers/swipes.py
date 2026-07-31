from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.match import Match
from ..models.pet import Pet
from ..schemas.swipe import MatchOut, SwipeIn, SwipeOut
from ..services.db import get_session
from ..services.matching import registrar_swipe

router = APIRouter(prefix="/api/swipes", tags=["swipes"])


@router.post("", response_model=SwipeOut, status_code=201)
def crear_swipe(payload: SwipeIn, session: Session = Depends(get_session)) -> SwipeOut:
    pet = session.get(Pet, payload.pet_id)
    if pet is None:
        raise HTTPException(404, "Mascota no encontrada")

    swipe = registrar_swipe(session, payload.user_id, payload.pet_id, payload.direccion)

    match_out = None
    if payload.direccion == "like":
        match = (
            session.execute(
                select(Match)
                .where(Match.user_id == payload.user_id, Match.pet_id == payload.pet_id)
                .order_by(Match.id.desc())
            )
            .scalars()
            .first()
        )
        if match is not None:
            match_out = MatchOut.model_validate(match)

    swipe_out = SwipeOut.model_validate(swipe)
    swipe_out.match = match_out
    return swipe_out
