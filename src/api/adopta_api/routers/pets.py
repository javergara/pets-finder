from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.favorite import Favorite
from ..models.home_profile import HomeProfile
from ..models.pet import Pet
from ..models.shelter import Shelter
from ..models.swipe import Swipe
from ..models.user import User
from ..schemas.pet import AfinidadOut, PetIn, PetOut, ShelterOut
from ..services.affinity import calcular_afinidad
from ..services.db import get_session
from ..services.deck import ordenar_deck
from ..services.filters import FiltrosDeck, aplicar_filtros

router = APIRouter(prefix="/api/pets", tags=["pets"])


def _pet_out(pet: Pet, home: HomeProfile | None, favoritos: set[int] | None = None) -> PetOut:
    data = PetOut.model_validate(pet)
    data.shelter = ShelterOut.model_validate(pet.shelter)
    if home is not None:
        resultado = calcular_afinidad(pet, home)
        data.afinidad = AfinidadOut(
            score=resultado.score,
            explicacion=resultado.explicacion,
            incompatible=resultado.incompatible,
        )
    if favoritos is not None:
        data.es_favorito = pet.id in favoritos
    return data


@router.get("", response_model=list[PetOut])
def listar_mascotas(
    user_id: int | None = None,
    incluir_incompatibles: bool = False,
    especie: list[str] | None = Query(None),
    tamano: list[str] | None = Query(None),
    energia: list[str] | None = Query(None),
    edad_categoria: list[str] | None = Query(None),
    apto_ninos: bool | None = None,
    apto_perros: bool | None = None,
    apto_gatos: bool | None = None,
    distancia_km: float | None = 15.0,
    session: Session = Depends(get_session),
) -> list[PetOut]:
    query = select(Pet).where(Pet.estado == "disponible")

    if user_id is not None:
        ya_swipeadas = select(Swipe.pet_id).where(Swipe.user_id == user_id)
        query = query.where(Pet.id.not_in(ya_swipeadas))

    pets = session.execute(query).scalars().all()

    home = None
    user_lat: float | None = None
    user_lng: float | None = None
    favoritos: set[int] | None = None
    if user_id is not None:
        home = session.get(HomeProfile, user_id)
        if home is None:
            raise HTTPException(404, f"El usuario {user_id} no tiene HomeProfile (cuestionario)")
        user = session.get(User, user_id)
        if user is not None:
            user_lat = user.lat
            user_lng = user.lng
        favoritos = set(
            session.execute(select(Favorite.pet_id).where(Favorite.user_id == user_id)).scalars()
        )

    resultados = [_pet_out(pet, home, favoritos) for pet in pets]

    filtros = FiltrosDeck(
        especie=especie,
        tamano=tamano,
        energia=energia,
        edad_categoria=edad_categoria,
        apto_ninos=apto_ninos,
        apto_perros=apto_perros,
        apto_gatos=apto_gatos,
        distancia_km=distancia_km,
    )
    resultados = aplicar_filtros(resultados, filtros, user_lat, user_lng)

    if home is not None and not incluir_incompatibles:
        resultados = [r for r in resultados if not (r.afinidad and r.afinidad.incompatible)]
        resultados = ordenar_deck(resultados)

    return resultados


@router.post("", response_model=PetOut, status_code=status.HTTP_201_CREATED)
def publicar_mascota(payload: PetIn, session: Session = Depends(get_session)) -> PetOut:
    """Publica una mascota nueva asociada a un refugio existente (feature `09-shelter-panel`).

    Valida que `shelter_id` exista ANTES de insertar. `estado` no viene en el payload:
    queda en su default `"disponible"` del modelo. Sin `lat`/`lng` (el formulario de
    publicación no captura ubicación individual, ver `schemas/pet.py::PetIn`).
    """
    shelter = session.get(Shelter, payload.shelter_id)
    if shelter is None:
        raise HTTPException(404, f"El refugio {payload.shelter_id} no existe")

    pet = Pet(**payload.model_dump())
    session.add(pet)
    session.commit()
    session.refresh(pet)

    return _pet_out(pet, home=None)


@router.get("/{pet_id}", response_model=PetOut)
def obtener_mascota(
    pet_id: int, user_id: int | None = None, session: Session = Depends(get_session)
) -> PetOut:
    pet = session.get(Pet, pet_id)
    if pet is None:
        raise HTTPException(404, "Mascota no encontrada")

    home = None
    favoritos: set[int] | None = None
    if user_id is not None:
        home = session.get(HomeProfile, user_id)
        if home is None:
            raise HTTPException(404, f"El usuario {user_id} no tiene HomeProfile (cuestionario)")
        favoritos = set(
            session.execute(select(Favorite.pet_id).where(Favorite.user_id == user_id)).scalars()
        )

    return _pet_out(pet, home, favoritos)
