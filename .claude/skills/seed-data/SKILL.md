---
name: seed-data
description: Genera datos artificiales deterministas (usuarios y reportes de mascotas perdidas/encontradas por zona) y descarga/gestiona fotos con fallback offline. Usar cuando haya que crear o regenerar scripts/seed.py o los datos en data/media/seed/.
---

# seed-data

## Cuándo usar
Al implementar la feature `02-reportes-backend`, o cuando cambie el modelo de datos y el seed necesite regenerarse.

## Cómo

1. Los datos van en `scripts/seed.py`, con semilla fija (`RANDOM_SEED = 42`) — misma semilla, mismos datos, siempre.
2. Vuelca a `data/app.db` (SQLite) usando los modelos de `src/api/reencuentro_api/models/` — no dupliques la definición del esquema en el script de seed.
3. Las coordenadas de los reportes se generan dentro del bounding box de cada zona **importando `services/ciudades.py`** — una sola fuente de verdad, nunca constantes duplicadas en el seed.
4. Fotos: intenta descargar desde placeholders públicos (`https://placedog.net` para perros, `https://cataas.com` para gatos) a `data/media/seed/`. Si falla la descarga (sin red, timeout, error HTTP) **nunca abortes el seed** — genera un placeholder SVG local con el nombre/especie y sigue. El seed debe correr igual de bien con o sin red.
5. Cobertura mínima: ~16 reportes repartidos en las zonas afectadas (mayoría Eje Cafetero), mezcla de tipos (perdido/encontrado) y especies, fechas alrededor del 2026-08-10, **al menos un par perdido↔encontrado diseñado como coincidencia obvia** (misma especie, misma zona, cerca) para demos y tests de la feature 08, y 2 reportes en estado `reunido` para la franja de la landing (feature 09).
6. El script debe ser idempotente: recrear el esquema desde cero en cada corrida (`drop_all` + `create_all`) es el mecanismo aceptado (ver skill `db-migrations`).

## Verificación
`python3 scripts/seed.py` (o `bash init.sh`, que ya lo invoca) debe terminar en 0 sin conexión a internet activa, y dos corridas seguidas deben producir los mismos datos.
