"""Radar de reencuentros (feature 43): qué parejas avisar en cada corrida.

Función pura sobre el motor de coincidencias existente: el radar no inventa
un score nuevo — reutiliza el orden determinista de `ordenar_coincidencias`
(distancia + penalización por días, ADR 0003 del plan de impacto) y solo
decide QUÉ es novedad digna de un correo.
"""

from ..models.report import Report
from .coincidencias import PESO_DIAS, ordenar_coincidencias, razones_coincidencia

MAX_POR_REPORTE = 3
# Umbral generoso: ~15 km-equivalentes (una pareja a 5 km y 20 días de
# diferencia ya no es creíble; una a 1 km y el mismo día, sí).
PUNTAJE_MAX = 15.0


def parejas_a_avisar(
    perdidos: list[Report],
    candidatos: list[Report],
    ya_avisadas: set[tuple[int, int]],
) -> list[tuple[Report, Report, float, list[str]]]:
    """[(perdido, candidato, distancia_km, razones)] — solo parejas nuevas.

    Por cada perdido activo: candidatos que el motor ya ordena (tipo opuesto,
    misma especie/zona, activos), excluyendo las parejas ya avisadas, con tope
    de `MAX_POR_REPORTE` y descartando puntajes peores que `PUNTAJE_MAX`.
    """
    resultado = []
    for perdido in perdidos:
        nuevas = 0
        for candidato, distancia in ordenar_coincidencias(perdido, candidatos):
            if nuevas >= MAX_POR_REPORTE:
                break
            if (perdido.id, candidato.id) in ya_avisadas:
                continue
            dias = abs((perdido.fecha_evento - candidato.fecha_evento).days)
            if distancia + PESO_DIAS * dias > PUNTAJE_MAX:
                continue
            razones = razones_coincidencia(perdido, candidato, distancia)
            resultado.append((perdido, candidato, distancia, razones))
            nuevas += 1
    return resultado
