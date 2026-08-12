"""Posibles coincidencias entre reportes perdidos y encontrados.

Función pura (sin I/O, sin DB): recibe el reporte de referencia y los candidatos
ya cargados, y devuelve los que podrían ser la misma mascota, ordenados del más
probable al menos probable. Sin AI (docs/product-research.md §2): el criterio es
explicable — misma especie, misma zona, cerca en el mapa y cerca en el tiempo.

El puntaje de ordenamiento es `distancia_km + PESO_DIAS * |Δdías|`: un día de
diferencia "cuesta" lo mismo que medio kilómetro. Es una heurística deliberada
y simple, no una probabilidad — por eso la UI habla de "posibles coincidencias".
"""

from ..models.report import Report
from .geo import distancia_km

PESO_DIAS = 0.5


def _tipo_opuesto(tipo: str) -> str:
    return "encontrado" if tipo == "perdido" else "perdido"


def ordenar_coincidencias(reporte: Report, candidatos: list[Report]) -> list[tuple[Report, float]]:
    """Filtra y ordena candidatos; devuelve pares (candidato, distancia_km).

    Filtro: tipo opuesto al del reporte, misma especie, misma zona y estado
    "activo". El propio reporte nunca es candidato de sí mismo (lo excluye el
    filtro de tipo). La distancia devuelta es la geográfica real (sin la
    penalización por fecha) — es lo que se muestra en la UI.
    """
    tipo_buscado = _tipo_opuesto(reporte.tipo)

    puntuados: list[tuple[Report, float, float]] = []
    for candidato in candidatos:
        if candidato.tipo != tipo_buscado:
            continue
        if candidato.especie != reporte.especie:
            continue
        if candidato.zona != reporte.zona:
            continue
        if candidato.estado != "activo":
            continue

        distancia = distancia_km(reporte.lat, reporte.lng, candidato.lat, candidato.lng)
        dias = abs((reporte.fecha_evento - candidato.fecha_evento).days)
        puntaje = distancia + PESO_DIAS * dias
        puntuados.append((candidato, distancia, puntaje))

    puntuados.sort(key=lambda item: item[2])
    return [(candidato, round(distancia, 2)) for candidato, distancia, _ in puntuados]
