# CHECKPOINTS.md — qué significa "terminado" (fuente de verdad del revisor)

El revisor no aprueba nada que no cumpla lo de este archivo, con evidencia ejecutable — no basta con que "parezca" correcto.

## Checkpoint global (aplica siempre)

- `bash init.sh` termina en verde: dependencias instaladas, seed corrido, linters sin errores, **todos** los tests pasan, `feature_list.json` válido (máximo 1 `in_progress`, ids únicos, `depends_on` referencian ids existentes).
- Ningún commit incluye `data/app.db`, `.env`, `node_modules/`, `.venv/`, ni fotos de `data/media/`.
- El mensaje del último commit sigue Conventional Commits y describe el porqué, no solo el qué.
- `progress/current.md` refleja el estado real (no quedó una feature "en progreso" sin actualizar tras terminarla).
- La rama `adopta-v1` y el tag `adopta-v1.0.0` siguen existiendo e intactos (nunca se reescriben ni se borran).

## Checkpoint por feature (antes de pasar `status` a `done` en `feature_list.json`)

1. Todos los criterios de `acceptance` de la feature en `feature_list.json` tienen un test que los ejercita, y ese test pasa.
2. El código sigue `docs/conventions.md` (estructura de carpetas, nombres, manejo de errores) — el revisor lo verifica leyendo el diff, no solo corriendo el linter.
3. Si la feature toca una decisión registrada en un ADR (`docs/decisions/`), el código es consistente con esa decisión (p. ej. ninguna feature puede introducir un chat interno o una librería de mapas externa — viola ADR 0005).
4. Hay al menos una entrada nueva en `changes.md` referenciando la feature y el commit.
5. Ninguna otra feature quedó `in_progress` en simultáneo.
6. El implementador no marcó la feature como aprobada — solo el revisor puede pasarla a `done`.
7. Al editar `feature_list.json` para aprobar: **edición de texto puntual, nunca `json.dump`** (reserializa y altera items no tocados) ni comandos git destructivos sobre el archivo (gotcha documentado en `memory/memory.md`).

## Checkpoints específicos del pivot (features 01-11)

- **Sincronía backend↔frontend de zonas**: los bounding boxes de `services/ciudades.py` y `lib/ciudades.ts` deben coincidir (idealmente verificado por test o al menos por revisión de diff).
- **Rutas literales antes que dinámicas**: `/api/reports/reunidos` registrado antes que `/api/reports/{report_id}` (comentado en `main.py`).
- **Dependencias bajo control**: cada dependencia nueva necesita un ADR que la justifique. La lista real vive en `docs/architecture.md` §1 (tabla por paquete, contrastable contra `src/api/requirements.txt` y `src/web/package.json`). Con ADR: `python-multipart` (uploads, ADR 0005), **`psycopg[binary]==3.3.4`** (Postgres — driver **v3**, no `psycopg2`, que no publica wheels para el runtime de Vercel; ADR 0006), `requests` (Supabase Storage + Resend, ADRs 0006 y 0011) y `leaflet` (mapa real OSM, ADR 0008 — que reemplazó la regla anterior de "sin librerías de mapas"). **Sin ADR y por tanto deuda anotada**: `qrcode` (cartel, feature 44) y `react-easy-crop` (recorte de foto, feature 35); `httpx` entró como dependencia de `TestClient`, no de producto. Sigue prohibido sin ADR: chat/WebSockets (ADR 0013 lo cierra a favor de WhatsApp), Google Maps (exige facturación), y cualquier SDK que duplique un flujo ya resuelto con REST.
- **Uploads seguros**: nombre de archivo uuid con extensión derivada del content-type, nunca del filename del cliente.
- **Tono**: nunca lenguaje de fracaso — los estados son "activo" y "reunido".

## Qué NO es un checkpoint válido

- "Los tests deberían pasar" sin haberlos corrido.
- Una feature en `done` sin que el revisor haya corrido `init.sh` en esa sesión.
- Documentación que describe un comportamiento que el código no tiene (revisar código, no solo el docstring/comentario).
