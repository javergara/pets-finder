from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.report import Report
from ..models.user import User
from ..schemas.report import ReportIn, ReportOut, ReportUpdate
from ..services.db import get_session

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.post("", response_model=ReportOut, status_code=status.HTTP_201_CREATED)
def crear_reporte(payload: ReportIn, session: Session = Depends(get_session)) -> ReportOut:
    user = session.get(User, payload.user_id)
    if user is None:
        raise HTTPException(404, f"El usuario {payload.user_id} no existe")

    report = Report(**payload.model_dump())
    session.add(report)
    session.commit()
    session.refresh(report)

    return ReportOut.model_validate(report)


@router.get("", response_model=list[ReportOut])
def listar_reportes(
    tipo: str | None = None,
    especie: str | None = None,
    zona: str | None = None,
    estado: str = "activo",
    session: Session = Depends(get_session),
) -> list[ReportOut]:
    """Listado con filtros opcionales, más reciente primero.

    `estado` por defecto es "activo": los reportes reunidos salen de las vistas
    activas (listado y mapa) — se piden explícitamente con `estado=reunido`, o
    todos con `estado=todos`.
    """
    query = select(Report)
    if estado != "todos":
        query = query.where(Report.estado == estado)
    if tipo is not None:
        query = query.where(Report.tipo == tipo)
    if especie is not None:
        query = query.where(Report.especie == especie)
    if zona is not None:
        query = query.where(Report.zona == zona)
    query = query.order_by(Report.fecha_evento.desc(), Report.id.desc())

    reports = session.execute(query).scalars().all()
    return [ReportOut.model_validate(r) for r in reports]


# Recordatorio (comentado también en main.py): cualquier ruta literal nueva bajo
# /api/reports (p. ej. /reunidos, feature 09) debe declararse ANTES que estas
# rutas dinámicas /{report_id} en este archivo, o queda eclipsada (422).


@router.get("/{report_id}", response_model=ReportOut)
def obtener_reporte(report_id: int, session: Session = Depends(get_session)) -> ReportOut:
    report = session.get(Report, report_id)
    if report is None:
        raise HTTPException(404, f"El reporte {report_id} no existe")

    return ReportOut.model_validate(report)


@router.put("/{report_id}", response_model=ReportOut)
def editar_reporte(
    report_id: int, payload: ReportUpdate, session: Session = Depends(get_session)
) -> ReportOut:
    """Edición parcial de los campos descriptivos, solo por el autor.

    Sin auth real (ADR 0005 §4): la autoría se valida contra el `user_id` del
    payload, el mismo nivel de confianza que el resto del MVP.
    """
    report = session.get(Report, report_id)
    if report is None:
        raise HTTPException(404, f"El reporte {report_id} no existe")
    if payload.user_id != report.user_id:
        raise HTTPException(403, "Solo quien creó el reporte puede editarlo")

    cambios = payload.model_dump(exclude={"user_id"}, exclude_none=True)
    for campo, valor in cambios.items():
        setattr(report, campo, valor)
    session.commit()
    session.refresh(report)

    return ReportOut.model_validate(report)
