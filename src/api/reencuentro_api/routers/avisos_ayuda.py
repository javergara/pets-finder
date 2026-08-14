"""Ayuda entre personas (feature 42): pido/ofrezco, con los patrones de siempre.

CRUD calcado de reportes/organizaciones: autoría por user_id (ADR 0005 §4),
filtros por query params, resolver solo el autor (409 si ya está), DELETE
definitivo solo el autor.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.aviso_ayuda import AvisoAyuda
from ..models.user import User
from ..schemas.aviso_ayuda import AvisoAyudaIn, AvisoAyudaOut, AvisoResueltoIn
from ..services.db import get_session

router = APIRouter(prefix="/api/avisos-ayuda", tags=["avisos-ayuda"])


@router.post("", response_model=AvisoAyudaOut, status_code=status.HTTP_201_CREATED)
def crear_aviso(payload: AvisoAyudaIn, session: Session = Depends(get_session)) -> AvisoAyudaOut:
    if session.get(User, payload.user_id) is None:
        raise HTTPException(404, f"El usuario {payload.user_id} no existe")

    aviso = AvisoAyuda(**payload.model_dump())
    session.add(aviso)
    session.commit()
    session.refresh(aviso)
    return AvisoAyudaOut.model_validate(aviso)


@router.get("", response_model=list[AvisoAyudaOut])
def listar_avisos(
    tipo: str | None = None,
    categoria: str | None = None,
    zona: str | None = None,
    estado: str = "activo",
    session: Session = Depends(get_session),
) -> list[AvisoAyudaOut]:
    """Más reciente primero; los resueltos salen del listado por defecto
    (`estado=resuelto` los pide, `estado=todos` trae todo)."""
    query = select(AvisoAyuda)
    if estado != "todos":
        query = query.where(AvisoAyuda.estado == estado)
    if tipo is not None:
        query = query.where(AvisoAyuda.tipo == tipo)
    if categoria is not None:
        query = query.where(AvisoAyuda.categoria == categoria)
    if zona is not None:
        query = query.where(AvisoAyuda.zona == zona)

    avisos = session.execute(query.order_by(AvisoAyuda.creado_en.desc())).scalars().all()
    return [AvisoAyudaOut.model_validate(a) for a in avisos]


@router.post("/{aviso_id}/resuelto", response_model=AvisoAyudaOut)
def marcar_resuelto(
    aviso_id: int, payload: AvisoResueltoIn, session: Session = Depends(get_session)
) -> AvisoAyudaOut:
    """La ayuda llegó: solo el autor lo declara, una sola vez (patrón reunido)."""
    aviso = session.get(AvisoAyuda, aviso_id)
    if aviso is None:
        raise HTTPException(404, f"El aviso {aviso_id} no existe")
    if payload.user_id != aviso.user_id:
        raise HTTPException(403, "Solo quien publicó el aviso puede marcarlo como resuelto")
    if aviso.estado == "resuelto":
        raise HTTPException(409, "Este aviso ya está marcado como resuelto")

    aviso.estado = "resuelto"
    aviso.resuelto_en = datetime.now(timezone.utc)
    session.commit()
    session.refresh(aviso)
    return AvisoAyudaOut.model_validate(aviso)


@router.delete("/{aviso_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_aviso(aviso_id: int, user_id: int, session: Session = Depends(get_session)) -> None:
    aviso = session.get(AvisoAyuda, aviso_id)
    if aviso is None:
        raise HTTPException(404, f"El aviso {aviso_id} no existe")
    if user_id != aviso.user_id:
        raise HTTPException(403, "Solo quien publicó el aviso puede eliminarlo")

    session.delete(aviso)
    session.commit()
