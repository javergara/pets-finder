"""Apadrinamiento (feature 12-sponsorship): mascotas difíciles de ubicar abiertas a
apoyo económico, creación de compromisos y su listado por usuario.

Registro de compromiso, no una transacción de dinero real: no hay integración de
pasarela de pago (design/prototypes/HANDOFF.md §11). Mismo criterio que
`routers/chat.py`: router propio agrupando rutas bajo distintos prefijos del mismo
`/api`, registrado en `main.py` junto a los demás.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models.pet import Pet
from ..models.sponsorship import Sponsorship
from ..models.user import User
from ..schemas.sponsorship import (
    MascotaNecesitaApoyoOut,
    SponsorshipIn,
    SponsorshipOut,
    SponsorshipPetResumen,
)
from ..services.db import get_session
from ..services.deck import es_dificil_de_ubicar
from .pets import _pet_out

router = APIRouter(prefix="/api", tags=["sponsorships"])

# Meta ilustrativa fija de demo, sin origen en ningún campo real de Pet/Shelter
# (HANDOFF §5.7).
META_MENSUAL_COP = 200_000


def _monto_recaudado_cop(session: Session, pet_id: int) -> int:
    """Suma de `Sponsorship.monto_cop` activos de una mascota. `SUM` de cero filas
    devuelve `NULL` en SQL, de ahí el `or 0`."""
    return (
        session.execute(
            select(func.sum(Sponsorship.monto_cop)).where(
                Sponsorship.pet_id == pet_id, Sponsorship.activo.is_(True)
            )
        ).scalar_one()
        or 0
    )


def _novedad_apadrinamiento(nombre_pet: str) -> str:
    """Novedad de plantilla estática por apadrinamiento activo -- sin scheduler real
    en el repo, decisión de alcance documentada (ver progress/current.md)."""
    return (
        f"¡{nombre_pet} está mejor gracias a tu ayuda! "
        "Este mes comió bien y tuvo su chequeo veterinario."
    )


@router.get("/pets/necesitan-apoyo", response_model=list[MascotaNecesitaApoyoOut])
def listar_mascotas_necesitan_apoyo(
    session: Session = Depends(get_session),
) -> list[MascotaNecesitaApoyoOut]:
    """Mascotas disponibles y difíciles de ubicar (`services/deck.py::es_dificil_de_ubicar`,
    reutilizada vía un `PetOut` construido sin `home` -- esta lista es pública, sin
    `user_id`, no necesita afinidad). Lista vacía (200, no 404) si ninguna califica."""
    pets = session.execute(select(Pet).where(Pet.estado == "disponible")).scalars().all()

    resultado: list[MascotaNecesitaApoyoOut] = []
    for pet in pets:
        pet_out = _pet_out(pet, home=None)
        if not es_dificil_de_ubicar(pet_out):
            continue

        monto_recaudado_cop = _monto_recaudado_cop(session, pet.id)
        porcentaje_cubierto = min(100, round(monto_recaudado_cop / META_MENSUAL_COP * 100))

        resultado.append(
            MascotaNecesitaApoyoOut(
                id=pet.id,
                nombre=pet.nombre,
                fotos=pet.fotos,
                historia=pet.historia,
                monto_recaudado_cop=monto_recaudado_cop,
                porcentaje_cubierto=porcentaje_cubierto,
            )
        )
    return resultado


@router.post("/sponsorships", response_model=SponsorshipOut, status_code=status.HTTP_201_CREATED)
def crear_apadrinamiento(
    payload: SponsorshipIn, session: Session = Depends(get_session)
) -> SponsorshipOut:
    """Crea el compromiso de apadrinamiento. `monto_cop>0` y `periodicidad` ya
    validados por Pydantic (`schemas/sponsorship.py`, 422 automático)."""
    user = session.get(User, payload.user_id)
    if user is None:
        raise HTTPException(404, f"El usuario {payload.user_id} no existe")

    pet = session.get(Pet, payload.pet_id)
    if pet is None:
        raise HTTPException(404, f"La mascota {payload.pet_id} no existe")

    sponsorship = Sponsorship(activo=True, **payload.model_dump())
    session.add(sponsorship)
    session.commit()
    session.refresh(sponsorship)

    return SponsorshipOut(
        id=sponsorship.id,
        pet=SponsorshipPetResumen(id=pet.id, nombre=pet.nombre, fotos=pet.fotos),
        monto_cop=sponsorship.monto_cop,
        periodicidad=sponsorship.periodicidad,
        activo=sponsorship.activo,
        iniciado_en=sponsorship.iniciado_en,
        # Recién creado: todavía no hubo un mes de seguimiento sobre el que reportar
        # novedad (la plantilla estática describe algo que "pasó este mes").
        novedad=None,
    )


@router.get("/users/{user_id}/sponsorships", response_model=list[SponsorshipOut])
def listar_apadrinamientos_usuario(
    user_id: int, session: Session = Depends(get_session)
) -> list[SponsorshipOut]:
    """Todos los apadrinamientos del usuario (activos e inactivos). `novedad` de
    plantilla estática solo si `activo` es `True`."""
    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(404, f"El usuario {user_id} no existe")

    sponsorships = (
        session.execute(select(Sponsorship).where(Sponsorship.user_id == user_id)).scalars().all()
    )

    resultado: list[SponsorshipOut] = []
    for sponsorship in sponsorships:
        pet = session.get(Pet, sponsorship.pet_id)
        resultado.append(
            SponsorshipOut(
                id=sponsorship.id,
                pet=SponsorshipPetResumen(id=pet.id, nombre=pet.nombre, fotos=pet.fotos),
                monto_cop=sponsorship.monto_cop,
                periodicidad=sponsorship.periodicidad,
                activo=sponsorship.activo,
                iniciado_en=sponsorship.iniciado_en,
                novedad=_novedad_apadrinamiento(pet.nombre) if sponsorship.activo else None,
            )
        )
    return resultado
