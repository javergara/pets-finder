# Match (modal / pantalla completa en móvil)

**Alcance:** MVP (`feature_list.json` → `02-swipe-deck`, `04-matches`). Fuente: `design/prototypes/HANDOFF.md` §5.4.

## Objetivo
Confirmar que el like creó el match de inmediato (ADR 0002 — no hay "aceptación" del refugio en este paso) y dar la siguiente acción clara.

## Cuándo se dispara
Al deslizar a la derecha en Descubrir o al pulsar `Me interesa adoptar` en la ficha.

## Estructura
- Escritorio: modal de 420px sobre `rgba(27,26,23,.42)`, animación `popIn .24s cubic-bezier(.2,.8,.3,1)` (desactivada con `prefers-reduced-motion`).
- Móvil: pantalla completa en `forest`.

## Contenido
- Etiqueta mono `Nuevo match`.
- Foto circular de la mascota.
- Titular `Te interesa <Nombre>`.
- Texto explicando que se envió el perfil y el cuestionario al refugio, con su tiempo de respuesta estimado.
- Dos acciones: `Escribir al refugio` (primaria — lleva a Mensajes, backlog `11-chat`; en el MVP puede llevar a la ficha del match si Mensajes no está implementado aún) y `Seguir viendo perfiles` (vuelve a Descubrir).

## Nota de alcance MVP
El envío real del cuestionario al refugio (`HomeProfile`) usa el sintético del seed en el MVP (ver `docs/product-research.md` §7); el copy no debe prometer nada que el backend no haga todavía (p. ej. no decir "chateando ahora" si `11-chat` sigue en backlog — usar el texto de tiempo de respuesta, que sí aplica).
