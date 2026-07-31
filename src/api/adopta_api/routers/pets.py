from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.home_profile import HomeProfile
from ..models.pet import Pet
from ..models.swipe import Swipe
from ..schemas.pet import AfinidadOut, PetOut, ShelterOut
from ..services.affinity import calcular_afinidad
from ..services.db import get_session

router = APIRouter(prefix="/api/pets", tags=["pets"])


def _pet_out(pet: Pet, home: HomeProfile | None) -> PetOut:
    data = PetOut.model_validate(pet)
    data.shelter = ShelterOut.model_validate(pet.shelter)
    if home is not None:
        resultado = calcular_afinidad(pet, home)
        data.afinidad = AfinidadOut(
            score=resultado.score,
            explicacion=resultado.explicacion,
            incompatible=resultado.incompatible,
        )
    return data


@router.get("", response_model=list[PetOut])
def listar_mascotas(
    user_id: int | None = None,
    incluir_incompatibles: bool = False,
    session: Session = Depends(get_session),
) -> list[PetOut]:
    query = select(Pet).where(Pet.estado == "disponible")

    if user_id is not None:
        ya_swipeadas = select(Swipe.pet_id).where(Swipe.user_id == user_id)
        query = query.where(Pet.id.not_in(ya_swipeadas))

    pets = session.execute(query).scalars().all()

    home = None
    if user_id is not None:
        home = session.get(HomeProfile, user_id)
        if home is None:
            raise HTTPException(404, f"El usuario {user_id} no tiene HomeProfile (cuestionario)")

    resultados = [_pet_out(pet, home) for pet in pets]

    if home is not None and not incluir_incompatibles:
        resultados = [r for r in resultados if not (r.afinidad and r.afinidad.incompatible)]
        resultados.sort(key=lambda r: r.afinidad.score if r.afinidad else 0, reverse=True)

    return resultados


@router.get("/{pet_id}", response_model=PetOut)
def obtener_mascota(
    pet_id: int, user_id: int | None = None, session: Session = Depends(get_session)
) -> PetOut:
    pet = session.get(Pet, pet_id)
    if pet is None:
        raise HTTPException(404, "Mascota no encontrada")

    home = None
    if user_id is not None:
        home = session.get(HomeProfile, user_id)
        if home is None:
            raise HTTPException(404, f"El usuario {user_id} no tiene HomeProfile (cuestionario)")

    return _pet_out(pet, home)
