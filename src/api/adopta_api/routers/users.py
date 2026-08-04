from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models.home_profile import HomeProfile
from ..models.match import Match
from ..models.sponsorship import Sponsorship
from ..models.user import User
from ..schemas.user import HomeProfileIn, HomeProfileOut, UserIn, UserMetricsOut, UserOut
from ..services.db import get_session

router = APIRouter(prefix="/api/users", tags=["users"])


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def registrar_usuario(payload: UserIn, session: Session = Depends(get_session)) -> UserOut:
    """Registro liviano de un adoptante nuevo, sin contraseña (ADR 0001/§6 architecture).

    Sin HomeProfile todavía (`home_profile: None`) y sin matches (métricas en cero):
    ambos se crean/actualizan en pasos posteriores del onboarding (cuestionario, swipes).
    """
    existente = session.execute(
        select(User).where(User.email == payload.email)
    ).scalar_one_or_none()
    if existente is not None:
        raise HTTPException(409, f"Ya existe una cuenta con el correo {payload.email}")

    user = User(
        nombre=payload.nombre,
        email=payload.email,
        ciudad=payload.ciudad,
        barrio=payload.barrio,
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    return UserOut(
        id=user.id,
        nombre=user.nombre,
        email=user.email,
        ciudad=user.ciudad,
        barrio=user.barrio,
        avatar_url=user.avatar_url,
        bio=user.bio,
        creado_en=user.creado_en,
        home_profile=None,
        metricas=UserMetricsOut(matches_activos=0, visitas_agendadas=0, apadrinamientos=0),
    )


@router.put("/{user_id}/home-profile", response_model=HomeProfileOut)
def guardar_home_profile(
    user_id: int, payload: HomeProfileIn, session: Session = Depends(get_session)
) -> HomeProfileOut:
    """Upsert real del cuestionario de hogar (crea si no existe, reemplaza si ya existe).

    El mismo endpoint sirve para "completar por primera vez" (paso del onboarding) y
    para "editar desde Mi perfil" — no hay una ruta separada para cada caso. No existe
    un campo `completado_en`: la sola existencia de la fila `HomeProfile` ya es la señal
    de "cuestionario completo" (mismo criterio que ya usa `GET /api/users/{id}`).
    """
    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(404, f"El usuario {user_id} no existe")

    home = session.get(HomeProfile, user_id)
    if home is None:
        home = HomeProfile(user_id=user_id, **payload.model_dump())
        session.add(home)
    else:
        for campo, valor in payload.model_dump().items():
            setattr(home, campo, valor)

    session.commit()
    session.refresh(home)

    return HomeProfileOut.model_validate(home)


@router.get("/{user_id}", response_model=UserOut)
def obtener_perfil(user_id: int, session: Session = Depends(get_session)) -> UserOut:
    """Perfil del adoptante + HomeProfile (si existe) + métricas agregadas.

    Definiciones exactas de las métricas (`Match.estado` tiene 5 valores posibles:
    `solicitado`, `en_revision`, `visita_agendada`, `adoptado`, `cerrado`):
    - `matches_activos` = count de `Match` del usuario con `estado NOT IN
      ('adoptado', 'cerrado')` (incluye `solicitado`, `en_revision`, `visita_agendada`).
    - `visitas_agendadas` = count de `Match` del usuario con `estado == 'visita_agendada'`.
    - `apadrinamientos` = count de `Sponsorship` del usuario con `activo == True`
      (feature `12-sponsorship`).

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

    apadrinamientos = session.execute(
        select(func.count())
        .select_from(Sponsorship)
        .where(Sponsorship.user_id == user_id, Sponsorship.activo.is_(True))
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
            apadrinamientos=apadrinamientos,
        ),
    )
