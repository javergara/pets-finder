"""Etiqueta de estado y reglas de transición de una solicitud de adopción (vista del
refugio, features 09 y 10).

Funciones puras (sin I/O, sin DB): solo dependen de sus argumentos.

`calcular_etiqueta_solicitud(estado, creado_en, ahora=None)` mapea las 6 ramas de
`Match.estado` (ver `models/match.py`) a un texto:

- `visita_agendada` -> "Visita agendada"
- `en_revision` -> "En revisión" (sin importar cuántos días lleve)
- `solicitado`, con menos de 2 días desde `creado_en` -> "Cuestionario nuevo"
- `solicitado`, con 2 días o más desde `creado_en` ->
  "Sin responder · N días" (N = días transcurridos, entero)
- `adoptado` -> "Adopción cerrada"
- `cerrado` -> "Solicitud cerrada"

Ninguna transición de `Match.estado` ocurre en esta función ni en `routers/shelters.py`
al calcular la etiqueta (ADR 0002): solo lee el estado para decidir qué texto mostrar.

`validar_transicion(estado_actual, accion)` valida, contra la matriz `TRANSICIONES_VALIDAS`,
si una acción del refugio (`agendar-visita`, `pedir-informacion`, `descartar`) es aplicable
al estado actual de la solicitud; lanza `TransicionInvalidaError` si no lo es. Esta función
sí muta el estado -- o mejor dicho, decide si el llamador (el router) puede hacerlo -- pero
no persiste nada, es responsabilidad del router/DB.
"""

from datetime import datetime, timezone


def calcular_etiqueta_solicitud(
    estado: str, creado_en: datetime, ahora: datetime | None = None
) -> str:
    if ahora is None:
        ahora = datetime.now(timezone.utc)

    if estado == "visita_agendada":
        return "Visita agendada"
    if estado == "adoptado":
        return "Adopción cerrada"
    if estado == "cerrado":
        return "Solicitud cerrada"
    if estado == "en_revision":
        return "En revisión"

    # "solicitado": depende de cuántos días lleva sin respuesta.
    # `creado_en` puede venir naive al leerlo de SQLite vía SQLAlchemy aunque se haya
    # guardado con datetime.now(timezone.utc) -- se normaliza antes de restar para
    # evitar `TypeError: can't subtract offset-naive and offset-aware datetimes`.
    if creado_en.tzinfo is None:
        creado_en = creado_en.replace(tzinfo=timezone.utc)

    dias = (ahora - creado_en).days
    if dias < 2:
        return "Cuestionario nuevo"
    return f"Sin responder · {dias} días"


class TransicionInvalidaError(Exception):
    """El refugio intentó una acción sobre una solicitud en un estado que no la permite."""


TRANSICIONES_VALIDAS: dict[str, set[str]] = {
    "agendar-visita": {"solicitado", "en_revision"},
    "pedir-informacion": {"solicitado"},
    "descartar": {"solicitado", "en_revision", "visita_agendada"},
}


def validar_transicion(estado_actual: str, accion: str) -> None:
    """Lanza `TransicionInvalidaError` si `accion` no es aplicable desde `estado_actual`.

    Los estados terminales (`adoptado`, `cerrado`) nunca aparecen en ninguno de los sets
    de `TRANSICIONES_VALIDAS`, así que cualquier acción sobre una solicitud en esos
    estados siempre lanza la excepción -- no hace falta un caso especial para ellos.
    """
    if estado_actual not in TRANSICIONES_VALIDAS[accion]:
        raise TransicionInvalidaError(
            f"No se puede '{accion}' una solicitud en estado '{estado_actual}'"
        )
