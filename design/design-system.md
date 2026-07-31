# Sistema de diseño — Adopta

> Formaliza (no reemplaza) `design/prototypes/HANDOFF.md` §3 y §9. Fuente de verdad: los 3 prototipos interactivos en `design/prototypes/*.dc.html`. Si este archivo y un prototipo difieren, el prototipo manda y este archivo está desactualizado — corregirlo.

## Tema

**Un solo tema**, claro, cálido, institucional — no hay modo oscuro diseñado. Introducir uno requeriría redefinir todos los tokens de contraste (§3 de HANDOFF.md ya deja los valores para "sobre fondo verde", que es lo más cercano a un tema alterno que existe hoy) y no aporta al objetivo del MVP; no se sobre-diseña esto sin una necesidad de producto concreta.

## Color

| Token | Hex | Uso |
|---|---|---|
| `bg` | `#F7F3EA` | fondo de página |
| `surface` | `#FFFDF8` | tarjetas, barras, campos |
| `surface-alt` | `#F3EDE0` | encabezados de tabla, avisos neutros |
| `ink` | `#1B1A17` | texto principal |
| `ink-soft` | `#3D3931` | párrafos largos |
| `muted` | `#6B665C` | texto secundario |
| `muted-2` | `#8A8172` | etiquetas mono, placeholders |
| `line` | `#E4DDCE` | bordes |
| `line-soft` | `#EFE9DC` | separadores internos |
| `forest` | `#1F4D3A` | acento primario, botones, activos |
| `forest-hover` | `#2E6E52` | hover del primario |
| `forest-tint` | `#E8EFE9` | fondos de acento (chips, tarjetas de afinidad) |
| `forest-tint-line` | `#CFDFD3` | borde sobre `forest-tint` |
| `ochre` | `#B57C2E` | avisos, "ahora no", estados en espera |
| `danger` | `#9B3B2E` | acciones destructivas |

Sobre fondo `forest`: texto `#F7F3EA`, secundario `#C3D8CB`, etiquetas mono `#A8C6B4`, bordes `#4A8468`.

Estas claves se mapean 1:1 a `tailwind.config` en la Fase 7 (mismo nombre de token) — ver `docs/architecture.md` §3. No se traducen a nombres genéricos de Tailwind (`green-800`, etc.) para que el diseño y el código compartan vocabulario.

## Tipografía

- **Newsreader** (serif, 400/500) — titulares, nombres de mascota, cifras grandes. `letter-spacing: -0.015em` a `-0.025em` según tamaño.
- **Work Sans** (400/500/600) — interfaz y párrafos.
- **IBM Plex Mono** (400/500) — etiquetas de sección en mayúsculas (11px, `letter-spacing: .06em`), badges numéricos, metadatos.

Escala: display 66/44/40/38 · título de pantalla 30/26 · subtítulo 20-24 · cuerpo 14.5-16 · secundario 12.5-13.5 · etiqueta mono 11-11.5. Mínimo absoluto en móvil: 12px.

## Forma y profundidad

- Radios: 8-11px controles · 14-16px tarjetas · 20-22px tarjeta de swipe y hojas inferiores · 9999px chips y avatares.
- Bordes de 1px `line` en vez de sombras, salvo la tarjeta activa del deck de swipe: `0 18px 40px -28px rgba(27,26,23,.5)` — es la única sombra del sistema, y por eso mismo comunica "esto es lo interactivo ahora".
- Espaciado en múltiplos de 4; gutter de página 22px en móvil, 32-56px en escritorio.

## Imágenes

En los prototipos, toda foto es un placeholder (`repeating-linear-gradient(135deg, #EDE6D8 0 10px, #E4DBCA 10px 20px)` + etiqueta mono `foto · <nombre>`). Al implementar (Fase 7), se sustituye por la foto real manteniendo el mismo radio y proporción: **4:3** en grillas, **3:4** en la tarjeta de swipe.

## Estados

- **Vacío:** siempre con una acción concreta (nunca un mensaje sin salida) — ver cada archivo de `design/screens/`.
- **Carga:** esqueletos con los mismos radios y el gradiente de placeholder de imágenes, nunca spinners.
- **Error:** copy en español, sin jerga técnica (ver `docs/conventions.md` §3); el swipe específicamente encola y reintenta en vez de mostrar error bloqueante.

## Accesibilidad

- Toda acción de gesto (swipe) tiene un botón equivalente y atajo de teclado (`←` `→` `Enter` `Esc`) — es la ruta accesible obligatoria, no un extra.
- Contraste mínimo AA: `forest` sobre `bg` e `ink` sobre `surface` cumplen; no usar `muted-2` para texto menor a 11px sobre fondos con textura.
- Objetivos táctiles ≥44px; chips de filtro en móvil 38-42px de alto visual con 44px de área efectiva de toque.
- `prefers-reduced-motion`: desactiva el `popIn` del modal de match y la rotación de la tarjeta de swipe; el swipe pasa a transición de opacidad.
- Placeholders de foto llevan `alt` descriptivo real una vez conectadas las imágenes (Fase 7) — no `alt=""` ni el texto del placeholder.

## Gesto de swipe (referencia de implementación)

Ya implementado y validado en `design/prototypes/Adopta Web App.dc.html` — la Fase 7 lo reutiliza, no lo reinventa:

- Arrastre con Pointer Events: `translateX(dx) rotate(dx/22)`.
- Umbral: ±110px.
- Sellos "Me interesa" (verde, arriba-derecha, `rotate(-8deg)`) y "Ahora no" (ocre, arriba-izquierda, `rotate(8deg)`), con `opacity = clamp(|dx|/110)`.
- Si se suelta sin superar el umbral: `transform .28s cubic-bezier(.2,.8,.3,1)` de vuelta al centro.
- Teclado: `←`/`→` para swipe, `Enter` para abrir ficha.
- Botones inferiores equivalentes: `✕` (56px), `i` (46px), `♥` (56px).
