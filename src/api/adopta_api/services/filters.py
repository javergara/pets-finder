"""Filtros de descubrimiento (especie, tamaño, energía, edad, convivencia, distancia).

Función pura (sin I/O, sin SQLAlchemy/FastAPI) — se aplica en routers/pets.py
antes de la exclusión de incompatibles y de ordenar_deck() (ver
docs/architecture.md §2 y design/prototypes/HANDOFF.md §5.2). Independiente de
la regla dura de services/affinity.py: los toggles de convivencia de esta
feature (apto_ninos/apto_perros/apto_gatos) no reemplazan ni dependen de esa
regla, ambas pueden aplicar a la vez.
"""

import math
from dataclasses import dataclass

from ..schemas.pet import PetOut
from .deck import EDAD_MESES_SENIOR
from .geo import distancia_km

# Rangos en meses por categoría de edad. El límite de "senior" se importa de
# services/deck.py (EDAD_MESES_SENIOR) para no duplicar el número 84.
EDAD_CATEGORIA_RANGOS: dict[str, tuple[int, float]] = {
    "cachorro": (0, 11),
    "joven": (12, 35),
    "adulto": (36, EDAD_MESES_SENIOR - 1),
    "senior": (EDAD_MESES_SENIOR, math.inf),
}


def _categoria_de_edad(edad_meses: int) -> str:
    for categoria, (minimo, maximo) in EDAD_CATEGORIA_RANGOS.items():
        if minimo <= edad_meses <= maximo:
            return categoria
    return "senior"  # inalcanzable: el rango de "senior" no tiene tope superior


@dataclass(frozen=True)
class FiltrosDeck:
    especie: list[str] | None = None
    tamano: list[str] | None = None
    energia: list[str] | None = None
    edad_categoria: list[str] | None = None
    apto_ninos: bool | None = None
    apto_perros: bool | None = None
    apto_gatos: bool | None = None
    distancia_km: float | None = None


def aplicar_filtros(
    pets: list[PetOut],
    filtros: FiltrosDeck,
    user_lat: float | None,
    user_lng: float | None,
) -> list[PetOut]:
    """Filtra el deck según ``filtros`` y calcula ``distancia_km`` al vuelo.

    Un filtro con valor ``None`` (o lista vacía) no restringe esa dimensión.
    Si falta alguna coordenada (usuario o mascota), la mascota no se excluye
    por distancia: se le asigna ``distancia_km=None`` y pasa ese filtro sin
    evaluarse (degradación elegante, ver progress/current.md).
    """
    resultado: list[PetOut] = []

    for pet in pets:
        distancia: float | None = None
        if user_lat is not None and user_lng is not None:
            if pet.lat is not None and pet.lng is not None:
                distancia = distancia_km(user_lat, user_lng, pet.lat, pet.lng)

        pet_con_distancia = pet.model_copy(update={"distancia_km": distancia})

        if filtros.especie and pet.especie not in filtros.especie:
            continue
        if filtros.tamano and pet.tamano not in filtros.tamano:
            continue
        if filtros.energia and pet.energia not in filtros.energia:
            continue
        if (
            filtros.edad_categoria
            and _categoria_de_edad(pet.edad_meses) not in filtros.edad_categoria
        ):
            continue
        if filtros.apto_ninos is not None and pet.apto_ninos != filtros.apto_ninos:
            continue
        if filtros.apto_perros is not None and pet.apto_perros != filtros.apto_perros:
            continue
        if filtros.apto_gatos is not None and pet.apto_gatos != filtros.apto_gatos:
            continue
        if (
            filtros.distancia_km is not None
            and distancia is not None
            and distancia > filtros.distancia_km
        ):
            continue

        resultado.append(pet_con_distancia)

    return resultado
