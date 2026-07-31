# changes.md — bitácora interna de cambios (append-only)

Cambios importantes con fecha y referencia a commit. Granular y técnico — el `CHANGELOG.md` es la versión curada para release.

## 2026-07-31

- Bootstrap del repo: git init, `.gitignore`, `.env.example`, README, diseño preexistente movido a `design/prototypes/`. (`87e5117`)
- `docs/product-research.md` + `feature_list.json` poblado con 15 features (5 MVP, 2 post-MVP, 8 backlog). (`09701b2`)
- `docs/architecture.md` + ADRs 0001 (stack), 0002 (match no-mutuo), 0003 (afinidad al vuelo). (`8ddf946`)
- `docs/conventions.md` + config de ruff/black/prettier + `.pre-commit-config.yaml`. (`30518da`)
- Sistema de harness engineering: `AGENTS.md`, `CHECKPOINTS.md`, `init.sh` + `scripts/validate_feature_list.py`, `memory/memory.md`, `.claude/agents/*`, `.claude/skills/*`, `.claude/settings.json`.
- `design/design-system.md` + `design/screens/*.md` (11 pantallas formalizadas desde HANDOFF.md).
- Backend del MVP (feature `01-foundations-data`, con `02`/`03`/`04`/`05` implícitas): modelos SQLAlchemy, schemas Pydantic, `services/affinity.py` + `services/matching.py`, routers `pets`/`swipes`/`matches`, `scripts/seed.py` (17 mascotas, 3 refugios, 5 adoptantes, fotos reales descargadas de placedog.net/cataas.com), 9 tests (persistencia + afinidad + endpoints), todos en verde; ruff/black limpios.
- Frontend del MVP: Vite+React+TS+Tailwind v4 (`src/web`), deck de swipe, ficha de mascota, modal de match, mis matches; `dev.sh` (un comando); verificado en navegador real. `init.sh` corregido (detección de scripts npm) y corre completo en verde.
- Revisión independiente (revisor): RECHAZADA la primera pasada — 3 gaps contra `CHECKPOINTS.md` (inserción de mascotas difíciles no implementada, sin test de `GET /api/pets/{id}`, sin test del estado vacío de matches). Corregidos: `services/deck.py` (inserción cada 4-5 tarjetas) + 6 tests nuevos en `tests/api/test_deck.py`, 3 tests nuevos de endpoint, 2 tests nuevos de frontend (`MisMatches.test.tsx`). 18 tests de API + 5 de web, todos en verde.
- Segunda revisión: APROBADA. `01-05` marcadas `done` en `feature_list.json`.
- `docs/verification.md` (Fase 8): evidencia real de `init.sh`, cobertura de tests por feature, verificación manual E2E en navegador.
