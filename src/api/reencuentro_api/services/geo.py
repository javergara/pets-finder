"""Distancia entre coordenadas geográficas.

Función pura (sin I/O): base del ordenamiento por cercanía entre un reporte
perdido y los encontrados candidatos (services/coincidencias.py, feature 08).
"""

import math

_RADIO_TIERRA_KM = 6371.0


def distancia_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Distancia en línea recta entre dos puntos (fórmula haversine)."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lng2 - lng1)

    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    return 2 * _RADIO_TIERRA_KM * math.asin(math.sqrt(a))
