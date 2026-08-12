# Sistema de diseño — Reencuentro

> Tokens heredados de la era Adopta (rama `adopta-v1`) — la paleta cálida/tierra es neutra y se reutiliza tal cual en el pivot. La fuente de verdad en código es `src/web/src/index.css` (bloque `@theme` de Tailwind v4, mismos nombres de token). Si este archivo y el código difieren, corregir el que esté desactualizado.

## Semántica del pivot

- **Perdido** = `danger` (#9B3B2E): badges, pins del mapa y CTA "Perdí a mi mascota".
- **Encontrado** = `forest` (#1F4D3A): badges, pins y CTA "Encontré una mascota".
- **Reunido** = `forest-tint` con texto `forest`: celebración, nunca lenguaje de fracaso.
- `ochre` queda para estados de espera/avisos neutros.

## Tema

**Un solo tema**, claro, cálido, institucional — no hay modo oscuro diseñado. No se sobre-diseña esto sin una necesidad de producto concreta.

## Color

| Token | Hex | Uso |
|---|---|---|
| `bg` | `#F7F3EA` | fondo de página |
| `surface` | `#FFFDF8` | tarjetas, barras, campos |
| `surface-alt` | `#F3EDE0` | encabezados de tabla, avisos neutros, lienzo del mapa |
| `ink` | `#1B1A17` | texto principal |
| `ink-soft` | `#3D3931` | párrafos largos |
| `muted` | `#6B665C` | texto secundario |
| `muted-2` | `#8A8172` | etiquetas mono, placeholders |
| `line` | `#E4DDCE` | bordes |
| `line-soft` | `#EFE9DC` | separadores internos |
| `forest` | `#1F4D3A` | acento primario, botones, "encontrado" |
| `forest-hover` | `#2E6E52` | hover del primario |
| `forest-tint` | `#E8EFE9` | fondos de acento (chips, franja de reencuentros) |
| `forest-tint-line` | `#CFDFD3` | borde sobre `forest-tint` |
| `ochre` | `#B57C2E` | avisos, estados en espera |
| `danger` | `#9B3B2E` | "perdido", acciones destructivas |

Sobre fondo `forest`: texto `#F7F3EA`, secundario `#C3D8CB`, etiquetas mono `#A8C6B4`, bordes `#4A8468`.

## Tipografía

- **Newsreader** (serif, 400/500) — titulares, nombres de mascota, cifras grandes. `letter-spacing: -0.015em` a `-0.025em` según tamaño.
- **Work Sans** (400/500/600) — interfaz y párrafos.
- **IBM Plex Mono** (400/500) — etiquetas de sección en mayúsculas (11px, `letter-spacing: .06em`), badges numéricos, metadatos.

Escala: display 66/44/40/38 · título de pantalla 30/26 · subtítulo 20-24 · cuerpo 14.5-16 · secundario 12.5-13.5 · etiqueta mono 11-11.5. Mínimo absoluto en móvil: 12px.

## Forma y profundidad

- Radios: 8-11px controles · 14-16px tarjetas · 9999px chips, pins y avatares.
- Bordes de 1px `line` en vez de sombras.
- Espaciado en múltiplos de 4; gutter de página 22px en móvil, 32-56px en escritorio.

## Imágenes

Fotos de reporte: proporción **4:3** en grillas y tarjetas, con el mismo radio de la tarjeta. Placeholder mientras carga: `repeating-linear-gradient(135deg, #EDE6D8 0 10px, #E4DBCA 10px 20px)`. Toda foto lleva `alt` descriptivo real (especie + nombre si se conoce), no `alt=""`.

## Estados

- **Vacío:** siempre con una acción concreta (nunca un mensaje sin salida) — p. ej. el listado vacío invita a crear el primer reporte.
- **Carga:** esqueletos con los mismos radios y el gradiente de placeholder de imágenes, nunca spinners.
- **Error:** copy en español, sin jerga técnica (ver `docs/conventions.md` §3).

## Accesibilidad

- El pin por click en el mapa tiene alternativa accesible (inputs de zona/barrio); ninguna acción depende solo de un gesto de puntero.
- Contraste mínimo AA: `forest` sobre `bg` e `ink` sobre `surface` cumplen; no usar `muted-2` para texto menor a 11px sobre fondos con textura.
- Objetivos táctiles ≥44px; chips de filtro en móvil 38-42px de alto visual con 44px de área efectiva de toque.
- `prefers-reduced-motion`: sin animaciones decorativas; transiciones de opacidad como máximo.
