# Verificación — Reencuentro 2.0.0

> La evidencia de la era Adopta vive en la rama `adopta-v1` (`git show adopta-v1:docs/verification.md`).

Todo lo de abajo se ejecutó de verdad el 2026-08-12 durante la feature `10-verificacion-final` (ver `CHECKPOINTS.md`, "qué NO es un checkpoint válido").

## 1. `bash init.sh` — verde completo

```
== 1. Dependencias del sistema ==   ✓ python3 / node / npm
== 2. feature_list.json ==          ✓ válido (validate_feature_list.py exit 0)
== 3. Entorno Python (.venv) ==     ✓ deps instaladas (única nueva: python-multipart)
== 5. Datos semilla (SQLite) ==     ✓ Seed listo: 5 usuarios, 17 reportes (15 activos, 2 reunidos)
== 7. Lint ==                       ✓ ruff / black / oxlint sin errores
== 8. Tests ==                      ✓ 51 de API (pytest) · ✓ 56 de web (Vitest)
Resultado: Todo en verde.
```

## 2. Determinismo del seed

`python3 scripts/seed.py` corrido dos veces seguidas: dump completo de las tablas `users` y `reports` **idéntico byte a byte** entre corridas (incluyendo `foto_url`, `creado_en` y `resuelto_en` — todos explícitos). Funciona sin red: la especie "otro" (loro, id 9) y cualquier descarga fallida caen a placeholder SVG local.

## 3. Recorrido manual en navegador real (Chrome)

Con `bash dev.sh` levantado, flujo completo sin errores de consola:

1. **`/`** — landing con eyebrow del sismo, H1, 2 CTAs gigantes (danger/forest), accesos a listado/mapa, franja "2 reencuentros logrados" con mini-galería de fotos reales.
2. **Gate de registro** — click en "Perdí a mi mascota" sin usuario → redirige a `/registro?volver=/reportar/perdido`; tras registrar a "Javier Vergara" vuelve exactamente al formulario.
3. **Reportar** — formulario de perdido con campos condicionales (nombre visible, situación ausente), pin que arranca en el centro de Armenia y **se mueve al punto exacto del click** en el lienzo; publicado como "Bruno E2E" (id 18) con teléfono 3005551234.
4. **`/reportes`** — la galería muestra las tarjetas con foto/badge/chips/zona/fecha, orden por fecha descendente; Bruno E2E aparece en su posición correcta (10/08).
5. **`/reporte/18`** — badge "Se perdió", pin en la posición del click, botón "Marcar como reunida" visible (soy el autor), href de WhatsApp **exacto**: `https://wa.me/573005551234?text=Hola%2C%20te%20escribo%20desde%20Reencuentro%20por%20tu%20reporte%20de%20Bruno%20E2E...`, y sección **"Posibles coincidencias"** con el perro encontrado de Armenia **"a 4.92 km"** del pin.
6. **Marcar como reunida** — franja de celebración 💚, contacto y coincidencias desaparecen.
7. **`/`** — el contador de la landing subió **2 → 3** en vivo.
8. **`/mapa`** — vista "Todo Colombia" con "15 reportes activos" (16 − Bruno reunido), pins danger/forest con leyenda; el cluster del Eje Cafetero, Bogotá, Cali y Quibdó visibles en sus posiciones.

Al terminar: `python3 scripts/seed.py` (datos limpios) y `data/media/uploads/` sin restos.

## 4. E2E de API en vivo (curl contra uvicorn)

- Upload: PNG → 201 con `foto_url` bajo `/media/uploads/` → GET del `foto_url` → **200 con los mismos bytes** (verificado también por el revisor de la feature 03 tras encontrar y hacer corregir un 404 real).
- Reporte con pin: POST con coords de Cali → persistidas exactas.
- Reunido: 403 no-autor → 200 autor (`resuelto_en` seteado) → 409 repetido → fuera del listado activo → contador `/api/reports/reunidos` 2→3.
- Coincidencias: `GET /api/reports/1/coincidencias` → el par sembrado a 0.6 km, en ambas direcciones.

## 5. Greps de cierre

- `adopta` en código vivo: solo 1 comentario en `ReporteCard.tsx` que documenta la herencia visual desde la rama `adopta-v1` (intencional y permitido por el acceptance).
- `leaflet|mapbox|google.maps|WebSocket`: solo la negación en el comentario de `mapa.ts` ("sin dependencia externa").
- Dependencias nuevas del pivot: **solo `python-multipart`** (requirements.txt).
- Rama `adopta-v1` y tag `adopta-v1.0.0` intactos en `cde337f`.
