# 0002 — El match no es mutuo (regla de negocio de backend, no solo de copy)

## Estado
Aceptado.

## Contexto
`design/prototypes/HANDOFF.md` §1 establece que, a diferencia de un Tinder genérico, el match en Adopta **no requiere aceptación de la otra parte**: cuando el adoptante desliza a la derecha ("Me interesa"), el match se crea de inmediato. El refugio no decide si existe el match; decide si acepta o rechaza la **solicitud de adopción**, un paso posterior. El cuestionario de hogar (`HomeProfile`) es obligatorio y es el input del cálculo de afinidad, no un formulario opcional de perfil.

Si esto se tratara solo como una decisión de copy/UI, sería fácil implementar por error un flujo de "doble consentimiento" (like del adoptante + aprobación del refugio para crear el match), que es el patrón por defecto en cualquier app de dating y el que un desarrollador asumiría sin este ADR.

## Decisión
- La tabla `Swipe` (dirección `like`/`pass`) es independiente de la tabla `Match`. Un `Swipe` con dirección `like` **crea un `Match` de forma automática y síncrona** en el mismo request (`POST /api/swipes`), sin ninguna acción del refugio.
- El estado inicial de un `Match` es `solicitado`; transiciones posteriores (`en_revision`, `visita_agendada`, `adoptado`, `cerrado`) las controla el refugio a través de la feature de backlog `10-adoption-request-flow`, y son sobre la **solicitud**, no sobre la existencia del match.
- La API expone `GET /api/matches?user_id=` mostrando todos los matches creados por like, sin filtrar por si el refugio "aceptó" — porque no hay tal aceptación de match.
- El score de afinidad requiere un `HomeProfile` existente para el usuario; en el MVP esto se resuelve con `HomeProfile` sintético sembrado (feature `01`), ya que el flujo interactivo de cuestionario (feature `08`) es backlog. La API no debe asumir que `HomeProfile` es opcional: es una relación 1:1 obligatoria con `User` en el modelo de datos.

## Consecuencias
- Los tests de `04-matches` deben verificar explícitamente que un `like` crea el match **sin ningún paso adicional** (no debe existir un endpoint de "aceptar match" — solo de aceptar/rechazar solicitud, en backlog).
- El copy de la UI (deck, ficha, modal de match) usa siempre "Me interesa" / "Ahora no", nunca "rechazar" — la capa de presentación respeta la misma decisión que la capa de datos.
