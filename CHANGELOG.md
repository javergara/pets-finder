# Changelog

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y [SemVer](https://semver.org/lang/es/).

## [Unreleased]

Sin cambios pendientes de release.

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
