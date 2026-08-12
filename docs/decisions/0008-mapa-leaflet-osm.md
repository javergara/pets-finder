# 0008 — Mapa real con Leaflet + OpenStreetMap

## Estado
Aceptado. Reemplaza la parte de "mapa propio sin dependencias" del ADR 0005 §5.

## Contexto

El pivot heredó de la era Adopta el lienzo CSS propio (interpolación lineal de lat/lng, sin tiles): correcto para reproducibilidad local sin red, pero sin calles ni geografía — el usuario lo percibió como "el mapa no funciona". Para una app real de emergencia, ubicar y encontrar una mascota exige un mapa de verdad. Se evaluó Google Maps (mejor estética, pero exige API key con facturación y tarjeta — inaceptable tras lo de Render) vs **Leaflet + tiles de OpenStreetMap** (gratis, sin API key, sin tarjeta, estándar open source). El usuario eligió Leaflet+OSM.

## Decisión

- `MapaLienzo` conserva su contrato (`zona`, `pines` con color por tipo, `onClickCoords`, `children`) pero renderiza un mapa Leaflet real: tiles de `tile.openstreetmap.org` con atribución, `fitBounds` al bounding box de la zona activa (`lib/ciudades.ts`, incluida la vista nacional), `CircleMarker` por pin con los hex de los tokens (`danger`/`forest`), tooltip con la etiqueta, y click del mapa que entrega **lat/lng reales** (adiós a la interpolación inversa: `lib/mapa.ts` se elimina).
- **Equivalente accesible**: además del mapa, cada pin se renderiza como botón real en una lista `sr-only` — es la ruta para lectores de pantalla y lo que ejercitan los tests (Leaflet no se inicializa en Vitest/jsdom: guard explícito `MODE === 'test'`, el contrato se verifica por la lista accesible y el mapa real por verificación manual en navegador).
- `leaflet` (+`@types/leaflet` en dev) es la única dependencia nueva del frontend.

## Consecuencias

- Los mapas de `/mapa`, el detalle y el formulario muestran calles reales; el click para ubicar el reporte es geográficamente exacto.
- Dependencia de red en runtime hacia los tiles de OSM (aceptada — es el punto de tener mapa real); la política de uso de tiles de OSM es adecuada para este volumen. Si algún día se necesita SLA de tiles: proveedor de tiles dedicado, sin cambiar código (solo la URL).
- El bundle crece ~44 kB gzip. `bash init.sh` sigue 100% verde offline (los tests no tocan Leaflet).
