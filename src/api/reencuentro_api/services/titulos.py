"""Título reconocible para un reporte (feature 36, product-research §9).

Espejo del `tituloReporte` del frontend (src/web/src/lib/titulo.ts): el nombre
si lo tiene; si no, "Perro mediano café" con los atributos presentes — para que
la vista previa al compartir (og tags) diga algo reconocible en vez de "Perro".
"""

from ..models.report import Report

ETIQUETA_ESPECIE = {"perro": "Perro", "gato": "Gato", "otro": "Otro animal"}


def titulo_reporte(report: Report) -> str:
    if report.nombre_mascota:
        return report.nombre_mascota

    partes = [
        ETIQUETA_ESPECIE.get(report.especie, "Mascota"),
        report.tamano,
        report.color.lower() if report.color and report.color != "Otro" else None,
    ]
    return " ".join(parte for parte in partes if parte)
