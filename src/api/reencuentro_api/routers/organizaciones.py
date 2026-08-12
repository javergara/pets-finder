from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.organizacion import Organizacion
from ..models.user import User
from ..schemas.organizacion import OrganizacionIn, OrganizacionOut, OrganizacionUpdate
from ..services.db import get_session

router = APIRouter(prefix="/api/organizaciones", tags=["organizaciones"])


@router.post("", response_model=OrganizacionOut, status_code=status.HTTP_201_CREATED)
def crear_organizacion(
    payload: OrganizacionIn, session: Session = Depends(get_session)
) -> OrganizacionOut:
    user = session.get(User, payload.user_id)
    if user is None:
        raise HTTPException(404, f"El usuario {payload.user_id} no existe")

    organizacion = Organizacion(**payload.model_dump())
    session.add(organizacion)
    session.commit()
    session.refresh(organizacion)

    return OrganizacionOut.model_validate(organizacion)


@router.get("", response_model=list[OrganizacionOut])
def listar_organizaciones(
    tipo: str | None = None,
    zona: str | None = None,
    estado: str = "activo",
    session: Session = Depends(get_session),
) -> list[OrganizacionOut]:
    """Directorio de la red de apoyo, más reciente primero.

    `estado` default "activo": los lugares cerrados salen de las vistas
    (se piden explícitamente con `estado=cerrado` o `estado=todos`).
    """
    query = select(Organizacion)
    if estado != "todos":
        query = query.where(Organizacion.estado == estado)
    if tipo is not None:
        query = query.where(Organizacion.tipo == tipo)
    if zona is not None:
        query = query.where(Organizacion.zona == zona)
    query = query.order_by(Organizacion.creado_en.desc(), Organizacion.id.desc())

    organizaciones = session.execute(query).scalars().all()
    return [OrganizacionOut.model_validate(o) for o in organizaciones]


@router.get("/{organizacion_id}", response_model=OrganizacionOut)
def obtener_organizacion(
    organizacion_id: int, session: Session = Depends(get_session)
) -> OrganizacionOut:
    organizacion = session.get(Organizacion, organizacion_id)
    if organizacion is None:
        raise HTTPException(404, f"La organización {organizacion_id} no existe")

    return OrganizacionOut.model_validate(organizacion)


@router.put("/{organizacion_id}", response_model=OrganizacionOut)
def editar_organizacion(
    organizacion_id: int, payload: OrganizacionUpdate, session: Session = Depends(get_session)
) -> OrganizacionOut:
    """Edición parcial solo por el autor (patrón de editar_reporte, ADR 0005 §4).

    Cerrar el lugar = `{"estado": "cerrado"}`; reabrirlo = `{"estado": "activo"}`.
    """
    organizacion = session.get(Organizacion, organizacion_id)
    if organizacion is None:
        raise HTTPException(404, f"La organización {organizacion_id} no existe")
    if payload.user_id != organizacion.user_id:
        raise HTTPException(403, "Solo quien registró la organización puede editarla")

    cambios = payload.model_dump(exclude={"user_id"}, exclude_none=True)
    for campo, valor in cambios.items():
        setattr(organizacion, campo, valor)
    session.commit()
    session.refresh(organizacion)

    return OrganizacionOut.model_validate(organizacion)


@router.delete("/{organizacion_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_organizacion(
    organizacion_id: int, user_id: int, session: Session = Depends(get_session)
) -> None:
    """Borrado definitivo solo por el autor (patrón de la feature 18).

    La foto queda huérfana en Storage — misma decisión documentada que en los
    reportes (feature 20 del backlog la resolverá para ambos).
    """
    organizacion = session.get(Organizacion, organizacion_id)
    if organizacion is None:
        raise HTTPException(404, f"La organización {organizacion_id} no existe")
    if user_id != organizacion.user_id:
        raise HTTPException(403, "Solo quien registró la organización puede eliminarla")

    session.delete(organizacion)
    session.commit()
