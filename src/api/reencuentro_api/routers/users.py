from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.home_profile import HomeProfile
from ..models.user import User
from ..schemas.user import HomeProfileIn, HomeProfileOut, UserIn, UserOut
from ..services.db import get_session

router = APIRouter(prefix="/api/users", tags=["users"])

# El mismo texto para las dos formas de pedir el hogar ajeno (con perfil y sin
# él): si el mensaje —o el código— cambiara según eso, el 403 sería un oráculo
# para averiguar desde fuera quién completó el cuestionario.
HOGAR_AJENO = "Solo puedes consultar tu propio perfil de hogar"


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


@router.put("/{user_id}/home-profile", response_model=HomeProfileOut)
def guardar_perfil_hogar(
    user_id: int, payload: HomeProfileIn, session: Session = Depends(get_session)
) -> HomeProfileOut:
    """Upsert del cuestionario de hogar: completarlo y reeditarlo son el mismo verbo.

    Responde **200 siempre, nunca 201**, aunque cree la fila. Quien llama es el
    wizard con las respuestas completas y no sabe (ni debe saber) si esa persona
    ya había contestado; un status distinto según el caso lo obligaría a ramificar
    para leer exactamente el mismo cuerpo.

    Reemplazar en vez de insertar no es una optimización: la PK de `home_profiles`
    es `user_id`, así que un segundo `INSERT` sería un `IntegrityError` → 500.

    ⚠️ `preferencia_especies`/`preferencia_tamanos` son columnas JSON **sin
    `MutableList`**: se reasigna la lista completa (que es lo que hace el
    `setattr`), nunca se muta in-place — un `.append` no se persistiría.
    """
    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(404, f"El usuario {user_id} no existe")
    if payload.user_id != user_id:
        raise HTTPException(403, "Solo puedes editar el perfil de hogar de tu cuenta")

    respuestas = payload.model_dump(exclude={"user_id"})
    perfil = session.get(HomeProfile, user_id)
    if perfil is None:
        perfil = HomeProfile(user_id=user_id, **respuestas)
        session.add(perfil)
    else:
        for campo, valor in respuestas.items():
            setattr(perfil, campo, valor)
    session.commit()
    session.refresh(perfil)

    return HomeProfileOut.model_validate(perfil)


@router.get("/{user_id}/home-profile", response_model=HomeProfileOut)
def obtener_perfil_hogar(
    user_id: int, solicitante_id: int, session: Session = Depends(get_session)
) -> HomeProfileOut:
    """El cuestionario propio, para precargar el wizard al reeditarlo.

    ⚠️ **El 403 va antes que cualquier consulta**, incluida la del usuario. Si el
    404-de-perfil se evaluara primero, la respuesta delataría si un tercero
    completó o no su cuestionario (403 = sí, 404 = no) — cuántas personas viven en
    su casa, si hay niños, cuánto puede gastar al mes. Hay **dos** tests, con
    perfil y sin él, porque con uno solo la inversión pasaría inadvertida.

    `solicitante_id` es requerido a propósito: opcional convertiría "olvidé mandar
    el parámetro" en un perfil ajeno servido sin más.

    El 404 sin perfil es el caso de negocio esperable de `docs/conventions.md` §3
    (mensaje de producto en español); el cliente de AD-04 lo mapea a `null` y el
    wizard arranca en blanco.
    """
    if solicitante_id != user_id:
        raise HTTPException(403, HOGAR_AJENO)

    if session.get(User, user_id) is None:
        raise HTTPException(404, f"El usuario {user_id} no existe")

    perfil = session.get(HomeProfile, user_id)
    if perfil is None:
        raise HTTPException(404, "Todavía no completaste el perfil de hogar de tu cuenta")

    return HomeProfileOut.model_validate(perfil)


@router.get("/{user_id}", response_model=UserOut)
def obtener_perfil(user_id: int, session: Session = Depends(get_session)) -> UserOut:
    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(404, f"El usuario {user_id} no existe")

    return UserOut.model_validate(user)
