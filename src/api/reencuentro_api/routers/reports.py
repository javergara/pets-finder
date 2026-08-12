from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models.report import Report
from ..models.user import User
from ..schemas.report import (
    CoincidenciaOut,
    ReportIn,
    ReportOut,
    ReportUpdate,
    ReunidoIn,
    ReunidosResumenOut,
)
from ..services.coincidencias import ordenar_coincidencias
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
    raza: str | None = None,
    color: str | None = None,
    tamano: str | None = None,
    user_id: int | None = None,
    estado: str = "activo",
    session: Session = Depends(get_session),
) -> list[ReportOut]:
    """Listado con filtros opcionales, más reciente primero.

    `estado` por defecto es "activo": los reportes reunidos salen de las vistas
    activas (listado y mapa) — se piden explícitamente con `estado=reunido`, o
    todos con `estado=todos`. `user_id` filtra "mis reportes" (feature 09), donde
    normalmente se combina con `estado=todos` para ver también los reunidos.
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
    if raza is not None:
        query = query.where(Report.raza == raza)
    if color is not None:
        query = query.where(Report.color == color)
    if tamano is not None:
        query = query.where(Report.tamano == tamano)
    if user_id is not None:
        query = query.where(Report.user_id == user_id)
    query = query.order_by(Report.fecha_evento.desc(), Report.id.desc())

    reports = session.execute(query).scalars().all()
    return [ReportOut.model_validate(r) for r in reports]


# Ruta literal declarada ANTES que las dinámicas /{report_id} (regla comentada
# también en main.py): al revés quedaría eclipsada y "reunidos" se parsearía
# como un report_id inválido (422).
@router.get("/reunidos", response_model=ReunidosResumenOut)
def resumen_reunidos(session: Session = Depends(get_session)) -> ReunidosResumenOut:
    """La métrica de esperanza de la landing: cuántos reencuentros y los últimos."""
    total = session.execute(
        select(func.count()).select_from(Report).where(Report.estado == "reunido")
    ).scalar_one()

    recientes = (
        session.execute(
            select(Report)
            .where(Report.estado == "reunido")
            .order_by(Report.resuelto_en.desc())
            .limit(6)
        )
        .scalars()
        .all()
    )

    return ReunidosResumenOut(
        total=total, recientes=[ReportOut.model_validate(r) for r in recientes]
    )


@router.post("/{report_id}/reunido", response_model=ReportOut)
def marcar_reunido(
    report_id: int, payload: ReunidoIn, session: Session = Depends(get_session)
) -> ReportOut:
    """El final feliz: solo el autor puede marcarlo, y solo una vez.

    El reporte sale de las vistas activas (listado/mapa filtran `estado=activo`)
    y pasa a alimentar el contador de reencuentros de la landing.
    """
    report = session.get(Report, report_id)
    if report is None:
        raise HTTPException(404, f"El reporte {report_id} no existe")
    if payload.user_id != report.user_id:
        raise HTTPException(403, "Solo quien creó el reporte puede marcarlo como reunido")
    if report.estado == "reunido":
        raise HTTPException(409, "Este reporte ya está marcado como reunido")

    report.estado = "reunido"
    report.resuelto_en = datetime.now(timezone.utc)
    session.commit()
    session.refresh(report)

    return ReportOut.model_validate(report)


@router.get("/{report_id}/coincidencias", response_model=list[CoincidenciaOut])
def listar_coincidencias(
    report_id: int, session: Session = Depends(get_session)
) -> list[CoincidenciaOut]:
    """Candidatos del tipo opuesto que podrían ser la misma mascota.

    El router solo carga los candidatos crudos; el filtro y el orden viven en
    la función pura `services/coincidencias.py::ordenar_coincidencias`.
    """
    reporte = session.get(Report, report_id)
    if reporte is None:
        raise HTTPException(404, f"El reporte {report_id} no existe")

    candidatos = session.execute(select(Report).where(Report.id != report_id)).scalars().all()
    resultado = ordenar_coincidencias(reporte, list(candidatos))

    return [
        CoincidenciaOut(distancia_km=distancia, **ReportOut.model_validate(c).model_dump())
        for c, distancia in resultado
    ]


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
