---
name: seed-data
description: Genera datos artificiales deterministas (usuarios, reportes de perdidas/encontradas, organizaciones de la red de apoyo y mascotas en adopción) y descarga/gestiona fotos con fallback offline. Usar cuando haya que crear o regenerar scripts/seed.py o los datos en data/media/seed/.
---

# seed-data

## Cuándo usar
Cuando cambie el modelo de datos y el seed necesite regenerarse, o al añadirle una entidad nueva.

⚠️ **Al extender el seed, nunca borres la cobertura que ya existe**: cada bloque de datos está diseñado para alimentar tests y pantallas concretas (ver §"Cobertura mínima"). El seed siembra hoy **cuatro** entidades: `users`, `organizaciones`, `pets` y `reports`, en ese orden de inserción (cada una cuelga de la anterior), con un `flush()` por nivel porque las fotos necesitan el id ya asignado.

## Cómo

1. Los datos van en `scripts/seed.py`, con semilla fija (`RANDOM_SEED = 42`) — misma semilla, mismos datos, siempre.
2. Vuelca a `data/app.db` (SQLite) usando los modelos de `src/api/reencuentro_api/models/` — no dupliques la definición del esquema en el script de seed.
3. Las coordenadas de **reportes, organizaciones y mascotas** se generan dentro del bounding box de su zona **importando `services/ciudades.py`** — una sola fuente de verdad, nunca constantes duplicadas en el seed. El helper `_validar_pin()` aborta con mensaje legible si un pin cae fuera.
4. Fotos: intenta descargar desde placeholders públicos (`https://placedog.net` para perros, `https://cataas.com` para gatos) a `data/media/seed/`. Si falla la descarga (sin red, timeout, error HTTP) **nunca abortes el seed** — genera un placeholder SVG local con el nombre/especie y sigue. El seed debe correr igual de bien con o sin red. El nombre del archivo lleva **prefijo por entidad** (`report_{id}`, `pet_{id}`): al añadir una entidad nueva, pasa su prefijo, no reuses el de otra o las fotos se pisan.
5. Cobertura mínima — **cada punto existe porque un test o una pantalla lo necesita; no lo recortes**:
   - **Reportes (~16-20)**: repartidos en las zonas afectadas (mayoría Eje Cafetero), mezcla de tipos y especies, fechas alrededor del 2026-08-10, **al menos un par perdido↔encontrado diseñado como coincidencia obvia** (misma especie, misma zona, cerca) para las coincidencias y el radar, y 2 en estado `reunido` para la franja de la landing.
   - **Organizaciones (2-3)**: fundaciones/veterinarias colgando de usuarios del seed, con dirección, teléfono y pin — son de quien cuelgan las mascotas en adopción.
   - **Mascotas en adopción (~8)**: mitad de organización y mitad de rescatista individual, **nunca ambos ni ninguno** (lo rechaza el `CheckConstraint` `ck_pets_publicador_exclusivo`); las de rescatista **necesitan `telefono_contacto`** porque el modelo `User` no tiene teléfono. Con al menos una **senior** (`edad_meses > 84`) y una con `tags=["necesita experiencia"]` (alimentan `es_dificil_de_ubicar` del deck), y una en `estado="adoptado"` con su `adoptado_en` (alimenta `GET /api/pets/adopciones` y la franja de celebración).
6. El script debe ser idempotente: recrear el esquema desde cero en cada corrida (`drop_all` + `create_all`) es el mecanismo aceptado (ver skill `db-migrations`). Fija explícitamente las fechas que van a la DB (`publicado_en`, `creado_en`): un `default=datetime.now` rompe el determinismo.

## Verificación
`python3 scripts/seed.py` (o `bash init.sh`, que ya lo invoca) debe terminar en 0 **sin conexión a internet activa**, y dos corridas seguidas deben producir los mismos datos. La prueba fuerte del determinismo es comparar un dump `select *` de **todas** las tablas entre dos corridas, no solo la que acabas de tocar: añadir datos que consuman la secuencia de `random` desplaza en silencio las coordenadas de las entidades ya sembradas.

## Qué no hacer
**`scripts/seed.py` JAMÁS se corre contra producción** — hace `drop_all` y borraría los datos reales. Ni siquiera "para probar" con `DATABASE_URL` apuntando a Supabase (ver `docs/deploy.md` §3 y la skill `db-migrations`).
