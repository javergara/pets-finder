from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..media import borrar_foto
from ..models.report import Report
from ..models.sighting import Sighting
from ..models.user import User
from ..schemas.report import (
    CoincidenciaOut,
    ConteosOut,
    ReportIn,
    ReportOut,
    ReportUpdate,
    ReunidoIn,
    ReunidosResumenOut,
    SightingIn,
    SightingOut,
)
from ..services.coincidencias import ordenar_coincidencias, razones_coincidencia
from ..services.db import get_session

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.post("", response_model=ReportOut, status_code=status.HTTP_201_CREATED)
def crear_reporte(
    payload: ReportIn, response: Response, session: Session = Depends(get_session)
) -> ReportOut:
    """Crea un reporte. Con `idempotency_id` (lo manda el crawler, ADR 0010) el
    POST es idempotente: repetirlo devuelve el reporte ya creado con 200 en vez
    de duplicarlo — el índice único de la columna garantiza esto incluso si dos
    requests llegan a la vez."""
    user = session.get(User, payload.user_id)
    if user is None:
        raise HTTPException(404, f"El usuario {payload.user_id} no existe")

    def _existente() -> Report | None:
        if payload.idempotency_id is None:
            return None
        return session.scalar(select(Report).where(Report.idempotency_id == payload.idempotency_id))

    if (previo := _existente()) is not None:
        response.status_code = status.HTTP_200_OK
        return ReportOut.model_validate(previo)

    report = Report(**payload.model_dump())
    session.add(report)
    try:
        session.commit()
    except IntegrityError:
        # Carrera: otro request con el mismo idempotency_id ganó el commit.
        session.rollback()
        if (previo := _existente()) is not None:
            response.status_code = status.HTTP_200_OK
            return ReportOut.model_validate(previo)
        raise
    session.refresh(report)

    return ReportOut.model_validate(report)


@router.get("", response_model=list[ReportOut])
def listar_reportes(
    response: Response,
    tipo: str | None = None,
    especie: str | None = None,
    zona: str | None = None,
    raza: str | None = None,
    color: str | None = None,
    tamano: str | None = None,
    user_id: int | None = None,
    estado: str = "activo",
    q: str | None = None,
    limit: int | None = Query(default=None, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
) -> list[ReportOut]:
    """Listado con filtros opcionales, más reciente primero.

    `estado` por defecto es "activo": los reportes reunidos salen de las vistas
    activas (listado y mapa) — se piden explícitamente con `estado=reunido`, o
    todos con `estado=todos`. `user_id` filtra "mis reportes" (feature 09), donde
    normalmente se combina con `estado=todos` para ver también los reunidos.

    Búsqueda y paginación (feature 30): `q` busca texto libre (case-insensitive)
    en nombre, descripción, barrio y ciudad_texto; `limit`/`offset` paginan con
    orden estable (fecha_evento desc, id desc) y el total de la consulta viaja
    SIEMPRE en el header `X-Total-Count` — sin `limit`, la respuesta sigue
    siendo la lista completa (compatibilidad con mapa y mis-reportes).
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
    if q is not None and q.strip():
        termino = f"%{q.strip()}%"
        query = query.where(
            or_(
                Report.nombre_mascota.ilike(termino),
                Report.descripcion.ilike(termino),
                Report.barrio.ilike(termino),
                Report.ciudad_texto.ilike(termino),
            )
        )

    total = session.execute(select(func.count()).select_from(query.subquery())).scalar_one()
    response.headers["X-Total-Count"] = str(total)

    query = query.order_by(Report.fecha_evento.desc(), Report.id.desc())
    if limit is not None:
        query = query.offset(offset).limit(limit)

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


# Ruta literal, también antes que las dinámicas (misma regla que /reunidos).
@router.get("/conteos", response_model=ConteosOut)
def conteos_activos(session: Session = Depends(get_session)) -> ConteosOut:
    """Cuántos reportes activos hay por tipo — prueba social del listado y la landing.

    Una sola query agregada; el cliente nunca cuenta arrays (feature 34).
    """
    filas = dict(
        session.execute(
            select(Report.tipo, func.count()).where(Report.estado == "activo").group_by(Report.tipo)
        ).all()
    )
    return ConteosOut(perdidos=filas.get("perdido", 0), encontrados=filas.get("encontrado", 0))


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
        CoincidenciaOut(
            distancia_km=distancia,
            razones=razones_coincidencia(reporte, c, distancia),
            **ReportOut.model_validate(c).model_dump(),
        )
        for c, distancia in resultado
    ]


@router.post(
    "/{report_id}/avistamientos", response_model=SightingOut, status_code=status.HTTP_201_CREATED
)
def crear_avistamiento(
    report_id: int, payload: SightingIn, session: Session = Depends(get_session)
) -> SightingOut:
    """ "La vi por aquí": cualquiera deja una pista georreferenciada, sin registro.

    Solo sobre reportes "perdido" activos — en un "encontrado" la mascota ya
    está ubicada, y en un "reunido" la búsqueda terminó.
    """
    report = session.get(Report, report_id)
    if report is None:
        raise HTTPException(404, f"El reporte {report_id} no existe")
    if report.tipo != "perdido" or report.estado != "activo":
        raise HTTPException(
            409, "Solo se pueden registrar avistamientos de mascotas perdidas con búsqueda activa"
        )

    sighting = Sighting(report_id=report_id, **payload.model_dump())
    session.add(sighting)
    session.commit()
    session.refresh(sighting)

    return SightingOut.model_validate(sighting)


@router.get("/{report_id}/avistamientos", response_model=list[SightingOut])
def listar_avistamientos(
    report_id: int, session: Session = Depends(get_session)
) -> list[SightingOut]:
    """Pistas más recientes primero (por fecha del avistamiento, luego llegada)."""
    if session.get(Report, report_id) is None:
        raise HTTPException(404, f"El reporte {report_id} no existe")

    sightings = (
        session.execute(
            select(Sighting)
            .where(Sighting.report_id == report_id)
            .order_by(Sighting.fecha.desc(), Sighting.id.desc())
        )
        .scalars()
        .all()
    )
    return [SightingOut.model_validate(s) for s in sightings]


@router.get("/{report_id}", response_model=ReportOut)
def obtener_reporte(report_id: int, session: Session = Depends(get_session)) -> ReportOut:
    report = session.get(Report, report_id)
    if report is None:
        raise HTTPException(404, f"El reporte {report_id} no existe")

    return ReportOut.model_validate(report)


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_reporte(report_id: int, user_id: int, session: Session = Depends(get_session)) -> None:
    """Borrado definitivo, solo por el autor (misma confianza que editar/reunido).

    La foto asociada se borra también (feature 20) con `borrar_foto`, que es
    tolerante: si el bucket falla, el reporte se elimina igual y queda un log.
    """
    report = session.get(Report, report_id)
    if report is None:
        raise HTTPException(404, f"El reporte {report_id} no existe")
    if user_id != report.user_id:
        raise HTTPException(403, "Solo quien creó el reporte puede eliminarlo")

    borrar_foto(report.foto_url)
    session.delete(report)
    session.commit()


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
