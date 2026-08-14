# Integración del módulo de adopción (revivir Adopta dentro de Pet Finder Col)

> Guía para el dev que integre la era **Adopta** (rama `adopta-v1`) en la app actual.
> Léela completa antes de tocar código. Las tareas viven en **`feature_list_adopcion.json`**
> (raíz del repo); este documento explica el contexto, las diferencias de stack y las
> decisiones ya tomadas o pendientes.

## 1. Contexto: qué estás integrando y por qué

Este repo fue primero **Adopta**, una app de adopción de mascotas tipo swipe: 15 features
terminadas, release 1.0.0. Tras el terremoto del Eje Cafetero (2026-08-10) el proyecto
pivotó a **Reencuentro / Pet Finder Col** (mascotas perdidas y encontradas, en producción
en <https://petfinder-col.com>). Todo el trabajo de Adopta quedó **intacto** en la rama
`adopta-v1` (tag `adopta-v1.0.0`, commit `cde337f`). Regla dura: **esa rama nunca se
borra ni se reescribe**.

El caso de uso volvió solo: tras la emergencia hay una ola de animales rescatados que
nadie reclama (el Centro de Bienestar Animal de Cali acumulándolos, avisos de la
Comunidad ofreciendo "hogar de paso **o adoptar**"). La adopción es la fase 2 natural de
Pet Finder Col, y ningún competidor analizado la tiene (docs/product-research.md §6-§10).

## 2. Dónde vive el código viejo y cómo consultarlo

El código de Adopta **no se mergea con git** (el pivot borró y renombró demasiado); se
consulta y se **porta a mano**, adaptándolo. Comandos útiles:

```bash
git show adopta-v1:feature_list.json                 # las 15 features originales
git show adopta-v1:src/api/adopta_api/models/pet.py  # cualquier archivo puntual
git ls-tree -r adopta-v1 --name-only                 # árbol completo
git diff adopta-v1 main -- src/web/src/lib/          # qué cambió en una carpeta
```

Inventario de la rama (lo relevante para la integración):

| Qué | Dónde en `adopta-v1` |
|---|---|
| Modelos | `src/api/adopta_api/models/`: `pet.py`, `shelter.py`, `match.py`, `swipe.py`, `favorite.py`, `sponsorship.py`, `home_profile.py`, `chat.py`, `user.py` |
| Servicios (funciones puras, muy portables) | `src/api/adopta_api/services/`: `affinity.py` (score de compatibilidad), `deck.py` (orden del deck), `filters.py`, `matching.py`, `solicitudes.py` (transiciones de estado), `chat.py` + `chat_manager.py` (WebSockets, **no portable**, ver §4.2) |
| Routers | `src/api/adopta_api/routers/`: `pets`, `swipes`, `matches`, `shelters`, `favorites`, `sponsorships`, `chat` |
| Pantallas React | `src/web/src/screens/`: `Descubrir` (deck swipe), `MascotaDetalle`, `MisMatches`, `SolicitudDetalle`, `Cuestionario`, `MiPerfil`, `PanelRefugio`, `PublicarMascota`, `Favoritos`, `Apadrinar`, `MensajesMatch`/`MensajesSolicitud`, `Mapa`, `LandingPublica` |
| Diseño por pantalla | `design/screens/*.md` (11 pantallas documentadas) |
| ADRs de la era Adopta | `docs/decisions/0001` (stack), `0002` (match NO mutuo), `0003` (afinidad calculada al vuelo), `0004` (chat WebSockets) |
| Tests | `tests/api/` (195 al cierre) y `src/web/src/**/*.test.tsx` (93) — canibalízalos al portar |

## 3. El stack actual (a dónde llega lo que portes)

- **API**: FastAPI + SQLAlchemy en `src/api/reencuentro_api/` (`{models,schemas,services,routers}`), montada como **función serverless en Vercel** (`api/index.py`). En prod la DB es **Supabase Postgres** (pooler :6543) con `SKIP_DB_CREATE_ALL=1`: **ninguna tabla se crea sola en prod**.
- **Web**: React + Vite + TS + Tailwind v4 en `src/web/`. Mapa real con **Leaflet+OSM** (`MapaLienzo`). Fotos vía `FotoUpload` (recorte + compresión en el navegador, hasta 3 fotos con `maxFotos`) → `POST /api/uploads` → **Supabase Storage**.
- **Cuenta liviana** sin contraseña (entrar-o-registrar por email, `lib/session.ts`); contacto directo por **WhatsApp** en toda la app; correos vía **Resend** (ADR 0011, no-op sin credenciales).
- Verificación: `bash init.sh` (lint + pytest + vitest + build) debe quedar **en verde** siempre.

## 4. Diferencias críticas entre Adopta y el stack actual

Estas son las trampas. Cada una ya tiene decisión tomada (✔) o exige un ADR nuevo (⚠).

### 4.1 ✔ `User` es el mismo modelo — no portes `user.py`
El pivot **conservó** el modelo `User` de Adopta campo por campo (nombre, email, ciudad,
barrio, lat/lng, avatar_url, bio). Los usuarios actuales de producción sirven tal cual
como adoptantes. `HomeProfile` (perfil de hogar del cuestionario) se porta tal cual,
colgando de `users`.

### 4.2 ⚠ El chat por WebSockets NO funciona en Vercel serverless
El ADR 0004 eligió WebSockets nativos de FastAPI con un `ConnectionManager` **en memoria
de un solo proceso**. En Vercel cada request es una función efímera: no hay proceso
persistente ni WebSockets. **No portes `chat.py`/`chat_manager.py` sin decidir antes.**
Opciones para el ADR nuevo (en orden de recomendación):
1. **WhatsApp directo** (convención de toda la app actual): la "mensajería" de una
   solicitud es el botón de WhatsApp con mensaje precargado. Cero infraestructura.
2. **Supabase Realtime** sobre una tabla `mensajes` (ya pagamos Supabase; SDK js en el
   front; la API solo escribe filas).
3. Polling sobre una tabla `mensajes` (simple, latencia de segundos).
La recomendación del equipo original es la **1** para el MVP de integración: mantiene la
coherencia de producto (ADR 0005: sin chat interno) y desbloquea todo lo demás.

### 4.3 ✔ `Shelter` ya existe y se llama `Organizacion` — no portes `shelter.py`
La red de apoyo (feature 32) creó `organizaciones` (tipo `fundacion`, `veterinaria`,
`centro_acopio`, `tienda`) con dirección, pin, teléfono y necesidades. Las mascotas en
adopción cuelgan de una organización **o de un usuario rescatista** (`Pet.organizacion_id`
nullable + `Pet.user_id` nullable, exactamente uno presente): en esta emergencia muchos
rescatistas individuales darán en adopción sin ser fundación.

### 4.4 ✔ Fotos: JSON de URLs sirve, el origen cambia
`Pet.fotos` (JSON list de URLs) es compatible: las URLs ahora salen de `POST /api/uploads`
(Supabase Storage). Reutiliza `FotoUpload` con `maxFotos={3}` — ya trae recorte,
compresión y cámara directa. No portes nada de manejo de archivos de Adopta.

### 4.5 ✔ Mapa: Leaflet reemplaza el lienzo CSS
El "mapa" de Adopta (feature 14) era un lienzo CSS propio porque aquella era prohibía
dependencias de red. Hoy `MapaLienzo` es Leaflet real: el mapa de refugios/mascotas se
hace con pins en `MapaLienzo` (ver cómo lo usa `RedDeApoyo.tsx`). No portes `Mapa.tsx`.

### 4.6 ✔ Renombres y convenciones
- Paquete: `adopta_api` → `reencuentro_api` en todo import portado.
- Marca: **Pet Finder Col** (nada de "Adopta" visible al usuario); todo en español.
- Tokens visuales: `design/design-system.md` sigue vigente (Adopta usaba los mismos);
  perdido=`danger`, encontrado/esperanza=`forest`. Sugerencia: adopción=`forest`/`ochre`.
- Rutas nuevas bajo `/adoptar` (la landing y la nav actuales se tocan en la última fase).

### 4.7 ⚠ Toda tabla nueva = migración SQL aditiva en prod ANTES del merge
Regla dura del repo: prod tiene datos reales; `scripts/seed.py` **JAMÁS** contra prod
(hace `drop_all`). El flujo probado: (1) feature aprobada por el revisor en `develop`,
(2) `CREATE TABLE`/`ALTER` aditivo en el SQL Editor de Supabase **con autorización
explícita del dueño** (+ `ENABLE ROW LEVEL SECURITY` en tablas nuevas — la app conecta
como owner y no le afecta; protege de la API REST anon), (3) merge a `main` (auto-deploy).
Tablas que introduce este módulo: `pets`, `home_profiles`, `swipes`, `matches`,
`favorites`, `sponsorships` (y `mensajes` si el ADR de chat elige 2 o 3).

## 5. Decisiones de producto que siguen vigentes (no re-litigar)

- **ADR 0002 — el match NO es mutuo**: un swipe-derecha del adoptante crea la solicitud;
  la organización la gestiona por estados (`solicitado → en_revision → visita_agendada →
  aprobado/descartado`). `services/solicitudes.py` tiene las transiciones y sus tests.
- **ADR 0003 — afinidad calculada al vuelo**: `services/affinity.py` es una función pura
  (HomeProfile vs atributos del Pet) sin persistencia de scores. Portable tal cual, y
  consistente con la filosofía actual ("parecido explicable", feature 38): muestra las
  razones del score en la UI.
- **Cuenta liviana**: nada de contraseñas ni roles formales. "Ser organización" = tener
  una `Organizacion` propia (mismo criterio que el panel de necesidades de la 33).

## 6. Estrategia de integración (resumen de fases)

El detalle con acceptance criteria está en `feature_list_adopcion.json` (ids `AD-01` …
`AD-09`). En una línea cada una:

1. **AD-01** Modelo `Pet` + catálogo `/adoptar` (galería con filtros, sin swipe aún).
2. **AD-02** Publicar en adopción: panel de la organización + rescatista individual +
   puente desde un reporte "encontrado" no reclamado ("darla en adopción").
3. **AD-03** Deck de swipe (`Descubrir`) + afinidad al vuelo + filtros.
4. **AD-04** Perfil de hogar: cuestionario interactivo (`HomeProfile`).
5. **AD-05** Solicitudes: swipe-derecha → solicitud → estados del refugio (match flow).
6. **AD-06** Comunicación de la solicitud (⚠ exige el ADR de chat de §4.2).
7. **AD-07** Favoritos + apadrinamiento (opcionales, cierran la paridad con Adopta 1.0).
8. **AD-08** Integración transversal: nav, landing, og tags de mascota, y el cruce con
   los flujos actuales (encontrados → adopción; Comunidad "quiero adoptar").
9. **AD-09** Migraciones de prod + deploy + verificación (cierra el módulo).

Orden pensado para que **cada fase deje algo usable en producción** (el catálogo solo,
sin swipe, ya tiene valor el primer día).

## 7. Proceso del repo (obligatorio, resumen)

- **Una feature a la vez**: `feature_list.json` admite máximo un item `in_progress` (el
  pre-commit lo valida). `feature_list_adopcion.json` es el **backlog fuente** de este
  módulo: al arrancar una tarea, **cópiala** (edición de texto puntual, nunca
  `json.dump`) a `feature_list.json` con status `in_progress`, y márcala aquí como
  `done` al cerrarla.
- **Ciclo líder→implementador→revisor** (`AGENTS.md`): el revisor corre `bash init.sh`
  de verdad y aprueba o rechaza — nadie se autoaprueba. Cada acceptance necesita un test
  real que lo cubra.
- Estado en disco: `progress/current.md` antes/después de cada paso; `changes.md` por
  cambio con su commit; Conventional Commits; ramas `main` (= producción, auto-deploy)
  y `develop` siempre sincronizadas tras cada cierre.
- Gotchas conocidos (ver `memory/memory.md`): prettier aborta el primer commit
  (re-add + re-commit); black pelea con comentarios intercalados en queries; el WAF de
  Vercel puede dar 403 en uploads por patrón de bytes (recomprimir y reintentar);
  variables de entorno siempre con `.strip()`.

## 8. Cómo levantar todo en local

```bash
bash init.sh   # una vez: venv, seed, lint, tests — debe quedar en verde
bash dev.sh    # API :8000 + web :5173
```

El seed (`scripts/seed.py`) es determinista y **solo local**. Al portar modelos nuevos,
extiéndelo con mascotas en adopción de ejemplo (mira cómo sembraba
`git show adopta-v1:scripts/seed.py`) para que el catálogo y el deck se puedan
desarrollar sin tocar prod.
