# Descubrir (`/descubrir`)

**Alcance:** MVP (`feature_list.json` → `02-swipe-deck`, `06-filters` post-MVP). Fuente: `design/prototypes/HANDOFF.md` §5.2 + `design/prototypes/Adopta Web App.dc.html`.

## Objetivo
Deck de descubrimiento tipo swipe con afinidad visible, para que el adoptante decida "Me interesa" o "Ahora no" mascota por mascota.

## Estructura
- Escritorio: columna central con la baraja + carril derecho de filtros.
- Móvil: baraja a ancho completo (menos 44px) + hoja inferior de filtros.
- Baraja de 3 capas: dos de atrás son rectángulos vacíos (`translateY(11px) scale(.97)`, `translateY(22px) scale(.94)`), la de arriba es la tarjeta interactiva (420×560 escritorio).

## Componentes
- **Tarjeta:** foto (flex:1) + badges superiores izquierdos (`NN% afín` sobre `forest`, `N,N km` sobre `surface` con borde) + contador de fotos. Bloque inferior: nombre (Newsreader 25-27px) + `edad · raza` (`muted`); chips de personalidad (máx. 3, `forest-tint`); pie con nombre del refugio + botón `Ver ficha`.
- **Botones de acción equivalentes al gesto:** `✕` "Ahora no" (56px), `i` abrir ficha (46px), `♥` "Me interesa" (56px).
- **Filtros** (post-MVP, `06-filters`): especie, tamaño, distancia (slider, 15km default), edad, energía, convivencia (niños/perros/gatos). Chips multi-selección. Contador `N perfiles cerca de ti`. Botón `Restablecer filtros`.

## Comportamiento del swipe
Ver `design/design-system.md` §"Gesto de swipe" — arrastre, umbral ±110px, sellos, retorno animado, equivalentes de teclado y botón. Al superar el umbral hacia la derecha: `POST /api/swipes` con dirección `like` → crea `Match` de inmediato (ADR 0002) y dispara la pantalla de match. Hacia la izquierda: `POST /api/swipes` con dirección `pass`, sin modal.

## Estados
- **Carga:** esqueletos de tarjeta con el mismo radio (20-22px) y gradiente de placeholder.
- **Vacío (fin de la baraja):** sugiere ampliar el radio o quitar filtros; ofrece "Avísame cuando lleguen nuevos perfiles" (backlog, notificaciones).
- **Error de red en el swipe:** se encola localmente y se reintenta — el gesto nunca se bloquea (ver `docs/conventions.md` §3).

## Orden de la baraja
Afinidad descendente (ver `docs/decisions/0003-afinidad-calculada-al-vuelo.md`), con inserción de una mascota difícil de ubicar (senior, condición médica, >90 días publicada) cada 4-5 tarjetas.
