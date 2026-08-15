"""Filtros del deck de descubrimiento (AD-03).

Función pura (sin I/O, sin SQLAlchemy ni FastAPI): recibe `PetOut` y devuelve
`PetOut`, calculando de paso la `distancia_km` de cada mascota a quien busca. La
aplica `routers/pets.py` en el deck, antes de excluir incompatibles y de
`descubrir.ordenar_deck()` (ver `docs/architecture.md` §2).

Es independiente de la regla dura de `services/afinidad.py`: los toggles de
convivencia de aquí (`apto_ninos`/`apto_perros`/`apto_gatos`) no la reemplazan ni
dependen de ella — las dos pueden aplicar a la vez.

Port de `origin/adopta-v1:src/api/adopta_api/services/filters.py` con tres
cambios y ninguno más:

1. `FiltrosDeck` gana **`zona`** (el filtro primario de un catálogo de seis
   ciudades; en adopta-v1, con una sola ciudad, no existía) y **`tags`**, que se
   resuelve aquí porque en SQL no es portable: la columna es JSON —TEXT en
   SQLite, `json` en Postgres— y ni `LIKE` ni `->>` funcionan en las dos. Por eso
   `tags` tampoco se ofrece como chip en la UI.
2. **`distancia_km` pierde el default de 15.0 y pasa a `None`.** Aquel radio
   venía de un producto urbano de Bogotá donde toda mascota tenía coordenadas;
   aquí muchas no tienen pin y el país entero es el alcance, así que un default
   así escondía resultados **en silencio**, sin que nadie hubiera pedido filtrar
   por distancia. La degradación elegante (sin lat/lng no se excluye a nadie) se
   conserva íntegra.
3. `EDAD_CATEGORIA_RANGOS` es ahora la **fuente de verdad única** de los tramos:
   `listar_mascotas` los traduce a SQL a partir de este diccionario en vez de
   repetir los cortes (ver `routers/pets.py::_condicion_edad`).

⚠️ Los mismos cortes están duplicados a conciencia en `src/web/src/lib/adopcion.ts`
(`MESES_JOVEN`/`MESES_ADULTO`/`MESES_SENIOR`), igual que pasa con
`services/ciudades.py` y `lib/ciudades.ts`: si cambian aquí, cambian allá.
"""

import math
from dataclasses import dataclass

from ..schemas.pet import PetOut
from .descubrir import EDAD_MESES_SENIOR
from .geo import distancia_km

# Rangos en meses por categoría de edad, ambos extremos incluidos. El corte de
# "senior" se importa de `descubrir.py` para no volver a escribir el 84: los dos
# módulos trabajan sobre `PetOut`, así que la dependencia es legal y no hay ciclo
# (`afinidad.py`, que trabaja sobre modelos, sí repite el literal a propósito).
# `math.inf` significa "sin tope superior".
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
    """Qué pide quien busca. `None` (o lista vacía) = ese criterio no restringe."""

    especie: list[str] | None = None
    tamano: list[str] | None = None
    energia: list[str] | None = None
    edad_categoria: list[str] | None = None
    zona: list[str] | None = None
    tags: list[str] | None = None
    apto_ninos: bool | None = None
    apto_perros: bool | None = None
    apto_gatos: bool | None = None
    # Sin default de radio a propósito (ver el punto 2 del docstring del módulo).
    distancia_km: float | None = None


def aplicar_filtros(
    pets: list[PetOut],
    filtros: FiltrosDeck,
    user_lat: float | None,
    user_lng: float | None,
) -> list[PetOut]:
    """Filtra el deck según ``filtros`` y calcula ``distancia_km`` al vuelo.

    Un filtro con valor ``None`` (o lista vacía) no restringe esa dimensión.
    Si falta alguna coordenada (usuario o mascota), la mascota **no se excluye**
    por distancia: se le asigna ``distancia_km=None`` y pasa ese filtro sin
    evaluarse. Esa degradación elegante es la que hace usable el filtro en este
    repo, donde la mayoría de las mascotas no tiene pin.

    Las listas son OR dentro del criterio y AND entre criterios, igual que los
    chips del catálogo (`listar_mascotas`): "perros o gatos, y además grandes".
    En ``tags`` basta con que la mascota tenga **alguna** de las pedidas.
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
        if filtros.zona and pet.zona not in filtros.zona:
            continue
        if filtros.tags and not set(filtros.tags) & set(pet.tags or []):
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
