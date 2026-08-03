from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models.home_profile import HomeProfile
from ..models.match import Match
from ..models.user import User
from ..schemas.user import HomeProfileOut, UserMetricsOut, UserOut
from ..services.db import get_session

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/{user_id}", response_model=UserOut)
def obtener_perfil(user_id: int, session: Session = Depends(get_session)) -> UserOut:
    """Perfil del adoptante + HomeProfile (si existe) + métricas agregadas.

    Definiciones exactas de las métricas (`Match.estado` tiene 5 valores posibles:
    `solicitado`, `en_revision`, `visita_agendada`, `adoptado`, `cerrado`):
    - `matches_activos` = count de `Match` del usuario con `estado NOT IN
      ('adoptado', 'cerrado')` (incluye `solicitado`, `en_revision`, `visita_agendada`).
    - `visitas_agendadas` = count de `Match` del usuario con `estado == 'visita_agendada'`.

    A diferencia de `GET /api/pets`, `home_profile` es `None` (no 404) si el usuario
    todavía no completó el cuestionario de hogar.
    """
    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(404, f"El usuario {user_id} no existe")

    matches_activos = session.execute(
        select(func.count())
        .select_from(Match)
        .where(Match.user_id == user_id, Match.estado.notin_(["adoptado", "cerrado"]))
    ).scalar_one()

    visitas_agendadas = session.execute(
        select(func.count())
        .select_from(Match)
        .where(Match.user_id == user_id, Match.estado == "visita_agendada")
    ).scalar_one()

    home = session.get(HomeProfile, user_id)

    return UserOut(
        id=user.id,
        nombre=user.nombre,
        email=user.email,
        ciudad=user.ciudad,
        barrio=user.barrio,
        avatar_url=user.avatar_url,
        bio=user.bio,
        creado_en=user.creado_en,
        home_profile=HomeProfileOut.model_validate(home) if home is not None else None,
        metricas=UserMetricsOut(
            matches_activos=matches_activos,
            visitas_agendadas=visitas_agendadas,
            apadrinamientos=0,
        ),
    )
