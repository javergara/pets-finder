"""Títulos reconocibles para un reporte (feature 36) y para una mascota en
adopción (AD-08), product-research §9.

Cada función es el espejo de una del frontend: el nombre si lo tiene; si no,
"Perro mediano café" con los atributos presentes — para que la vista previa al
compartir (og tags) diga algo reconocible en vez de "Perro".

Los dos pares (`titulo_reporte`↔`tituloReporte`, `titulo_pet`↔`tituloMascota`)
son la misma regla escrita dos veces, en Python y en TypeScript, y **ningún
candado automático las mantiene sincronizadas**: la del backend alimenta el HTML
que ven los rastreadores y la del frontend lo que ve la persona. Es deuda
consciente; cada docstring apunta a su espejo para que se pueda contrastar.
"""

from ..models.pet import Pet
from ..models.report import Report

ETIQUETA_ESPECIE = {"perro": "Perro", "gato": "Gato", "otro": "Otro animal"}


def titulo_reporte(report: Report) -> str:
    """Espejo de `tituloReporte` (src/web/src/lib/titulo.ts)."""
    if report.nombre_mascota:
        return report.nombre_mascota

    partes = [
        ETIQUETA_ESPECIE.get(report.especie, "Mascota"),
        report.tamano,
        report.color.lower() if report.color and report.color != "Otro" else None,
    ]
    return " ".join(parte for parte in partes if parte)


def titulo_pet(pet: Pet) -> str:
    """Espejo de `tituloMascota` (src/web/src/lib/adopcion.ts): mismo orden de
    partes y mismas exclusiones.

    Dos diferencias con `titulo_reporte`, que vienen del modelo y no del gusto:
    `Pet.nombre` es obligatorio (por eso el `.strip()`: un formulario puede
    mandar espacios y un título en blanco se ve roto), y las señas las da la
    `raza`, no el `color` — con "Otra" fuera, que no aporta nada.

    `tamano` se interpola crudo ("mediano"), igual que en `titulo_reporte`: la
    etiqueta de la UI ("Mediana") vive en el frontend y aquí daría "Perro Mediana".
    """
    nombre = (pet.nombre or "").strip()
    if nombre:
        return nombre

    partes = [
        ETIQUETA_ESPECIE.get(pet.especie, "Mascota"),
        pet.tamano,
        pet.raza.lower() if pet.raza and pet.raza != "Otra" else None,
    ]
    return " ".join(parte for parte in partes if parte)
