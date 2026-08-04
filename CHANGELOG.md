# Changelog

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y [SemVer](https://semver.org/lang/es/).

## [Unreleased]

Sin cambios pendientes de release.

## [1.0.0] - 2026-08-04

Backlog completo: las 15 features de `feature_list.json` en `done`. Sesión continua sobre el MVP (`0.1.0`), cerrando post-MVP (`06`-`07`) y todo el backlog (`08`-`15`).

### Added
- **`06-filters`**: filtros de descubrimiento (especie, tamaño, energía, edad, convivencia, distancia) sobre `GET /api/pets`, aplicados al instante; `services/geo.py` (haversine) y `User.lat/lng`.
- **`07-adopter-profile`**: `GET /api/users/{id}` con perfil, resumen de `HomeProfile` y métricas agregadas; pantalla "Mi perfil".
- **`08-onboarding-cuestionario`**: registro liviano sin contraseña, cuestionario de hogar interactivo de 6 pasos (reemplaza el `HomeProfile` sintético), guard `RequiereHomeProfile` que bloquea el deck hasta completarlo.
- **`09-shelter-panel`**: panel del refugio de solo lectura (perfil, métricas, cola de solicitudes con el cuestionario del adoptante adjunto) y publicación de mascotas nuevas.
- **`10-adoption-request-flow`**: acciones del refugio sobre la solicitud (agendar visita, pedir más información, descartar con motivo obligatorio y privado) con una matriz de transiciones de estado validada.
- **`11-chat`**: mensajería en tiempo real adoptante↔refugio por match, sobre WebSockets nativos de FastAPI (ver ADR 0004 — sin migrar a un BaaS externo).
- **`12-sponsorship`**: apadrinamiento de mascotas (niveles de donación, lista de "necesitan apoyo ahora"), sin pasarela de pago real — registro de compromiso en base de datos.
- **`13-favorites`**: guardar mascotas para revisar después sin que cuente como swipe (independiente de `Swipe`/`Match`).
- **`14-shelter-map`**: mapa de refugios con lienzo propio en CSS/SVG (interpolación de `lat`/`lng`), sin tiles externos ni dependencias nuevas.
- **`15-public-landing`**: landing pública de marketing en `/` (reemplaza el redirect a `/descubrir`), con el copy del prototipo original `Adopta Landing.dc.html`.
- ADR 0004 (`docs/decisions/0004-chat-websockets-fastapi.md`): WebSockets sobre FastAPI en vez de un BaaS para el chat en tiempo real.

### Changed
- `UserMetricsOut.apadrinamientos` y `ShelterMetricsOut.apadrinamientos_recaudados_cop` (antes fijos en `0`, features `07`/`09`) ahora reflejan datos reales de `Sponsorship`.
- `App.tsx` reestructurado con un layout `AppLayout` (`Nav`+`Outlet`) para que la landing pública en `/` no muestre la navegación interna de la app.

## [0.1.0] - 2026-07-31

Primer MVP funcional en local, con datos artificiales.

### Added
- Sistema de harness engineering completo: `AGENTS.md`, `CHECKPOINTS.md`, `init.sh`, `.claude/agents` (líder/implementador/revisor/investigador/diseñador), `.claude/skills` (seed-data, db-migrations, run-verification, update-memory, match-scoring), hooks de validación de `feature_list.json` y de formato post-edit.
- Investigación de producto (`docs/product-research.md`) y arquitectura (`docs/architecture.md` + ADRs 0001-0003) a partir del diseño preexistente de Adopta.
- Sistema de diseño formalizado (`design/design-system.md`, `design/screens/*.md`) para las 11 pantallas del producto.
- Backend (FastAPI + SQLAlchemy + SQLite): modelo de datos (`User`, `HomeProfile`, `Shelter`, `Pet`, `Swipe`, `Match`), cálculo de compatibilidad adoptante↔mascota con reglas duras de incompatibilidad, creación de match no-mutuo al hacer like, orden del deck con inserción de mascotas difíciles de ubicar, seed determinista con 17 mascotas/3 refugios/5 adoptantes y descarga de fotos con fallback offline.
- Frontend (React + Vite + TypeScript + Tailwind v4): deck de descubrimiento con gesto de swipe (arrastre + equivalentes de teclado/botón), ficha de mascota, modal de match, listado de matches.
- `dev.sh`: comando único para levantar API + web en local.
- 18 tests de backend (pytest) y 5 de frontend (Vitest + Testing Library), todos en verde. Evidencia completa en `docs/verification.md`.

### Fixed
- Tag inexistente en la config de pre-commit de `mirrors-prettier` (`v3.3.3` → `v3.1.0`).
- Deprecación de `on_event` de FastAPI, migrado a `lifespan`.
- `target-version` de ruff/black desalineado con el intérprete real (3.11 asumido → 3.10 real).
