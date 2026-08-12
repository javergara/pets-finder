# 0005 — Pivot de Adopta a Reencuentro (mascotas perdidas/encontradas post-terremoto)

## Estado
Aceptado.

## Contexto

El 10 de agosto de 2026 un terremoto afectó el Eje Cafetero (Armenia, Pereira, Manizales, con efectos en Cali y Chocó). Miles de mascotas se perdieron o fueron encontradas entre escombros. El dueño del proyecto decidió convertir Adopta (app de adopción tipo swipe, 15 features `done`, release 1.0.0) en **Reencuentro**: una app para que dueños reporten mascotas perdidas y rescatistas reporten mascotas encontradas, y el sistema ayude a reunirlas.

Referentes reales investigados: el mapa colaborativo de Google My Maps del Eje Cafetero, Patitas a Salvo y mascotasporvenezuela.com (terremotos de Venezuela 2026), PawBoost y Love Lost/Petco (EE. UU.). El patrón común: dos entradas ("Perdí" / "Encontré"), reportes geolocalizados con foto, mapa con color por estado, contacto directo, coincidencias sugeridas y "reunido" como métrica de esperanza.

## Decisión

1. **Archivo, no borrado histórico**: todo el trabajo de adopción queda en la rama `adopta-v1` + tag `adopta-v1.0.0` (commit `cde337f`). El working tree de `develop`/`main` se limpia de código de adopción para no confundir a nadie que retome el repo. Nunca se hace force-push ni se borra esa rama.
2. **Un solo modelo `Report`** con `tipo: perdido|encontrado` en vez de dos modelos: los únicos campos asimétricos (`nombre_mascota`, `situacion`) son nullable con validación condicional en el schema. Evita duplicar CRUD, filtros, seed, mapa y tests.
3. **Contacto directo por WhatsApp/teléfono** (`wa.me` + `tel:`), sin chat interno: es lo que usan las plataformas reales de desastre (mínima fricción) y elimina la infraestructura WebSocket (el ADR 0004 de la era Adopta se archiva con la rama).
4. **Se reutiliza el registro liviano** (sin contraseña, id en localStorage): los reportes quedan ligados a `user_id` y solo el autor puede editarlos o marcarlos reunidos. Validación por `user_id` en el payload, consistente con el nivel de auth del MVP (ninguno real).
5. **Zonas con bounding box propio** en `services/ciudades.py` (fuente de verdad, duplicada con comentario de sync en `lib/ciudades.ts`): Armenia, Pereira, Manizales, Cali, Quibdó y Bogotá, más un bounding box nacional ("Todo Colombia") como vista agregada y fallback para reportar desde cualquier lugar del país. El mapa sigue siendo el lienzo CSS/SVG propio, sin tiles externos (misma razón que en la era Adopta: reproducibilidad sin red).
6. **Upload de fotos local**: endpoint multipart que guarda en `data/media/uploads/` con nombre uuid (extensión derivada del content-type, nunca del filename del cliente), servido bajo `/media`. Única dependencia nueva: `python-multipart`.
7. **Sin migración de datos**: SQLite local sin usuarios reales; `scripts/seed.py` hace `drop_all` + `create_all`. La "migración" es correr el seed.
8. **Rename del paquete** `adopta_api` → `reencuentro_api`: tras el borrado quedan pocos archivos vivos y el costo del rename es mínimo ahora; un paquete con nombre mentiroso confunde para siempre.

## Consecuencias

- La app queda enfocada en velocidad de reporte (cero fricción: registro mínimo, formulario corto, foto y pin) — cada paso extra en una emergencia cuesta reportes.
- El despliegue (feature 11) necesita disco persistente para SQLite + uploads: Vercel solo para el frontend estático; la API va a un host con volumen (Render/Fly.io). Si el tráfico crece: Postgres + storage S3-compatible (ADR futuro).
- Para retomar la adopción: `git switch adopta-v1`. Las tarjetas de mascota de esa rama se reutilizan como base visual de `ReporteCard` (`git show adopta-v1:src/web/src/components/SwipeCard.tsx`).
