"""Mascotas en adopción (AD-01), el módulo `/adoptar`.

⚠️ Orden obligatorio de las rutas en este archivo: **literal antes que
dinámica**. `POST ""` → `GET ""` → `GET "/adopciones"` → `GET "/{pet_id}"`. Si
`/adopciones` se registrara después de `/{pet_id}`, FastAPI intentaría parsearla
como int y respondería 422 (misma regla que ya sigue `routers/reports.py`).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..models.organizacion import Organizacion
from ..models.pet import Pet
from ..models.report import Report
from ..models.user import User
from ..schemas.pet import PetIn, PetOut
from ..services.db import get_session

router = APIRouter(prefix="/api/pets", tags=["pets"])

REPORTE_YA_PUBLICADO = "Este reporte ya tiene una mascota publicada en adopción"


def _dueno_user_id(session: Session, pet: Pet) -> int | None:
    """Quién puede gestionar esta mascota: el autor de la organización que la
    publicó, o el rescatista dueño (`Pet.user_id`). Lo reusan las lecturas del
    paso 6 y la edición/borrado de AD-02.

    Devuelve `None` si la mascota cuelga de una organización que ya no existe
    (se puede eliminar, feature 32, y SQLite no fuerza las FK): así nadie queda
    autorizado, en vez de reventar con un 500 o autorizar de más.
    """
    if pet.organizacion_id is not None:
        organizacion = session.get(Organizacion, pet.organizacion_id)
        return organizacion.user_id if organizacion is not None else None
    return pet.user_id


def _mascota_del_reporte(session: Session, report_id: int) -> Pet | None:
    return session.scalar(select(Pet).where(Pet.report_id == report_id))


@router.post("", response_model=PetOut, status_code=status.HTTP_201_CREATED)
def publicar_mascota(payload: PetIn, session: Session = Depends(get_session)) -> PetOut:
    """Publica una mascota en adopción: cuelga de una organización O de un
    rescatista, nunca de ambos (el XOR lo rechaza `PetIn` con 422 en español).

    ⚠️ Colisión de nombres a tener presente: `payload.user_id` es **quien hace
    el request** (sirve para la autoría → 403), mientras que la columna
    `Pet.user_id` es **el rescatista dueño** de la mascota, que en el contrato
    HTTP viaja como `payload.rescatista_id`. Cuando publica una organización,
    `Pet.user_id` queda en `None`: nunca se guardan los dos.

    `report_id` (puente con un "encontrado" que nadie reclamó) aquí solo se
    valida como existente y no repetido; las reglas de tipo/situación/autoría
    del reporte son de AD-02.
    """
    if payload.organizacion_id is not None:
        organizacion = session.get(Organizacion, payload.organizacion_id)
        if organizacion is None:
            raise HTTPException(404, f"La organización {payload.organizacion_id} no existe")
        if organizacion.user_id != payload.user_id:
            raise HTTPException(
                403, "Solo quien registró la organización puede publicar mascotas en adopción"
            )

    if payload.rescatista_id is not None and session.get(User, payload.rescatista_id) is None:
        raise HTTPException(404, f"El usuario {payload.rescatista_id} no existe")

    if payload.report_id is not None:
        if session.get(Report, payload.report_id) is None:
            raise HTTPException(404, f"El reporte {payload.report_id} no existe")
        if _mascota_del_reporte(session, payload.report_id) is not None:
            raise HTTPException(409, REPORTE_YA_PUBLICADO)

    # El dueño rescatista se persiste en la columna `Pet.user_id` (ver el aviso
    # del docstring); `payload.user_id`, que es quien pide la operación, no se
    # guarda en ningún lado.
    pet = Pet(
        **payload.model_dump(exclude={"user_id", "rescatista_id"}),
        user_id=payload.rescatista_id,
    )
    session.add(pet)
    try:
        session.commit()
    except IntegrityError:
        # Carrera: otro request publicó el mismo `report_id` entre el select de
        # arriba y este commit. El índice único de la columna es la garantía
        # real; el select solo da el 409 limpio en el caso normal.
        session.rollback()
        if payload.report_id is not None and _mascota_del_reporte(session, payload.report_id):
            raise HTTPException(409, REPORTE_YA_PUBLICADO) from None
        raise
    session.refresh(pet)

    # `publicador` queda en None: lo completa el paso 6 con las queries batch de
    # `_publicadores_por_pet` (el modelo `Pet` no declara `relationship()`).
    return PetOut.model_validate(pet)
