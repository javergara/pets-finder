# Estado vivo — pivot Reencuentro

> Actualizado: 2026-08-12. La era Adopta (15 features done, release 1.0.0) cerró y vive en la rama `adopta-v1` + tag `adopta-v1.0.0` (commit `cde337f`). Este archivo arranca de cero para el pivot.

## Qué está pasando

**Feature activa: `01-pivot-fundaciones` (in_progress).** Pivot del producto a app de reporte de mascotas perdidas/encontradas tras el terremoto del Eje Cafetero (2026-08-10). Plan completo aprobado por el usuario (11 features, ver `feature_list.json` y ADR 0005).

## Decisiones vigentes del pivot (resumen — detalle en ADR 0005)

- Nombre: **Reencuentro**. Contacto directo WhatsApp/tel (sin chat). Registro liviano reutilizado.
- Zonas: Armenia, Pereira, Manizales, Cali, Quibdó, Bogotá + vista "Todo Colombia" (fallback nacional). Fuente de verdad: `services/ciudades.py` (feature 02).
- Un solo modelo `Report` (tipo perdido|encontrado). Upload multipart local (`python-multipart`, única dep nueva).
- `ReporteCard` (feature 05) adapta el JSX de las tarjetas de `adopta-v1` (`git show adopta-v1:src/web/src/components/SwipeCard.tsx`).
- Despliegue (feature 11): Vercel (web) + Render con disco (API).

## Hecho en la feature 01

- [x] Rama `adopta-v1` + tag `adopta-v1.0.0` creados y verificados (`git log adopta-v1 -1` → `cde337f`).
- [x] Borrado masivo del código/tests/diseño de adopción (git rm, ~100 archivos).
- [x] Rename `adopta_api` → `reencuentro_api` (git mv) + adaptación de main/models/schemas/routers/conftest/dev.sh.
- [x] Frontend mínimo: `App.tsx` nuevo (nav Reencuentro), `LandingEmergencia` v1 (2 CTAs), `Registro` con `?volver=` seguro, session con clave nueva + `hasActiveUser()`, client.ts recortado.
- [x] Seed provisional (5 usuarios, determinista). `data/seed/` → `data/media/{seed,uploads}` + .gitignore.
- [x] `feature_list.json` v2 (11 features), CLAUDE.md, AGENTS.md, CHECKPOINTS.md, README, ADR 0005, adenda ADR 0001, product-research y architecture reescritos, conventions/skills/agents actualizados, CHANGELOG Unreleased 2.0.0.
- [x] Verificación parcial: validate_feature_list OK, seed OK, ruff/black OK, pytest 9/9, oxlint OK, vitest 12/12.

## Próximo paso

1. Corrida completa de `bash init.sh` + revisión del diff.
2. Revisor independiente (agente `reviewer`) corre `init.sh` y aprueba → `01-pivot-fundaciones` a `done`.
3. Commit `feat!: pivot a Reencuentro (fundaciones)` en `develop`.
4. Siguiente: `02-reportes-backend` (líder → plan de pasos aquí).
