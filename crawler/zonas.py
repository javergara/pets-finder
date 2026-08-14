"""Resolución de zona para reportes crawleados.

Las zonas y sus centros vienen de la fuente de verdad de la API
(services/ciudades.py, importada vía crawler/__init__) — si el proyecto suma
una zona (como Medellín en la feature 26), el crawler la ve automáticamente.
"""

import unicodedata

from reencuentro_api.services.ciudades import COLOMBIA, ZONA_OTRO, ZONAS

CENTROS: dict[str, tuple[float, float]] = {
    zona: (caja["centro_lat"], caja["centro_lng"]) for zona, caja in ZONAS.items()
}

CENTRO_COLOMBIA: tuple[float, float] = (COLOMBIA["centro_lat"], COLOMBIA["centro_lng"])


def normalizar_texto(texto: str) -> str:
    sin_tildes = unicodedata.normalize("NFD", texto)
    sin_tildes = "".join(c for c in sin_tildes if unicodedata.category(c) != "Mn")
    return sin_tildes.strip().lower()


def resolver_zona(ciudad_texto: str | None) -> tuple[str, str | None, float, float]:
    """Mapea la ciudad extraída a (zona, ciudad_texto, lat, lng).

    Los posts casi nunca traen coordenadas: el pin cae en el centro de la zona
    (el mismo fallback que usa el formulario web cuando no mueven el pin). Una
    ciudad fuera de las zonas va como "Otro" + ciudad_texto; sin ciudad, el
    reporte cae en "Otro" / "Colombia" sobre el mapa nacional.
    """
    if ciudad_texto and ciudad_texto.strip():
        buscado = normalizar_texto(ciudad_texto)
        for zona, (lat, lng) in CENTROS.items():
            if normalizar_texto(zona) == buscado:
                return zona, None, lat, lng
        lat, lng = CENTRO_COLOMBIA
        return ZONA_OTRO, ciudad_texto.strip(), lat, lng
    lat, lng = CENTRO_COLOMBIA
    return ZONA_OTRO, "Colombia", lat, lng
