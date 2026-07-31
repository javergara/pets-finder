# Créditos de fotos del seed

`scripts/seed.py` descarga una foto por mascota (una sola vez; si el archivo ya existe en `data/seed/images/` no se vuelve a descargar):

- **Perros:** [placedog.net](https://placedog.net) — servicio público de imágenes placeholder de perros, uso libre para desarrollo/pruebas.
- **Gatos:** [cataas.com](https://cataas.com) ("Cat as a Service") — servicio público de imágenes de gatos, uso libre para desarrollo/pruebas.

Ninguna de estas fotos corresponde a una mascota real de un refugio — son solo placeholders visuales para el MVP local.

## Fallback offline

Si la descarga falla (sin red, timeout, error HTTP), `scripts/seed.py` genera un SVG local simple con el nombre de la mascota sobre un color plano (mismo criterio de placeholder que `design/design-system.md`). El seed nunca falla por falta de conexión.
