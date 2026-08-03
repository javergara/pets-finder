"""Etiqueta de estado de una solicitud de adopción (vista del refugio, feature 09).

Función pura (sin I/O, sin DB): solo depende de `estado` y `creado_en` del `Match`.
El mapeo completo (5 valores de `Match.estado`, ver `models/match.py`) es:

- `visita_agendada` -> "Visita agendada"
- `solicitado` / `en_revision`, con menos de 2 días desde `creado_en` -> "Cuestionario nuevo"
- `solicitado` / `en_revision`, con 2 días o más desde `creado_en` ->
  "Sin responder · N días" (N = días transcurridos, entero)
- `adoptado` -> "Adopción cerrada"
- `cerrado` -> "Solicitud cerrada"

Ninguna transición de `Match.estado` ocurre acá ni en `routers/shelters.py` (ADR 0002):
esta función solo lee el estado para decidir qué texto mostrar.
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

    # "solicitado" o "en_revision": depende de cuántos días lleva sin respuesta.
    # `creado_en` puede venir naive al leerlo de SQLite vía SQLAlchemy aunque se haya
    # guardado con datetime.now(timezone.utc) -- se normaliza antes de restar para
    # evitar `TypeError: can't subtract offset-naive and offset-aware datetimes`.
    if creado_en.tzinfo is None:
        creado_en = creado_en.replace(tzinfo=timezone.utc)

    dias = (ahora - creado_en).days
    if dias < 2:
        return "Cuestionario nuevo"
    return f"Sin responder · {dias} días"
