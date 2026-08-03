"""Panel del refugio — feature 09-shelter-panel, solo lectura (ADR 0002).

Ningún endpoint de este router muta `Match.estado`: las transiciones de una solicitud
(`en_revision`, `visita_agendada`, `adoptado`, `cerrado`) son de la feature de backlog
`10-adoption-request-flow`. Acá solo se lee `Match.estado` para filtrar/calcular
métricas y la etiqueta de cada solicitud.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models.home_profile import HomeProfile
from ..models.match import Match
from ..models.pet import Pet
from ..models.shelter import Shelter
from ..models.user import User
from ..schemas.pet import AfinidadOut
from ..schemas.shelter import (
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
from ..services.solicitudes import calcular_etiqueta_solicitud

router = APIRouter(prefix="/api/shelters", tags=["shelters"])


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
    - `apadrinamientos_recaudados_cop` = siempre 0, no existe tabla `Sponsorship`
      todavía (feature `12-sponsorship`, backlog).
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
            apadrinamientos_recaudados_cop=0,
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
    """Detalle de una solicitud: cuestionario completo (`HomeProfile`) + "Sobre mí".

    404 si el refugio no existe, o si el match no existe, o si el match existe pero
    pertenece a OTRO refugio — se verifica `match.shelter_id == shelter_id` explícito,
    no solo que el match exista, para no filtrar datos de otro refugio.
    """
    shelter = session.get(Shelter, shelter_id)
    if shelter is None:
        raise HTTPException(404, f"El refugio {shelter_id} no existe")

    match = session.get(Match, match_id)
    if match is None or match.shelter_id != shelter_id:
        raise HTTPException(404, f"La solicitud {match_id} no existe en el refugio {shelter_id}")

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
