from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..media import borrar_foto
from ..models.pet import Pet
from ..models.report import Report
from ..models.report_foto import ReportFoto
from ..models.sighting import Sighting
from ..models.suscripcion import Suscripcion
from ..models.user import User
from ..schemas.report import (
    BusquedaResultadoOut,
    CoincidenciaOut,
    ConteosOut,
    ReportIn,
    ReportOut,
    ReportUpdate,
    ReunidoIn,
    ReunidosResumenOut,
    SightingIn,
    SightingOut,
    SuscripcionIn,
    SuscripcionOut,
)
from ..services.busqueda import ConsultaBusqueda, buscar_parecidos
from ..services.coincidencias import ordenar_coincidencias, razones_coincidencia
from ..services.db import get_session
from ..services.notificaciones import notificar_novedad
from ..services.titulos import titulo_reporte

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

    report = Report(**payload.model_dump(exclude={"fotos_extra"}))
    report.fotos_adicionales = [
        ReportFoto(foto_url=url, orden=n) for n, url in enumerate(payload.fotos_extra)
    ]
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


@router.get("/busqueda", response_model=list[BusquedaResultadoOut])
def buscar_por_descripcion(
    especie: str,
    tipo: str = Query(pattern="^(perdido|encontrado)$"),
    zona: str | None = None,
    color: str | None = None,
    tamano: str | None = None,
    senas: str | None = None,
    session: Session = Depends(get_session),
) -> list[BusquedaResultadoOut]:
    """Busca a tu mascota (feature 38): descríbela y rankeamos por parecido.

    `tipo` es el tipo de reportes donde buscar (perdí la mía → "encontrado";
    encontré una → "perdido"). Solo reportes activos; la especie filtra exacto
    y el resto de criterios puntúa (services/busqueda.py, sin AI). Ruta estática
    declarada antes de las dinámicas /{report_id}.
    """
    candidatos = (
        session.execute(select(Report).where(Report.estado == "activo", Report.tipo == tipo))
        .scalars()
        .all()
    )
    consulta = ConsultaBusqueda(especie=especie, zona=zona, color=color, tamano=tamano, senas=senas)
    resultado = buscar_parecidos(consulta, list(candidatos))

    return [
        BusquedaResultadoOut(
            parecido=parecido, razones=razones, **ReportOut.model_validate(r).model_dump()
        )
        for r, parecido, razones in resultado[:20]
    ]


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
def conteos_activos(zona: str | None = None, session: Session = Depends(get_session)) -> ConteosOut:
    """Cuántos reportes activos hay por tipo — prueba social del listado y la landing.

    Una sola query agregada; el cliente nunca cuenta arrays (feature 34).
    `zona` opcional (feature 46): los conteos de una landing de zona.
    """
    query = select(Report.tipo, func.count()).where(Report.estado == "activo")
    if zona is not None:
        query = query.where(Report.zona == zona)
    filas = dict(session.execute(query.group_by(Report.tipo)).all())
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

    _avisar_suscritos(session, report, f"💚 {titulo_reporte(report)} volvió a casa.")
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

    _avisar_suscritos(
        session,
        report,
        f"Alguien reportó que vio a {titulo_reporte(report)}: “{payload.comentario}”.",
    )

    return SightingOut.model_validate(sighting)


@router.post(
    "/{report_id}/suscripciones",
    response_model=SuscripcionOut,
    status_code=status.HTTP_201_CREATED,
)
def suscribirse(
    report_id: int,
    payload: SuscripcionIn,
    response: Response,
    session: Session = Depends(get_session),
) -> SuscripcionOut:
    """ "Avísame si hay novedades" (feature 39): correo sin cuenta.

    Idempotente por (reporte, correo): repetir el POST devuelve 200 con la
    suscripción existente en vez de duplicarla o fallar."""
    import secrets

    report = session.get(Report, report_id)
    if report is None:
        raise HTTPException(404, f"El reporte {report_id} no existe")

    correo = payload.email.strip().lower()
    existente = session.scalar(
        select(Suscripcion).where(Suscripcion.report_id == report_id, Suscripcion.email == correo)
    )
    if existente is not None:
        response.status_code = status.HTTP_200_OK
        return SuscripcionOut.model_validate(existente)

    suscripcion = Suscripcion(report_id=report_id, email=correo, token=secrets.token_hex(16))
    session.add(suscripcion)
    try:
        session.commit()
    except IntegrityError:
        # Carrera: el mismo correo llegó dos veces a la vez.
        session.rollback()
        existente = session.scalar(
            select(Suscripcion).where(
                Suscripcion.report_id == report_id, Suscripcion.email == correo
            )
        )
        if existente is not None:
            response.status_code = status.HTTP_200_OK
            return SuscripcionOut.model_validate(existente)
        raise
    session.refresh(suscripcion)
    return SuscripcionOut.model_validate(suscripcion)


def _avisar_suscritos(session: Session, report: Report, novedad: str) -> None:
    """Dispara los correos tras el commit; un fallo jamás rompe el endpoint."""
    suscripciones = list(
        session.execute(select(Suscripcion).where(Suscripcion.report_id == report.id)).scalars()
    )
    notificar_novedad(report, suscripciones, novedad)


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
    """El detalle es el ÚNICO sitio que resuelve `adopcion_pet_id` (AD-02).

    Una query extra por reporte es barata cuando se pide un reporte; en
    `listar_reportes` sería una por fila (N+1 contra el pooler de Supabase) en la
    vista más caliente de la app, y ni el listado ni el mapa lo usan: allí el
    campo se queda en su default `None`.
    """
    report = session.get(Report, report_id)
    if report is None:
        raise HTTPException(404, f"El reporte {report_id} no existe")

    out = ReportOut.model_validate(report)
    out.adopcion_pet_id = session.scalar(select(Pet.id).where(Pet.report_id == report_id))
    return out


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_reporte(report_id: int, user_id: int, session: Session = Depends(get_session)) -> None:
    """Borrado definitivo, solo por el autor (misma confianza que editar/reunido).

    La foto asociada se borra también (feature 20) con `borrar_foto`, que es
    tolerante: si el bucket falla, el reporte se elimina igual y queda un log.

    ⚠️ Si de este reporte salió una mascota en adopción (AD-02), no se borra: en
    Postgres la FK `pets.report_id` haría reventar el commit con un
    `IntegrityError` (500 con traza), y en SQLite —que no fuerza las FK— pasaría
    algo peor: el reporte se iría dejando una mascota publicada apuntando a la
    nada. Se responde 409 y se pide despublicarla primero.

    ⚠️ Ese 409 va **antes** de `borrar_foto`, y ese orden es el punto: al revés,
    el endpoint se llevaría las fotos del bucket (que además son las de la ficha
    de adopción, viva) y solo después fallaría, dejando al usuario sin imágenes y
    con el reporte intacto. Como `borrar_foto` no lanza, el status no delataría
    nada: por eso el test espía las llamadas.
    """
    report = session.get(Report, report_id)
    if report is None:
        raise HTTPException(404, f"El reporte {report_id} no existe")
    if user_id != report.user_id:
        raise HTTPException(403, "Solo quien creó el reporte puede eliminarlo")
    if session.scalar(select(Pet.id).where(Pet.report_id == report_id)) is not None:
        raise HTTPException(
            409, "Este reporte tiene una mascota publicada en adopción: despublícala primero"
        )

    borrar_foto(report.foto_url)
    for foto in report.fotos_adicionales:
        borrar_foto(foto.foto_url)
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
