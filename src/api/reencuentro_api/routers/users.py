from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.user import User
from ..schemas.user import UserIn, UserOut
from ..services.db import get_session

router = APIRouter(prefix="/api/users", tags=["users"])


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def entrar_o_registrar(
    payload: UserIn, response: Response, session: Session = Depends(get_session)
) -> UserOut:
    """Entrar o crear cuenta con el mismo formulario, sin contraseña (ADR 0001/0005).

    Si el correo ya existe devuelve ESA cuenta (200) en vez de un 409: la sesión
    vive solo en localStorage, así que sin esto un usuario que cambie de
    navegador/dispositivo (o pierda el storage) quedaba bloqueado para siempre
    — su correo "ya existía" y no había forma de volver a entrar (bug real de
    producción). El nombre/ciudad enviados se ignoran para una cuenta existente:
    entrar no edita el perfil.
    """
    email = payload.email.strip().lower()
    existente = session.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if existente is not None:
        response.status_code = status.HTTP_200_OK
        return UserOut.model_validate(existente)

    user = User(
        nombre=payload.nombre,
        email=email,
        ciudad=payload.ciudad,
        barrio=payload.barrio,
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    return UserOut.model_validate(user)


@router.get("/{user_id}", response_model=UserOut)
def obtener_perfil(user_id: int, session: Session = Depends(get_session)) -> UserOut:
    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(404, f"El usuario {user_id} no existe")

    return UserOut.model_validate(user)
