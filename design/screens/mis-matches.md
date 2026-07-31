# Mis matches (`/matches`)

**Alcance:** MVP (`feature_list.json` → `04-matches`). Fuente: `design/prototypes/HANDOFF.md` §5.5.

## Objetivo
Listar las mascotas con las que el adoptante hizo match (creado por like, no mutuo — ADR 0002), con su estado.

## Estructura
- Filtros de estado: `Todos` · `Esperando refugio` · `Visita agendada` (los dos últimos dependen de `10-adoption-request-flow`, backlog; en el MVP todos los matches nuevos quedan en `solicitado`).
- Escritorio: grilla `minmax(228px,1fr)`. Móvil: lista horizontal con miniatura de 76px.

## Componentes
- Cada tarjeta: foto, badge de afinidad, nombre, `edad · raza`, punto de estado (`forest` = visita agendada, `ochre` = esperando/en revisión) con su texto, y `Abrir conversación` (backlog `11-chat`; en MVP puede enlazar a la ficha de la mascota).

## Estados
- **Vacío:** enlace directo a Descubrir.
- **Mascota adoptada:** la tarjeta pasa a estado `adoptado` con mensaje del sistema; no se borra (ver `design/prototypes/HANDOFF.md` §8).
- **Refugio sin responder 3+ días:** aviso al adoptante de que puede seguir explorando; nunca se culpa al refugio en el copy (backlog, depende de `09-shelter-panel`).
