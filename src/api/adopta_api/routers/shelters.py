"""Panel del refugio — lectura (feature 09-shelter-panel) + acciones sobre la
solicitud (feature 10-adoption-request-flow).

Los 3 `GET` de este router (`obtener_refugio`, `listar_solicitudes`, `obtener_solicitud`)
NO mutan `Match.estado`: solo lo leen para filtrar/calcular métricas y la etiqueta de
cada solicitud.

Los 3 `POST` (`agendar-visita`, `pedir-informacion`, `descartar`) SÍ mutan
`Match.estado` (y, solo en el caso de `descartar`, también `Match.motivo_descarte`).
Esto es exactamente lo que ADR 0002 (`docs/decisions/0002-mecanica-match-no-mutuo.md`)
asigna a esta feature: el `Match` en sí se crea de forma automática e inmutable al hacer
`like` (no hay "aceptar match"), pero las transiciones de la **solicitud** posterior
(`solicitado` -> `en_revision`/`visita_agendada`/`cerrado`/`adoptado`) sí las controla
el refugio, y es precisamente el backlog `10-adoption-request-flow` el que las
implementa. La matriz de transiciones válidas vive en `services/solicitudes.py`
(`validar_transicion`/`TRANSICIONES_VALIDAS`), no en este router: acá solo se llama,
se atrapa `TransicionInvalidaError` como 409, y se persiste.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models.home_profile import HomeProfile
from ..models.match import Match
from ..models.pet import Pet
from ..models.shelter import Shelter
from ..models.sponsorship import Sponsorship
from ..models.user import User
from ..schemas.pet import AfinidadOut
from ..schemas.shelter import (
    DescartarIn,
    ShelterMapOut,
    ShelterMapPetOut,
    ShelterMetricsOut,
    ShelterProfileOut,
    SolicitanteResumen,
    SolicitudDetalleOut,
    SolicitudOut,
    SolicitudPetResumen,
)
from ..schemas.user import HomeProfileOut
from ..services.affinity import calcular_afinidad
from ..services.db import get_session
from ..services.geo import distancia_km
from ..services.solicitudes import (
    TransicionInvalidaError,
    calcular_etiqueta_solicitud,
    validar_transicion,
)

router = APIRouter(prefix="/api/shelters", tags=["shelters"])


def _cargar_match_o_404(session: Session, shelter_id: int, match_id: int) -> Match:
    """404 si el refugio no existe, o si el match no existe, o si el match existe pero
    pertenece a OTRO refugio -- se verifica `match.shelter_id == shelter_id` explícito,
    no solo que el match exista, para no filtrar ni mutar datos de otro refugio."""
    shelter = session.get(Shelter, shelter_id)
    if shelter is None:
        raise HTTPException(404, f"El refugio {shelter_id} no existe")

    match = session.get(Match, match_id)
    if match is None or match.shelter_id != shelter_id:
        raise HTTPException(404, f"La solicitud {match_id} no existe en el refugio {shelter_id}")
    return match


def _solicitud_detalle_out(session: Session, match: Match) -> SolicitudDetalleOut:
    """Construye el detalle completo de una solicitud: cuestionario (`HomeProfile`),
    afinidad, etiqueta y "Sobre mí" del adoptante."""
    pet = session.get(Pet, match.pet_id)
    user = session.get(User, match.user_id)
    home = session.get(HomeProfile, match.user_id)
    if home is None:
        # Mismo criterio defensivo que matches.py: sin HomeProfile no hay cuestionario
        # que mostrar, y es el contenido principal de esta pantalla.
        raise HTTPException(
            404, f"El adoptante {match.user_id} no tiene HomeProfile (cuestionario)"
        )

    afinidad = calcular_afinidad(pet, home)
    return SolicitudDetalleOut(
        id=match.id,
        estado=match.estado,
        creado_en=match.creado_en,
        adoptante=SolicitanteResumen(id=user.id, nombre=user.nombre),
        pet=SolicitudPetResumen(id=pet.id, nombre=pet.nombre, raza=pet.raza, fotos=pet.fotos),
        afinidad=AfinidadOut(
            score=afinidad.score,
            explicacion=afinidad.explicacion,
            incompatible=afinidad.incompatible,
        ),
        etiqueta=calcular_etiqueta_solicitud(match.estado, match.creado_en),
        bio=user.bio,
        home_profile=HomeProfileOut.model_validate(home),
    )


@router.get("", response_model=list[ShelterMapOut])
def listar_refugios_mapa(
    user_id: int | None = None, session: Session = Depends(get_session)
) -> list[ShelterMapOut]:
    """Refugios para el mapa propio en CSS/SVG (feature 14-shelter-map, sin librería de
    mapas ni conexión a internet en runtime): cada uno con su conteo/lista de mascotas
    disponibles y, si se pasa `user_id`, la distancia en línea recta hacia él.

    `mascotas_disponibles`/`mascotas` solo cuentan `Pet.estado == "disponible"` -- es
    distinto de `ShelterMetricsOut.mascotas_publicadas`, que cuenta el histórico total
    de mascotas del refugio sin filtrar por estado.

    `distancia_km` es `None` salvo que `user_id` sea válido y tanto el usuario como el
    refugio tengan `lat`/`lng` no nulos (degradación elegante, mismo criterio que
    `services/filters.py`). `user_id` inexistente -> 404 en español. Lista vacía (200,
    no 404) si no hay refugios sembrados.
    """
    user_lat: float | None = None
    user_lng: float | None = None
    if user_id is not None:
        user = session.get(User, user_id)
        if user is None:
            raise HTTPException(404, f"El usuario {user_id} no existe")
        user_lat, user_lng = user.lat, user.lng

    shelters = session.execute(select(Shelter)).scalars().all()

    resultado: list[ShelterMapOut] = []
    for shelter in shelters:
        mascotas_disponibles = (
            session.execute(
                select(Pet).where(Pet.shelter_id == shelter.id, Pet.estado == "disponible")
            )
            .scalars()
            .all()
        )

        distancia: float | None = None
        if (
            user_lat is not None
            and user_lng is not None
            and shelter.lat is not None
            and shelter.lng is not None
        ):
            distancia = distancia_km(user_lat, user_lng, shelter.lat, shelter.lng)

        resultado.append(
            ShelterMapOut(
                id=shelter.id,
                nombre=shelter.nombre,
                verificado=shelter.verificado,
                lat=shelter.lat,
                lng=shelter.lng,
                mascotas_disponibles=len(mascotas_disponibles),
                mascotas=[ShelterMapPetOut.model_validate(pet) for pet in mascotas_disponibles],
                distancia_km=distancia,
            )
        )
    return resultado


@router.get("/{shelter_id}", response_model=ShelterProfileOut)
def obtener_refugio(shelter_id: int, session: Session = Depends(get_session)) -> ShelterProfileOut:
    """Perfil del refugio + métricas agregadas.

    Definiciones exactas de las métricas:
    - `mascotas_publicadas` = count de TODAS las `Pet` de este refugio, sin filtrar por
      `estado` — es "cuántas ha publicado en total", no "cuántas están disponibles
      ahora mismo" (esa es una vista distinta, no la de esta tarjeta).
    - `interesados_este_mes` = count de `Match` de este refugio con `creado_en` dentro
      del mes calendario actual, en UTC.
    - `visitas_agendadas` = count de `Match` de este refugio con
      `estado == "visita_agendada"` (mismo criterio que `UserMetricsOut.visitas_agendadas`
      en `routers/users.py`, ahora filtrado por refugio en vez de por adoptante).
    - `adopciones_cerradas` = columna `Shelter.adopciones_cerradas` directa: ya es un
      contador almacenado, no se recalcula contando `Match` con `estado == "adoptado"`.
    - `apadrinamientos_recaudados_cop` = suma de `Sponsorship.monto_cop` con
      `activo == True` sobre las mascotas de este refugio (join por `Pet.shelter_id`,
      feature `12-sponsorship`).
    """
    shelter = session.get(Shelter, shelter_id)
    if shelter is None:
        raise HTTPException(404, f"El refugio {shelter_id} no existe")

    mascotas_publicadas = session.execute(
        select(func.count()).select_from(Pet).where(Pet.shelter_id == shelter_id)
    ).scalar_one()

    # Mismo criterio que services/deck.py: se compara contra un datetime naive en UTC
    # porque SQLite/SQLAlchemy puede devolver `Match.creado_en` naive al leerlo aunque
    # se haya guardado con datetime.now(timezone.utc).
    ahora_naive_utc = datetime.now(timezone.utc).replace(tzinfo=None)
    inicio_mes = ahora_naive_utc.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    interesados_este_mes = session.execute(
        select(func.count())
        .select_from(Match)
        .where(Match.shelter_id == shelter_id, Match.creado_en >= inicio_mes)
    ).scalar_one()

    visitas_agendadas = session.execute(
        select(func.count())
        .select_from(Match)
        .where(Match.shelter_id == shelter_id, Match.estado == "visita_agendada")
    ).scalar_one()

    apadrinamientos_recaudados_cop = (
        session.execute(
            select(func.sum(Sponsorship.monto_cop))
            .join(Pet, Pet.id == Sponsorship.pet_id)
            .where(Pet.shelter_id == shelter_id, Sponsorship.activo.is_(True))
        ).scalar_one()
        or 0
    )

    return ShelterProfileOut(
        id=shelter.id,
        nombre=shelter.nombre,
        ciudad=shelter.ciudad,
        verificado=shelter.verificado,
        tiempo_respuesta_horas=shelter.tiempo_respuesta_horas,
        logo_url=shelter.logo_url,
        metricas=ShelterMetricsOut(
            mascotas_publicadas=mascotas_publicadas,
            interesados_este_mes=interesados_este_mes,
            visitas_agendadas=visitas_agendadas,
            adopciones_cerradas=shelter.adopciones_cerradas,
            apadrinamientos_recaudados_cop=apadrinamientos_recaudados_cop,
        ),
    )


@router.get("/{shelter_id}/solicitudes", response_model=list[SolicitudOut])
def listar_solicitudes(
    shelter_id: int, session: Session = Depends(get_session)
) -> list[SolicitudOut]:
    """Solicitudes (`Match`) de las mascotas de este refugio, más recientes primero.

    Filtra por `Match.shelter_id` directo (ya es FK, no hace falta joinear por `Pet`).
    Un refugio sin solicitudes devuelve lista vacía (200), no 404 — un refugio nuevo
    o recién publicado legítimamente no tiene ninguna todavía.
    """
    shelter = session.get(Shelter, shelter_id)
    if shelter is None:
        raise HTTPException(404, f"El refugio {shelter_id} no existe")

    matches = (
        session.execute(
            select(Match).where(Match.shelter_id == shelter_id).order_by(Match.creado_en.desc())
        )
        .scalars()
        .all()
    )

    resultado: list[SolicitudOut] = []
    for match in matches:
        pet = session.get(Pet, match.pet_id)
        user = session.get(User, match.user_id)
        home = session.get(HomeProfile, match.user_id)
        if home is None:
            # No debería pasar (el onboarding exige el cuestionario), pero si ocurre no
            # podemos calcular afinidad ni mostrar el detalle del hogar: se excluye esa
            # fila en vez de tumbar toda la lista con un 500.
            continue

        afinidad = calcular_afinidad(pet, home)
        resultado.append(
            SolicitudOut(
                id=match.id,
                estado=match.estado,
                creado_en=match.creado_en,
                adoptante=SolicitanteResumen(id=user.id, nombre=user.nombre),
                pet=SolicitudPetResumen(
                    id=pet.id, nombre=pet.nombre, raza=pet.raza, fotos=pet.fotos
                ),
                afinidad=AfinidadOut(
                    score=afinidad.score,
                    explicacion=afinidad.explicacion,
                    incompatible=afinidad.incompatible,
                ),
                etiqueta=calcular_etiqueta_solicitud(match.estado, match.creado_en),
            )
        )
    return resultado


@router.get("/{shelter_id}/solicitudes/{match_id}", response_model=SolicitudDetalleOut)
def obtener_solicitud(
    shelter_id: int, match_id: int, session: Session = Depends(get_session)
) -> SolicitudDetalleOut:
    """Detalle de una solicitud: cuestionario completo (`HomeProfile`) + "Sobre mí"."""
    match = _cargar_match_o_404(session, shelter_id, match_id)
    return _solicitud_detalle_out(session, match)


@router.post(
    "/{shelter_id}/solicitudes/{match_id}/agendar-visita", response_model=SolicitudDetalleOut
)
def agendar_visita(
    shelter_id: int, match_id: int, session: Session = Depends(get_session)
) -> SolicitudDetalleOut:
    """Agenda una visita: válido desde `solicitado`/`en_revision` (ver
    `services/solicitudes.py::TRANSICIONES_VALIDAS`). 409 en cualquier otro estado."""
    match = _cargar_match_o_404(session, shelter_id, match_id)
    try:
        validar_transicion(match.estado, "agendar-visita")
    except TransicionInvalidaError as exc:
        raise HTTPException(409, str(exc)) from exc

    match.estado = "visita_agendada"
    session.commit()
    return _solicitud_detalle_out(session, match)


@router.post(
    "/{shelter_id}/solicitudes/{match_id}/pedir-informacion", response_model=SolicitudDetalleOut
)
def pedir_informacion(
    shelter_id: int, match_id: int, session: Session = Depends(get_session)
) -> SolicitudDetalleOut:
    """Pide información adicional al adoptante: válido solo desde `solicitado`. 409 en
    cualquier otro estado (incluyendo `en_revision`, no es un no-op idempotente)."""
    match = _cargar_match_o_404(session, shelter_id, match_id)
    try:
        validar_transicion(match.estado, "pedir-informacion")
    except TransicionInvalidaError as exc:
        raise HTTPException(409, str(exc)) from exc

    match.estado = "en_revision"
    session.commit()
    return _solicitud_detalle_out(session, match)


@router.post("/{shelter_id}/solicitudes/{match_id}/descartar", response_model=SolicitudDetalleOut)
def descartar_solicitud(
    shelter_id: int,
    match_id: int,
    payload: DescartarIn,
    session: Session = Depends(get_session),
) -> SolicitudDetalleOut:
    """Descarta la solicitud con un motivo obligatorio: válido desde
    `solicitado`/`en_revision`/`visita_agendada`. 409 en cualquier otro estado.

    `motivo_descarte` se persiste pero nunca se devuelve al adoptante -- ni en
    `SolicitudDetalleOut` (contrato mínimo, decisión explícita del documento de diseño)
    ni en `MatchWithPetOut` (`schemas/match.py`, lado adoptante, sin tocar en esta
    feature): el adoptante nunca ve el motivo en crudo (`docs/product-research.md`).
    """
    match = _cargar_match_o_404(session, shelter_id, match_id)
    try:
        validar_transicion(match.estado, "descartar")
    except TransicionInvalidaError as exc:
        raise HTTPException(409, str(exc)) from exc

    match.estado = "cerrado"
    match.motivo_descarte = payload.motivo
    session.commit()
    return _solicitud_detalle_out(session, match)
