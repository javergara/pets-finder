from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.home_profile import HomeProfile
from ..models.match import Match
from ..models.pet import Pet
from ..schemas.match import MatchPetSummary, MatchWithPetOut
from ..schemas.pet import AfinidadOut
from ..services.affinity import calcular_afinidad
from ..services.db import get_session

router = APIRouter(prefix="/api/matches", tags=["matches"])


@router.get("", response_model=list[MatchWithPetOut])
def listar_matches(user_id: int, session: Session = Depends(get_session)) -> list[MatchWithPetOut]:
    home = session.get(HomeProfile, user_id)
    if home is None:
        raise HTTPException(404, f"El usuario {user_id} no tiene HomeProfile (cuestionario)")

    matches = (
        session.execute(
            select(Match).where(Match.user_id == user_id).order_by(Match.creado_en.desc())
        )
        .scalars()
        .all()
    )

    resultado = []
    for match in matches:
        pet = session.get(Pet, match.pet_id)
        afinidad = calcular_afinidad(pet, home)
        resultado.append(
            MatchWithPetOut(
                id=match.id,
                estado=match.estado,
                creado_en=match.creado_en,
                pet=MatchPetSummary.model_validate(pet),
                afinidad=AfinidadOut(
                    score=afinidad.score,
                    explicacion=afinidad.explicacion,
                    incompatible=afinidad.incompatible,
                ),
            )
        )
    return resultado
