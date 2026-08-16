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
    misma especie y activos; la zona dejó de ser filtro duro con el ADR 0012,
    pero la puerta de puntaje de abajo los descarta igual), excluyendo las
    parejas ya avisadas, con tope de `MAX_POR_REPORTE` y descartando puntajes
    peores que `PUNTAJE_MAX`.
    """
    resultado = []
    for perdido in perdidos:
        nuevas = 0
        # El motor devuelve también la similitud visual (ADR 0012); el radar
        # no la usa todavía: su puerta de calidad sigue siendo distancia+días,
        # que ya descarta por sí sola a los candidatos de otra zona. Si algún
        # día se quiere avisar por un parecido fuerte y lejano, este es el
        # lugar — pero es una decisión de producto del radar, no del motor.
        for candidato, distancia, _similitud in ordenar_coincidencias(perdido, candidatos):
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
