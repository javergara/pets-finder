"""Zonas cubiertas por Reencuentro: fuente de verdad de los bounding boxes.

Función pura / datos estáticos (sin I/O). Coordenadas reales aproximadas del
casco urbano de cada ciudad. `COLOMBIA` es el bounding box continental del país
(sin San Andrés): se usa como vista agregada del mapa y como lienzo para
reportar desde cualquier lugar del país (zona "Otro").

Duplicada conscientemente en `src/web/src/lib/ciudades.ts` (el frontend no
consulta estos valores por HTTP) — si cambian aquí, cambiar allá también.
"""

ZONAS: dict[str, dict[str, float]] = {
    "Armenia": {
        "lat_min": 4.49,
        "lat_max": 4.58,
        "lng_min": -75.75,
        "lng_max": -75.63,
        "centro_lat": 4.534,
        "centro_lng": -75.681,
    },
    "Pereira": {
        "lat_min": 4.77,
        "lat_max": 4.85,
        "lng_min": -75.76,
        "lng_max": -75.65,
        "centro_lat": 4.813,
        "centro_lng": -75.696,
    },
    "Manizales": {
        "lat_min": 5.02,
        "lat_max": 5.12,
        "lng_min": -75.55,
        "lng_max": -75.44,
        "centro_lat": 5.070,
        "centro_lng": -75.514,
    },
    "Cali": {
        "lat_min": 3.33,
        "lat_max": 3.50,
        "lng_min": -76.60,
        "lng_max": -76.44,
        "centro_lat": 3.452,
        "centro_lng": -76.532,
    },
    "Quibdó": {
        "lat_min": 5.65,
        "lat_max": 5.72,
        "lng_min": -76.68,
        "lng_max": -76.62,
        "centro_lat": 5.695,
        "centro_lng": -76.661,
    },
    "Bogotá": {
        "lat_min": 4.55,
        "lat_max": 4.80,
        "lng_min": -74.20,
        "lng_max": -74.00,
        "centro_lat": 4.65,
        "centro_lng": -74.08,
    },
}

COLOMBIA: dict[str, float] = {
    "lat_min": -4.3,
    "lat_max": 12.6,
    "lng_min": -79.1,
    "lng_max": -66.9,
    "centro_lat": 4.6,
    "centro_lng": -74.1,
}

# Reportes desde fuera de las zonas con bounding box propio: el pin se pone
# sobre el mapa nacional y la ciudad real va en texto libre (Report.ciudad_texto).
ZONA_OTRO = "Otro"


def zona_valida(zona: str) -> bool:
    return zona in ZONAS or zona == ZONA_OTRO
