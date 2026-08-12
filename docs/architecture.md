# Arquitectura — Reencuentro

> La arquitectura de la era Adopta vive en la rama `adopta-v1`. Este documento describe el estado tras el pivot (ADR 0005).

## 1. Stack

Sin cambios respecto al ADR 0001: **FastAPI + SQLAlchemy + SQLite** (`src/api/reencuentro_api/`), **React + Vite + TypeScript + Tailwind v4** (`src/web/`). Un comando de arranque (`bash dev.sh`), todo reproducible en local sin credenciales de terceros. Única dependencia nueva del pivot: `python-multipart` (upload de fotos).

## 2. Modelo de datos

- **`User`** — quien reporta (dueño o rescatista). Registro liviano sin contraseña; el id vive en localStorage del navegador (`src/web/src/lib/session.ts`).
- **`Report`** — el corazón de la app. Un solo modelo para ambos tipos (`tipo: perdido|encontrado`, ADR 0005 §2): especie, descripción, `foto_url`, zona + `lat`/`lng` (pin), `fecha_evento`, `telefono_contacto`, `estado: activo|reunido`. Campos condicionales: `nombre_mascota` (solo perdido), `situacion: conmigo|vista` (solo encontrado).

Sin migraciones formales: `scripts/seed.py` hace `drop_all` + `create_all` (skill `db-migrations`).

## 3. Servicios (funciones puras, sin I/O)

- `services/geo.py` — distancia haversine entre dos coordenadas.
- `services/ciudades.py` — fuente de verdad de las zonas (bounding box + centro): Armenia, Pereira, Manizales, Cali, Quibdó, Bogotá + `COLOMBIA` (nacional). Duplicada a mano en `src/web/src/lib/ciudades.ts` — mantener en sync.
- `services/coincidencias.py` — ordena candidatos del tipo opuesto por distancia + penalización por diferencia de fechas.

## 4. API

- `POST/GET /api/users`, `GET /api/users/{id}` — registro liviano y perfil.
- `POST/GET /api/reports`, `GET/PUT /api/reports/{id}` — CRUD de reportes con filtros (tipo/especie/zona; `estado=activo` por defecto). Solo el autor (por `user_id`) puede editar.
- `GET /api/reports/reunidos` y `POST /api/reports/{id}/reunido` — la métrica de esperanza. **La ruta literal `reunidos` se registra antes que `/{report_id}`** o queda eclipsada (lección heredada, comentada en `main.py`).
- `GET /api/reports/{id}/coincidencias` — posibles matches del tipo opuesto.
- `POST /api/uploads` — multipart; valida content-type (jpeg/png/webp) y tamaño (≤5 MB), guarda con nombre uuid en `data/media/uploads/`.
- `/media` — estáticos desde `data/media/` (`seed/` regenerable + `uploads/`).

## 5. Frontend

Pantallas: landing de emergencia (`/`), registro, reportar (`/reportar/perdido|encontrado`, un componente con campos condicionales), listado (`/reportes`), detalle (`/reporte/:id`), mapa (`/mapa`), mis reportes (`/mis-reportes`). El mapa es un lienzo CSS/SVG propio que interpola lat/lng en el bounding box de la zona activa (`lib/mapa.ts`), invertible para poner un pin con click. El contacto es directo: `wa.me` + `tel:` (`lib/contacto.ts`), sin chat interno.

## 6. Autenticación y sesión

Igual que en la era Adopta: ninguna real. `localStorage` guarda el `reencuentro_active_user_id`; el backend recibe la identidad como parte del payload/query. Suficiente para el MVP de emergencia; si el proyecto crece, se decide auth real con un ADR nuevo.

## 7. Despliegue (feature 11)

Frontend estático en Vercel; API en un host con disco persistente (Render/Fly.io) porque SQLite + uploads necesitan disco. CORS configurable vía `CORS_ORIGINS`. Guía en `docs/deploy.md`.
