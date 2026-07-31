---
name: seed-data
description: Genera datos artificiales deterministas (mascotas, refugios, adoptantes con HomeProfile) y descarga/gestiona fotos de mascotas con fallback offline. Usar cuando haya que crear o regenerar scripts/seed.py o los datos en data/seed/.
---

# seed-data

## Cuándo usar
Al implementar la feature `01-foundations-data`, o cuando cambie el modelo de datos y el seed necesite regenerarse.

## Cómo

1. Los datos van en `scripts/seed.py`, con semilla fija (`SEED_RANDOM_SEED` de `.env`/`.env.example`, default 42) — misma semilla, mismos datos, siempre.
2. Vuelca a `data/app.db` (SQLite) usando los modelos de `src/api/adopta_api/models/` — no dupliques la definición del esquema en el script de seed.
3. Fotos: intenta descargar desde una fuente de placeholders públicos (p. ej. `https://placedog.net`) a `data/seed/images/`. Si falla la descarga (sin red, timeout, error HTTP) **nunca abortes el seed** — genera un placeholder local (imagen simple con el nombre de la mascota, p. ej. con Pillow) y sigue. El seed debe correr igual de bien con o sin red.
4. Registra la fuente y licencia real de las fotos descargadas en `data/seed/CREDITS.md`.
5. Cobertura mínima: ≥15 mascotas variadas (especie, tamaño, edad, energía, necesidades especiales), ≥3 refugios, ≥5 adoptantes con `HomeProfile` sintético que cubra casos de alta y baja afinidad a propósito (para que los tests de `05-affinity-score` tengan casos reales que ejercitar).
6. El script debe ser idempotente: correrlo dos veces no debe duplicar filas (recrear el esquema desde cero en cada corrida es aceptable para datos semilla desechables — ver ADR sobre migraciones en `docs/architecture.md` §6).

## Verificación
`python3 scripts/seed.py` (o `bash init.sh`, que ya lo invoca) debe terminar en 0 sin conexión a internet activa.
