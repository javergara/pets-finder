# Estado actual

**Fase activa:** 8 — Verificación (completa, pendiente checkpoint del usuario)
**Feature en progreso:** ninguna — las 5 features MVP (`01-05`) están `done`

## Hecho en esta fase
- `bash init.sh` corrido de nuevo desde cero (working tree limpio): en verde — deps, seed (3/17/5), ruff/black/oxlint/prettier, 18 tests de API + 5 de web.
- `docs/verification.md`: evidencia real (salida completa de `init.sh`, tabla de cobertura de tests por feature, verificación manual end-to-end en navegador con `dev.sh`, y confirmación de que ADR 0002/0003 y "sin lenguaje de descarte" se cumplen en el código).
- La app se dejó corriendo en local (`bash dev.sh`) a pedido del usuario para que la viera en su navegador; luego se re-corrió el seed para dejar `data/app.db` en el estado limpio.

## Decisiones vigentes (ver plan.md)
- Producto = **Adopta**, es-CO únicamente. Stack: React+Vite+TS+Tailwind (v4) / FastAPI+SQLAlchemy / SQLite local. Match no mutuo (ADR 0002); afinidad al vuelo (ADR 0003).
- Usuario demo: `id=1` (Ana Martínez).

## Próximo paso
Fase 9 — Cierre: `CLAUDE.md`, actualizar `CHANGELOG.md`/`changes.md`/`progress/history.md`/`memory/memory.md`, commit final limpio.
