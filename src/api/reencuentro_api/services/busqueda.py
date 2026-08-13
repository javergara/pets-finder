"""Busca a tu mascota (feature 38): parecido explicable, sin AI.

El dueño describe a su mascota y la app rankea los reportes del tipo relevante
por parecido. Benchmark encontradogs (product-research §9), con la misma regla
de UX: lo que se deja en blanco simplemente no se compara — el porcentaje es
relativo a los criterios que sí se dieron, no a un máximo absoluto.

Función pura (sin I/O): recibe la consulta y los candidatos ya cargados.
"""

import unicodedata
from dataclasses import dataclass

from ..models.report import Report

PESO_ZONA = 25
PESO_COLOR = 20
PESO_TAMANO = 15
PESO_SENAS = 40

# Palabras que no describen a una mascota: conectores y verbos de relleno.
_STOPWORDS = {
    "con",
    "una",
    "uno",
    "unas",
    "unos",
    "las",
    "los",
    "del",
    "que",
    "por",
    "para",
    "muy",
    "tiene",
    "esta",
    "este",
    "cuando",
    "donde",
    "como",
    "pero",
    "mas",
    "sus",
}


@dataclass(frozen=True)
class ConsultaBusqueda:
    especie: str
    zona: str | None = None
    color: str | None = None
    tamano: str | None = None
    senas: str | None = None


def _normalizar(texto: str) -> str:
    """Minúsculas y sin tildes: 'Café' y 'cafe' deben coincidir."""
    sin_tildes = "".join(
        c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn"
    )
    return sin_tildes.lower()


def _palabras(texto: str) -> set[str]:
    tokens = "".join(c if c.isalnum() else " " for c in _normalizar(texto)).split()
    return {t for t in tokens if len(t) >= 3 and t not in _STOPWORDS}


def puntuar_reporte(consulta: ConsultaBusqueda, reporte: Report) -> tuple[int, list[str]]:
    """(parecido 0-100, razones) de un candidato frente a la consulta.

    El parecido es la fracción de los criterios DADOS que el reporte cumple,
    ponderada por peso; con señas, el aporte es proporcional al solapamiento
    de palabras entre las señas y el texto del reporte.
    """
    puntos = 0.0
    maximo = 0
    razones: list[str] = []

    if consulta.zona:
        maximo += PESO_ZONA
        if reporte.zona == consulta.zona:
            puntos += PESO_ZONA
            razones.append(f"misma zona ({reporte.zona})")

    if consulta.color and consulta.color != "Otro":
        maximo += PESO_COLOR
        if reporte.color == consulta.color:
            puntos += PESO_COLOR
            razones.append(f"mismo color ({reporte.color.lower()})")

    if consulta.tamano:
        maximo += PESO_TAMANO
        if reporte.tamano == consulta.tamano:
            puntos += PESO_TAMANO
            razones.append(f"mismo tamaño ({reporte.tamano})")

    if consulta.senas and _palabras(consulta.senas):
        maximo += PESO_SENAS
        buscadas = _palabras(consulta.senas)
        texto_reporte = " ".join(
            parte
            for parte in (
                reporte.descripcion,
                reporte.nombre_mascota,
                reporte.raza,
                reporte.barrio,
            )
            if parte
        )
        comunes = buscadas & _palabras(texto_reporte)
        if comunes:
            puntos += PESO_SENAS * len(comunes) / len(buscadas)
            muestra = ", ".join(sorted(comunes)[:4])
            razones.append(f"señas en común: {muestra}")

    parecido = round(100 * puntos / maximo) if maximo else 0
    return parecido, razones


def buscar_parecidos(
    consulta: ConsultaBusqueda, candidatos: list[Report]
) -> list[tuple[Report, int, list[str]]]:
    """Solo la especie pedida, ordenados por parecido (desc) y recencia."""
    puntuados = []
    for reporte in candidatos:
        if reporte.especie != consulta.especie:
            continue
        parecido, razones = puntuar_reporte(consulta, reporte)
        puntuados.append((reporte, parecido, razones))

    puntuados.sort(key=lambda item: (-item[1], -item[0].id))
    return puntuados
