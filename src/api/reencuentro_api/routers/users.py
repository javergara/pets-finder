from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.user import User
from ..schemas.user import UserIn, UserOut
from ..services.db import get_session

router = APIRouter(prefix="/api/users", tags=["users"])


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def registrar_usuario(payload: UserIn, session: Session = Depends(get_session)) -> UserOut:
    """Registro liviano de quien reporta, sin contraseña (ADR 0001/0005).

    En una emergencia cada paso extra cuesta reportes: solo nombre, email y ciudad.
    El id devuelto se guarda en localStorage y liga los reportes a su autor.
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

    return UserOut.model_validate(user)


@router.get("/{user_id}", response_model=UserOut)
def obtener_perfil(user_id: int, session: Session = Depends(get_session)) -> UserOut:
    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(404, f"El usuario {user_id} no existe")

    return UserOut.model_validate(user)
