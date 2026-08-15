"""Orden del deck de descubrimiento (AD-03).

Afinidad descendente, con inserción periódica (cada 4-5 tarjetas) de mascotas
difíciles de ubicar (senior, con etiqueta "necesita experiencia", o publicadas
hace más de 90 días) — ver `docs/product-research.md` §5. Sin esto, el propio
score de afinidad esconde sistemáticamente a los animales que más necesitan
visibilidad.

Port de `origin/adopta-v1:src/api/adopta_api/services/deck.py` **sin cambios de
lógica**: solo el renombre del archivo al español, como el resto de servicios de
este repo. Trabaja sobre `PetOut` (schemas), no sobre modelos — por eso
`afinidad.py`, que trabaja sobre modelos, repite el literal 84 en vez de importar
`EDAD_MESES_SENIOR` de aquí.

⚠️ Quien no tenga perfil de hogar llega con `afinidad=None` en **todas** las
mascotas (decisión de AD-03: el deck responde 200 sin perfil). Ese es el camino
mayoritario, no un borde: el `else 0` del `sorted` los empata a todos y la
inserción de difíciles sigue siendo lo único que ordena algo.
"""

from datetime import datetime, timezone

from ..schemas.pet import PetOut

EDAD_MESES_SENIOR = 84
DIAS_PUBLICADA_DIFICIL = 90


def es_dificil_de_ubicar(pet: PetOut) -> bool:
    if pet.edad_meses > EDAD_MESES_SENIOR:
        return True
    if "necesita experiencia" in (pet.tags or []):
        return True
    # ⚠️ Naive a propósito, y no un descuido heredado: `pets.publicado_en` es
    # `timestamp without time zone` tanto en el `create_all` de SQLite como en
    # `migrations/AD-01-pets.sql`, así que llega naive. Restarle un datetime
    # aware lanza `TypeError` en producción. (Y nunca `datetime.UTC`: el
    # intérprete de este repo es 3.10.)
    ahora_naive_utc = datetime.now(timezone.utc).replace(tzinfo=None)
    dias_publicada = (ahora_naive_utc - pet.publicado_en).days
    return dias_publicada > DIAS_PUBLICADA_DIFICIL


def ordenar_deck(pets: list[PetOut]) -> list[PetOut]:
    ordenados_por_afinidad = sorted(
        pets, key=lambda p: p.afinidad.score if p.afinidad else 0, reverse=True
    )
    dificiles = [p for p in ordenados_por_afinidad if es_dificil_de_ubicar(p)]
    normales = [p for p in ordenados_por_afinidad if not es_dificil_de_ubicar(p)]

    if not dificiles:
        return ordenados_por_afinidad

    resultado: list[PetOut] = []
    idx_normal = idx_dificil = posicion = 0
    intervalo = 4  # alterna 4/5 para cubrir "cada 4-5 tarjetas"

    while idx_normal < len(normales) or idx_dificil < len(dificiles):
        posicion += 1
        toca_insertar_dificil = idx_dificil < len(dificiles) and posicion % intervalo == 0
        if toca_insertar_dificil:
            resultado.append(dificiles[idx_dificil])
            idx_dificil += 1
            intervalo = 9 - intervalo  # 4 -> 5 -> 4 -> ...
        elif idx_normal < len(normales):
            resultado.append(normales[idx_normal])
            idx_normal += 1
        else:
            resultado.append(dificiles[idx_dificil])
            idx_dificil += 1

    return resultado
